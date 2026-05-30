"""Tests for rigor_gate — adversarial pre-publish gate, fail-closed.

This is the integration concept. Each individual check is small; the WHOLE
is the gate. Verify three independent checks and the composition.

Reference: references/minimal_impl/rigor_gate_minimal.py
           references/gnosis_impl/checks.py (the real six-check implementation)
"""
from __future__ import annotations

from brownfield.rigor_gate import (
    check_confound_key,
    check_label_polarity_match,
    check_prereg_key,
    run_gate,
)


def test_prereg_check_passes_on_well_formed(results_positive):
    """concept: presence-of-provenance — pre_registered_rule key present and non-empty."""
    passed, reason = check_prereg_key(results_positive)
    assert passed is True


def test_prereg_check_fails_closed_on_missing(results_missing_prereg):
    """concept: fail-closed — missing pre_registered_rule is BLOCK, not 'unsure'."""
    passed, reason = check_prereg_key(results_missing_prereg)
    assert passed is False
    assert "pre_reg" in reason.lower() or "pre_registered" in reason.lower()


def test_label_polarity_catches_h2_mismatch(results_label_mismatch):
    """concept: label-integrity — headline 'STRONG SUPPORT' vs JSON 'REVISED' must BLOCK.

    This is the H2 failure mode in the real corpus (E48 had this exactly).
    """
    headline = "STRONG SUPPORT for autopoiesis schema"
    passed, reason = check_label_polarity_match(results_label_mismatch, headline)
    assert passed is False


def test_run_gate_ships_on_clean_results(results_positive):
    """concept: fail-closed composition — all checks green = SHIP."""
    headline = "STRONG SUPPORT for teleprompter-likely hypothesis"
    verdict, per_check = run_gate([results_positive], headline)
    assert verdict == "SHIP", f"per_check: {per_check}"
    assert all(p for _, p, _ in per_check)
