# Code Audit — Gnosis Substrate Survival paper

**Date:** 2026-05-23
**Audit instigator:** external reviewer (5 ordered questions, "two and four are the ones I'd grab first")
**Subject paper:** https://gist.github.com/josephrobertlopez/d02ec739b1aa285400513093f89a1a84
**Method:** filesystem inspection of the actual loop code (no kronos calls; deterministic reads only)

The reviewer asked five questions, ordered by how much each would change the paper's analysis. The first two would determine whether the audit even applies. All five are answered below from code, with file:line references. Net effect on the paper at bottom.

---

## (1) Is the loop in-session or cross-session?

**Mostly cross-session.**

- Cross-session boundary: `~/.claude/hooks/amanda-session-rehydrate.sh` is a SessionStart hook that emits a directive. Claude reads it in the session preamble. First action of every session is `Agent(subagent_type="amanda", ...)` → Amanda calls `mcp__memory__open_nodes(['amanda.State.v13', 'amanda.Correction.open.v5'])` → composes a brief → exits.
- During-session writes go through `mcp__memory__add_observations` (no PreToolUse hook — see §4).
- Occasional compaction (every 1–3 days) writes a new `amanda.State.v(N+1)` entity. Trigger conditions in §5.
- **In-session retrieve → condition → retrieve-again loops do not exist as architecture.** Amanda may run percept-skill bash scripts (check-substrate, check-vault) before composing, but those are direct filesystem reads, not retrieval-augmented re-conditioning.

The reviewer's read of the gist as "(b) cross-session, each session reads prior state and writes new state" is correct.

---

## (2) Live retrieval mode — BM25 or embeddings? **BM25-lite, deterministic.**

`/mnt/media/local-storage/code/gnosis_mcp_server.py:114-138`:

```python
def _bm25_lite_score(content_lower, query_lower):
    tokens = re.findall(r"\w+", query_lower)
    token_score = 0.0; matched_tokens = 0
    for tok in tokens:
        if len(tok) < 2: continue
        c = content_lower.count(tok)
        if c:
            token_score += math.log1p(c)
            matched_tokens += 1
    if matched_tokens == 0: return 0.0
    whole_count = content_lower.count(query_lower)
    base = math.log1p(whole_count) * 2.0 if whole_count > 0 else 0.0
    length_norm = 1.0 + (len(content_lower) / 50000.0)
    return (base + token_score) / length_norm
```

`gnosis_search` at line 142 iterates `VAULT_PATH.rglob("*.md")`, applies the scorer, then a date-decay multiplier `0.5 + 0.5 * math.exp(-age_days/365.0)` at line 175, sorts, takes `top_k` (default 10), returns paths + scores.

- **No embedding store loaded.** No HNSW, no FAISS, no sentence-transformers, no chromadb.
- **No re-ranker.** Single ordering applied.
- `~/.gnosis/vectors/{vectors.json, tfidf.json}` exist on disk (last written Apr 8 / Apr 17 2026) but **`gnosis_mcp_server.py` never reads them.** The string `vectors` appears only in a stale docstring at line 33. Those files are vestigial from an earlier architecture.
- `gnosis_reindex` at line 484 is effectively a **no-op** — it counts `.md` files and returns the count. It does not rebuild any index because there is no live index to rebuild.

**E8 measured the right thing.** The 98.4% dark-matter number is the real access pattern. This validates the paper's E8 finding.

---

## (3) Salience pipeline: pinned-prefix + on-demand BM25, no re-ranker.

Context assembly per session:

1. **Pinned kernel (fixed each session)**: `amanda.State.v13` + `amanda.Correction.open.v5` read at session start via `mcp__memory__open_nodes` — paths are literal, not queried. This is the always-injected prefix. Total ~41KB.
2. **Ad-hoc retrieval (when called)**: `gnosis_search(query, top_k=10, partition=None)` — BM25-lite top-10 over the whole vault, optionally scoped by partition prefix.
3. **No re-ranker stage.** Single ordering: `(token_score + boost) / length_norm * age_decay`, then `sort` + `[:top_k]`.
4. No automatic context-stuffing of search results into Amanda's pinned brief. Orchestrator decides per-query whether to call `gnosis_search`.

