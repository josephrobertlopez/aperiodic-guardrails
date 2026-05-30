"""Tests for retire_audit — anti-resurrection window + unlock conditions.

Hardest module. The discipline is: once retired with a falsifier-met record,
a schema cannot reappear in active state during the V2-verifier window
unless a NEW locked falsifier is registered. Nostalgia is not enough.

Reference: references/minimal_impl/retire_audit_minimal.py
           references/gnosis_impl/retire_audit_e48_ledger.json (real ledger)
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from brownfield.retire_audit import (
    audit_active_set,
    can_resurrect,
    is_resurrection_blocked,
    retire_schema,
)


def test_retire_moves_schema_and_opens_window(retire_ledger):
    """concept: retirement-as-state-transition — active -> retired with armed window."""
    now = datetime(2026, 5, 30, tzinfo=timezone.utc)
    # Singularity-BS-T1 is currently active in the ledger
    new_ledger = retire_schema(
        retire_ledger,
        schema_id="Singularity-BS-T1",
        retire_reason="empirical falsification example",
        falsifier_met="cross-family negative result",
        armed_days=14,
        now_ts=now,
    )
    active_ids = [s["schema_id"] for s in new_ledger["active_schemas"]]
    retired_ids = [s["schema_id"] for s in new_ledger["retired_schemas"]]
    assert "Singularity-BS-T1" not in active_ids
    assert "Singularity-BS-T1" in retired_ids


def test_resurrection_blocked_during_window(retire_ledger):
    """concept: anti-resurrection temporal invariant — open window means blocked.

    E48-autopoiesis has v2_verifier_armed_until = 2026-06-12. At 2026-05-30,
    the window is OPEN, so resurrection is blocked.
    """
    inside_window = datetime(2026, 5, 30, tzinfo=timezone.utc)
    assert is_resurrection_blocked(retire_ledger, "E48-autopoiesis", inside_window) is True

    outside_window = datetime(2026, 7, 1, tzinfo=timezone.utc)
    assert is_resurrection_blocked(retire_ledger, "E48-autopoiesis", outside_window) is False


def test_nostalgia_does_not_unlock(retire_ledger):
    """concept: unlock-condition predicate — 'I liked auto-whats-it' is NOT enough.

    The real corpus: Joey said 'I liked the idea of auto-whats-it' for E48.
    Amanda classified that as feature-grief, not evidence. This test encodes
    that classifier: a falsifier text must mention 'falsifier', 'criterion',
    or 'predicate' to count as real evidence.
    """
    inside_window = datetime(2026, 5, 30, tzinfo=timezone.utc)
    nostalgia = "I liked auto-whats-it"
    assert can_resurrect(retire_ledger, "E48-autopoiesis", inside_window, nostalgia) is False

    real_falsifier = "new locked falsifier: p<0.05 on cross-family N=20 batch"
    assert can_resurrect(retire_ledger, "E48-autopoiesis", inside_window, real_falsifier) is True
