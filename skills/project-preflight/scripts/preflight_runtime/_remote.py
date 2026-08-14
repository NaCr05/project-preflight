"""Bounded, redirect-aware remote fetching for Artifact Evidence adapters."""

from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
import urllib.parse
from dataclasses import dataclass, field
from typing import Callable, Mapping


DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_BYTES = 1_048_576
DEFAULT_MAX_REDIRECTS = 3
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
SENSITIVE_HEADERS = frozenset({"authorization", "cookie", "proxy-authorization"})


class RemoteFetchError(OSError):
    """A remote request was unsafe, invalid, or unsuccessful."""


@dataclass(frozen=True)
class RemoteRequest:
    url: str
    headers: Mapping[str, str] = field(default_factory=dict)
    allowed_content_types: tuple[str, ...] = ()
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_bytes: int = DEFAULT_MAX_BYTES
    max_redirects: int = DEFAULT_MAX_REDIRECTS


@dataclass(frozen=True)
class RemoteResponse:
    status: int
    url: str
    headers: Mapping[str, str]
    body: bytes


@dataclass(frozen=True)
class TransportResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


class RemoteTransport:
    """Transport Interface at the true external network Seam."""

    def request(
        self,
        *,
        scheme: str,
        host: str,
        port: int,
        address: str,
        target: str,
        headers: Mapping[str, str],
        timeout_seconds: float,
        max_bytes: int,
    ) -> TransportResponse:
        raise NotImplementedError


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host: str, port: int, address: str, timeout: float) -> None:
        super().__init__(host, port, timeout=timeout)
        self._address = address

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self._address, self.port), self.timeout, self.source_address
        )


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, port: int, address: str, timeout: float) -> None:
        super().__init__(host, port, timeout=timeout, context=ssl.create_default_context())
        self._address = address

    def connect(self) -> None:
        raw_socket = socket.create_connection(
            (self._address, self.port), self.timeout, self.source_address
        )
        self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)


class SocketRemoteTransport(RemoteTransport):
    """Production Adapter that connects to the exact address approved by the policy Module."""

    def request(
        self,
        *,
        scheme: str,
        host: str,
        port: int,
        address: str,
        target: str,
        headers: Mapping[str, str],
        timeout_seconds: float,
        max_bytes: int,
    ) -> TransportResponse:
        connection_type = _PinnedHTTPSConnection if scheme == "https" else _PinnedHTTPConnection
        connection = connection_type(host, port, address, timeout_seconds)
        try:
            connection.request("GET", target, headers=dict(headers))
            response = connection.getresponse()
            response_headers = {key.casefold(): value for key, value in response.getheaders()}
            declared_length = response_headers.get("content-length")
            if declared_length is not None:
                try:
                    if int(declared_length) > max_bytes:
                        raise RemoteFetchError(
                            f"remote response exceeds the {max_bytes}-byte limit"
                        )
                except ValueError as exc:
                    raise RemoteFetchError("remote response has an invalid Content-Length") from exc
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise RemoteFetchError(f"remote response exceeds the {max_bytes}-byte limit")
            return TransportResponse(response.status, response_headers, body)
        except (OSError, http.client.HTTPException) as exc:
            if isinstance(exc, RemoteFetchError):
                raise
            raise RemoteFetchError(f"remote request failed: {exc}") from exc
        finally:
            connection.close()


Resolver = Callable[..., list[tuple[object, object, object, object, tuple[object, ...]]]]


