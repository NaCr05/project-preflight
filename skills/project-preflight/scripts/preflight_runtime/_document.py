"""Restricted Markdown/YAML document parsing and rendering."""

from __future__ import annotations

import json
import re
from typing import Any

from ._contract import TOP_LEVEL_ORDER


class ParseError(ValueError):
    """Raised when restricted YAML or the state document cannot be parsed."""


def _parse_scalar(raw: str, line_number: int) -> Any:
    value = raw.strip()
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value.startswith(("\"", "'")):
        if not value.startswith("\""):
            raise ParseError(
                f"line {line_number}: quote strings with double quotes in restricted YAML"
            )
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ParseError(f"line {line_number}: invalid quoted value: {exc.msg}") from exc
        if not isinstance(parsed, str):
            raise ParseError(f"line {line_number}: quoted values must be strings")
        return parsed
    if not value:
        raise ParseError(f"line {line_number}: missing scalar value")
    if value[0] in "[{&*!>|":
        raise ParseError(f"line {line_number}: unsupported YAML construct")
    return value


def parse_restricted_yaml(lines: list[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_map: str | None = None
    for index, line in enumerate(lines, start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line:
            raise ParseError(f"line {index}: tabs are not allowed")
        if line.startswith("  "):
            if line.startswith("    ") or current_map is None:
                raise ParseError(f"line {index}: only one two-space mapping level is allowed")
            entry = line[2:]
            if ":" not in entry:
                raise ParseError(f"line {index}: expected key: value")
            key, raw = entry.split(":", 1)
            key = key.strip()
            if not key or key in data[current_map]:
                raise ParseError(f"line {index}: empty or duplicate nested key")
            data[current_map][key] = _parse_scalar(raw, index)
            continue
        if line.startswith(" "):
            raise ParseError(f"line {index}: top-level keys must not be indented")
        if ":" not in line:
            raise ParseError(f"line {index}: expected key: value")
        key, raw = line.split(":", 1)
        key = key.strip()
        if not key or key in data:
            raise ParseError(f"line {index}: empty or duplicate top-level key")
        if raw.strip():
            data[key] = _parse_scalar(raw, index)
            current_map = None
        else:
            data[key] = {}
            current_map = key
    return data


def split_state(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ParseError("state file must begin with YAML frontmatter delimiter ---")
    try:
        closing = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise ParseError("state file is missing the closing frontmatter delimiter ---") from exc
    return parse_restricted_yaml(lines[1:closing]), "\n".join(lines[closing + 1 :]).strip()


def _render_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    raise TypeError(f"unsupported restricted YAML value: {type(value).__name__}")


def render_state(data: dict[str, Any], body: str) -> str:
    lines = ["---"]
    emitted: set[str] = set()
    for key in TOP_LEVEL_ORDER:
        if key not in data:
            continue
        emitted.add(key)
        value = data[key]
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for nested_key, nested_value in value.items():
                lines.append(f"  {nested_key}: {_render_scalar(nested_value)}")
        else:
            lines.append(f"{key}: {_render_scalar(value)}")
    for key in sorted(data.keys() - emitted):
        value = data[key]
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for nested_key, nested_value in value.items():
                lines.append(f"  {nested_key}: {_render_scalar(nested_value)}")
        else:
            lines.append(f"{key}: {_render_scalar(value)}")
    lines.extend(("---", "", body.strip(), ""))
    return "\n".join(lines)


def section(body: str, heading: str) -> str | None:
    level = len(heading) - len(heading.lstrip("#"))
    pattern = re.compile(
        rf"(?ms)^{re.escape(heading)}[ \t]*\n(.*?)(?=^#{{1,{level}}} |\Z)"
    )
    match = pattern.search(body)
    return match.group(1).strip() if match else None


def replace_section(body: str, heading: str, content: str) -> str:
    level = len(heading) - len(heading.lstrip("#"))
    pattern = re.compile(
        rf"(?ms)^{re.escape(heading)}[ \t]*\n.*?(?=^#{{1,{level}}} |\Z)"
    )
    replacement = f"{heading}\n\n{content.strip()}\n\n"
    if not pattern.search(body):
        raise ParseError(f"missing Markdown heading: {heading}")
    return pattern.sub(lambda _: replacement, body, count=1).rstrip()


def anchors(body: str) -> set[str]:
    found: set[str] = set()
    for line in body.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        label = match.group(1).strip().lower()
        label = re.sub(r"[^\w\- ]", "", label, flags=re.UNICODE)
        label = re.sub(r"[\s\-]+", "-", label).strip("-")
        found.add(label)
    return found
