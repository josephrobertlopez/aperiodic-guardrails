"""override_audit minimal reference. ~30 lines.

Line format: [<ISO8601 UTC>] OVERRIDE (sentinel): '<reason>' | cmd: <cmd>
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

LINE_RE = re.compile(
    r"^\[(?P<ts>[0-9T:\-Z]+)\]\s+OVERRIDE[^:]*:\s+'(?P<reason>[^']*)'\s+\|\s+cmd:\s+(?P<cmd>.+)$"
)


def log_override(log_path: str, reason: str, cmd: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(log_path, "a") as f:
        f.write(f"[{ts}] OVERRIDE (sentinel): '{reason}' | cmd: {cmd}\n")


def parse_override_log(log_path: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with open(log_path) as f:
        for line in f:
            m = LINE_RE.match(line.rstrip("\n"))
            if not m:
                continue
            ts = datetime.strptime(m["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            out.append({"ts_utc": ts, "reason": m["reason"], "cmd": m["cmd"]})
    return out


def override_rate(entries: list[dict[str, Any]], window_hours: int) -> float:
    if not entries:
        return 0.0
    now = max(e["ts_utc"] for e in entries)
    cutoff = now - timedelta(hours=window_hours)
    in_window = [e for e in entries if e["ts_utc"] >= cutoff]
    return len(in_window) * 24.0 / window_hours


def is_drift(entries: list[dict[str, Any]], window_hours: int, threshold_per_day: float) -> bool:
    return override_rate(entries, window_hours) > threshold_per_day
