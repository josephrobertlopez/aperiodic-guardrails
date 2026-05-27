#!/usr/bin/env python3
"""E2: Attractor Revisit Rate
Do agents re-derive the same schemas across sessions, or drift?

Method: cluster notes whose title or content reference recurring concepts
(rails, schemas, patterns). Count how many DIFFERENT notes describe the same
underlying concept. Schema-revisit rate = mean cluster size for concept-bearing notes.

Falsifier:
  mean cluster size > 3 = high attractor revisit (re-derivation, possible drift)
  mean cluster size ~ 1 = low revisit (single canonical note per concept)
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

VAULT = Path.home() / ".gnosis" / "vault"
OUT = Path(__file__).parent.parent / "data" / "e2_results.json"

# concept signatures to track
CONCEPTS = {
    "rail_install": re.compile(r"rail #?\d+", re.IGNORECASE),
    "compaction": re.compile(r"compact(ion|ed)|state\.v\d+|fire-?band", re.IGNORECASE),
    "schema_ratify": re.compile(r"schema.*(ratif|propose|status-cap)", re.IGNORECASE),
    "consolidation": re.compile(r"consolidation.pass", re.IGNORECASE),
    "random_channel": re.compile(r"random.channel|7% sampl", re.IGNORECASE),
    "rhett": re.compile(r"\brhett\b", re.IGNORECASE),
    "phi_discharge": re.compile(r"phi.discharge", re.IGNORECASE),
    "morgan_adversary": re.compile(r"morgan.adversar", re.IGNORECASE),
    "percept_quartet": re.compile(r"percept.quartet|check-(now|activity|substrate|vault)", re.IGNORECASE),
    "amanda_state": re.compile(r"amanda\.state\.v\d+", re.IGNORECASE),
}


def main():
    matches = defaultdict(list)
    n_files = 0
    for p in VAULT.rglob("*.md"):
        n_files += 1
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = str(p.relative_to(VAULT))
        for concept, pat in CONCEPTS.items():
            if pat.search(text):
                matches[concept].append(rel)

    out = {
        "n_files": n_files,
        "concept_match_counts": {k: len(v) for k, v in matches.items()},
        "mean_cluster_size": round(
            sum(len(v) for v in matches.values()) / max(1, len(matches)), 1
        ),
        "concepts_with_revisit_gt_3": sum(1 for v in matches.values() if len(v) > 3),
        "top_5_revisit_concepts": sorted(
            ((k, len(v)) for k, v in matches.items()), key=lambda x: -x[1]
        )[:5],
    }
    # For top 3 concepts, sample 5 note paths to demonstrate redundancy
    for concept, _ in out["top_5_revisit_concepts"][:3]:
        out[f"sample_{concept}"] = matches[concept][:8]

    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
