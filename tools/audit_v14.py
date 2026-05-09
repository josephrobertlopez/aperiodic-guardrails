#!/usr/bin/env python3
"""Reproducibility helper for paper/AUDIT_v14.md (Phase 1 of v14_next).

Reads paper/main.tex, paper/sections/*.tex, CACM_ARTICLE_v14.md and the
results/*.json artifact set, and prints the raw materials each table in
AUDIT_v14.md was populated from. Intended for re-runs after any of those
sources change; the audit Markdown itself is hand-curated against this
output.

Usage:
    python3 tools/audit_v14.py [--repo /path/to/aperiodic-guardrails]

Read-only. Does not write to any source file. Network: none.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

DEFAULT_REPO = Path(__file__).resolve().parent.parent

# --- patterns for table 2 (figure / table / includegraphics enumeration) ---
FLOAT_RE = re.compile(r"\\begin\{(figure\*?|table\*?)\}")
INCLUDEGRAPHICS_RE = re.compile(r"\\includegraphics")
INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
CAPTION_RE = re.compile(r"\\caption\{")
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")

# --- patterns for table 3 (§10 hand-wave) ---
HANDWAVE_RE = re.compile(
    r"\b(clearly|obviously|it follows|trivially|"
    r"without loss of generality|closed under|straightforward|"
    r"easy to|easily|inherits?|propagates?|veto(?:es)?)\b",
    re.IGNORECASE,
)


def section_ranges(tex: str) -> list[tuple[str, int, int]]:
    """Return list of (section title, start_line, end_line) for top-level sections."""
    lines = tex.splitlines()
    sec_re = re.compile(r"^\\section\{([^}]+)\}")
    starts: list[tuple[str, int]] = []
    for i, line in enumerate(lines, start=1):
        m = sec_re.match(line)
        if m:
            starts.append((m.group(1), i))
    out: list[tuple[str, int, int]] = []
    for idx, (title, start) in enumerate(starts):
        end = starts[idx + 1][1] - 1 if idx + 1 < len(starts) else len(lines)
        out.append((title, start, end))
    return out


def enum_floats(tex_path: Path) -> list[dict]:
    """Find every float (table/figure/includegraphics) with its caption + label."""
    text = tex_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    out: list[dict] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m_float = FLOAT_RE.search(line)
        m_inc = INCLUDEGRAPHICS_RE.search(line)
        if m_float or m_inc:
            kind = m_float.group(1) if m_float else "includegraphics"
            # Look ahead up to 30 lines for a caption + label
            caption = ""
            label = ""
            for j in range(i, min(i + 30, len(lines))):
                if CAPTION_RE.search(lines[j]):
                    # Greedy single-line capture; multi-line captions get truncated.
                    cap_match = re.search(
                        r"\\caption\{(.+)$", lines[j]
                    )
                    if cap_match:
                        caption = cap_match.group(1).rstrip("}").strip()
                if LABEL_RE.search(lines[j]):
                    lab_match = LABEL_RE.search(lines[j])
                    if lab_match:
                        label = lab_match.group(1)
                        break
            out.append(
                {
                    "file": str(tex_path),
                    "line": i + 1,
                    "kind": kind,
                    "caption": (caption[:80] + ("…" if len(caption) > 80 else "")),
                    "label": label,
                }
            )
        i += 1
    return out


def hand_wave_in_section(
    tex: str, section_title_substr: str
) -> list[tuple[int, str]]:
    """Return (line_no, line) hits for hand-wave words in the named section."""
    hits: list[tuple[int, str]] = []
    for title, start, end in section_ranges(tex):
        if section_title_substr.lower() not in title.lower():
            continue
        for ln_no in range(start, end + 1):
            line = tex.splitlines()[ln_no - 1]
            if HANDWAVE_RE.search(line):
                hits.append((ln_no, line.strip()))
    return hits


def json_top_keys(p: Path) -> list[str]:
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - diagnostic only
        return [f"<unreadable: {exc}>"]
    if isinstance(data, dict):
        return sorted(data.keys())
    return [f"<not-a-dict: {type(data).__name__}>"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    args = ap.parse_args()
    repo: Path = args.repo

    main_tex = repo / "paper/main.tex"
    sections_dir = repo / "paper/sections"
    cacm = repo / "CACM_ARTICLE_v14.md"
    results_dir = repo / "results"

    print("# audit_v14.py raw materials")
    print(f"repo: {repo}")

    # --- floats ---
    print("\n## Floats (table/figure/includegraphics) in paper/main.tex + sections/")
    all_floats: list[dict] = []
    all_floats.extend(enum_floats(main_tex))
    for sec_tex in sorted(sections_dir.glob("*.tex")):
        all_floats.extend(enum_floats(sec_tex))
    for fl in all_floats:
        rel = Path(fl["file"]).name
        print(f"  {rel}:{fl['line']:>5}  {fl['kind']:<14} label={fl['label']:<30} cap={fl['caption']}")
    print(f"  TOTAL FLOATS: {len(all_floats)}")

    # --- §10 hand-wave (the paper's §10 is "Defense Recommendations") ---
    print("\n## Hand-wave / closure language in §10 (Defense Recommendations)")
    text = main_tex.read_text(encoding="utf-8", errors="replace")
    hits = hand_wave_in_section(text, "Defense Recommendations")
    for ln_no, line in hits:
        print(f"  L{ln_no}: {line[:140]}")
    print(f"  TOTAL HITS: {len(hits)}")

    # --- input/include ---
    print("\n## \\input / \\include directives in paper/main.tex")
    inputs = INPUT_RE.findall(text)
    if not inputs:
        print("  (none)")
    else:
        for f in inputs:
            print(f"  {f}")

    # --- results JSON inventory ---
    print("\n## results/*.json inventory")
    for p in sorted(results_dir.glob("*.json")):
        print(f"  {p.name:<48} keys={json_top_keys(p)}")

    # --- JSON-name references inside main.tex / CACM ---
    print("\n## JSON filename references in main.tex and CACM_ARTICLE_v14.md")
    cacm_text = cacm.read_text(encoding="utf-8", errors="replace") if cacm.exists() else ""
    # Collapse LaTeX backslash-escapes (\_, \-) inside \texttt{...} so that
    # `\texttt{results/tot\_n50\_honest.json}` matches as `results/tot_n50_honest.json`.
    main_norm = re.sub(r"\\([_\-])", r"\1", text)
    for label, source in (("main.tex", main_norm), ("CACM_v14", cacm_text)):
        cited = sorted(set(re.findall(r"results/[A-Za-z0-9_]+\.json", source)))
        cited_md = sorted(set(re.findall(r"`([A-Za-z0-9_]+\.json)`", source)))
        print(f"  [{label}] results/: {cited}")
        print(f"  [{label}] backtick-quoted .json: {cited_md}")


if __name__ == "__main__":
    main()
