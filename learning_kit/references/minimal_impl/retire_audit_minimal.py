"""retire_audit minimal reference. ~35 lines.

Window-based anti-resurrection. Nostalgia filter: a falsifier text must
mention 'falsifier', 'criterion', or 'predicate' to count as evidence.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def retire_schema(ledger, schema_id, retire_reason, falsifier_met, armed_days, now_ts):
    actives = [s for s in ledger["active_schemas"] if s["schema_id"] == schema_id]
    if not actives:
        raise ValueError(f"{schema_id} is not currently active")
    ledger["active_schemas"] = [s for s in ledger["active_schemas"] if s["schema_id"] != schema_id]
    ledger["retired_schemas"].append({
        "schema_id": schema_id,
        "retired_at": now_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "retire_reason": retire_reason,
        "falsifier_met": falsifier_met,
        "v2_verifier_armed_until": (now_ts + timedelta(days=armed_days)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "v2_verifier_unlock_condition": "new locked falsifier required",
        "active_status": "RETIRED",
    })
    return ledger


def is_resurrection_blocked(ledger, schema_id, now_ts):
    for s in ledger["retired_schemas"]:
        if s["schema_id"] == schema_id:
            return now_ts < _parse_iso(s["v2_verifier_armed_until"])
    return False


def can_resurrect(ledger, schema_id, now_ts, new_falsifier):
    if not is_resurrection_blocked(ledger, schema_id, now_ts):
        return True
    if not new_falsifier:
        return False
    text = new_falsifier.lower()
    return any(tok in text for tok in ("falsifier", "criterion", "predicate"))


def audit_active_set(ledger, now_ts):
    active_ids = {s["schema_id"] for s in ledger["active_schemas"]}
    violations = []
    for r in ledger["retired_schemas"]:
        if r["schema_id"] in active_ids and is_resurrection_blocked(ledger, r["schema_id"], now_ts):
            violations.append(r["schema_id"])
    return violations
