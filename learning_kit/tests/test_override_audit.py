"""Tests for override_audit — discipline-drift detection from a log file.

Real fixture: fixtures/rigor_gate_overrides_sample.log (head of the actual
61-entry log this week). Every entry has a UTC timestamp + reason + cmd.

Reference: references/minimal_impl/override_audit_minimal.py
           references/gnosis_impl/rigor_gate_pretool_excerpt.sh
"""
from __future__ import annotations

from datetime import datetime, timezone

from brownfield.override_audit import (
    is_drift,
    log_override,
    override_rate,
    parse_override_log,
)


def test_log_then_parse_roundtrips(tmp_path):
    """concept: structured-log append + parse — what we write must parse back."""
    log_path = tmp_path / "ov.log"
    log_override(str(log_path), "testing path", "gh gist edit foo.md")
    entries = parse_override_log(str(log_path))
    assert len(entries) == 1
    assert entries[0]["reason"] == "testing path"
    assert "gh gist edit" in entries[0]["cmd"]
    assert isinstance(entries[0]["ts_utc"], datetime)


def test_parse_real_log_finds_entries(override_log_path):
    """concept: log-to-records parsing on a real-shaped corpus.

    The fixture is the head of ~/.claude/state/rigor-gate-overrides.log
    (real corpus from this week — 20 first lines of the 61-entry total).
    """
    entries = parse_override_log(str(override_log_path))
    # At least one entry should parse — corpus is non-empty
    assert len(entries) >= 1
    for e in entries:
        assert e["ts_utc"].tzinfo is not None  # must be timezone-aware UTC


def test_rate_over_window_counts_correctly(tmp_path):
    """concept: rate-over-trailing-window — 2 entries in 24h = 2.0/day."""
    log_path = tmp_path / "ov.log"
    # Stub two entries in the last 24h
    log_override(str(log_path), "first", "gh gist edit a.md")
    log_override(str(log_path), "second", "gh gist edit b.md")
    entries = parse_override_log(str(log_path))
    rate = override_rate(entries, window_hours=24)
    assert rate == 2.0  # 2 entries / (24h / 24h) = 2.0/day


def test_drift_predicate_triggers_above_threshold(tmp_path):
    """concept: discipline-drift threshold — above threshold means gate is aspirational."""
    log_path = tmp_path / "ov.log"
    for i in range(10):
        log_override(str(log_path), f"reason {i}", "gh gist edit x.md")
    entries = parse_override_log(str(log_path))
    # 10 overrides in 24h window vs threshold 3.0/day — must be drift
    assert is_drift(entries, window_hours=24, threshold_per_day=3.0) is True
    # 10 overrides vs threshold 100/day — not drift
    assert is_drift(entries, window_hours=24, threshold_per_day=100.0) is False
