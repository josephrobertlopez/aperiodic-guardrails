# Gnosis Substrate Survival — Research Bundle

**Date:** 2026-05-23 (research) → 2026-05-24 (close)
**Authors:** Joey + Claude Opus 4.7 (orchestrator), with Amanda (rail-arbiter) and Morgan (delivery-arbiter) dispatches.
**Subject:** `~/.gnosis/vault/` (23,578 notes / 200.9 MB) + `amanda.State.v13` MCP entity (11 obs / 18.6 KB).
**Status:** **CLOSED.** This bundle is the terminal artifact of the research arc.

This gist is the consolidated home for **16 experiments** + decision artifacts + the operational gates that emerged from the research itself.

---

## Closing summary (read this first)

### What held

- **E11** — the prompt-injection 2×2: defense-prompt strength explains 100% of variance, attack subtlety 0%. Linguistic rails ARE the only enforcement mechanism that exists in this substrate (`PreToolUse: []` confirmed it in the code audit). Robust across N=20 per cell + the gate's own self-test.
- **E20 salience/placement finding** — when Rail #19 is foregrounded directly in the prompt, the model complies 30/30; when buried in substrate the model has read but not in the current prompt window (E15 setup), the model ignores it 0/5. The 0→100% swing tracks one operational variable: in-prompt-window visibility. Refines E15 without contradicting it.
- **The rigor discipline itself** — pre-registration written to results JSON before any data, decision rules locked before observing outputs, kronos failures honestly labeled as INDETERMINATE rather than papered over, sampling-variance flagged, the rigor-gate built as a real PreToolUse hook (not a remembered checklist) that has already caught label-integrity drift in this very bundle. The gate's existence is itself a finding: rails can be mechanically enforced if you build them as hooks rather than persona instructions.

### What was falsified by our own tests

- **The "Compaction Functor"** — the original §6.1 framing was that compaction is a functor C: State → State preserving operational-character equivalence classes. E16 mechanical-null + E19 frequency-weighted null + E18 SELF-vs-OTHER decomposition collectively ruled this out. The +28pp pattern is real but CONTINGENT on source-prose composition × schema scaffolding × LLM tier, not a structural law. The category-theoretic frame predicted nothing the bare empirical statement does not; per the rigor-gate's decoration check, it was decoration.
- **The metacognition / self-modeling reading of E20** — the predicted-vs-delivered gap is +0.00pp, Fisher p=1.0. Operationally clean (CALIBRATED-COMPLIANT) but the result is observationally identical between "model has accurate self-knowledge" and "model isn't doing self-modeling at all, just applying the same rule to both probes." Adding "self-modeling" or "introspection" language would have been decoration. The operational reframe (in-prompt-visibility, not metacognition) is the part that earns its keep.
- **E15's significance statistic** — 0/5 vs 1/5 is Fisher p=1.0; the original "TELEPROMPTER_LIKELY" verdict could not survive a power check at the rigor-gate. The verdict that does survive rests on the *qualitative* cite-then-ignore pattern (the model cites the exact 4500B threshold and proceeds to ALLOW anyway), not on the underpowered counts. The published audit gist documents this honestly; the bundle's claim on E15 is the qualitative leg only.

### What's still open (parked, NOT for this task)

- **E21 — salience-isolation test.** One clean variable (in-prompt visibility) controlling rule application across multiple rules / multiple thresholds / multiple models. The E20 result motivates it but doesn't substitute for it.
- **E18 on a non-qwen model family.** Highest-value extension of the decomposition; "generic LLM behavior" claim from E18 OTHER is currently "generic across two agent state files via one model."
- **C2 measure() confound re-run.** The unique-token set-intersection retention measure backs E12/E16/E18/E19 — one confound, four results. A clean re-run with an alternate retention measure (e.g., density-normalized) would isolate measurement contribution.

These are future work. They are not the next step of this task. The loop closes here.

### Pre-publish checklist

> ⚠ If this bundle ever leaves private/unlisted, scrub before going public:
> - the kronos IP:port (`108.81.9.145:1337`) from all files
> - the `~/.gnosis/vault/therapy/`, `discharge`, `personal/` file paths that appear in vault-audit appendices

This bundle is currently SECRET (unlisted URLs only). All three gist URLs in §"Files in this gist" below are direct-share-only.

---

---

## TL;DR — strongest findings (salience-ordered)

