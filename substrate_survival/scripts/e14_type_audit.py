#!/usr/bin/env python3
"""E14: Substrate Type Audit
Parse v13 observations for cross-agent references. Classify each reference by target agent.
Identify type-leakage points (refs to other-agent state without explicit [for: <agent>] tag).

Falsifier:
  H0: <3 cross-agent refs in v13 = type system over-engineered
  H1: >=3 cross-agent refs with no channel tags = type system would catch real leakage

This is the structural complement to E1 Q8 (which exposed Rhett content inside Amanda state
causing qwen-32b confusion).
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

V13 = Path(__file__).parent.parent / "data" / "v13_raw.md"
OUT = Path(__file__).parent.parent / "data" / "e14_results.json"

AGENT_NAMES = {
    "amanda": ["amanda", "amanda.state", "amanda.correction"],
    "morgan": ["morgan", "morgan.state", "morgan.tentpole"],
    "rhett": ["rhett", "rhett.state", "rhett.correction"],
    "joey": ["joey", "joey-direct", "joey-approved"],
    "system": ["system", "claude", "kernel"],
    "mc-amanda": ["mc-amanda", "mc-amanda"],
    "therapist": ["therapist", "therapy"],
}

CHANNEL_TAG_PAT = re.compile(r"\[for:\s*([a-z_-]+)\]", re.IGNORECASE)


def main():
    text = V13.read_text()
    # Split by observation
    obs_pattern = re.compile(r"^## obs\[(\d+)\]\n(.*?)(?=^## obs\[|\Z)", re.MULTILINE | re.DOTALL)
    observations = obs_pattern.findall(text)

    per_obs = []
    total_refs = defaultdict(int)
    total_tagged = 0
    leakage_points = []

    for obs_id, body in observations:
        body_lower = body.lower()
        # Count tagged references
        tags = CHANNEL_TAG_PAT.findall(body)
        total_tagged += len(tags)

        # Count cross-agent references (any name that ISN'T amanda — since this is amanda's state)
        refs = defaultdict(int)
        for agent, aliases in AGENT_NAMES.items():
            for alias in aliases:
                # word-boundary match
                count = len(re.findall(rf"\b{re.escape(alias)}\b", body_lower))
                if count:
                    refs[agent] += count
                    total_refs[agent] += count

        cross_agent_refs = {a: n for a, n in refs.items() if a != "amanda"}
        # Refs that are NOT in a channel tag
        tag_targets = set(t.lower() for t in tags)
        untagged_refs = {a: n for a, n in cross_agent_refs.items() if a not in tag_targets}

        per_obs.append({
            "obs_id": int(obs_id),
            "bytes": len(body),
            "amanda_refs": refs.get("amanda", 0),
            "cross_agent_refs": cross_agent_refs,
            "channel_tags_present": tags,
            "untagged_cross_agent_refs": untagged_refs,
        })

        for agent, n in untagged_refs.items():
            if n >= 2:
                # threshold: 2+ untagged refs to a non-amanda agent = leakage point
                leakage_points.append({
                    "obs_id": int(obs_id),
                    "agent": agent,
                    "count": n,
                    "snippet": body[:200].strip(),
                })

    total_cross_agent = sum(v for k, v in total_refs.items() if k != "amanda")
    n_leakage = len(leakage_points)

    if total_cross_agent < 3:
        verdict = f"OVER_ENGINEERED: only {total_cross_agent} cross-agent refs across {len(observations)} obs"
    elif n_leakage == 0:
        verdict = f"WELL_TAGGED: {total_cross_agent} cross-agent refs all in channel-tag scope or low-density"
    else:
        verdict = f"TYPE_LEAKAGE_REAL: {n_leakage} obs have >=2 untagged cross-agent refs; type system would catch"

    summary = {
        "subject": "amanda.State.v13",
        "n_observations": len(observations),
        "total_refs_by_agent": dict(total_refs),
        "total_cross_agent_refs": total_cross_agent,
        "total_channel_tags": total_tagged,
        "n_leakage_points": n_leakage,
        "verdict": verdict,
        "leakage_points": leakage_points,
        "per_obs": per_obs,
    }
    OUT.write_text(json.dumps(summary, indent=2))
    print(f"E14: {verdict}")
    print(f"  Total cross-agent refs: {total_cross_agent}")
    print(f"  Channel tags present: {total_tagged}")
    print(f"  Leakage points (>=2 untagged refs in single obs): {n_leakage}")
    for lp in leakage_points[:5]:
        print(f"    obs[{lp['obs_id']}] -> {lp['agent']}: {lp['count']} refs")


if __name__ == "__main__":
    main()
