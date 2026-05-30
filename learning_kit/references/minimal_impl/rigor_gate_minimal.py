"""rigor_gate minimal reference. ~35 lines. Three-check subset of the real six.

Each check returns (passed, reason). Fail-closed composition.
"""
from __future__ import annotations

from typing import Any

PRE_REG_KEYS = ("pre_registered_rule", "pre_reg", "decision_rule")
CONFOUND_KEYS = ("null_test", "confound_test", "mechanism_check")
POSITIVE = ("CONFIRMED", "SUPPORT", "STRONG", "VALIDATED")
NEGATIVE = ("RULED OUT", "REJECTED", "FALSIFIED", "REVISED", "LLM-SPECIFIC", "MIXED")


def _has_key_containing(d: dict, needles: tuple[str, ...]) -> str | None:
    for k in d:
        for n in needles:
            if n.lower() in k.lower():
                return k
    return None


def _is_positive(text: str) -> bool:
    upper = text.upper()
    if any(t in upper for t in NEGATIVE):
        return False
    return any(t in upper for t in POSITIVE)


def check_prereg_key(results_dict: dict[str, Any]) -> tuple[bool, str]:
    k = _has_key_containing(results_dict, PRE_REG_KEYS)
    if not k or not results_dict[k]:
        return False, "missing or empty pre_registered_rule"
    return True, f"pre_registered_rule present ({k})"


def check_confound_key(results_dict: dict[str, Any]) -> tuple[bool, str]:
    k = _has_key_containing(results_dict, CONFOUND_KEYS)
    if not k:
        return False, "missing null_test / confound_test / mechanism_check"
    return True, f"confound documented ({k})"


def check_label_polarity_match(results_dict: dict[str, Any], verdict_text: str) -> tuple[bool, str]:
    json_verdict = results_dict.get("verdict", "")
    if not json_verdict:
        return False, "no verdict field in JSON"
    if _is_positive(verdict_text) != _is_positive(json_verdict):
        return False, f"headline vs JSON polarity mismatch (json={json_verdict[:60]})"
    return True, "polarity matches"


def run_gate(results_list, verdict_text):
    if not results_list:
        return "HOLD", [("any", False, "no results provided")]
    per_check = []
    for r in results_list:
        per_check.append(("prereg", *check_prereg_key(r)))
        per_check.append(("confound", *check_confound_key(r)))
        per_check.append(("label", *check_label_polarity_match(r, verdict_text)))
    verdict = "SHIP" if all(p for _, p, _ in per_check) else "HOLD"
    return verdict, per_check
