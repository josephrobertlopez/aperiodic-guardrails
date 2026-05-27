#!/usr/bin/env python3
"""E6: Frontmatter Utility Profile + E7: Duplicate Schema Detection
For each frontmatter field across 23K notes:
  - occurrence count
  - cardinality of values (low = enum-like / status; high = unique-id / timestamp)
  - mean value byte length

E7: cluster notes by frontmatter field-set signature; identify near-duplicates.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
import hashlib

VAULT = Path.home() / ".gnosis" / "vault"
OUT6 = Path(__file__).parent.parent / "data" / "e6_results.json"
OUT7 = Path(__file__).parent.parent / "data" / "e7_results.json"

FM_PAT = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
FIELD_PAT = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:(.*)$", re.MULTILINE)


def main():
    field_occurrence = Counter()
    field_values = defaultdict(list)  # field -> list of values (truncated)
    field_value_lens = defaultdict(list)
    schema_signatures = Counter()  # frozenset of field names -> count
    notes_by_signature = defaultdict(list)

    n_files = 0
    n_with_fm = 0
    for p in VAULT.rglob("*.md"):
        n_files += 1
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        m = FM_PAT.match(text)
        if not m:
            continue
        n_with_fm += 1
        fm = m.group(1)
        fields = []
        for line in fm.split("\n"):
            fm_match = FIELD_PAT.match(line)
            if not fm_match:
                continue
            fname = fm_match.group(1).strip()
            fval = fm_match.group(2).strip()
            fields.append(fname)
            field_occurrence[fname] += 1
            if len(field_values[fname]) < 1000:
                field_values[fname].append(fval[:200])
            field_value_lens[fname].append(len(fval))

        sig = frozenset(fields)
        schema_signatures[sig] += 1
        if len(notes_by_signature[sig]) < 5:
            notes_by_signature[sig].append(str(p.relative_to(VAULT)))

    # E6: per-field profile
    field_profile = []
    for fname, count in field_occurrence.most_common():
        vals = field_values[fname]
        unique = len(set(vals))
        cardinality_ratio = round(unique / max(1, len(vals)), 3)
        lens = field_value_lens[fname]
        mean_len = round(sum(lens) / max(1, len(lens)), 1)
        field_profile.append({
            "field": fname,
            "occurrence": count,
            "occurrence_pct": round(100 * count / max(1, n_with_fm), 1),
            "value_cardinality": unique,
            "cardinality_ratio": cardinality_ratio,
            "value_mean_len_bytes": mean_len,
            "value_total_bytes": sum(lens),
        })

    e6 = {
        "n_files": n_files,
        "n_with_frontmatter": n_with_fm,
        "n_unique_fields": len(field_occurrence),
        "field_profile": field_profile[:60],
    }
    OUT6.write_text(json.dumps(e6, indent=2))

    # E7: schema clustering
    n_signatures = len(schema_signatures)
    top_signatures = []
    for sig, count in schema_signatures.most_common(20):
        top_signatures.append({
            "field_count": len(sig),
            "fields": sorted(sig),
            "note_count": count,
            "examples": notes_by_signature[sig][:3],
        })

    # near-duplicate detection: cluster signatures by Jaccard >= 0.8
    sig_list = list(schema_signatures.keys())
    # sample the top 500 by note-count to bound cost
    top_sigs = [s for s, _ in schema_signatures.most_common(500)]
    clusters = []
    seen = set()
    for i, a in enumerate(top_sigs):
        if i in seen:
            continue
        cluster = [i]
        for j in range(i + 1, len(top_sigs)):
            if j in seen:
                continue
            b = top_sigs[j]
            inter = len(a & b)
            union = len(a | b)
            jac = inter / max(1, union)
            if jac >= 0.8:
                cluster.append(j)
                seen.add(j)
        if len(cluster) > 1:
            cluster_notes = sum(schema_signatures[top_sigs[k]] for k in cluster)
            clusters.append({
                "members": len(cluster),
                "total_notes": cluster_notes,
                "anchor_fields": sorted(top_sigs[cluster[0]]),
            })

    e7 = {
        "n_unique_signatures": n_signatures,
        "n_notes_analyzed": n_with_fm,
        "uniqueness_ratio": round(n_signatures / max(1, n_with_fm), 3),
        "top_20_signatures_by_note_count": top_signatures,
        "near_duplicate_clusters_jac08": clusters[:20],
        "n_clusters_found": len(clusters),
    }
    OUT7.write_text(json.dumps(e7, indent=2))
    print(f"E6: {len(field_occurrence)} unique fields across {n_with_fm} notes")
    print(f"E7: {n_signatures} unique schema signatures, {len(clusters)} near-duplicate clusters")


if __name__ == "__main__":
    main()
