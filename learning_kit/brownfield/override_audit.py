"""override_audit — log-based discipline drift detection.

Concept: every time a gate is overridden, log it as a structured line. The
audit is a rate computation: if override_rate exceeds a threshold over a
time window, the gate has become aspirational (overridden more than enforced)
and a process review is triggered.

Real source: ~/.claude/state/rigor-gate-overrides.log — 61 entries over the
research-arc, each with a UTC timestamp + reason + originating command.

You implement:
    1. log_override(log_path, reason, cmd) -> None
    2. parse_override_log(log_path) -> list[dict]
    3. override_rate(entries, window_hours) -> float
    4. is_drift(entries, window_hours, threshold_per_day) -> bool
"""
from __future__ import annotations

from typing import Any


def log_override(log_path: str, reason: str, cmd: str) -> None:
    """Append a single override entry to `log_path`.

    Concept: structured-log append. Line format:
        [<UTC ISO8601>] OVERRIDE (sentinel): '<reason>' | cmd: <cmd>
    The timestamp must be a parseable UTC ISO8601 with trailing Z.
    """
    raise NotImplementedError("concept: structured-log append")


def parse_override_log(log_path: str) -> list[dict[str, Any]]:
    """Parse the override log into a list of dicts.

    Concept: log-to-records lift. Each returned dict has keys:
        'ts_utc' (datetime), 'reason' (str), 'cmd' (str)
    Lines that don't match the format are skipped (be tolerant of multi-line
    reasons — only well-formed single-line entries count).
    """
    raise NotImplementedError("concept: log-to-records parsing")


def override_rate(
    entries: list[dict[str, Any]],
    window_hours: int,
) -> float:
    """Return overrides per 24h, averaged over the trailing `window_hours`.

    Concept: rate-over-window. If no entries fall in the window, return 0.0.
    Use the most-recent entry's timestamp as 'now' (so the function is
    pure — no wall-clock dependency).
    """
    raise NotImplementedError("concept: rate-over-trailing-window")


def is_drift(
    entries: list[dict[str, Any]],
    window_hours: int,
    threshold_per_day: float,
) -> bool:
    """Return True iff override_rate over the window exceeds the threshold.

    Concept: discipline-drift predicate. True means the gate is being
    overridden more often than the threshold allows; this is the signal to
    review the gate's design (the rule itself, not the overrider's intent).
    """
    raise NotImplementedError("concept: discipline-drift threshold check")
