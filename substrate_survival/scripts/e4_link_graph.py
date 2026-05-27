#!/usr/bin/env python3
"""E4: Link-Graph Topology
Parse [[wikilinks]] and frontmatter from all notes in ~/.gnosis/vault/.
Compute: degree distribution, hub identification, clustering coefficient (approx).
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

VAULT = Path.home() / ".gnosis" / "vault"
OUT = Path(__file__).parent.parent / "data" / "e4_results.json"

WIKILINK = re.compile(r"\[\[([^\]\|#]+?)(?:\|[^\]]+)?\]\]")
FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def note_id(path):
    return path.stem


def main():
    edges = []
    outlinks = defaultdict(set)
    inlinks = defaultdict(set)
    all_notes = set()

    n_files = 0
    n_with_links = 0
    for p in VAULT.rglob("*.md"):
        n_files += 1
        nid = note_id(p)
        all_notes.add(nid)
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        links = set(WIKILINK.findall(text))
        if links:
            n_with_links += 1
        for tgt in links:
            tgt = tgt.strip()
            if not tgt:
                continue
            outlinks[nid].add(tgt)
            inlinks[tgt].add(nid)
            edges.append((nid, tgt))

    # degree stats
    out_deg = [len(v) for v in outlinks.values()]
    in_deg = [len(v) for v in inlinks.values()]

    def stats(arr, label):
        if not arr:
            return {f"{label}_n": 0}
        s = sorted(arr)
        return {
            f"{label}_n": len(s),
            f"{label}_min": s[0],
            f"{label}_p50": s[len(s) // 2],
            f"{label}_p90": s[int(len(s) * 0.90)],
            f"{label}_p99": s[int(len(s) * 0.99)],
            f"{label}_max": s[-1],
            f"{label}_mean": round(sum(s) / len(s), 2),
        }

    # top hubs
    in_counter = Counter({k: len(v) for k, v in inlinks.items()})
    top_hubs = in_counter.most_common(20)

    # dangling links (link target not in vault)
    all_targets = set(inlinks.keys())
    dangling = all_targets - all_notes
    resolved = all_targets & all_notes

    # dark matter: notes with no inlinks AND no outlinks
    no_in = all_notes - all_targets
    has_outlinks = set(outlinks.keys())
    dark_matter = no_in - has_outlinks

    # 2-hop reach approximation (sample): for 100 random hub-source nodes, how big is 2-hop set?
    import random
    random.seed(42)
    sample = random.sample(list(has_outlinks), min(100, len(has_outlinks)))
    reach_two_hop = []
    for s in sample:
        one_hop = outlinks.get(s, set()) & all_notes
        two_hop = set()
        for h in one_hop:
            two_hop |= outlinks.get(h, set()) & all_notes
        reach_two_hop.append(len(one_hop | two_hop))

    out = {
        "n_files": n_files,
        "n_files_with_outlinks": n_with_links,
        "n_unique_notes": len(all_notes),
        "n_edges": len(edges),
        "n_link_targets_total": len(all_targets),
        "n_link_targets_resolved": len(resolved),
        "n_link_targets_dangling": len(dangling),
        "pct_dangling": round(100 * len(dangling) / max(1, len(all_targets)), 2),
        "n_dark_matter_notes": len(dark_matter),
        "pct_dark_matter": round(100 * len(dark_matter) / max(1, len(all_notes)), 2),
        **stats(out_deg, "out_deg"),
        **stats(in_deg, "in_deg"),
        "top20_hubs_by_inlinks": top_hubs,
        "two_hop_reach_sample_n": len(reach_two_hop),
        "two_hop_reach_mean": round(sum(reach_two_hop) / max(1, len(reach_two_hop)), 1),
        "two_hop_reach_max": max(reach_two_hop) if reach_two_hop else 0,
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