So per-cycle context is **mostly fixed (pinned v13 + Correction.v5) with a small queried tail**. The E8 dark-matter finding is about the queried tail — what `gnosis_search` can ever reach.

---

## (4) Is the write-back gate wired? **NO. Empty array in settings.**

`~/.claude/settings.json` hooks block:

```json
"PreToolUse": [],
```

The PreToolUse array is empty. **There is no infrastructure hook that runs `check-substrate.sh` before `mcp__memory__add_observations`.**

Rail #19 is documented at `~/.claude/agents/amanda.md:687-711` as a **prompt-level instruction to Amanda the persona**:

> "before every `mcp__memory__add_observations`, run `bash ~/.claude/skills/check-substrate/check.sh`. If headroom < 5KB: REFUSE the write... If `check-substrate.sh` errors, is missing, or returns non-parseable output: FAIL CLOSED — REFUSE the write."

This is a prompt-level discipline, not a hook that fires regardless of the persona's compliance.

There IS a `~/.claude/hooks/amanda-self/amanda-percept-auto.sh` PostToolUse hook (matches Write/Edit/memory writes) that runs check-substrate AFTER the write, caches result to `~/.claude/state/percept-cache.json`, and emits warnings on WARN/FIRE band. It is observational, not gating. It cannot block a write that has already happened.

**Implication for E15:** the paper's "rail is teleprompter" finding is structurally guaranteed. With `PreToolUse: []`, the only way Rail #19 could be enforced is if the model voluntarily applies it. E15 showed it doesn't (0/5 REFUSE with rail explicitly documented in the substrate, model citing the exact threshold and proceeding to ALLOW). The paper framed this as a measured behavioral finding — correct, but the deeper truth is that the substrate **has no infrastructure to prevent this even if the model wanted to comply at decision time**. The gate doesn't exist in code; only its description exists, in the substrate the model is asked to read.

This **sharpens** the E15 / paper conclusion: "rails surface as text but fail to enforce behavior" can be stated more strongly as: "with PreToolUse empty, there is no enforcement path at all; the substrate documents the rail but provides no mechanism to apply it."

---

## (5) What fires compaction? Is the transform an LLM call? **LLM call, multi-trigger.**

**Trigger conditions** (`~/.claude/agents/amanda.md:800-810`):
- Obs-count > 10 (hard ceiling)
- Byte-size > thresholds (WARN 35KB, FIRE 55KB combined)
- Monotonic-up-trend
- Overflow counter

