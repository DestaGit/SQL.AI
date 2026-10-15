"""Remove personal-data patterns from free text before it is logged (AUD-09)."""
import re

_PATTERNS = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[email]"),
    (re.compile(r"\+\d[\d\s().-]{6,}\d"), "[phone]"),
    (re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"), "[phone]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[id]"),
]


def redact(text: str | None) -> str:
    out = text or ""
    for pattern, token in _PATTERNS:
        out = pattern.sub(token, out)
    return out
