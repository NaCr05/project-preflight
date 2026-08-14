"""Locale-aware user-visible messages for orchestration directives."""

from __future__ import annotations

from typing import Mapping


DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ("en", "zh-CN")
_ALIASES = {
    "en": "en",
    "en-us": "en",
    "en-gb": "en",
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "zh-hans": "zh-CN",
}
_MESSAGES: Mapping[str, Mapping[str, str]] = {
    "en": {
        "idea": "Project Preflight · Idea — Capturing your rough idea. One paragraph is enough.",
        "ready": "Project Preflight · Ready — All four Gates passed. Preparing the implementation handoff.",
        "blocked": "Project Preflight · {stage} — The `{skill}` stage adapter is unavailable.",
        "running": (
            "Project Preflight · {stage} — Using `{skill}` "
            "(bundled Project Preflight adapter). Just answer or confirm."
        ),
    },
    "zh-CN": {
        "idea": "Project Preflight · Idea — 正在记录你的初步想法。你只需用一段话描述它。",
        "ready": "Project Preflight · Ready — 四道 Gate 已通过，正在整理实施交接。",
        "blocked": "Project Preflight · {stage} — `{skill}` 阶段适配器当前不可用。",
        "running": (
            "Project Preflight · {stage} — 正在使用 `{skill}`"
            "（Project Preflight 内置适配器）。你只需回答或确认。"
        ),
    },
}


def normalize_locale(locale: str | None) -> str:
    if locale is None:
        return DEFAULT_LOCALE
    normalized = _ALIASES.get(locale.strip().casefold())
    if normalized is None:
        raise ValueError(f"unsupported locale {locale!r}; choose one of: {', '.join(SUPPORTED_LOCALES)}")
    return normalized


def message(locale: str | None, key: str, **values: str) -> str:
    selected = normalize_locale(locale)
    try:
        template = _MESSAGES[selected][key]
    except KeyError as exc:
        raise ValueError(f"unknown orchestration message: {key}") from exc
    return template.format(**values)