class SafeRemoteFetcher:
    """Small Interface hiding DNS, redirect, credential, timeout, and size policy."""

    def __init__(
        self,
        transport: RemoteTransport | None = None,
        resolver: Resolver | None = None,
    ) -> None:
        self._transport = transport or SocketRemoteTransport()
        self._resolver = resolver or socket.getaddrinfo

    def fetch(self, request: RemoteRequest) -> RemoteResponse:
        if request.timeout_seconds <= 0:
            raise RemoteFetchError("remote timeout must be positive")
        if request.max_bytes <= 0:
            raise RemoteFetchError("remote response-size limit must be positive")
        if request.max_redirects < 0:
            raise RemoteFetchError("remote redirect limit cannot be negative")

        headers = self._validated_headers(request.headers)
        current_url = request.url
        previous_origin: tuple[str, str, int] | None = None

        for redirect_count in range(request.max_redirects + 1):
            parsed, origin, address, target = self._validated_target(current_url)
            if previous_origin is not None and origin != previous_origin:
                headers = {
                    key: value
                    for key, value in headers.items()
                    if key.casefold() not in SENSITIVE_HEADERS
                }
            headers["Host"] = self._host_header(parsed)

            response = self._transport.request(
                scheme=parsed.scheme,
                host=parsed.hostname or "",
                port=origin[2],
                address=address,
                target=target,
                headers=headers,
                timeout_seconds=request.timeout_seconds,
                max_bytes=request.max_bytes,
            )
            normalized_headers = {
                key.casefold(): value for key, value in response.headers.items()
            }
            if len(response.body) > request.max_bytes:
                raise RemoteFetchError(
                    f"remote response exceeds the {request.max_bytes}-byte limit"
                )
            if response.status in REDIRECT_STATUSES:
                location = normalized_headers.get("location")
                if not location:
                    raise RemoteFetchError("remote redirect is missing a Location header")
                if redirect_count >= request.max_redirects:
                    raise RemoteFetchError(
                        f"remote request exceeded {request.max_redirects} redirects"
                    )
                previous_origin = origin
                current_url = urllib.parse.urljoin(current_url, location)
                continue
            if not 200 <= response.status < 300:
                raise RemoteFetchError(f"remote URL returned unexpected HTTP {response.status}")
            self._check_content_type(normalized_headers, request.allowed_content_types)
            return RemoteResponse(
                response.status,
                current_url,
                normalized_headers,
                response.body,
            )
        raise AssertionError("redirect loop must return or raise")

    def _validated_target(
        self, url: str
    ) -> tuple[urllib.parse.ParseResult, tuple[str, str, int], str, str]:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise RemoteFetchError("remote URL must use HTTP(S) and include a hostname")
        if parsed.username is not None or parsed.password is not None:
            raise RemoteFetchError("remote URL must not contain user credentials")
        host = parsed.hostname
        if host.casefold() == "localhost" or host.casefold().endswith(".local"):
            raise RemoteFetchError("remote checking refuses localhost and local-network hostnames")
        try:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
        except ValueError as exc:
            raise RemoteFetchError("remote URL has an invalid port") from exc
        addresses = self._public_addresses(host, port)
        target = urllib.parse.urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
        return parsed, (parsed.scheme, host.casefold(), port), addresses[0], target

    def _public_addresses(self, host: str, port: int) -> tuple[str, ...]:
        try:
            literal = ipaddress.ip_address(host)
        except ValueError:
            try:
                resolved = {
                    str(item[4][0])
                    for item in self._resolver(host, port, type=socket.SOCK_STREAM)
                }
            except OSError as exc:
                raise RemoteFetchError(f"remote hostname cannot be resolved safely: {exc}") from exc
            if not resolved:
                raise RemoteFetchError("remote hostname resolved to no addresses")
            addresses = tuple(sorted(resolved))
        else:
            addresses = (str(literal),)
        if any(not ipaddress.ip_address(address).is_global for address in addresses):
            if len(addresses) == 1 and addresses[0] == host:
                raise RemoteFetchError("remote checking refuses non-public IP addresses")
            raise RemoteFetchError(
                "remote checking refuses hostnames that resolve to non-public addresses"
            )
        return addresses

    @staticmethod
    def _validated_headers(headers: Mapping[str, str]) -> dict[str, str]:
        validated: dict[str, str] = {}
        for key, value in headers.items():
            if not key or any(character in key for character in "\r\n:"):
                raise RemoteFetchError("remote request contains an invalid header name")
            if "\r" in value or "\n" in value:
                raise RemoteFetchError("remote request contains an invalid header value")
            if key.casefold() == "host":
                continue
            validated[key] = value
        return validated

    @staticmethod
    def _host_header(parsed: urllib.parse.ParseResult) -> str:
        host = parsed.hostname or ""
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        default_port = 443 if parsed.scheme == "https" else 80
        return host if parsed.port in {None, default_port} else f"{host}:{parsed.port}"

    @staticmethod
    def _check_content_type(
        headers: Mapping[str, str], allowed_content_types: tuple[str, ...]
    ) -> None:
        if not allowed_content_types:
            return
        observed = headers.get("content-type", "").split(";", 1)[0].strip().casefold()
        allowed = {item.casefold() for item in allowed_content_types}
        if observed not in allowed:
            raise RemoteFetchError(
                f"remote response Content-Type {observed or 'missing'} is not allowed"
            )
