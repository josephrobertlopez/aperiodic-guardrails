#!/usr/bin/env python3
"""E9: Agent-Write Fingerprinting
For each note, extract `agent` or `source` frontmatter field.
Compute stylometric features per agent: mean note length, sentence length,
lexical density (unique-tokens / total-tokens), structural markers (lists, code blocks).

Test: do agents produce distinguishable styles, or homogenized output?
"""
import json
import re
from collections import defaultdict, Counter
from pathlib import Path
import statistics

VAULT = Path.home() / ".gnosis" / "vault"
OUT = Path(__file__).parent.parent / "data" / "e9_results.json"

FM_PAT = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
AGENT_PAT = re.compile(r"^(agent|source|author|written_by|written-by|created_by):\s*(.+)$", re.MULTILINE)
TOKEN_PAT = re.compile(r"[a-zA-Z]+")
CODE_BLOCK_PAT = re.compile(r"```")
LIST_PAT = re.compile(r"^[-*]\s", re.MULTILINE)


def main():
    by_agent = defaultdict(list)  # agent -> list of feature dicts
    n_files = 0
    n_with_agent = 0
    unknown_agents = Counter()

    for p in VAULT.rglob("*.md"):
        n_files += 1
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        m = FM_PAT.match(text)
        agent = None
        if m:
            fm = m.group(1)
            am = AGENT_PAT.search(fm)
            if am:
                agent = am.group(2).strip().strip("'\"").lower()
        if not agent:
            continue
        n_with_agent += 1
        unknown_agents[agent] += 1
        body = text[m.end():] if m else text
        body_len = len(body)
        tokens = TOKEN_PAT.findall(body.lower())
        unique = len(set(tokens))
        tot = len(tokens)
        lex_density = unique / max(1, tot)
        n_code = len(CODE_BLOCK_PAT.findall(body)) // 2
        n_list = len(LIST_PAT.findall(body))
        by_agent[agent].append({
            "bytes": body_len,
            "tokens": tot,
            "lex_density": lex_density,
            "n_code_blocks": n_code,
            "n_list_items": n_list,
        })

    profile = {}
    for agent, samples in by_agent.items():
        if len(samples) < 5:
            continue  # not enough to profile
        bytes_arr = [s["bytes"] for s in samples]
        density_arr = [s["lex_density"] for s in samples]
        code_arr = [s["n_code_blocks"] for s in samples]
        list_arr = [s["n_list_items"] for s in samples]
        profile[agent] = {
            "n_notes": len(samples),
            "byte_mean": round(statistics.mean(bytes_arr), 1),
            "byte_stdev": round(statistics.stdev(bytes_arr) if len(bytes_arr) > 1 else 0, 1),
            "lex_density_mean": round(statistics.mean(density_arr), 3),
            "code_blocks_mean": round(statistics.mean(code_arr), 2),
            "list_items_mean": round(statistics.mean(list_arr), 1),
        }

    # rank agents by note count
    top_agents = sorted(profile.items(), key=lambda x: -x[1]["n_notes"])[:20]

    out = {
        "n_files": n_files,
        "n_with_agent_field": n_with_agent,
        "n_unique_agent_values": len(unknown_agents),
        "top_agents_by_volume": [(a, n) for a, n in unknown_agents.most_common(30)],
        "profile_top_20": dict(top_agents),
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(f"Profiled {len(profile)} agents (≥5 notes each)")
    for a, p in top_agents[:10]:
        print(f"  {a}: n={p['n_notes']}, byte_mean={p['byte_mean']}, lex_density={p['lex_density_mean']}")


if __name__ == "__main__":
    main()
