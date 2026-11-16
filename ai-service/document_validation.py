"""Shared, conservative validation for discharge-summary extraction."""
from __future__ import annotations

import re
from typing import Any

PLACEHOLDER_RE = re.compile(r"\[[^\[\]]*\]")
SPACE_RE = re.compile(r"\s+")


def normalize_text(value: Any) -> str:
    return SPACE_RE.sub(" ", str(value or "")).strip()


def normalized_analysis_text(text: str) -> str:
    """Remove bracketed template fields/examples while preserving line breaks."""
    cleaned = PLACEHOLDER_RE.sub(" ", str(text or ""))
    return "\n".join(SPACE_RE.sub(" ", line).strip() for line in cleaned.splitlines() if line.strip())


def clean_string(value: Any) -> str:
    return normalize_text(value) if isinstance(value, str) else ""


def source_is_supported(source: str, document_text: str) -> bool:
    quote = normalize_text(source).casefold()
    clean_doc = normalize_text(normalized_analysis_text(document_text)).casefold()
    return bool(quote and clean_doc and quote in clean_doc)


def is_blank_or_placeholder(value: str) -> bool:
    value = normalize_text(value).casefold()
    if not value:
        return True
    return value in {"not found", "unknown", "none", "null", "n/a", "na", "-", "—", "tbd", "to be confirmed", "example", "placeholder", "condition / procedure"} or bool(
        re.fullmatch(r"(?:e\.g\.|example text|placeholder text|medication\s*\d+)", value)
    )


def has_template_markers(text: str) -> bool:
    raw = str(text or "")
    patterns = (
        r"\[\s*e\.g\.", r"\[\s*example\b", r"\[\s*condition\s*/\s*procedure\s*\]",
        r"\[\s*medication\s*\d+\b", r"\[\s*specialty\s*/", r"\[\s*1\s*[–-]\s*2\s*sentences?\b",
    )
    return any(re.search(p, raw, re.IGNORECASE) for p in patterns)


def template_confirmation_messages(text: str) -> list[str]:
    raw = str(text or "")
    checks = (
        (r"\[\s*condition\s*/\s*procedure\s*\]", "Primary diagnosis is not filled in."),
        (r"\[\s*medication\s*\d+\b", "Medication details are not filled in."),
        (r"\[\s*e\.g\.", "The document contains example instructions rather than confirmed patient instructions."),
        (r"\[\s*specialty\s*/", "Follow-up provider details require confirmation."),
        (r"\[\s*\d{1,2}/\d{1,2}/\d{2,4}", "Follow-up appointment date and time require confirmation."),
        (r"\[\s*1\s*[–-]\s*2\s*sentences?", "Discharge treatment summary is not filled in."),
    )
    return list(dict.fromkeys(msg for pattern, msg in checks if re.search(pattern, raw, re.IGNORECASE)))


def has_valid_12_hour_times(text: str) -> bool:
    times = re.findall(r"\b(\d{1,2}):(\d{2})\s*(AM|PM)\b", str(text or ""), re.IGNORECASE)
    return all(1 <= int(h) <= 12 and 0 <= int(m) <= 59 for h, m, _ in times)


def contains_date(text: str) -> bool:
    return bool(re.search(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b", text or ""))


def contains_time(text: str) -> bool:
    return bool(re.search(r"\b\d{1,2}:\d{2}\s*(?:AM|PM)\b", text or "", re.IGNORECASE))
