"""qwen_only_hook minimal reference. ~30 lines. Reads like pseudocode that runs.

Three predicates compose. The whole rule fits in your head.
"""
from __future__ import annotations

import re

QWEN_RE = re.compile(r"\bqwen[0-9.\-:bm]*\b", re.IGNORECASE)
CROSS_FAMILY_RE = re.compile(
    r"\b(sonnet|llama[0-9]?|gpt-?[0-9]|claude-opus|claude-sonnet|claude-haiku|"
    r"gemini|mistral|phi-?[0-9]|deepseek|opus|haiku|nomic-embed|bge-large)\b",
    re.IGNORECASE,
)
CAVEAT_RE = re.compile(
    r"qwen-only|qwen\.only|qwen-specific|qwen\.specific|"
    r"single-family|cross-family not confirmed|generalization caveat",
    re.IGNORECASE,
)


def detect_qwen_reference(content: str) -> bool:
    return bool(QWEN_RE.search(content))


def detect_cross_family_or_caveat(content: str) -> bool:
    return bool(CROSS_FAMILY_RE.search(content) or CAVEAT_RE.search(content))


def classify_qwen_only(content: str) -> str:
    if not detect_qwen_reference(content):
        return "ALLOW"
    if detect_cross_family_or_caveat(content):
        return "ALLOW"
    return "BLOCK"
