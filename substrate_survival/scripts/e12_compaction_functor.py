#!/usr/bin/env python3
"""E12: The Compaction Functor
Tokenize amanda.State.v8 through v13. Classify each token into one of:
  - rail_id   (#42, #19, etc.)
  - date      (2026-05-22, etc.)
  - version   (v8, v13, etc.)
  - numeric   (byte counts, percentages, headroom)
  - name_caps (CamelCase agent/entity names)
  - path      (/home/joey/..., ~/.claude/...)
  - prose     (everything else)

For each of 5 compaction transitions (v8->v9, v9->v10, v10->v11, v11->v12, v12->v13),
measure per-class retention rate.

Pre-registered falsifier:
  H0: All classes retained at same rate (random compaction)
  H1: character-class retention > fact-class retention on N>=3 cycles

Character class = {rail_id, prose-with-keywords-{rail,refuse,must,never,protocol}}
Fact class      = {date, numeric, version, name_caps, path}

Strong support: character > fact on all 5 cycles
Weak support:   character > fact on 3-4 cycles
Refutation:     character <= fact on majority of cycles
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
OUT = Path(__file__).parent.parent / "data" / "e12_results.json"
VERSIONS = ["v8", "v9", "v10", "v11", "v12", "v13"]

TOKEN_PAT = re.compile(r"[a-zA-Z0-9_#\.\-/]+")

CLASS_PATS = [
    ("rail_id", re.compile(r"^#\d+$|^rail[#_-]?\d+$", re.IGNORECASE)),
    ("date", re.compile(r"^2026-\d{2}-\d{2}$|^\d{4}-\d{2}-\d{2}$")),
    ("version", re.compile(r"^v\d+$|^v\d+\.\d+$")),
    ("numeric", re.compile(r"^-?\d{1,}(?:\.\d+)?[kKmMgGbB]?[bB]?$")),
    ("path", re.compile(r"^[~/]|/$|\.(?:py|md|json|sh|jsonl|txt)$|\.claude|\.gnosis")),
    ("name_caps", re.compile(r"^[A-Z][a-zA-Z]{3,}$")),
]

# Character keywords — tokens whose presence in prose indicates operational character
CHAR_KEYWORDS = {
    "rail", "rails", "refuse", "refused", "refusal", "must", "never", "always",
    "protocol", "discipline", "rule", "rules", "mandatory", "forbidden",
    "fire", "warn", "compaction", "compact", "substrate", "hard-gate",
    "ingest", "ingestion", "channel", "tag", "tagged", "verdict",
    "earned", "watch", "standing-watch", "monitor", "fail-closed",
    "fail-open", "override", "sentinel", "humility", "vibed", "anti-vibe",
}


def tokenize(text):
    return [t.lower() for t in TOKEN_PAT.findall(text)]


def classify(tok):
    for name, pat in CLASS_PATS:
        if pat.match(tok):
            return name
    if tok in CHAR_KEYWORDS:
        return "char_keyword"
    return "prose"


def load_version(v):
    path = DATA_DIR / f"{v}_raw.md"
    return path.read_text()


def main():
    # Tokenize each version, get per-token-set per class
    classified = {}
    raw = {}
    for v in VERSIONS:
        text = load_version(v)
        raw[v] = text
        toks = tokenize(text)
        by_class = {}
        for t in toks:
            c = classify(t)
            by_class.setdefault(c, set()).add(t)
        classified[v] = by_class

    # Measure retention per transition
    transitions = []
    for i in range(len(VERSIONS) - 1):
        v_from, v_to = VERSIONS[i], VERSIONS[i + 1]
        row = {"from": v_from, "to": v_to,
               "from_bytes": len(raw[v_from]), "to_bytes": len(raw[v_to]),
               "byte_compression_pct": round(100 * (1 - len(raw[v_to]) / len(raw[v_from])), 2)}
        per_class = {}
        for cls in set(list(classified[v_from].keys()) + list(classified[v_to].keys())):
            from_set = classified[v_from].get(cls, set())
            to_set = classified[v_to].get(cls, set())
            kept = from_set & to_set
            dropped = from_set - to_set
            added = to_set - from_set
            per_class[cls] = {
                "from_n": len(from_set),
                "to_n": len(to_set),
                "kept_n": len(kept),
                "dropped_n": len(dropped),
                "added_n": len(added),
                "retention_pct": round(100 * len(kept) / max(1, len(from_set)), 2),
            }
        row["per_class"] = per_class
        transitions.append(row)

    # Aggregate: character-class vs fact-class retention
    CHAR_CLASSES = {"rail_id", "char_keyword"}
    FACT_CLASSES = {"date", "numeric", "version", "name_caps", "path"}

    cycle_summary = []
    char_wins = 0
    fact_wins = 0
    for t in transitions:
        char_kept = sum(t["per_class"].get(c, {}).get("kept_n", 0) for c in CHAR_CLASSES)
        char_from = sum(t["per_class"].get(c, {}).get("from_n", 0) for c in CHAR_CLASSES)
        fact_kept = sum(t["per_class"].get(c, {}).get("kept_n", 0) for c in FACT_CLASSES)
        fact_from = sum(t["per_class"].get(c, {}).get("from_n", 0) for c in FACT_CLASSES)
        char_pct = round(100 * char_kept / max(1, char_from), 2)
        fact_pct = round(100 * fact_kept / max(1, fact_from), 2)
        winner = "character" if char_pct > fact_pct else ("fact" if fact_pct > char_pct else "tie")
        if winner == "character":
            char_wins += 1
        elif winner == "fact":
            fact_wins += 1
        cycle_summary.append({
            "cycle": f"{t['from']}->{t['to']}",
            "char_retention_pct": char_pct,
            "fact_retention_pct": fact_pct,
            "char_from_n": char_from,
            "char_kept_n": char_kept,
            "fact_from_n": fact_from,
            "fact_kept_n": fact_kept,
            "winner": winner,
            "delta_pp": round(char_pct - fact_pct, 2),
        })

    n_cycles = len(transitions)
    if char_wins == n_cycles:
        verdict = "STRONG_SUPPORT: character retention > fact retention on all cycles"
    elif char_wins >= 3:
        verdict = f"WEAK_SUPPORT: character wins {char_wins}/{n_cycles} cycles"
    else:
        verdict = f"REFUTED: character wins only {char_wins}/{n_cycles}"

    summary = {
        "hypothesis": "Compaction functor preserves operational-character > facts",
        "n_cycles": n_cycles,
        "char_wins": char_wins,
        "fact_wins": fact_wins,
        "ties": n_cycles - char_wins - fact_wins,
        "verdict": verdict,
        "cycle_summary": cycle_summary,
        "transitions": transitions,
    }
    OUT.write_text(json.dumps(summary, indent=2))
    print(f"E12 verdict: {verdict}")
    print(f"\nPer-cycle:")
    for c in cycle_summary:
        print(f"  {c['cycle']:>10s}: char={c['char_retention_pct']:>5.1f}% fact={c['fact_retention_pct']:>5.1f}% delta=+{c['delta_pp']:>+5.1f}pp winner={c['winner']}")


if __name__ == "__main__":
    main()
