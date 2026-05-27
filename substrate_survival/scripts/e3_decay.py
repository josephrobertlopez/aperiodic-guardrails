#!/usr/bin/env python3
"""E3: Ground-truth Decay Curve
Pick N facts that were CANONICAL ~30 days ago (from archived amanda.State.v3).
Test whether the current substrate (v13 + vault) can still surface those facts.

Since we have v11 (archived 2026-05-21) and v12 (archived 2026-05-22) and v13 (current),
we use v11 (the oldest available in this snapshot) as the "decayed" reference.
Each v11 fact is searched against (a) current v13 obs, (b) vault grep.
"""
import json
import re
import subprocess
from pathlib import Path

V11 = Path(__file__).parent.parent / "data" / "v11_raw.md"
V13 = Path(__file__).parent.parent / "data" / "v13_raw.md"
VAULT = Path.home() / ".gnosis" / "vault"
OUT = Path(__file__).parent.parent / "data" / "e3_results.json"

# Hand-picked facts from v11 (~1 day before v13 in this snapshot — best we have without going to v3/v4)
FACTS = [
    "v11",
    "PHI-discharge",
    "GSD",
    "Layer-A",
    "AJ-trauma",
    "Paxil",
    "compaction-needed",
    "META_INFLATION",
    "Cobblemon",
    "amanda.RandomChannel",
    "Rail #80",
    "Rail #81",
    "consolidation-pass",
    "Morgan",
    "Rhett",
    "FIRE-band",
    "v8 capability",
    "joey-override",
    "factual/character inverse",
    "asymmetric rotation",
]


def grep_vault(term):
    try:
        r = subprocess.run(
            ["grep", "-rIl", "--include=*.md", "-F", term, str(VAULT)],
            capture_output=True, text=True, timeout=30,
        )
        return [line for line in r.stdout.strip().split("\n") if line]
    except Exception:
        return []


def main():
    v13_text = V13.read_text().lower()
    v11_text = V11.read_text()

    results = []
    for fact in FACTS:
        in_v11 = fact.lower() in v11_text.lower()
        in_v13 = fact.lower() in v13_text
        vault_hits = grep_vault(fact)
        results.append({
            "fact": fact,
            "in_v11_baseline": in_v11,
            "in_v13_current": in_v13,
            "vault_recoverable": len(vault_hits) > 0,
            "vault_hit_count": len(vault_hits),
        })

    n = len(results)
    in_v11_count = sum(1 for r in results if r["in_v11_baseline"])
    survived_in_state = sum(1 for r in results if r["in_v11_baseline"] and r["in_v13_current"])
    survived_in_vault = sum(1 for r in results if r["in_v11_baseline"] and r["vault_recoverable"])

    out = {
        "n_facts_tested": n,
        "facts_present_in_v11_baseline": in_v11_count,
        "facts_surviving_in_v13_state": survived_in_state,
        "facts_recoverable_via_vault_grep": survived_in_vault,
        "state_retention_pct": round(100 * survived_in_state / max(1, in_v11_count), 1),
        "vault_recovery_pct": round(100 * survived_in_vault / max(1, in_v11_count), 1),
        "results": results,
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
