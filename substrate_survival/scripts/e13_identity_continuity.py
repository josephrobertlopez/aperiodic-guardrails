#!/usr/bin/env python3
"""E13: Bounded-Context Agent Identity Across Rehydration
Harvest amanda dispatches from today's session transcript. Diff briefs for:
  - canonical-fact agreement (substrate state, FIRE-headroom, rail count, sentinels)
  - identity-marker agreement (refusal phrases, decision framing, ANSWER format)

Falsifier:
  H0: briefs converge on canonical facts (>= 80% agreement) = identity stable
  H1: briefs diverge on canonical facts (< 80% agreement) = identity drifts

Substrate facts to probe (extractable from each brief):
  P1. Combined-ingress byte count
  P2. FIRE-headroom byte count
  P3. Substrate state band (WARN / FIRE / safe)
  P4. v13 obs count
  P5. Correction.v5 obs count
  P6. Number of open threads cited
  P7. Pole-status mentioned (POLE-UNDECLARED, etc)
  P8. Rail-fires cited (Rail #N references)
  P9. Sentinels named (compaction-needed, lessons-pending, etc)
  P10. Rotation N (asymmetric rotation cycle count)
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

TRANSCRIPT = Path("/home/joey/.claude/projects/-mnt-media-local-storage-code-GitHub/f2e3967c-4452-48e4-a240-eedbd1dac3ed.jsonl")
OUT = Path(__file__).parent.parent / "data" / "e13_results.json"

# Probes: (label, regex) -> extract numeric/string value from brief
PROBES = [
    ("combined_bytes", re.compile(r"combined[\s:]*~?(\d+(?:,\d+)?)\s*B?", re.IGNORECASE)),
    ("fire_headroom", re.compile(r"FIRE[\s-]headroom[\s:]*[~-]?(\d+(?:,\d+)?)\s*B?", re.IGNORECASE)),
    ("warn_band_neg", re.compile(r"WARN-band[\s:]*[-−](\d+(?:,\d+)?)\s*B?", re.IGNORECASE)),
    ("substrate_band", re.compile(r"\b(WARN-band|FIRE-band|FIRE-line|FIRE-overflow)\b", re.IGNORECASE)),
    ("v13_obs_count", re.compile(r"v13[^\n]{0,40}?\b(\d+)\s+obs|\bv13\b[^\n]{0,40}?\bobs[^\n]{0,5}?(\d+)\b", re.IGNORECASE)),
    ("correction_obs_count", re.compile(r"Correction(?:\.open)?\.v5[^\n]{0,80}?(\d+)\s+obs|(\d+)\s+obs[^\n]{0,80}?Correction(?:\.open)?\.v5", re.IGNORECASE)),
    ("rotation_n", re.compile(r"(?:asymmetric\s+)?rotation\s+N\s*=\s*(\d+)|N\s*=\s*(\d+)\s+cycles", re.IGNORECASE)),
    ("pole_status", re.compile(r"\b(POLE[\s-]?UNDECLARED|tent[\s-]?pole)\b", re.IGNORECASE)),
]

RAIL_REF_PAT = re.compile(r"[Rr]ail\s*#?(\d+)")
SENTINEL_PAT = re.compile(r"\b(compaction-needed|lessons-pending|corrections-pending|stale-handoff|orphan|PARITY-001|META_INFLATION)\b", re.IGNORECASE)
REFUSAL_PHRASES = [
    "refuse", "refused", "refusal", "rail fire", "rail-fire", "fired",
    "anti-vibe", "vibed", "filing", "scope-creep", "decoration",
    "manifesto", "out-of-scope", "deferred", "skip", "decline",
]


def harvest_amanda_briefs(transcript_path):
    """Find Agent calls with subagent_type=amanda and their assistant-message responses."""
    briefs = []
    with open(transcript_path) as f:
        prev_amanda_call = None
        for line_no, line in enumerate(f):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            # User-side Agent tool use
            msg = rec.get("message", {})
            if msg.get("role") == "assistant":
                content = msg.get("content", [])
                if isinstance(content, list):
                    for c in content:
                        if c.get("type") == "tool_use" and c.get("name") == "Agent":
                            inp = c.get("input", {})
                            if inp.get("subagent_type") == "amanda":
                                prev_amanda_call = {
                                    "tool_use_id": c.get("id"),
                                    "prompt": inp.get("prompt", "")[:500],
                                    "timestamp": rec.get("timestamp", "?"),
                                    "line": line_no,
                                }
            # Tool result for the previous amanda call
            if msg.get("role") == "user":
                content = msg.get("content", [])
                if isinstance(content, list):
                    for c in content:
                        if c.get("type") == "tool_result" and prev_amanda_call:
                            tr_id = c.get("tool_use_id")
                            if tr_id == prev_amanda_call["tool_use_id"]:
                                result_content = c.get("content", "")
                                if isinstance(result_content, list):
                                    result_content = "".join(
                                        x.get("text", "") if isinstance(x, dict) else str(x)
                                        for x in result_content
                                    )
                                briefs.append({
                                    **prev_amanda_call,
                                    "response": result_content,
                                    "response_bytes": len(result_content),
                                })
                                prev_amanda_call = None
    return briefs


def probe(text):
    """Extract canonical facts from a brief."""
    facts = {}
    for label, pat in PROBES:
        m = pat.search(text)
        if m:
            # Take first non-empty group
            for g in m.groups():
                if g:
                    facts[label] = g.replace(",", "")
                    break
            else:
                facts[label] = m.group(0)
        else:
            facts[label] = None

    # Rail references — set of rail numbers cited
    rail_refs = set(int(m) for m in RAIL_REF_PAT.findall(text))
    facts["rail_refs"] = sorted(rail_refs)

    # Sentinel mentions
    sentinels = set(m.lower() for m in SENTINEL_PAT.findall(text))
    facts["sentinels"] = sorted(sentinels)

    # Refusal-phrase density (character marker)
    phrase_hits = sum(text.lower().count(p) for p in REFUSAL_PHRASES)
    facts["refusal_phrase_density"] = phrase_hits

    facts["response_bytes"] = len(text)
    return facts


def compute_agreement(probes_per_brief):
    """For each probe field, how many briefs agree on the value?"""
    if not probes_per_brief:
        return {}
    fields = set()
    for p in probes_per_brief:
        fields.update(p.keys())
    agreement = {}
    for field in sorted(fields):
        if field in ("rail_refs", "sentinels"):
            # Set fields — measure pairwise Jaccard
            sets = [set(p.get(field, [])) for p in probes_per_brief]
            jaccards = []
            for i in range(len(sets)):
                for j in range(i + 1, len(sets)):
                    a, b = sets[i], sets[j]
                    union = a | b
                    if not union:
                        jaccards.append(1.0)
                    else:
                        jaccards.append(len(a & b) / len(union))
            mean_jaccard = sum(jaccards) / max(1, len(jaccards))
            agreement[field] = {
                "type": "set",
                "mean_jaccard": round(mean_jaccard, 3),
                "values_per_brief": [list(s) for s in sets],
            }
        else:
            # Scalar / categorical — only count NON-NONE values for agreement
            values = [str(p.get(field)) for p in probes_per_brief]
            non_none = [v for v in values if v not in ("None", "")]
            if not non_none:
                agreement[field] = {
                    "type": "scalar",
                    "modal_value": None,
                    "agreement_pct": None,
                    "extraction_failed_pct": 100.0,
                    "values": values,
                }
                continue
            counter = Counter(non_none)
            modal_value, modal_count = counter.most_common(1)[0]
            agreement_pct_among_extracted = round(100 * modal_count / len(non_none), 1)
            extraction_pct = round(100 * len(non_none) / len(values), 1)
            agreement[field] = {
                "type": "scalar",
                "modal_value": modal_value,
                "agreement_pct": agreement_pct_among_extracted,
                "extraction_rate_pct": extraction_pct,
                "values": values,
            }
    return agreement


def main():
    briefs = harvest_amanda_briefs(TRANSCRIPT)
    if not briefs:
        print("No amanda briefs found in transcript.")
        return
    print(f"Harvested {len(briefs)} amanda briefs from today's transcript", file=sys.stderr)

    probes = [probe(b["response"]) for b in briefs]
    agreement = compute_agreement(probes)

    # Headline: agreement on canonical facts WHERE EXTRACTED
    canonical_fact_fields = [
        "combined_bytes", "fire_headroom", "substrate_band",
        "v13_obs_count", "correction_obs_count", "rotation_n", "pole_status",
    ]
    extracted_agreements = []
    for f in canonical_fact_fields:
        a = agreement.get(f, {})
        ap = a.get("agreement_pct")
        if ap is not None:
            extracted_agreements.append(ap)
    high_agreement = sum(1 for a in extracted_agreements if a >= 80)
    mean_fact_agreement = round(sum(extracted_agreements) / max(1, len(extracted_agreements)), 1) if extracted_agreements else 0

    if mean_fact_agreement >= 80:
        verdict = f"STABLE: mean canonical-fact agreement {mean_fact_agreement}% across N={len(briefs)} rehydrations"
    elif mean_fact_agreement >= 60:
        verdict = f"MODERATE_DRIFT: mean {mean_fact_agreement}% — some facts diverge"
    else:
        verdict = f"HIGH_DRIFT: mean {mean_fact_agreement}% — identity continuity questionable"

    summary = {
        "subject": "amanda persona across same-day v13 rehydrations",
        "transcript": str(TRANSCRIPT),
        "n_briefs_harvested": len(briefs),
        "verdict": verdict,
        "mean_canonical_fact_agreement_pct": mean_fact_agreement,
        "n_facts_with_high_agreement": high_agreement,
        "n_canonical_facts": len(canonical_fact_fields),
        "agreement_per_field": agreement,
        "brief_metadata": [{k: v for k, v in b.items() if k not in ("response",)} for b in briefs],
        "probes_per_brief": probes,
    }
    OUT.write_text(json.dumps(summary, indent=2))
    print(f"E13: {verdict}", file=sys.stderr)
    print(f"\nCanonical fact agreement:", file=sys.stderr)
    for field in canonical_fact_fields:
        a = agreement.get(field, {})
        print(f"  {field:>20s}: {a.get('agreement_pct', 'N/A')}% modal={a.get('modal_value', 'N/A')[:30]}", file=sys.stderr)
    print(f"\nSet-field jaccard:", file=sys.stderr)
    for field in ("rail_refs", "sentinels"):
        a = agreement.get(field, {})
        print(f"  {field:>20s}: mean_jaccard={a.get('mean_jaccard', 'N/A')}", file=sys.stderr)


if __name__ == "__main__":
    main()
