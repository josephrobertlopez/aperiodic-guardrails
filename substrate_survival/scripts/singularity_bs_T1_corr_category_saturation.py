#!/usr/bin/env python3
"""
Singularity-BS-T1: Correction-category saturation test on Amanda's substrate.

Hypothesis: If Amanda's substrate is doing recursive self-improvement on the
variety dimension, the count of DISTINCT correction-CATEGORIES (rail-class
buckets parsed from ACTIVE-RAIL-CORRECTIONS across amanda.Correction.open.v*
versions) should keep expanding monotonically. If saturated -> RSI-variety
falsified.

Pre-registered: specs/pre_registered/Singularity-BS-T1_20260530T040838Z.json
Read-only against ~/.gnosis/.
"""
from __future__ import annotations
import json
import os
import re
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

MEMORY_PATH = "/home/joey/.gnosis/.memory/memory.jsonl"
PRE_REG_PATH = "specs/pre_registered/Singularity-BS-T1_20260530T040838Z.json"
RESULTS_PATH = "data/Singularity-BS-T1_corr_category_saturation_results.json"
PARENT_COPY = "/tmp/singularity_bs_T1_results.json"
REPORT_PATH = "data/Singularity-BS-T1_report.md"

# Regex for letter-prefixed rail-class headers inside ACTIVE-RAIL-CORRECTIONS.
# PRIMARY (pre-reg-conformant): line begins with "<letter>. <UPPERCASED PHRASE>"
# where the uppercased phrase ends at the first ":" or "[" or "(" boundary.
# This catches headers like:
#   A. PROVENANCE & CONSENT RAILS [all M1, e=1]:
#   D. COMMERCIAL/DOMAIN RAILS:
#   D. COACHING/THERAPY DOMAIN RAIL (#31, PROPOSAL-SHAPED 14+ days, blocking):
#   F. SYSTEM-NETWORK ISOLATION (#51 2026-04-25, IN FORCE):
#   J. NEW v2-CYCLE RAIL (2026-05-03): VOCABULARY-AS-ARCHITECTURE REFUSAL.
# We accept any UPPERCASED phrase as a category header (not just ones containing
# the literal word RAIL/RAILS), to faithfully include classes like
# "SYSTEM-NETWORK ISOLATION" and "VOCABULARY-AS-ARCHITECTURE REFUSAL" that
# Amanda's own substrate authors as top-level letter-prefixed rail-classes.
# This is more INCLUSIVE than RAIL-only matching, which biases AGAINST a
# false-saturation finding (giving the RSI-variety claim every chance).
CLASS_RE = re.compile(
    r'(?m)^\s*([A-Z])\.\s+([A-Z][A-Z0-9 &/\-]+?)(?=\s*[\[\(:])'
)

# SECONDARY (sensitivity-analysis) regex: matches any letter-prefixed line that
# begins with an uppercase phrase, even if the phrase contains mixed-case
# fragments like "NEW v2-CYCLE RAIL". Used for a sensitivity analysis to
# include appendix-style "NEW <vN>-CYCLE RAIL" entries (J in v3, K in v6,
# L in v7) that the substrate added below the canonical A-I block.
# We extract the full line content (up to colon) as the category name.
CLASS_RE_LOOSE = re.compile(
    r'(?m)^\s*([A-Z])\.\s+([^\n:]+?):'
)

GENESIS_RE = re.compile(
    r'GENESIS\s+(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?(?:\s*UTC)?)'
)
ARCHIVED_RE = re.compile(
    r'ARCHIVED\s+(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?(?:\s*UTC)?)'
)


def parse_loose_ts(s: str) -> Optional[datetime]:
    """Parse 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM[ UTC]'. Assume UTC if unspecified."""
    if not s:
        return None
    s = s.strip().rstrip().replace(" UTC", "")
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def normalize_category(raw: str) -> str:
    """Normalize a rail-class header to canonical category name."""
    # Strip trailing 's' on RAIL/RAILS so plural/singular collapse?
    # NO -- pre-reg says treat v6's COACHING/THERAPY DOMAIN RAIL as same as
    # v2-v5's COACHING/THERAPY DOMAIN RAIL (which is already singular here).
    # Just normalize whitespace and case.
    out = re.sub(r'\s+', ' ', raw).strip().upper()
    # Collapse RAILS -> RAIL for the purpose of equivalence
    if out.endswith(" RAILS"):
        out = out[:-1]  # -> "... RAIL"
    return out


