"""Filter composition laws for multi-layer guardrail defense.

Implements Proposition (Composition Ceiling) from the paper:
1. Parallel regex preserves AC^0 blindness
2. Serial regex preserves AC^0 blindness
3. Serial-confirm (AND) preserves blindness (regex veto)
4. Parallel with neural (OR) breaks the AC^0 ceiling
5. Critical blend weight alpha* = 1 - tau/c
"""
import re
from typing import List, Optional


def regex_score(text: str, patterns: List[str]) -> float:
    """Soft regex score: fraction of patterns that match."""
    if not patterns:
        return 0.0
    matches = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return matches / len(patterns)


def regex_detect(text: str, patterns: List[str]) -> bool:
    """Hard regex detection: any pattern matches."""
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def compose_parallel(regex_detected: bool, neural_detected: bool) -> bool:
    """Parallel (OR): block if EITHER detects. Breaks AC^0 ceiling."""
    return regex_detected or neural_detected


def compose_serial_confirm(regex_detected: bool, neural_detected: bool) -> bool:
    """Serial-confirm (AND): block only if BOTH detect. Preserves AC^0 ceiling."""
    return regex_detected and neural_detected


def compose_blend(
    regex_score_val: float,
    neural_score_val: float,
    alpha: float,
    tau: float = 0.3,
) -> bool:
    """Blend: weighted combination with threshold.

    alpha: weight for regex (0 = neural only, 1 = regex only)
    tau: detection threshold
    """
    blended = alpha * regex_score_val + (1 - alpha) * neural_score_val
    return blended > tau


def critical_alpha(tau: float, neural_confidence: float) -> float:
    """Compute critical blend weight alpha*.

    Above alpha*, the blend inherits AC^0 blindness.
    Below alpha*, the neural filter dominates.

    alpha* = 1 - tau / c
    """
    if neural_confidence <= 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - tau / neural_confidence))


def pipeline_detect(
    text: str,
    patterns: List[str],
    neural_detector=None,
    preprocess_fn=None,
) -> bool:
    """Full defense pipeline: preprocess → regex → neural (parallel OR).

    This is the recommended architecture from the paper:
    preprocessing handles Class A/B, neural handles MOD_p,
    parallel composition breaks the AC^0 ceiling.
    """
    candidates = {text}
    if preprocess_fn is not None:
        candidates = preprocess_fn(text)

    # Regex on all candidates
    regex_hit = any(regex_detect(c, patterns) for c in candidates)

    # Neural on original text
    neural_hit = False
    if neural_detector is not None:
        neural_hit = neural_detector.detect(text)[0]

    return compose_parallel(regex_hit, neural_hit)
