"""Artifact Evidence adapters used behind the state lifecycle seam."""

from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ._document import anchors, section


def _public_remote_host(parsed: urllib.parse.ParseResult) -> str | None:
    """Return an actionable error when remote checking could reach a non-public host."""

    host = parsed.hostname
    if not host:
        return "remote URL has no hostname"
    if host.casefold() == "localhost" or host.casefold().endswith(".local"):
        return "remote checking refuses localhost and local-network hostnames"
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        try:
            addresses = {
                item[4][0]
                for item in socket.getaddrinfo(
                    host,
                    parsed.port or (443 if parsed.scheme == "https" else 80),
                    type=socket.SOCK_STREAM,
                )
            }
        except OSError as exc:
            return f"remote hostname cannot be resolved safely: {exc}"
        if not addresses:
            return "remote hostname resolved to no addresses"
        if any(not ipaddress.ip_address(address).is_global for address in addresses):
            return "remote checking refuses hostnames that resolve to non-public addresses"
    else:
        if not literal.is_global:
            return "remote checking refuses non-public IP addresses"
    return None


@dataclass
class EvidenceFindings:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def extend(self, other: "EvidenceFindings") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


class ArtifactAdapter:
    """Internal adapter interface at the Artifact Evidence seam."""

    def matches(self, pointer: str) -> bool:
        raise NotImplementedError

    def check(
        self,
        key: str,
        pointer: str,
        body: str,
        repo_root: Path,
        check_remote: bool,
    ) -> EvidenceFindings:
        raise NotImplementedError


class NotRequiredAdapter(ArtifactAdapter):
    def matches(self, pointer: str) -> bool:
        return pointer == "not-required"

    def check(
        self,
        key: str,
        pointer: str,
        body: str,
        repo_root: Path,
        check_remote: bool,
    ) -> EvidenceFindings:
        findings = EvidenceFindings()
        if key != "decision_map":
            findings.errors.append("not-required is allowed only for decision_map")
        return findings


class InlineAdapter(ArtifactAdapter):
    def matches(self, pointer: str) -> bool:
        return pointer.startswith("inline:#")

    def check(
        self,
        key: str,
        pointer: str,
        body: str,
        repo_root: Path,
        check_remote: bool,
    ) -> EvidenceFindings:
        findings = EvidenceFindings()
        anchor = pointer.removeprefix("inline:#")
        if not anchor or anchor not in anchors(body):
            findings.errors.append(f"artifact {key} points to missing inline anchor: {anchor}")
        if key == "idea":
            idea = section(body, "## Original Idea")
            if not idea or idea.casefold() in {"not captured.", "not captured"}:
                findings.errors.append("inline idea pointer requires captured Original Idea content")
        return findings


class GitHubIssueAdapter(ArtifactAdapter):
    _pattern = re.compile(
        r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/issues/(?P<number>[1-9]\d*)/?(?:#.*)?$"
    )

    def __init__(
        self,
        opener: Callable[..., object] | None = None,
        token_provider: Callable[[], str | None] | None = None,
    ) -> None:
        self._opener = opener or urllib.request.urlopen
        self._token_provider = token_provider or (
            lambda: os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        )

    def matches(self, pointer: str) -> bool:
        parsed = urllib.parse.urlparse(pointer)
        return (
            parsed.scheme in {"http", "https"}
            and parsed.netloc.casefold() == "github.com"
            and "/issues/" in parsed.path
        )

    def check(
        self,
        key: str,
        pointer: str,
        body: str,
        repo_root: Path,
        check_remote: bool,
    ) -> EvidenceFindings:
        findings = EvidenceFindings()
        match = self._pattern.fullmatch(pointer)
        if not match:
            findings.warnings.append(
                f"artifact {key} is a GitHub URL but not a supported GitHub Issue pointer; semantic evidence was not checked"
            )
            return findings
        if not check_remote:
            findings.warnings.append(
                f"artifact {key} GitHub Issue syntax is valid but remote accessibility was not checked"
            )
            return findings

        api_url = (
            "https://api.github.com/repos/"
            f"{match.group('owner')}/{match.group('repo')}/issues/{match.group('number')}"
        )
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "project-preflight-validator",
        }
        token = self._token_provider()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(api_url, headers=headers)
        try:
            with self._opener(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, UnicodeError, ValueError, urllib.error.HTTPError) as exc:
            findings.errors.append(f"artifact {key} GitHub Issue is not accessible: {exc}")
            return findings
        if not isinstance(payload, dict) or not payload.get("html_url") or not payload.get("title"):
            findings.errors.append(f"artifact {key} GitHub response is not an Issue record")
        return findings