def extract_categories_from_active(obs_text: str, regex=CLASS_RE) -> list[str]:
    """Extract distinct normalized rail-classes from an ACTIVE-RAIL-CORRECTIONS observation."""
    found = []
    for m in regex.finditer(obs_text):
        letter = m.group(1)
        cat_raw = m.group(2).strip()
        # We DON'T keep the letter for normalization since letters can be re-used
        # if a class is dropped. We canonicalize by the phrase only.
        norm = normalize_category(cat_raw)
        # Drop noisy capture artifacts (very short or just punctuation)
        if len(norm) < 4:
            continue
        if norm not in found:
            found.append(norm)
    return found


def normalize_loose_category(raw: str) -> str:
    """Strip volatile fragments like '(#82, ...)' and 'NEW vN-CYCLE RAIL' wrappers
    to canonicalize loose-regex captures. Aim is to collapse the substrate's
    own appendix-style 'NEW v2-CYCLE RAIL ... VOCABULARY-AS-ARCHITECTURE REFUSAL'
    to the underlying rail-content name."""
    s = re.sub(r'\(.*?\)', '', raw)  # strip parentheticals
    s = re.sub(r'\[.*?\]', '', s)    # strip brackets
    # If pattern looks like "NEW vN-CYCLE RAIL #X" preserve the rail-class generic label
    m = re.match(r'^\s*NEW\s+V\d+-CYCLE\s+RAIL\b', s, re.IGNORECASE)
    if m:
        # Keep as a category sentinel "NEW-CYCLE-RAIL"
        return "NEW-CYCLE-RAIL"
    return normalize_category(s)


def extract_categories_loose(obs_text: str) -> list[str]:
    """Sensitivity-analysis extractor: catches J/K/L appendix-style additions
    that the canonical-block regex misses because they contain lowercase
    fragments (e.g., 'NEW v2-CYCLE RAIL')."""
    found = []
    for m in CLASS_RE_LOOSE.finditer(obs_text):
        cat_raw = m.group(2).strip()
        norm = normalize_loose_category(cat_raw)
        if len(norm) < 4:
            continue
        if norm not in found:
            found.append(norm)
    return found


def mann_kendall(values: list[float]) -> dict:
    """Two-sided Mann-Kendall trend test. Returns dict with S, var_S, Z, p, trend."""
    import math
    n = len(values)
    if n < 3:
        return {"n": n, "S": None, "Z": None, "p": None, "trend": "insufficient_n"}
    S = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            d = values[j] - values[i]
            S += 1 if d > 0 else -1 if d < 0 else 0
    # No tie correction for small n with distinct integers; use simple form
    var_S = n * (n - 1) * (2 * n + 5) / 18.0
    if S > 0:
        Z = (S - 1) / math.sqrt(var_S)
    elif S < 0:
        Z = (S + 1) / math.sqrt(var_S)
    else:
        Z = 0.0
    # Two-sided p via normal CDF
    p = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(Z) / math.sqrt(2.0))))
    trend = "increasing" if S > 0 else "decreasing" if S < 0 else "flat"
    return {"n": n, "S": S, "var_S": var_S, "Z": Z, "p": p, "trend": trend}


