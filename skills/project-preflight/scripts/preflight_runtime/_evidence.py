"""Artifact Evidence adapters used behind the state lifecycle seam."""

from __future__ import annotations

import json
import os
import re
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ._document import anchors, section
from ._remote import RemoteFetchError, RemoteRequest, SafeRemoteFetcher


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
        fetcher: SafeRemoteFetcher | None = None,
        token_provider: Callable[[], str | None] | None = None,
    ) -> None:
        self._fetcher = fetcher or SafeRemoteFetcher()
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
        try:
            response = self._fetcher.fetch(
                RemoteRequest(
                    api_url,
                    headers=headers,
                    allowed_content_types=("application/json",),
                )
            )
            payload = json.loads(response.body.decode("utf-8"))
        except (RemoteFetchError, UnicodeError, ValueError) as exc:
            findings.errors.append(f"artifact {key} GitHub Issue is not accessible: {exc}")
            return findings
        if not isinstance(payload, dict) or not payload.get("html_url") or not payload.get("title"):
            findings.errors.append(f"artifact {key} GitHub response is not an Issue record")
        return findings


class RemoteUrlAdapter(ArtifactAdapter):
    def __init__(self, fetcher: SafeRemoteFetcher | None = None) -> None:
        self._fetcher = fetcher or SafeRemoteFetcher()

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
        try:
            self._fetcher.fetch(
                RemoteRequest(
                    pointer,
                    headers={"User-Agent": "project-preflight-validator"},
                    max_bytes=65_536,
                )
            )
        except RemoteFetchError as exc:
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

    def __init__(
        self,
        adapters: tuple[ArtifactAdapter, ...] | None = None,
        remote_fetcher: SafeRemoteFetcher | None = None,
    ) -> None:
        if adapters is not None and remote_fetcher is not None:
            raise ValueError("provide adapters or remote_fetcher, not both")
        fetcher = remote_fetcher or SafeRemoteFetcher()
        self._adapters = adapters or (
            NotRequiredAdapter(),
            InlineAdapter(),
            GitHubIssueAdapter(fetcher),
            RemoteUrlAdapter(fetcher),
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