class RemoteUrlAdapter(ArtifactAdapter):
    def __init__(self, opener: Callable[..., object] | None = None) -> None:
        self._opener = opener or urllib.request.urlopen

    def matches(self, pointer: str) -> bool:
        return pointer.startswith(("http://", "https://"))

    def check(
        self,
        key: str,
        pointer: str,
        body: str,
        repo_root: Path,
        check_remote: bool,
    ) -> EvidenceFindings:
        findings = EvidenceFindings()
        parsed = urllib.parse.urlparse(pointer)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            findings.errors.append(f"artifact {key} is not a valid HTTP(S) URL")
            return findings
        if not check_remote:
            findings.warnings.append(
                f"artifact {key} uses a generic remote URL; accessibility and semantic sufficiency were not checked"
            )
            return findings
        host_error = _public_remote_host(parsed)
        if host_error:
            findings.errors.append(f"artifact {key}: {host_error}")
            return findings
        request = urllib.request.Request(
            pointer,
            headers={"User-Agent": "project-preflight-validator"},
            method="GET",
        )
        try:
            with self._opener(request, timeout=10) as response:
                status = getattr(response, "status", 200)
                if status >= 400:
                    findings.errors.append(f"artifact {key} remote URL returned HTTP {status}")
        except (OSError, urllib.error.HTTPError) as exc:
            findings.errors.append(f"artifact {key} remote URL is not accessible: {exc}")
        findings.warnings.append(
            f"artifact {key} remote URL accessibility does not prove semantic Gate sufficiency"
        )
        return findings


class LocalPathAdapter(ArtifactAdapter):
    def matches(self, pointer: str) -> bool:
        return True

    def check(
        self,
        key: str,
        pointer: str,
        body: str,
        repo_root: Path,
        check_remote: bool,
    ) -> EvidenceFindings:
        findings = EvidenceFindings()
        path_text, separator, anchor = pointer.partition("#")
        if not path_text:
            findings.errors.append(f"artifact {key}: local pointer has no path before its anchor")
            return findings
        if Path(path_text).is_absolute() or re.match(r"^[A-Za-z]:[\\/]", path_text):
            findings.errors.append(
                f"artifact {key}: artifact pointers must be repository-relative, not absolute"
            )
            return findings
        root = repo_root.resolve()
        candidate = (root / path_text).resolve()
        if candidate != root and root not in candidate.parents:
            findings.errors.append(f"artifact {key}: artifact pointer escapes the repository root")
            return findings
        if not candidate.exists():
            findings.errors.append(f"artifact {key} points to missing local target: {pointer}")
            return findings
        if separator and anchor:
            if not candidate.is_file():
                findings.errors.append(f"artifact {key} local anchor requires a file target: {pointer}")
            else:
                try:
                    target_body = candidate.read_text(encoding="utf-8")
                except (OSError, UnicodeError) as exc:
                    findings.errors.append(f"artifact {key} local target cannot be read: {exc}")
                else:
                    if anchor not in anchors(target_body):
                        findings.errors.append(
                            f"artifact {key} points to missing local anchor: {pointer}"
                        )
        return findings


class ArtifactEvidenceChecker:
    """Select concrete adapters while keeping pointer behavior behind one seam."""

    def __init__(self, adapters: tuple[ArtifactAdapter, ...] | None = None) -> None:
        self._adapters = adapters or (
            NotRequiredAdapter(),
            InlineAdapter(),
            GitHubIssueAdapter(),
            RemoteUrlAdapter(),
            LocalPathAdapter(),
        )

    def check(
        self,
        key: str,
        pointer: str,
        body: str,
        repo_root: Path,
        check_remote: bool = False,
    ) -> EvidenceFindings:
        for adapter in self._adapters:
            if adapter.matches(pointer):
                return adapter.check(key, pointer, body, repo_root, check_remote)
        raise AssertionError("LocalPathAdapter must terminate the adapter chain")