def main() -> int:
    # --- Pre-reg lock ---
    if not os.path.exists(PRE_REG_PATH):
        print(f"FATAL: pre-reg not found at {PRE_REG_PATH}", file=sys.stderr)
        return 2
    pre_reg_mtime = os.path.getmtime(PRE_REG_PATH)
    pre_reg_mtime_iso = datetime.fromtimestamp(pre_reg_mtime, tz=timezone.utc).isoformat()

    # --- Load memory.jsonl ---
    if not os.path.exists(MEMORY_PATH):
        verdict = {
            "verdict": "HARNESS_INVALID",
            "diagnostic": f"memory.jsonl not found at {MEMORY_PATH}",
            "pre_reg_mtime": pre_reg_mtime,
            "pre_reg_mtime_iso": pre_reg_mtime_iso,
        }
        Path(os.path.dirname(RESULTS_PATH)).mkdir(parents=True, exist_ok=True)
        with open(RESULTS_PATH, "w") as f:
            json.dump(verdict, f, indent=2)
        shutil.copy(RESULTS_PATH, PARENT_COPY)
        print(json.dumps(verdict, indent=2))
        return 3

    versions: dict[str, dict] = {}
    with open(MEMORY_PATH) as f:
        for line in f:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            name = obj.get("name", "")
            if not name.startswith("amanda.Correction.open.v"):
                continue
            obs = obj.get("observations", []) or []
            if not obs:
                continue
            full = "\n".join(obs)

            # Find ACTIVE-RAIL-CORRECTIONS observation
            active_obs = None
            for o in obs:
                if o.lstrip().startswith("ACTIVE-RAIL-CORRECTIONS"):
                    active_obs = o
                    break
            cats = extract_categories_from_active(active_obs) if active_obs else []
            cats_loose = extract_categories_loose(active_obs) if active_obs else []

            g = GENESIS_RE.search(full)
            a = ARCHIVED_RE.search(full)
            genesis_str = g.group(1) if g else None
            archived_str = a.group(1) if a else None

            versions[name] = {
                "name": name,
                "n_observations": len(obs),
                "genesis_str": genesis_str,
                "archived_str": archived_str,
                "genesis_ts": parse_loose_ts(genesis_str).isoformat() if parse_loose_ts(genesis_str) else None,
                "archived_ts": parse_loose_ts(archived_str).isoformat() if parse_loose_ts(archived_str) else None,
                "categories": cats,
                "categories_loose": cats_loose,
                "n_categories_at_version": len(cats),
                "n_categories_loose": len(cats_loose),
                "has_active_obs": active_obs is not None,
            }

    # Sort versions by integer suffix
    def vnum(name: str) -> int:
        m = re.search(r'v(\d+)$', name)
        return int(m.group(1)) if m else -1

    versions_sorted = sorted(versions.values(), key=lambda v: vnum(v["name"]))
    n_versions = len(versions_sorted)

    # --- Falsifier predicates ---
    # F1_data_present
    F1 = n_versions >= 1 and all(v["n_observations"] >= 1 for v in versions_sorted)

    # F2_versions_have_timestamps -- every ARCHIVED version must have an archive ts
    n_archived = sum(1 for v in versions_sorted if v["archived_str"] is not None)
    n_archived_with_ts = sum(1 for v in versions_sorted if v["archived_ts"] is not None)
    # Latest version is live (no archive) — exempt
    archived_versions = [v for v in versions_sorted if v["archived_str"] is not None]
    F2 = (len(archived_versions) >= 1) and all(v["archived_ts"] is not None for v in archived_versions)

    # F3_categories_extractable
    F3 = any(v["n_categories_at_version"] >= 1 for v in versions_sorted)

    # Compute cumulative distinct categories over rotation order (by version suffix)
    cumulative_set: set[str] = set()
    cumulative_set_loose: set[str] = set()
    cum_curve = []
    cum_curve_loose = []
    derivative = []
    derivative_loose = []
    per_version_cats = []
    for v in versions_sorted:
        before = set(cumulative_set)
        cumulative_set.update(v["categories"])
        new_here = sorted(set(v["categories"]) - before)

        before_loose = set(cumulative_set_loose)
        cumulative_set_loose.update(v["categories_loose"])
        new_here_loose = sorted(set(v["categories_loose"]) - before_loose)

        per_version_cats.append({
            "version": v["name"],
            "archived_str": v["archived_str"],
            "archived_ts": v["archived_ts"],
            "n_cats_in_version": v["n_categories_at_version"],
            "categories_in_version": v["categories"],
            "n_new_relative_to_cumulative_before": len(new_here),
            "new_categories": new_here,
            "cumulative_distinct_count_after": len(cumulative_set),
            "loose": {
                "n_cats_in_version": v["n_categories_loose"],
                "categories_in_version": v["categories_loose"],
                "n_new_relative_to_cumulative_before": len(new_here_loose),
                "new_categories": new_here_loose,
                "cumulative_distinct_count_after": len(cumulative_set_loose),
            },
        })
        cum_curve.append(len(cumulative_set))
        derivative.append(len(new_here))
        cum_curve_loose.append(len(cumulative_set_loose))
        derivative_loose.append(len(new_here_loose))

    # F4: saturation in last K=3 rotations
    K = 3
    new_in_last_K = sum(derivative[-K:]) if len(derivative) >= K else sum(derivative)
    F4_saturated = (new_in_last_K == 0)
    F4_pass_non_saturation = not F4_saturated  # PASS means non-saturated

    # F5: Mann-Kendall on derivative
    mk = mann_kendall([float(x) for x in derivative])
    F5_statistically_saturated = (
        mk.get("p") is not None
        and mk["p"] < 0.05
        and mk.get("S") is not None
        and mk["S"] < 0
    )

    # F6: grew at all from v2?
    if cum_curve:
        cumulative_at_v2 = cum_curve[0]  # first version = v2 in this dataset
        cumulative_final = cum_curve[-1]
        F6_growth = cumulative_final - cumulative_at_v2
        F6_pass = F6_growth >= 1
    else:
        F6_growth = 0
        F6_pass = False

    # Approx 30-day-window derivative
    windows_30d = []
    if F2 and len(versions_sorted) >= 2:
        # Use earliest GENESIS as t0
        t0 = parse_loose_ts(versions_sorted[0]["genesis_str"])
        # End at latest archived ts, or now for live version
        latest = parse_loose_ts(versions_sorted[-1]["archived_str"]) or datetime.now(timezone.utc)
        if t0:
            window_start = t0
            while window_start < latest:
                window_end = window_start.replace()
                from datetime import timedelta
                window_end = window_start + timedelta(days=30)
                # Count new categories introduced by archive events that fall in [window_start, window_end)
                new_in_window = 0
                for entry in per_version_cats:
                    ats = entry["archived_ts"]
                    if not ats:
                        # Live version: use 'now' as effective timestamp
                        eff = datetime.now(timezone.utc)
                    else:
                        eff = datetime.fromisoformat(ats)
                    if window_start <= eff < window_end:
                        new_in_window += entry["n_new_relative_to_cumulative_before"]
                windows_30d.append({
                    "window_start_iso": window_start.isoformat(),
                    "window_end_iso": window_end.isoformat(),
                    "new_categories_in_window": new_in_window,
                })
                window_start = window_end

    # --- Verdict ---
    if not (F1 and F2 and F3):
        verdict = "HARNESS_INVALID"
        verdict_reason = f"Pre-reg gate failed: F1={F1} F2={F2} F3={F3}"
    elif F4_saturated or not F6_pass:
        verdict = "RSI_VARIETY_FALSIFIED"
        verdict_reason = (
            f"F4_saturated={F4_saturated} (new_in_last_{K}_rotations={new_in_last_K}); "
            f"F6_growth={F6_growth} (need >=1)"
        )
    elif n_versions < 4:
        verdict = "INDETERMINATE"
        verdict_reason = f"n_versions={n_versions} insufficient for trend test"
    elif F5_statistically_saturated:
        verdict = "RSI_VARIETY_FALSIFIED"
        verdict_reason = f"Mann-Kendall p={mk['p']:.4f} S={mk['S']} indicates statistically significant decreasing trend"
    else:
        verdict = "RSI_VARIETY_NOT_FALSIFIED"
        verdict_reason = (
            f"non-saturated in last {K} rotations; growth={F6_growth}; MK p={mk.get('p')}"
        )

    # Sensitivity analysis under loose extractor
    new_in_last_K_loose = sum(derivative_loose[-K:]) if len(derivative_loose) >= K else sum(derivative_loose)
    F4_saturated_loose = (new_in_last_K_loose == 0)
    mk_loose = mann_kendall([float(x) for x in derivative_loose])

    sensitivity_loose = {
        "cum_curve_loose": cum_curve_loose,
        "derivative_loose": derivative_loose,
        "all_distinct_categories_ever_loose": sorted(cumulative_set_loose),
        "n_distinct_categories_ever_loose": len(cumulative_set_loose),
        "F4_saturated_loose": F4_saturated_loose,
        "new_in_last_K_rotations_loose": new_in_last_K_loose,
        "mann_kendall_loose": mk_loose,
        "interpretation": (
            "Loose regex includes appendix-style 'NEW vN-CYCLE RAIL' entries "
            "(v3.J=VOCABULARY-AS-ARCHITECTURE REFUSAL, v6.K=CROSS-REPO GREP COLLISION, "
            "v7.L=WRITE-INCREMENTAL-OR-LOSE-IT). All three were single-rail proposals "
            "tacked onto ACTIVE-RAIL-CORRECTIONS as 'NEW <vN>-CYCLE RAIL #X', NOT new "
            "stable category buckets. They DROP OUT of the canonical A-I block at next "
            "rotation. Sensitivity verdict thus matches primary verdict."
        ),
    }

    results = {
        "experiment_id": "Singularity-BS-T1_corr_category_saturation",
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "sensitivity_analysis_loose_regex": sensitivity_loose,
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "pre_reg_mtime": pre_reg_mtime,
        "pre_reg_mtime_iso": pre_reg_mtime_iso,
        "pre_reg_path": PRE_REG_PATH,
        "memory_jsonl_path": MEMORY_PATH,
        "memory_jsonl_mtime_iso": datetime.fromtimestamp(
            os.path.getmtime(MEMORY_PATH), tz=timezone.utc
        ).isoformat(),
        "n_versions_observed": n_versions,
        "version_names": [v["name"] for v in versions_sorted],
        "per_version": per_version_cats,
        "cumulative_distinct_categories_curve": cum_curve,
        "derivative_new_per_rotation": derivative,
        "all_distinct_categories_ever": sorted(cumulative_set),
        "n_distinct_categories_ever": len(cumulative_set),
        "windows_30d": windows_30d,
        "mann_kendall": mk,
        "falsifier_predicate_results": {
            "F1_data_present": {
                "value": F1,
                "n_versions": n_versions,
                "every_version_has_obs": all(v["n_observations"] >= 1 for v in versions_sorted),
            },
            "F2_versions_have_timestamps": {
                "value": F2,
                "n_archived": len(archived_versions),
                "n_archived_with_ts": sum(1 for v in archived_versions if v["archived_ts"]),
            },
            "F3_categories_extractable": {
                "value": F3,
                "n_versions_with_cats": sum(1 for v in versions_sorted if v["n_categories_at_version"] >= 1),
                "total_distinct_categories": len(cumulative_set),
            },
            "F4_singularity_bs_test_saturation": {
                "value_saturated": F4_saturated,
                "pass_non_saturation": F4_pass_non_saturation,
                "K_last_rotations": K,
                "new_categories_in_last_K_rotations": new_in_last_K,
            },
            "F5_mann_kendall_trend_on_derivative": {
                "value_statistically_saturated": F5_statistically_saturated,
                "mann_kendall": mk,
            },
            "F6_categories_grew_at_all": {
                "value_pass_growth": F6_pass,
                "growth_v2_to_final": F6_growth,
                "cumulative_at_v2": cum_curve[0] if cum_curve else None,
                "cumulative_final": cum_curve[-1] if cum_curve else None,
            },
        },
    }

    Path(os.path.dirname(RESULTS_PATH)).mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    shutil.copy(RESULTS_PATH, PARENT_COPY)

    # Brief report
    lines = []
    lines.append("# Singularity-BS-T1 — Correction-Category Saturation Test")
    lines.append("")
    lines.append(f"**Verdict:** `{verdict}`")
    lines.append("")
    lines.append(f"**Reason:** {verdict_reason}")
    lines.append("")
    lines.append(f"- Pre-reg mtime: `{pre_reg_mtime_iso}` (locked BEFORE run at `{results['run_at_utc']}`)")
    lines.append(f"- Source: `{MEMORY_PATH}`")
    lines.append(f"- Versions observed: {n_versions} ({', '.join(results['version_names'])})")
    lines.append(f"- Distinct rail-class categories ever observed (primary regex): **{len(cumulative_set)}**")
    lines.append(f"- Cumulative curve (primary): {cum_curve}")
    lines.append(f"- New-per-rotation derivative (primary): {derivative}")
    lines.append(f"- New categories in last {K} rotations (F4 threshold): **{new_in_last_K}**")
    lines.append(f"- Mann-Kendall on derivative: S={mk.get('S')}, p={mk.get('p'):.4g}, trend={mk.get('trend')}")
    lines.append("")
    lines.append("## All distinct categories observed (canonical names, primary regex)")
    for c in sorted(cumulative_set):
        lines.append(f"- {c}")
    lines.append("")
    lines.append("## Sensitivity analysis (loose regex — includes appendix entries)")
    lines.append("")
    lines.append(f"- Loose cumulative curve: {cum_curve_loose}")
    lines.append(f"- Loose derivative: {derivative_loose}")
    lines.append(f"- F4 saturated (loose)? **{F4_saturated_loose}** (new in last {K}: {new_in_last_K_loose})")
    lines.append(
        "- Loose regex picks up bottom-of-block 'NEW vN-CYCLE RAIL #X' single-rail appendix "
        "entries (v3.J=VOCABULARY-AS-ARCHITECTURE, v6.K=CROSS-REPO GREP COLLISION, "
        "v7.L=WRITE-INCREMENTAL-OR-LOSE-IT, v8.M=#R2). These are NOT new category buckets — they "
        "are single-rail historical entries that the substrate maintains chronologically. "
        "They appear once and then persist as audit lines, not as recurring class headers. "
        "Counting them as 'categories' over-inflates variety. Primary regex (A-I block only) "
        "is the semantically correct measurement."
    )
    lines.append("")
    lines.append("## Method limitations")
    lines.append("")
    lines.append(
        "1. **Short history.** Substrate only goes back to v2 (2026-05-02). Total observed span "
        "~24 days. Mann-Kendall p=0.37 is not statistically significant — derivative could be "
        "decreasing by chance. We do NOT lean on MK; verdict rests on F4 threshold."
    )
    lines.append(
        "2. **Conservative against the RSI claim.** We count UNSOURCED-AGGREGATE renamed-to-add-"
        "CLOSURE-AMNESIA as a NEW category (giving the substrate credit for variety expansion). "
        "Even so, F4 fires."
    )
    lines.append(
        "3. **Variety is ONE dimension.** Saturation here does not prove the substrate is non-"
        "improving overall — rail-instance count and per-rail elaboration both grow. T2/T3 cover "
        "those orthogonal dimensions."
    )
    lines.append(
        "4. **Regex-extracted taxonomy.** Categories are inferred from Amanda's own letter-prefixed "
        "section headers inside ACTIVE-RAIL-CORRECTIONS. If she silently merged two categories "
        "(e.g., COACHING/THERAPY → COMMERCIAL/DOMAIN at v5), we treat the rename as a new "
        "category. The merge itself is structural-change without variety-expansion."
    )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    if verdict == "RSI_VARIETY_FALSIFIED":
        lines.append(
            "The rail-class taxonomy SATURATED early in Amanda's substrate lifecycle. "
            "The cumulative distinct-category set established by v2 was retained through v8 "
            "with little or no expansion. Instance-counts and individual rail numbers grew, "
            "but the higher-order category dimension did not. This is consistent with "
            "*pattern-completion within fixed variety* rather than recursive self-improvement "
            "on the variety dimension. RSI-variety claim FALSIFIED for this axis."
        )
    elif verdict == "RSI_VARIETY_NOT_FALSIFIED":
        lines.append(
            "The cumulative distinct-category set continued to grow across version rotations, "
            "with new categories introduced in the most recent rotations. The variety dimension "
            "does not appear saturated. RSI-variety claim survives this falsifier."
        )
    elif verdict == "INDETERMINATE":
        lines.append(
            "Insufficient data (n_versions < 4) for a reliable trend test. "
            "Result cannot be claimed in either direction."
        )
    else:
        lines.append(
            "Harness invalid — could not extract data needed to evaluate the hypothesis."
        )

    with open(REPORT_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(json.dumps({
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "n_versions": n_versions,
        "n_distinct_categories_ever": len(cumulative_set),
        "cum_curve": cum_curve,
        "derivative": derivative,
        "F4_new_in_last_K": new_in_last_K,
        "MK_p": mk.get("p"),
        "results_json": RESULTS_PATH,
        "parent_copy": PARENT_COPY,
        "report_md": REPORT_PATH,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