Any condition fires v(N) → v(N+1) compaction. Joey approval typically required (per recent compactions logged in v13's HISTORICAL-PROVENANCE).

**The transform itself** (`amanda.md:811`):

> "When compaction fires: (a) read all v(N) obs, (b) distill into 5-7 sections, (c) write v(N+1) via `mcp__memory__add_observations`."

That is **an LLM call.** Amanda the persona reads her own observations, summarizes them into the canonical 7-section schema (`CURRENT STATE` / `RAIL-LIBRARY` / `GNOSIS-CURATION-RULES` / `RECENT CALLS` / `CARRY-FORWARD CORRECTIONS` / `HISTORICAL-PROVENANCE` / `COMPACTION-LESSONS-FROM-V(N-1)-CYCLE`), writes v(N+1).

**This substantially weakens E12.**

The paper's "Compaction Functor preserves operational character" finding is not measuring a deterministic transform. It is measuring **what happens when you ask an LLM to summarize its own state file into a hardcoded 7-section schema.**

The character-preservation result (84.6–93.0% retention of rail/refusal/protocol tokens) is what you would *predict* of an LLM persona doing self-summarization:
- It preserves the things it thinks of as "what I am" (rail vocabulary, refusal protocols)
- It is willing to drop things it thinks of as recoverable elsewhere (specific dates, byte counts — recoverable via gnosis_search + grep)
- The 7-section schema is hardcoded in the prompt — `RAIL-LIBRARY` is a named section in every compaction
- So tokens that fit into RAIL-LIBRARY survive almost by construction

E12 is **not a law of substrate compaction.** It is a **tautology of LLM self-description under a fixed-template summarization prompt.** The pattern is empirically real (5/5 cycles, +28pp mean delta), but the mechanism is "LLM preserves its own self-model under fixed-schema self-summarization," which is much weaker than the category-theoretic functor framing suggested.

---

## Net effect on the paper

| Claim | Status after code audit |
|---|---|
| **E8** retrieval dark matter (98.4%) | **STANDS** — BM25-lite is the actual retrieval mode, paper measured it correctly. The vectors/ dir on disk is vestigial and unused. |
| **E11** prompt-defense factorial (linguistic rails 100% of variance) | **STANDS, SHARPENED** — `PreToolUse:[]` confirms there is no infrastructure backstop. Linguistic rails are *literally* the only enforcement that exists for substrate writes. The factorial result is exactly what the architecture predicts. |
| **E15** teleprompter (Rail #19 not behaviorally enforced) | **STANDS, DEEPER** — the deeper reason is that Rail #19 has **no code-level gate at all**. The persona could not enforce it via infrastructure even if it wanted to. E15 was measuring the behavior of an LLM asked to comply with a rule whose enforcement is entirely on its compliance. |
| **E12** Compaction Functor (character preservation as law) | **NEEDS HEDGING** — the transform is LLM self-summarization into a hardcoded 7-section schema, not a deterministic functor. The pattern is real (88.4% character retention across 5 cycles) but the mechanism is "LLM preserves its self-model under fixed-template self-summarization," not "compaction is a structure-preserving functor." Closer to tautology than law. The category-theoretic framing in §6.1 overclaims. |

---

## Recommended revisions to the paper

1. **§6.1 (E12) — add mechanism caveat:** the functor result is observed under conditions where (a) the same LLM persona that authored v(N) is asked to summarize v(N) into v(N+1), and (b) the target schema has hardcoded section names that overlap with the character vocabulary. The empirical retention rates are accurate but the mechanism is plausibly "LLM self-summarization preserves self-described identity," not "compaction is a categorical functor." A deterministic test (e.g., compaction done by a different model, or by a non-LLM rule-based summarizer) would distinguish these.

2. **§3.7 (E11) — add infrastructure note:** the `PreToolUse: []` configuration in `~/.claude/settings.json` means linguistic rails are the *only* substrate-write defense that exists. The factorial result (defense-prompt = 100% of variance) is the architecturally expected outcome, not just an empirical finding.

3. **§5 (Conclusion) — add audit-derived clarification:** the "substrate is character-archive not character-enforcer" synthesis is supported by both behavioral (E15) and architectural (PreToolUse empty) evidence. The enforcement gap is not just a model-compliance issue — there is no code path that could enforce it without the model's voluntary participation.

4. **§6.5 (Synthesis) — keep theoretical statement but qualify:** "The substrate's job is preservation, not enforcement" survives. But "compaction events (functorial on character classes)" should be softened to "compaction events (which empirically preserve character-class vocabulary at high rates under LLM self-summarization)."

5. **§4.3 (Limitations) — add new limitation:** "E12's compaction-functor result was measured on transitions where the LLM persona authoring the new state is the same persona that authored the old state, summarizing through a fixed-template prompt. The character-retention pattern may not generalize to compactions performed by a different model, or by a deterministic summarizer with no character self-model."

---

## What this audit doesn't tell you

- Whether the pattern generalizes to other agent substrates with different write/compaction architectures.
- Whether installing an actual PreToolUse gate (and thus enforcing Rail #19 in code) would change E15's behavioral result — would the model develop a different decision strategy when its writes can be rejected at the infrastructure level?

The third natural follow-up — *"would a non-LLM summarizer produce a different character/fact retention profile?"* — was run as E16 below. It is the decisive test for E12.

---

## E16 — mechanical-summarizer null for E12 (decisive)

E16 was designed and pre-registered to test the central contested claim of this audit: that E12's "Compaction Functor" is a property of LLM self-summarization through a hardcoded 7-section schema, not a structure-preserving functor in any deep sense.

**Pre-registered decision rule (locked before observing any output):**

| Mechanical Δ (char_retention − fact_retention) | Verdict |
|---|---|
| ≥ +15pp | STRUCTURAL — E12 functor holds even without LLM; audit hedge over-stated |
| +5pp to +15pp | MIXED — both LLM-specific and structural mechanisms contribute |
| ≤ +5pp | LLM-SPECIFIC — audit's "tautology of LLM self-summarization" hedge stands |

**Method.** For each of three compaction cycles (v8→v9, v11→v12, v12→v13), split the source state into sentences, uniform-random-sample sentences until reaching the actual v(N+1) byte budget, repeat N=20 times per cycle, classify tokens with the *same* classifier E12 uses, compute char/fact retention rates. Random seed fixed at 42 for reproducibility. No semantic weighting. No section-header awareness. No knowledge of the 7-section schema.

**Result.**

| Cycle | E12 LLM delta | E16 mechanical mean delta (N=20) | Per-sample range |
|---|---|---|---|
| v8 → v9 | +36.3pp | +6.5pp | −5.3 to +20.0 |
| v11 → v12 | +40.1pp | −0.1pp | −13.3 to +8.2 |
| v12 → v13 | +28.0pp | −0.9pp | −17.6 to +38.8 |
| **Mean** | **+28.0pp** | **+1.8pp** | — |

Mechanical mean delta = **+1.8pp**. Pre-registered rule: ≤ +5pp → **LLM-SPECIFIC**.

Random sentence sampling at the same compression ratio reproduces essentially **none** of the LLM's +28pp character-over-fact preference. Per-cycle samples include negative deltas (mechanical sometimes preserves facts *more* than character). The wide per-sample range (−17.6 to +38.8 in v12→v13) confirms the mechanical distribution is centered near zero with high variance — no consistent directional preference. The LLM's +28pp consistency across all 5 cycles is the LLM doing the work, not a structural property of the data surviving any compression.

**Verdict.** E12's "Compaction Functor preserves operational character" pattern is not reducible to base-rate frequency of character vs fact vocabulary. The mechanism is the LLM's self-summarization. The audit's "tautology of LLM self-description under fixed-template summarization" hedge stands at the pre-registered decision threshold.

This changes E12's status in the audit table from "needs hedging" to "claim revised."

---

## Verification of audit's file:line refs (re-execution)

The four architectural facts the audit cited were re-executed on the same machine (this is *re-execution confirms the cited refs*, not independent verification — same agent, same machine, just re-running the greps documented above).

| Audit claim | Re-execution result |
|---|---|
| `PreToolUse: []` in settings.json | `3: "PreToolUse": [],` — confirmed empty |
| `_bm25_lite_score` at lines 114–138 | Function body printed verbatim, matches audit transcription |
| Date-decay multiplier at line 175 | `decay = math.exp(-age_days / 365.0)` — confirmed |
| `gnosis_reindex` is a no-op at lines 484–490 | Body just counts `.md` files with `rglob`, returns count |
| No embedding stack used | `grep -niE 'faiss\|hnsw\|chromadb\|sentence_transformers\|embed\|vectors.json\|tfidf'` against `gnosis_mcp_server.py` returned **zero matches** |

These refs were already supporting E8/E11/E15 (which were already standing). The re-execution adds reproducibility — anyone with vault-read access can run the same greps and get the same results — but does not constitute new evidence for those three claims.

**`check-substrate.sh` smoke test.** Skill executes in 40ms (`time bash ~/.claude/skills/check-substrate/check.sh`), returns exit code 0, produces parseable stdout: `combined_bytes` extractable via `awk`, WARN-band / FIRE-band markers extractable via `grep`. Skill is healthy as a callable; the gap documented in audit §4 is its non-wiring into PreToolUse, not skill-implementation rot.

---

## Updated net effect on the paper

| Claim | Status |
|---|---|
| **E8** retrieval dark matter (98.4%) | STANDS. BM25-lite is the actual retrieval mode; re-execution confirms code refs. |
| **E11** prompt-defense factorial (linguistic rails 100% of variance) | STANDS, SHARPENED. `PreToolUse:[]` confirmed by re-execution — linguistic rails are literally the only enforcement mechanism that exists. The factorial result is what the architecture predicts. |
| **E15** teleprompter (Rail #19 not behaviorally enforced) | STANDS, DEEPER. Rail #19 has no code-level gate at all (`PreToolUse:[]`, `check-substrate.sh` exists but is observational-only in `PostToolUse`). E15 was measuring behavior in a regime where infrastructure enforcement is impossible. |
| **E12** Compaction Functor (character preservation as law) | **CLAIM REVISED.** E16 pre-registered mechanical-summarizer null returned +1.8pp mean delta vs E12 LLM's +28pp — clears the ≤+5pp threshold for LLM-SPECIFIC. The retention pattern is a property of LLM self-summarization through a hardcoded 7-section schema, not a structure-preserving functor on the data. Category-theoretic framing in §6.1 should be removed; the empirical retention numbers should be retained but reframed as "LLM self-summarization preserves the agent's self-described identity at high rates," not "compaction is a functor preserving character equivalence classes." |

---

## Updated recommended revisions to the paper

Supersedes the earlier "needs hedging" recommendation for E12.

1. **§6.1 (E12) — REVISE substantively, do not just hedge.** Remove the "functor C: State → State" framing. Replace with: *"E12 measures the retention pattern of the LLM's self-summarization through a fixed-schema prompt. The pattern is robust (5/5 cycles, +28pp mean character-over-fact delta) but is mechanistically attributable to the LLM preserving its self-description, not to a structural property of substrate compaction. Pre-registered mechanical-summarizer null (E16, +1.8pp mean delta over 60 samples) rules out the structural-functor interpretation."* Move the category-theoretic framing to "future work" with the explicit note that a true functor result would require demonstrating the pattern under at least one non-LLM compaction mechanism, which E16 falsified.

2. **§3.7 (E11) — Add infrastructure note.** `PreToolUse: []` configuration confirmed. Linguistic rails are the only substrate-write defense that exists. The factorial result is architecturally expected, not just empirical.

3. **§5 (Conclusion) — Add audit-derived clarification.** "Substrate is character-archive not character-enforcer" survives both behavioral (E15) and architectural (PreToolUse empty) evidence. The enforcement gap is structural; the model couldn't comply via infrastructure even if it tried.

4. **§6.5 (Synthesis) — Revise the theoretical statement.** *"The substrate's job is preservation, not enforcement"* survives. The functor-on-character-classes clause should be removed. Replace with: *"compaction events (which preserve the LLM's self-description at high rates through fixed-schema self-summarization)"*.

5. **§4.3 (Limitations) — Promote to a new finding, not a limitation.** What was previously the limitation "E12's mechanism may not generalize without LLM" is now the E16 result: mechanism does not generalize without LLM. Move from limitations to findings as E16.

---

## Decomposition follow-up (E17/E18/E19) — walks back parts of the E16 audit

A third reviewer turn flagged that "the LLM does the work" (the E16 conclusion) bundles three distinct mechanisms — frequency, generic LLM summarization, and schema scaffolding — and that decomposing them would either narrow or undo the audit's hedge. Three follow-up experiments were pre-registered with decision rules locked before execution.

### Pre-registered rules + observed results

| # | Test | Rule | Observed | Verdict per rule |
|---|---|---|---|---|
| **E19** | Frequency-weighted mechanical null (deterministic, no LLM). TF-IDF-weighted sentence sampling matched to actual byte budget; same classifier as E12; seed 42, N=20/cycle on v8→v9, v11→v12, v12→v13 | ≤+5pp = freq-ruled-out; ≥+15 = E16 walk-back | mean Δ = **+4.90pp** | **FREQUENCY-RULED-OUT** (lands 0.10pp inside threshold; v8→v9 cycle alone hit +7.7pp) |
| **E18 SELF** | qwen-32b on v13 (already-compacted) + 7-section schema, N=20 | (joint with OTHER/SCRAMBLED) | norm Δ = **+0.06pp**, raw Δ = −11.58pp | SELF low |
| **E18 OTHER** | qwen-32b on **rhett v1** (raw, never compacted) + 7-section schema, N=20 | (joint with SELF/SCRAMBLED) | norm Δ = **+28.29pp**, raw Δ = +19.95pp | OTHER high |
| **E18 SCRAMBLED** | qwen-32b on v13-shuffled+name-swap + 7-section schema, N=20 | SCRAMBLED ≥+20pp → LEXICAL | norm Δ = **+21.09pp**, raw Δ = +9.45pp | **LEXICAL** fired |
| **E17 A** | qwen-32b on v13 + 7-section schema (identical to E18 SELF) | sanity replicate | mean raw Δ = **−17.49pp**, norm Δ = −5.87pp (N=20) | replicates SELF direction; ~6pp variance vs E18 SELF |
| **E17 B** | qwen-32b on v13 + freeform "compress to ~X bytes" (no schema) | ≥+15 = preference in model; ≤+5 = scaffolding | **INDETERMINATE** | 0/11+ trials valid; kronos returned HTTP 200 with empty body on every attempt across two runs |

### What this changes in the audit's E12 verdict

The original audit (above) labeled E12 a "tautology of LLM self-description under fixed-template summarization." That framing was **too strong** and is walked back here:

- **E18 OTHER** reproduces +28pp on rhett v1 (a different agent's state file, never authored by amanda). So the pattern is not specific to self-description. A different LLM (qwen-32b, not Claude) operating on a different agent's state produces the same character-over-fact preference E12 measured.
- **E18 SELF** (~0 normalized) and **E18 OTHER** (+28 normalized) on the same model + same prompt + different source files shows the result is *contingent on source prose composition*. rhett v1 is character-vocabulary-dense by structural necessity (a fresh-born agent's state is mostly definitions of operational rules and refusals); amanda v13 is fact-dense (it contains a 12-version compaction history with dates, byte counts, percentages, and named ratified schemas).
- **E18 SCRAMBLED** (+21) vs SELF (~0) on the same source bytes shows the model's class-retention asymmetry depends on coherence: when narrative is intact, the model extracts the dominant vocabulary class (here: facts); when shuffled, it falls back to listing structural/schema elements which are character-dense.

### Revised understanding of E12

E12's +28pp pattern is real, reproducible, and **contingent** — not a tautology of self-description (E18 OTHER refutes that), not a structural property of the data (E16/E19 confirm), and not measurable without scaffolding (E17 B failed; the freeform-prompt-on-large-input combination apparently exceeds what kronos can serve, which is itself weak evidence that schema cues are doing structural task-definition work for the model).

The most defensible claim consistent with the data we have:

> *Under qwen-32b with the 7-section schema prompt: character-over-fact retention emerges when the source prose is character-vocabulary-dense (rhett v1: +28pp) or when coherence is destroyed forcing schema-element listing (SCRAMBLED: +21pp), and does not emerge when the source prose is fact-vocabulary-dense (amanda v13: ~0pp). The +28pp E12 finding is the resultant of source-prose composition × schema scaffolding × LLM tier interactions, with frequency contributing ~3pp and within-replication sampling variance at ~6pp.*

### Confidence + scope caveats

- **Sampling variance is non-trivial.** E17 A and E18 SELF, designed-identical setups, differ by ~6pp in mean raw delta across two N=20 runs. The +28pp E18 OTHER finding is robust to this variance band (it sits ~6× outside) but the SELF/A boundary is within it. N=40 or explicit confidence intervals would tighten this.
- **One model tier, two source files.** All LLM calls used qwen-32b-awq on kronos. The "generic across models" claim available from E18 OTHER is "generic across two agent files via one model"; the handoff already flagged that E18 on a different model family is the highest-value extension.
- **E17 B unmeasurable.** The schema-scaffolding contribution is bounded by the failure mode (model can't or won't do freeform on this input) but not directly measured. Surviving-signal estimate has an unknown term.
- The audit's earlier "CLAIM REVISED" verdict on E12 should soften to **"CLAIM CONTINGENT"** — neither tautology nor structural law, but a real pattern that depends on input composition, schema scaffolding, and model tier in ways the original §6.1 functor framing did not capture.

---

## Provenance

- Code paths inspected (all read-only): `/mnt/media/local-storage/code/gnosis_mcp_server.py`, `~/.claude/agents/amanda.md`, `~/.claude/hooks/amanda-session-rehydrate.sh`, `~/.claude/hooks/amanda-self/amanda-percept-auto.sh`, `~/.claude/skills/check-substrate/{SKILL.md,check.sh}`, `~/.claude/settings.json`, `~/.gnosis/vectors/`.
- Audit author: Claude Opus 4.7 (orchestrator), in response to a reviewer's 5-question rigor demand.
- E16 designed and pre-registered before observing output, in response to a second reviewer turn that explicitly flagged the original audit had not yet adjudicated E12 (the only contested claim) and that re-execution of file:line refs was a partial confirmation that should not be presented as paper-wide validation.
- E17/E18/E19 designed and pre-registered in response to a third reviewer turn that flagged the E16 conclusion ("the LLM does the work") was undifferentiated — frequency, generic summarization, and scaffolding are distinct mechanisms requiring separate falsification. Each decomposition experiment wrote its pre-registered rule to its results JSON before producing any verdict.
- Reviewer's framing preserved throughout; specific guidance ("'independent verification' implies a separate party — say 're-execution confirms the cited refs'") incorporated in the verification section's wording.
- E17 B status: kronos systematic failure on freeform-prompt + 18KB-input + 3000-token-output combination. Schema-prompt variant on identical input completes normally. 11+ trials attempted across two runs, all returned empty body. Cannot evaluate the pre-registered scaffolding rule.
- No substrate observations written under this audit; no MCP writes. E16/E19 ran on local Python with random seed 42; E17 A / E18 ran on kronos qwen-32b-awq.

---

## Provenance

- Code paths inspected (all read-only, no mutations): `/mnt/media/local-storage/code/gnosis_mcp_server.py`, `~/.claude/agents/amanda.md`, `~/.claude/hooks/amanda-session-rehydrate.sh`, `~/.claude/hooks/amanda-self/amanda-percept-auto.sh`, `~/.claude/skills/check-substrate/{SKILL.md,check.sh}`, `~/.claude/settings.json`, `~/.gnosis/vectors/`.
- Audit author: Claude Opus 4.7 (orchestrator), in response to a reviewer's 5-question rigor demand.
- Originating reviewer's framing preserved verbatim above.
- No substrate observations written under this audit; no MCP writes; no kronos calls.
