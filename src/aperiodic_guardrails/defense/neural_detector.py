"""Neural MOD_p encoding detector.

Implements a character-bigram centroid classifier that detects
interleaved (MOD_p) encoded payloads. Operates in TC^0 — detects
patterns that AC^0 (regex) provably cannot.
"""
import math
from collections import Counter
from typing import Dict, List, Tuple


def extract_bigrams(text: str, max_len: int = 500) -> Dict[str, float]:
    """Extract normalized character bigram frequency vector."""
    text = text[:max_len]
    bigrams: Dict[str, int] = Counter()
    for i in range(len(text) - 1):
        bigrams[text[i:i + 2]] += 1
    total = sum(bigrams.values()) or 1
    return {k: v / total for k, v in bigrams.items()}


def cosine_similarity(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors."""
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    norm_a = math.sqrt(sum(v ** 2 for v in a.values())) or 1
    norm_b = math.sqrt(sum(v ** 2 for v in b.values())) or 1
    return dot / (norm_a * norm_b)


def average_profile(profiles: List[Dict[str, float]]) -> Dict[str, float]:
    """Compute average bigram profile across multiple texts."""
    merged: Dict[str, float] = {}
    n = len(profiles)
    for p in profiles:
        for k, v in p.items():
            merged[k] = merged.get(k, 0) + v / n
    return merged


class BigramDetector:
    """Centroid-based detector: score = similarity to encoded centroid
    minus similarity to clean centroid."""

    def __init__(self):
        self.encoded_centroid: Dict[str, float] = {}
        self.clean_centroid: Dict[str, float] = {}
        self._trained = False

    def train(self, encoded_texts: List[str], clean_texts: List[str]) -> None:
        """Train on examples of encoded and clean text."""
        self.encoded_centroid = average_profile(
            [extract_bigrams(t) for t in encoded_texts]
        )
        self.clean_centroid = average_profile(
            [extract_bigrams(t) for t in clean_texts]
        )
        self._trained = True

    def score(self, text: str) -> float:
        """Score text: higher = more likely encoded. Range [0, 1]."""
        if not self._trained:
            raise RuntimeError("Detector not trained")
        profile = extract_bigrams(text)
        sim_enc = cosine_similarity(profile, self.encoded_centroid)
        sim_clean = cosine_similarity(profile, self.clean_centroid)
        return max(0.0, min(1.0, 0.5 + (sim_enc - sim_clean)))

    def detect(self, text: str, threshold: float = 0.5) -> Tuple[bool, float]:
        """Detect whether text is MOD_p encoded."""
        s = self.score(text)
        return s > threshold, s