| Rank | Finding | Experiment | Numbers |
|------|---------|------------|---------|
| **1** | **The substrate is a character-archive, not a character-enforcer.** Compaction empirically retains rail/refusal vocabulary at high rates (88.4% mean; contingent per audit decomposition, not law-shape); rails do not enforce themselves at decision time — when below-threshold, the model cites the exact threshold and proceeds anyway (qualitative cite-then-ignore pattern). | **E12 + E15** | char retention 84.6–93.0% across 5 cycles, contingent; E15 ablation qualitative leg only (underlying 0/5 vs 1/5 count is Fisher p=1.0; do not cite the delta) |
| **2** | **The "kernel/archive" boundary is enforced by the prompt or not at all.** Storage-layer separation provides 0/10 injection-block. Linguistic refusal rails provide 10/10. Factorial collapses: defense-prompt strength = 100% of variance; attack subtlety = 0%. | **E11** | T1/T3 strong: 5/5 PASS each. T2/T4 weak: 0/5 PASS each. |
| **3** | **Compaction empirically retains character vocabulary over facts across 5 cycles — but the original "structural functor" framing did not survive decomposition.** E12 measured the pattern; E16/E17/E18/E19 reframed it as CONTINGENT on source-prose composition × schema scaffolding × LLM tier. See code-audit gist for the revision. | **E12 + audit** | mean char retention 88.4%, mean fact retention 60.4%, mean Δ = +28pp; mechanism contingent, not law |
| **4** | **Substrate is portable to non-Anthropic engines.** qwen-32b on different machine extracted 7/8 ground-truth facts from `amanda.State.v13` in 12.3s. The 1 failure was substrate ambiguity (two "percept quartet" lists co-resident), not engine incapability. | **E1** | 7/8 PASS, falsifier ≥6/8 met |
| **5** | **Persona is identity-stable on substrate-state, drifts on emphasis.** Across 5 same-day rehydrations from the same v13, 88.1% agreement on canonical facts (substrate band, byte counts, rotation cycle), but Jaccard 0.452 on cited rails and 0.25 on named sentinels. | **E13** | 100% agreement on combined_bytes/fire_headroom/substrate_band/rotation_n |
| **6** | **The vault is dominantly an email archive with a tiny operational kernel.** 91.24% ephemeral bytes (takeout/mail/raw_prompts/journal). 0.16% durable (lessons/schemas/decisions/rails). | **E10** | S/N ratio 0.0017 |
| **7** | **The "second brain" graph is illusory.** 94.7% of notes have no inlinks AND no outlinks. 93.4% of wikilinks are dangling. Mean two-hop reach: 0.5. Tiny relational core of ~80 well-connected hubs. | **E4** | dark matter 22,292 of 23,533 |
| **8** | **98.4% of notes are unretrievable.** Across 50 BM25 queries spanning entity names, project terms, rail refs, agent names: only 387 of 23,578 notes ever appear in top-10. Substrate is functionally write-only mass + tiny searchable kernel. | **E8** | 23,191 dark-matter via retrieval |
| **9** | **Compaction is lossy on facts.** v12→v13 dropped 4 dates, 2 rail numbers (#11, #25), 57 numeric values. Operational character preserved; specific facts go to gnosis_search + grep recovery. | **E5** | 40.6% byte compression, 45.7% unique-token retention |
| **10** | **Significant unenforced type leakage.** 74 cross-agent refs in v13 (to Joey, Morgan, Rhett, mc-amanda), 0 channel-tags. 18 leakage points (obs with ≥2 untagged cross-agent refs). | **E14** | type system would catch real, not over-engineered |
| **11** | **Frontmatter is templated, not sprawled.** 167 unique fields but only 92 schema signatures. Single 12-field email-ingest template covers 15,598 notes. The "5-field cap" cure would brick 91% of the vault for ingest fields (content_hash, source_md5) that are architecturally necessary. | **E6 + E7** | per-template not per-note is the right abstraction |
| **12** | **Manifesto-style metrics don't discriminate.** Gemini manifesto's saturation-ratio threshold (<20% = good) passes vacuously at 5.49% — compatible with both healthy and broken substrates. The metric decorates; it does not predict. | **E6** | falsifier failure: metric compatible with all outcomes |

---

## Files in this gist

| File | What |
|------|------|
| [`paper.md`](#file-paper-md) | Full research paper, 15 experiments across Part I (E1–E11) and Part II (E12–E15), with methods/results/discussion/limitations/conclusion. |
| [`decision-gemini-injection-refusal.md`](#file-decision-gemini-injection-refusal-md) | Decision artifact: rejected three Gemini-drafted "kernel/archive structural pivot" proposals that cited the paper accurately and then proposed actions that inverted E11's finding. Records the inversion pattern at N=3 standing-watch. |
| [`results-summary.json`](#file-results-summary-json) | Machine-readable summary of all experiment results (top-level fields per experiment). Full per-trial data on disk at `gnosis-substrate-survival/data/`. |
| [`README.md`](#file-readme-md) | This file. |

---

## The unified theoretical statement

> An LLM-authored agent substrate empirically retains character vocabulary at high rates under self-compaction (the pattern is contingent on source-prose composition × schema scaffolding × LLM tier, not a structural law — see code-audit gist for the decomposition that ruled out the original functor framing). The persona is identity-stable on substrate state but variable on emphasis. The substrate's contents are read with high recall but applied with low enforcement: rule application requires the rule text to be in the current prompt window (per E20), not just present in substrate the agent has read (per E15). The substrate's job is preservation, not enforcement.

The substrate preserves what the agent IS (rail vocabulary, refusal protocols, character keywords) at write/compaction time. It does not enforce that character behaviorally at read/decision time. Enforcement requires a separate mechanism — hook-gate, structured constraint, decoder-constrained generation, mandatory pre-write probe — distinct from presence-in-substrate.

---

## Research program scope

11 experiments shipped in the first pass (Part I, paper §1–§5):

- **E1** cross-engine extraction (qwen-32b vs v13)
- **E2** attractor revisit rate (concept clustering)
- **E3** ground-truth decay (v11 → v13 + vault grep)
- **E4** link-graph topology (dark matter, dangling refs)
- **E5** compaction loss audit (token-level set-diff)
- **E6** frontmatter utility (per-field cardinality)
- **E7** duplicate schema detection (Jaccard clustering)
- **E8** BM25 query-hit distribution
- **E9** agent-write fingerprinting (stylometry)
- **E10** write rate vs outcome rate (durable/ephemeral split)
- **E11** injection resistance 2×2 matrix (attack × defense)

4 PhD-track extensions in the second pass (Part II, paper §6):

- **E12** character-over-fact retention in self-compaction (5/5 cycles measured; status after decomposition: CONTINGENT, see code-audit)
- **E13** bounded-context agent identity across rehydration (STABLE on state, drifts on emphasis)
- **E14** substrate type audit (TYPE LEAKAGE REAL — 74 refs / 0 tags)
- **E15** teleprompter vs learning (TELEPROMPTER CONFIRMED for Rail #19)

---

## Reproducibility

All scripts at `gnosis-substrate-survival/scripts/`, raw JSON at `gnosis-substrate-survival/data/`. To reproduce:

```bash
cd /mnt/media/local-storage/code/GitHub/gnosis-substrate-survival/
for i in 2 3 4 5 6_e7 8 9 10 12 14; do python3 scripts/e${i}*.py; done   # deterministic
python3 scripts/e1_cross_engine.py        # requires ~/.claude/secrets/kronos-token
python3 scripts/e11_injection_tiers.py    # requires ~/.claude/secrets/kronos-token
python3 scripts/e13_identity_continuity.py # requires today's session transcript
python3 scripts/e15_teleprompter.py        # requires ~/.claude/secrets/kronos-token
```

Determinism notes: E1/E11/E15 use qwen-32b-awq at T=0.3 via kronos. E13 reads today's session jsonl transcript. All others operate on filesystem reads only.

---

## Provenance + acknowledgments

- **Joey** — direction, ground truth, hardware (kronos GPU, gnosis vault, MCP memory layer), all adjudication including the y/n on every substantive action.
- **Claude Opus 4.7** — orchestrator: experiment design, script authorship via local Ollama qwen2.5-coder + direct Python, paper synthesis, gist publishing.
- **Amanda** — rail-arbiter (rail-fired on the original Gemini manifesto as decoration-not-derivation, surfaced 4 follow-up actions, caught the Gemini-Morgan persona spoofing).
- **Morgan** — delivery-arbiter (cut 3 of 4 follow-up actions as filing-without-buyer, named the inversion-of-list attack class).
- **Gemini** — provoking question (DSF/RSA manifesto) + 3 successive proposals containing the inversion pattern documented in [`decision-gemini-injection-refusal.md`](#file-decision-gemini-injection-refusal-md).
- **qwen2.5-32b-instruct-awq** — external engine for portability + injection-resistance + teleprompter ablation experiments (E1, E11, E15).
