"""rigor_gate — adversarial pre-publish gate, fail-closed by default.

Concept: a composition of N independent checks against a results JSON +
draft verdict text. Each check returns (passed: bool, reason: str). The
verdict is SHIP iff ALL checks pass; HOLD otherwise. Crucially, if a check
CANNOT be evaluated (missing key, parse error, ambiguous input), it returns
False — fail-closed on uncheckable conditions.

Real source: ~/.claude/skills/rigor-gate/checks.py (six-check implementation).
This kit uses a minimal three-check subset: pre-registration present,
confound key present, label-polarity match.

You implement:
    1. check_prereg_key(results_dict)            -> (bool, str)
    2. check_confound_key(results_dict)          -> (bool, str)
    3. check_label_polarity_match(results_dict, verdict_text) -> (bool, str)
    4. run_gate(results_list, verdict_text)      -> (str, list[tuple])

    where run_gate returns ('SHIP'|'HOLD', per-check results).
"""
from __future__ import annotations

from typing import Any


def check_prereg_key(results_dict: dict[str, Any]) -> tuple[bool, str]:
    """Return (passed, reason). Pass iff results_dict has a non-empty
    'pre_registered_rule' (or close variant) key.

    Concept: presence-of-provenance check. Fail-closed: missing key is BLOCK,
    not 'unsure'.
    """
    raise NotImplementedError("concept: presence-of-provenance check")


def check_confound_key(results_dict: dict[str, Any]) -> tuple[bool, str]:
    """Return (passed, reason). Pass iff results_dict documents a
    null/confound/mechanism check (key name containing one of those tokens).

    Concept: alternative-explanation gate. Fail-closed.
    """
    raise NotImplementedError("concept: alternative-explanation gate")


def check_label_polarity_match(
    results_dict: dict[str, Any],
    verdict_text: str,
) -> tuple[bool, str]:
    """Return (passed, reason). Pass iff the headline verdict_text's polarity
    (positive/negative) matches the polarity of the JSON's 'verdict' field.

    Concept: label-integrity check. Catches the H2-classic failure where a
    headline says 'STRONG SUPPORT' while the JSON verdict says 'REVISED' or
    'RULED OUT'. Negative tokens take precedence over positive ones in the
    same string.

    Positive tokens (subset): CONFIRMED, SUPPORT, STRONG, VALIDATED.
    Negative tokens (subset): RULED OUT, REJECTED, FALSIFIED, REVISED,
    LLM-SPECIFIC, MIXED.
    """
    raise NotImplementedError("concept: label-integrity polarity match")


def run_gate(
    results_list: list[dict[str, Any]],
    verdict_text: str,
) -> tuple[str, list[tuple[str, bool, str]]]:
    """Compose all three checks across all results dicts. Return
    ('SHIP' | 'HOLD', [(check_name, passed, reason), ...]).

    Concept: fail-closed composition. SHIP iff every check on every result
    passes. If results_list is empty, return 'HOLD' (cannot check nothing).
    """
    raise NotImplementedError("concept: fail-closed composition")
