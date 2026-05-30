"""Tests for pre_reg_lock — anti-tuning via mtime ordering.

The discipline this codifies: a pre-registration is credible iff its mtime
predates the results. The mtime IS the audit anchor.

Reference: references/minimal_impl/pre_reg_lock_minimal.py
           references/gnosis_impl/pre_reg_singularity_T1.json (anti_tuning_attestation field)
"""
from __future__ import annotations

import json
import os
import time

import pytest

from brownfield.pre_reg_lock import (
    attach_prereg_mtime,
    audit_prereg_ordering,
    write_prereg,
)


def test_write_prereg_captures_mtime(tmp_path):
    """concept: write-and-capture-mtime — returned float equals filesystem mtime."""
    spec = {"hypothesis": "X", "falsifier_predicates": ["p<0.05"]}
    prereg_path = tmp_path / "spec.json"
    captured = write_prereg(spec, str(prereg_path))
    assert prereg_path.exists()
    assert abs(captured - os.path.getmtime(prereg_path)) < 0.01
    with prereg_path.open() as f:
        assert json.load(f) == spec


def test_attach_prereg_mtime_writes_provenance(tmp_path, pre_reg_singularity):
    """concept: provenance attachment — pre_reg_path AND pre_reg_mtime appear in results."""
    prereg_path = tmp_path / "spec.json"
    with prereg_path.open("w") as f:
        json.dump(pre_reg_singularity, f)
    results = {"experiment_id": "test", "verdict": "CONFIRMED"}
    enriched = attach_prereg_mtime(results, str(prereg_path))
    assert enriched["pre_reg_path"] == str(prereg_path)
    assert isinstance(enriched["pre_reg_mtime"], (int, float))
    assert enriched["pre_reg_mtime"] == os.path.getmtime(prereg_path)


def test_audit_passes_when_prereg_predates_results(tmp_path):
    """concept: temporal-ordering audit — pre_reg_mtime < results_mtime is the proof."""
    prereg_path = tmp_path / "spec.json"
    results_path = tmp_path / "results.json"
    with prereg_path.open("w") as f:
        json.dump({"hypothesis": "X"}, f)
    prereg_mtime = os.path.getmtime(prereg_path)
    time.sleep(0.05)  # guarantee monotonic ordering
    with results_path.open("w") as f:
        json.dump({"pre_reg_mtime": prereg_mtime, "pre_reg_path": str(prereg_path),
                   "verdict": "CONFIRMED"}, f)
    assert audit_prereg_ordering(
        {"pre_reg_mtime": prereg_mtime, "pre_reg_path": str(prereg_path)},
        str(results_path),
    ) is True


def test_audit_fails_when_results_predate_prereg(tmp_path):
    """concept: anti-tuning failure mode — results older than pre-reg means tuning is possible."""
    results_path = tmp_path / "results.json"
    with results_path.open("w") as f:
        json.dump({"verdict": "CONFIRMED"}, f)
    results_mtime = os.path.getmtime(results_path)
    time.sleep(0.05)
    prereg_path = tmp_path / "spec.json"
    with prereg_path.open("w") as f:
        json.dump({"hypothesis": "X"}, f)
    prereg_mtime = os.path.getmtime(prereg_path)
    # Pre-reg is NEWER than results -> tuning suspicion
    assert audit_prereg_ordering(
        {"pre_reg_mtime": prereg_mtime, "pre_reg_path": str(prereg_path)},
        str(results_path),
    ) is False


def test_audit_raises_on_missing_provenance(tmp_path):
    """concept: fail-closed on missing audit anchor — no mtime means cannot trust."""
    results_path = tmp_path / "r.json"
    results_path.write_text("{}")
    with pytest.raises(ValueError):
        audit_prereg_ordering({}, str(results_path))
