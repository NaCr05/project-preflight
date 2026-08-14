from __future__ import annotations

import socket
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skills" / "project-preflight" / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from preflight_runtime._remote import (  # noqa: E402
    RemoteFetchError,
    RemoteRequest,
    RemoteTransport,
    SafeRemoteFetcher,
    TransportResponse,
)


PUBLIC_IP = "93.184.216.34"


def resolver_for(addresses):
    def resolve(host, port, **kwargs):
        address = addresses[host] if isinstance(addresses, dict) else addresses
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]

    return resolve


class FakeTransport(RemoteTransport):
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


class SafeRemoteFetcherTests(unittest.TestCase):
    def test_fetch_pins_the_approved_public_address(self):
        transport = FakeTransport([TransportResponse(200, {}, b"ok")])
        fetcher = SafeRemoteFetcher(transport, resolver_for(PUBLIC_IP))

        response = fetcher.fetch(RemoteRequest("https://example.com/evidence"))

        self.assertEqual(b"ok", response.body)
        self.assertEqual(PUBLIC_IP, transport.calls[0]["address"])
        self.assertEqual("example.com", transport.calls[0]["headers"]["Host"])

    def test_timeout_is_required_and_forwarded_to_the_transport(self):
        transport = FakeTransport([TransportResponse(200, {}, b"ok")])
        fetcher = SafeRemoteFetcher(transport, resolver_for(PUBLIC_IP))

        fetcher.fetch(RemoteRequest("https://example.com", timeout_seconds=2.5))

        self.assertEqual(2.5, transport.calls[0]["timeout_seconds"])
        with self.assertRaisesRegex(RemoteFetchError, "timeout must be positive"):
            fetcher.fetch(RemoteRequest("https://example.com", timeout_seconds=0))

    def test_redirect_target_is_revalidated_before_a_second_request(self):
        transport = FakeTransport(
            [TransportResponse(302, {"location": "http://127.0.0.1/private"}, b"")]
        )
        fetcher = SafeRemoteFetcher(transport, resolver_for(PUBLIC_IP))

        with self.assertRaisesRegex(RemoteFetchError, "non-public IP"):
            fetcher.fetch(RemoteRequest("https://example.com/start"))

        self.assertEqual(1, len(transport.calls))

    def test_cross_origin_redirect_strips_credentials(self):
        transport = FakeTransport(
            [
                TransportResponse(302, {"location": "https://files.example/result"}, b""),
                TransportResponse(200, {}, b"ok"),
            ]
        )
        fetcher = SafeRemoteFetcher(
            transport,
            resolver_for({"api.example": PUBLIC_IP, "files.example": "8.8.8.8"}),
        )

        fetcher.fetch(
            RemoteRequest(
                "https://api.example/start",
                headers={"Authorization": "Bearer secret", "Accept": "application/json"},
            )
        )

        self.assertIn("Authorization", transport.calls[0]["headers"])
        self.assertNotIn("Authorization", transport.calls[1]["headers"])
        self.assertEqual("application/json", transport.calls[1]["headers"]["Accept"])

    def test_response_size_is_enforced_at_the_module_interface(self):
        transport = FakeTransport([TransportResponse(200, {}, b"12345")])
        fetcher = SafeRemoteFetcher(transport, resolver_for(PUBLIC_IP))

        with self.assertRaisesRegex(RemoteFetchError, "4-byte limit"):
            fetcher.fetch(RemoteRequest("https://example.com", max_bytes=4))

    def test_redirect_limit_and_content_type_are_enforced(self):
        transport = FakeTransport(
            [TransportResponse(302, {"location": "/again"}, b"")]
        )
        fetcher = SafeRemoteFetcher(transport, resolver_for(PUBLIC_IP))
        with self.assertRaisesRegex(RemoteFetchError, "exceeded 0 redirects"):
            fetcher.fetch(RemoteRequest("https://example.com", max_redirects=0))

        transport = FakeTransport(
            [TransportResponse(200, {"content-type": "text/html"}, b"not json")]
        )
        fetcher = SafeRemoteFetcher(transport, resolver_for(PUBLIC_IP))
        with self.assertRaisesRegex(RemoteFetchError, "Content-Type text/html"):
            fetcher.fetch(
                RemoteRequest(
                    "https://example.com",
                    allowed_content_types=("application/json",),
                )
            )

        transport = FakeTransport([TransportResponse(304, {}, b"")])
        fetcher = SafeRemoteFetcher(transport, resolver_for(PUBLIC_IP))
        with self.assertRaisesRegex(RemoteFetchError, "unexpected HTTP 304"):
            fetcher.fetch(RemoteRequest("https://example.com"))

    def test_private_dns_answer_and_header_injection_are_rejected(self):
        transport = FakeTransport([])
        fetcher = SafeRemoteFetcher(transport, resolver_for("10.0.0.8"))
        with self.assertRaisesRegex(RemoteFetchError, "non-public addresses"):
            fetcher.fetch(RemoteRequest("https://example.com"))
        self.assertEqual([], transport.calls)

        fetcher = SafeRemoteFetcher(FakeTransport([]), resolver_for(PUBLIC_IP))
        with self.assertRaisesRegex(RemoteFetchError, "invalid header value"):
            fetcher.fetch(
                RemoteRequest("https://example.com", headers={"X-Test": "ok\r\nInjected: yes"})
            )


if __name__ == "__main__":
    unittest.main()
