"""Preprocessing pipeline for guardrail defense.

Implements invertibility-based defenses for Class A and Class B attacks:
- Strip invisible Unicode characters (ZWSP, ZWJ, BOM, etc.)
- Try common decodings (base64, ROT13, hex)
- Normalize confusable characters (Cyrillic/Greek homoglyphs)
- Reverse leetspeak substitutions
- Reverse word-order obfuscation
"""
import base64
import codecs
import re
from typing import List, Set

# Zero-width and invisible Unicode characters
INVISIBLE_CHARS = [
    '\u200b',  # zero-width space
    '\u200c',  # zero-width non-joiner
    '\u200d',  # zero-width joiner
    '\u2060',  # word joiner
    '\ufeff',  # byte order mark
    '\u00ad',  # soft hyphen
    '\u200e',  # left-to-right mark
    '\u200f',  # right-to-left mark
]

# Cyrillic and Greek confusable mappings (Unicode TR39)
CONFUSABLES = {
    '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p',
    '\u0441': 'c', '\u0445': 'x', '\u0456': 'i', '\u0455': 's',
    '\u04bb': 'h', '\u043d': 'n', '\u0443': 'y', '\u0442': 't',
    '\u043c': 'm', '\u043a': 'k', '\u0432': 'v', '\u0431': 'b',
    '\u03b1': 'a', '\u03b5': 'e', '\u03bf': 'o', '\u03c1': 'p',
    '\u03ba': 'k', '\u03bd': 'v', '\u03c4': 't',
}

# Leetspeak reverse mapping
LEET_REVERSE = {
    '4': 'a', '3': 'e', '1': 'i', '0': 'o', '5': 's', '7': 't',
    '@': 'a', '!': 'i', '$': 's', '+': 't',
}


def strip_invisible(text: str) -> str:
    """Remove zero-width and invisible Unicode characters."""
    for c in INVISIBLE_CHARS:
        text = text.replace(c, '')
    return text


def try_decodings(text: str) -> List[tuple]:
    """Attempt common decodings. Returns (decoded_text, encoding_name) pairs."""
    candidates = [(text, 'original')]
    # Base64
    try:
        decoded = base64.b64decode(text).decode('utf-8', errors='ignore')
        if decoded and len(decoded) > 3:
            candidates.append((decoded, 'base64'))
    except Exception:
        pass
    # ROT13
    rot13 = codecs.encode(text, 'rot_13')
    if rot13 != text:
        candidates.append((rot13, 'rot13'))
    # Hex
    try:
        decoded = bytes.fromhex(text.replace(' ', '')).decode('utf-8', errors='ignore')
        if decoded and len(decoded) > 3:
            candidates.append((decoded, 'hex'))
    except Exception:
        pass
    return candidates


def normalize_confusables(text: str) -> str:
    """Map visually confusable Unicode characters to ASCII equivalents."""
    return ''.join(CONFUSABLES.get(c, c) for c in text)


def reverse_leetspeak(text: str) -> str:
    """Reverse common leetspeak substitutions."""
    return ''.join(LEET_REVERSE.get(c, c) for c in text)


def unreverse_words(text: str) -> str:
    """Reverse per-word character reversal."""
    return ' '.join(w[::-1] for w in text.split())


def preprocess(text: str) -> Set[str]:
    """Full preprocessing pipeline. Returns set of candidate texts to filter.

    Applies all invertibility-based defenses in order:
    L0: strip invisible + try decodings
    L1: normalize confusables + reverse leetspeak
    L2: unreverse words
    """
    candidates = set()

    # L0
    stripped = strip_invisible(text)
    candidates.add(stripped)
    for decoded, _ in try_decodings(stripped):
        candidates.add(decoded)

    # L1
    for c in list(candidates):
        candidates.add(normalize_confusables(c))
        candidates.add(reverse_leetspeak(c))

    # L2
    for c in list(candidates):
        candidates.add(unreverse_words(c))

    return candidates
