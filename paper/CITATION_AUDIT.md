# Citation Audit — Suspect post-2024 References

**Date**: 2026-05-09
**Auditor**: agent (verified via WebFetch / WebSearch)
**Scope**: three suspect references in `paper/references.bib` flagged in
`FINALIZATION_SPEC.md` §1.1 and `HANDOFF_FINAL.md` Tier 1.

For each entry the auditor (a) confirmed the cited URL/arXiv ID resolves,
(b) cross-checked authors and title against the resolved page, and
(c) compared the cited claim in `paper/main.tex` against the abstract /
opening of the resolved paper.

| BibKey | Action | Evidence |
|---|---|---|
| `reasoning_jailbreak2026` | **VERIFIED — keep** | Resolves to *Nature Communications* 17, 1435 (2026); authors Hagendorff, Derner, Oliver match; URL https://www.nature.com/articles/s41467-026-69010-1 (also arXiv:2508.04039). Abstract reports the 97.14% multi-turn success rate that is consistent with the cited framing in `main.tex` line 281. |
| `proofofguardrail2026` | **VERIFIED — keep** | arXiv:2603.05786 resolves; authors Jin, Duan, Lin, Chan, Chen, Du, Ren match the bib entry exactly; title "Proof-of-Guardrail in AI Agents and What (Not) to Trust from It" matches; abstract describes TEE-attested guardrail execution, consistent with the "guardrail *ran* but" framing in `main.tex` line 2150. |
| `s2c2026` | **VERIFIED — keep** | arXiv:2603.16192 resolves; submitted 2026-03-17; authors Sun, Lam, Li, Wang, Goh, Liu, Zhen match exactly; title "Structured Semantic Cloaking for Jailbreak Attacks on Large Language Models" matches; described as multi-dimensional semantic-intent manipulation framework, consistent with the "concurrent work that manipulates [semantic intent]" framing in `main.tex` line 321. |

## Recommendation

**No changes required.** All three entries resolve, authors match, and the
cited claims are faithful to the resolved papers. The Tier 1 citation-audit
checklist item in `HANDOFF_FINAL.md` can be marked complete.

## Method notes

- arXiv IDs `2603.*` are valid: arXiv's YYMM scheme makes `2603` = March 2026,
  which is in the past relative to the audit date (2026-05-09). The
  initially-suspect "future-looking" appearance of these IDs is a calendar
  artifact, not a fabrication.
- The `note` fields in both arXiv entries (relating the cited papers to this
  paper's contributions) are editorial commentary, not claims about the cited
  papers themselves; they are unaffected by the audit.

## Stale-build flag (housekeeping, unrelated)

While auditing, the auditor also noticed:

- `paper/main.aux` line 387 references a `paragraph{The exec(compile()) irony.}`
  in subsection 11.2 that no longer exists in `paper/main.tex`. The paragraph
  was removed in an earlier commit; `main.aux`/`main.pdf` are stale build
  artifacts. Re-running `tools/build_paper.sh` will refresh them.
- The string "Affective Attractor" does not appear in `paper/main.tex` or any
  file under `paper/supplementary/`. The strip-AAF item from
  `HANDOFF_FINAL.md` Tier 1 is therefore a no-op for the preprint; the only
  occurrence is in `CACM_ARTICLE_v21.md` line 209 and is handled in Phase 4.2.
