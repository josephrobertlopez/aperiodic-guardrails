#!/usr/bin/env python3
"""E5: Compaction Loss Audit
Diff amanda.State.v12 (archived) vs amanda.State.v13 (current).
Identify dropped tokens/facts and classify as load-bearing or recoverable.

Falsifier (pre-registered):
  load-bearing tokens dropped (dates, rail numbers, version refs, named entities)
  with no recovery path = compaction LOSSY
  only redundant prose dropped = compaction LEAN
"""
import json
import re
from collections import Counter
from pathlib import Path

V12 = Path(__file__).parent.parent / "data" / "v12_raw.md"
V13 = Path(__file__).parent.parent / "data" / "v13_raw.md"
OUT = Path(__file__).parent.parent / "data" / "e5_results.json"

TOKEN_PAT = re.compile(r"[a-zA-Z0-9_#\.\-]+")
DATE_PAT = re.compile(r"^2026-\d{2}-\d{2}$")
VERSION_PAT = re.compile(r"^v\d+$")
RAIL_PAT = re.compile(r"^#\d+$")
BYTES_PAT = re.compile(r"^\d{3,}b?$", re.IGNORECASE)
NUMERIC_PAT = re.compile(r"^-?\d+\.?\d*[kmKMgG]?[bB]?$")


def tokenize(text):
    return [t.lower() for t in TOKEN_PAT.findall(text)]


def classify(tok):
    if DATE_PAT.match(tok):
        return "date"
    if VERSION_PAT.match(tok):
        return "version"
    if RAIL_PAT.match(tok):
        return "rail"
    if BYTES_PAT.match(tok) or NUMERIC_PAT.match(tok):
        return "numeric"
    if tok.startswith("[[") or "/" in tok:
        return "path_or_link"
    if any(c.isupper() for c in tok) and len(tok) > 3:
        return "name_caps"
    return "prose"


def main():
    v12_text = V12.read_text()
    v13_text = V13.read_text()

    v12_toks = tokenize(v12_text)
    v13_toks = tokenize(v13_text)
    v12_set = set(v12_toks)
    v13_set = set(v13_toks)

    dropped = v12_set - v13_set
    added = v13_set - v12_set
    kept = v12_set & v13_set

    # classify
    dropped_by_class = Counter(classify(t) for t in dropped)
    added_by_class = Counter(classify(t) for t in added)
    kept_by_class = Counter(classify(t) for t in kept)

    # surface load-bearing dropped tokens (non-prose)
    dropped_load_bearing = sorted(
        [t for t in dropped if classify(t) != "prose"]
    )

    # token-occurrence in v12 (for context on whether dropped tokens were frequent)
    v12_counter = Counter(v12_toks)
    dropped_with_count = sorted(
        [(t, v12_counter[t], classify(t)) for t in dropped],
        key=lambda x: -x[1],
    )[:50]

    out = {
        "v12_bytes": len(v12_text),
        "v13_bytes": len(v13_text),
        "compression_pct": round(100 * (1 - len(v13_text) / len(v12_text)), 2),
        "v12_unique_tokens": len(v12_set),
        "v13_unique_tokens": len(v13_set),
        "tokens_dropped": len(dropped),
        "tokens_added": len(added),
        "tokens_kept": len(kept),
        "retention_pct": round(100 * len(kept) / len(v12_set), 2),
        "dropped_by_class": dict(dropped_by_class),
        "added_by_class": dict(added_by_class),
        "kept_by_class": dict(kept_by_class),
        "load_bearing_dropped_sample": dropped_load_bearing[:80],
        "top_dropped_by_v12_frequency": [
            {"tok": t, "v12_count": c, "class": cl}
            for t, c, cl in dropped_with_count
        ],
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(f"v12: {len(v12_text)}B / {len(v12_set)} unique tokens")
    print(f"v13: {len(v13_text)}B / {len(v13_set)} unique tokens")
    print(f"compression: {out['compression_pct']}% byte / retention {out['retention_pct']}% unique-token")
    print(f"dropped by class: {dict(dropped_by_class)}")
    print(f"load-bearing dropped (non-prose, sample): {dropped_load_bearing[:20]}")


if __name__ == "__main__":
    main()
