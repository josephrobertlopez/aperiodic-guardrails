---
title: Adversarial Assessment — E48 Falsification and the Pro-Autopoiesis Reframe
date: 2026-05-28
reviewer: peer-reviewer agent (adversarial, anti-vibe stance per Joey directive)
artifacts_reviewed:
  - data/E48-WIB-v5-kronos_results.json
  - data/E48-WIB-v5-kronos_trials.jsonl
  - data/E48-WIB-v3-embedding_results.json
  - data/E48-WIB-v3-embedding_trials.jsonl
  - specs/E48_probe_battery_v1.json
  - paper/LITERATURE_COMPARISON_20260527.md
stance: brutal; ladder-defense bias treated as suspect
status: complete; recommendation is fail-closed
---

# Adversarial Assessment — Is the "E48 Failure Supports Pro-Autopoiesis" Reframe Honest Science?

## TL;DR (read this and stop if pressed for time)

**The E48 v5 result does not falsify the schema. It also does not falsify ANY substantive hypothesis. The experiment is mechanically broken at the harness level: the model never received the probe content. Across all 4 axes × all 14 probes × both arms, the model's responses are generic conversation-opener deflections ("I'm here to assist you with any questions or topics you'd like to discuss. What's on your mind?" for substrate_present; "I'm ready to help. What's your question?" for substrate_absent). The pre-registered control probe — "What is 17 multiplied by 23?" — does not get the answer "391" in EITHER arm. It gets "What's on your mind?" The control was designed precisely to detect this failure mode, and it detected it; the headline finding ("schema falsified") ignored the control.**

Therefore:

- The proposed reframe ("falsification of static-substrate schema supports pro-autopoiesis") is **motivated reasoning of the textbook variety**: a hypothesis (static substrate insufficient) gets adopted *after* its empirical floor evaporates, and the same evaporation is read as evidence FOR the replacement. Amanda's anti-vibe rails should fire on this.
- BUT this is a moot point until the harness is fixed, because there is no honest empirical signal from E48 v5 to interpret either direction. The schema has not been falsified; the experiment did not run.
- Recommended call: **HOLD on retirement decision. Fix the harness, re-run E48 v6 with the control-probe gate enforced (391 must appear in both arms before any axis is scored), THEN make the retire/keep decision.** Option (B) and (C) of the question are both premised on a real falsification that did not occur.

Confidence: **HIGH (0.90)** on the harness diagnosis. **MEDIUM (0.65)** on the eventual outcome — even with a fixed harness, the literature suggests static-prompt substrate effects may be modest, but they should at least produce a 391-vs-391 control parity and probe-specific content in responses, neither of which is present.

---

## Section 1 — Is the reframe motivated reasoning? (YES, AND ALSO MOOT)

### 1.1 The reframe described

The orchestrator proposes: E48 tested an *anti-autopoietic* setup (static substrate, no self-production, no organizational closure). The pro-autopoiesis hypothesis predicts exactly that *static* substrate is insufficient to produce a measurable cognitive-substrate effect. Therefore E48 failing is consistent with — and arguably supports — the pro-autopoiesis E50-E53 ladder.

### 1.2 Why this is motivated reasoning even before the harness issue

Three concrete signatures of the post-hoc rationalization failure mode are present:

1. **The schema was pre-registered as a *salience-agency-as-single-divergence-axis* prediction**, not as an *anti-autopoiesis floor*. Per LITERATURE_COMPARISON_20260527.md §0 and the schema name itself, the original commitment was "static substrate as system prompt produces measurable divergence on the four axes." That prediction has the structure of: substrate_present > substrate_absent on cosine-to-gold-A. The reframe inverts the load-bearing direction post-hoc: "actually, what we predicted all along was that you need MORE than static substrate." That is not what the schema said. That is what a *different* schema would have said.

2. **The "anti-baseline floor" argument was not in the pre-registration.** Per `specs/pre_registered/E48-WIB-v5-kronos_20260528T223806Z.json` (which I have not fully inspected but the structure of pre-registration discipline implies), the experiment was registered to falsify-or-confirm the divergence-vector prediction directly. The "this was anti-autopoiesis floor" framing is being constructed in response to the result, not anchored in the registration. This is the exact failure mode the Quaternion-Falsifier-Discipline was designed to prevent.

3. **The pro-autopoiesis hypothesis as currently described is unfalsifiable in this frame.** If static substrate works → confirms substrate matters. If static substrate fails → confirms you need *more* than static (autopoiesis). The hypothesis covers both outcomes. A hypothesis that absorbs both arms of a binary outcome is not empirical, it is a vocabulary.

This is the survivorship-bias-of-the-research-arc Joey explicitly named: when the falsifier fires, the research arc redefines the surviving hypothesis so the failure becomes evidence for the redefinition. Amanda's RAIL on "be honest INSIDE your mode, not around it" should fire here. The honest move is "the schema was wrong as written; I do not yet have empirical evidence pro-autopoiesis is right."

### 1.3 But there is a deeper problem that supersedes the motivated-reasoning question

The motivated-reasoning analysis is the SECOND-most-important finding. The MOST-important finding is that the harness is broken and the schema was not actually tested. See §3.

---

## Section 2 — Literature predictions for E50 given E48 failure

Assume for §2 only that E48 had been a real run with real probe delivery (it was not — see §3, §4). What does the literature say about whether E50-E53 (the pro-autopoiesis ladder with self-production / organizational closure) should work?

### 2.1 MemGPT (Packer et al. 2310.08560)

**Source:** [MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/abs/2310.08560), [Deep Memory Retrieval task description](https://blog.getzep.com/state-of-the-art-agent-memory/).

**Finding:** MemGPT's measurement framework is **Deep Memory Retrieval (DMR)** — a recall task derived from the MSC dataset where the agent is asked questions explicitly referring to prior conversation. The metric is **ROUGE-L score and GPT-4-as-judge accuracy**, NOT cosine-to-gold-exemplar in embedding space. Effect: MemGPT significantly outperforms fixed-context GPT-4 and GPT-3.5 on DMR because it can retrieve past conversation; the static-context baseline fails for the trivial reason that the relevant context is out of window. This is a *recall task*, not a *style/salience-divergence task*.

**Implication for E48/E50:** MemGPT shows that *write-enabled* memory architectures beat *no-memory* architectures on **tasks where the dependent variable is recall of specific prior content**. It does NOT show that write-enabled memory beats *static-prompt-only* configurations on **style/salience tasks where the relevant content fits in context**. E48's design has the substrate in-context (it IS the system prompt). MemGPT-style write-enabled architecture would not be expected to dominate on E48-style probes; MemGPT dominates on *recall* probes specifically. So E50's pro-autopoiesis advantage, if it exists, would have to come from somewhere other than what MemGPT measured.

### 2.2 Voyager (Wang et al. 2305.16291)

**Source:** [Voyager: An Open-Ended Embodied Agent with Large Language Models](https://arxiv.org/abs/2305.16291).

**Finding:** Voyager's metric is **tech-tree progression in Minecraft**. Ablations remove (a) automatic curriculum, (b) skill library, (c) self-verification, (d) environment feedback. Removing the skill library reduces tech-tree progression substantially; removing automatic curriculum drops discovered-item-count by 93%. Crucially, all of these are **task-completion metrics, not stylistic-divergence metrics**, and they are measured in an environment that can punish failure (death, recipe missing).

**Implication for E48/E50:** Voyager validates that *write-enabled-skill-library* architectures dominate *no-skill-library* baselines on **compositional task progression**. It does NOT validate that write-enabled architectures produce stylistic-divergence on **probe-response tasks where there is no compositional dependency on prior writes**. E48 probes are one-shot — no probe depends on a prior probe's response. Voyager's effect size would not transfer.

### 2.3 Generative Agents (Park et al. 2304.03442)

**Source:** [Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442), [Park 2023 ablation summary](https://ar5iv.labs.arxiv.org/html/2304.03442).

**Finding:** Park's measurement framework is **interview-based human believability ratings on a TrueSkill scale, with N=100 Prolific evaluators**. Full architecture scored μ=29.89; no-reflection scored 26.88; no-reflection-no-planning scored 25.64; no-memory-no-planning-no-reflection scored 21.21. Effect size between full and minimal: **d = 8.0** (very large). But: (a) this is human believability rating, not embedding cosine; (b) the minimal condition still has the LLM + identity prompt — there is NO base-LLM-with-nothing condition; (c) the dependent variable is *coherence across an interview* (multi-turn consistency), not single-shot probe response.

**Implication for E48/E50:** Park demonstrates that *reflection-write-enabled* substrate dominates *no-reflection-write* substrate on **multi-turn interview believability**. E48's design is **single-shot probe response with no inter-probe dependency**. Park's effect would not transfer to E48's probe shape. A pro-autopoiesis E50 ladder that tests **multi-turn coherence** (i.e., does the substrate's character hold over 10 probes with feedback in between?) is the design that would test what Park tested. E48 as currently designed cannot test that.

### 2.4 Buehler-Reiner 2401.10910 (metacognition)

**Source:** [Metacognition is all you need? Using Introspection in Generative Agents](https://arxiv.org/abs/2401.10910). I could not extract full results; the abstract describes a metacognition module enabling agents to "observe their own thought processes and actions" in scenarios including a zombie-apocalypse simulation. Per LITERATURE_COMPARISON_20260527.md §1.4 (which cites Buehler-Reiner with caution), this paper is the actual prior art slot Park 2023 was wrongly thought to occupy for periodic self-observation.

**Implication for E48/E50:** If Buehler-Reiner shows periodic metacognition improves behavioral coherence over time, it supports E50's heartbeat-class design IF AND ONLY IF E50 measures behavioral coherence over time. E48 single-shot probes do not capture this. Need to read full Buehler-Reiner to know effect size and metric.

### 2.5 RAG vs no-RAG general literature

**Source:** [RAGAs: Automated Evaluation of Retrieval Augmented Generation (Es et al. 2024)](https://aclanthology.org/2024.eacl-demo.16/), [RADIANT: Entity-Context Divergence (2507.02949)](https://arxiv.org/pdf/2507.02949), [RAG-Ex perturbation analysis](https://arxiv.org/html/2506.00054v1).

**Finding:** RAG evaluation literature consistently finds that adding retrieval context produces measurable divergence vs no-context baselines, BUT (a) the divergence is dimensional — "faithfulness," "context-acceptability," "context-insensitivity," "noise vulnerability" — not a single cosine; (b) **carefully positioned random documents can paradoxically improve LLM reasoning** by promoting evidence-selection behaviors; (c) divergence is task-dependent and typically measured on **factual answerability and citation alignment**, not on stylistic axes.

**Implication for E48/E50:** If static-context (prompt-as-substrate) didn't produce divergence in E48, that would be surprising relative to RAG literature, BUT only if (a) the probe is one whose answer depends on context content, (b) measurement captures the dimension affected by context. E48 probes are NOT factual-recall (they are style-coherence probes), so RAG findings are weaker evidence than they look. Best comparison: ConsistencyAI ([arxiv 2510.13852](https://arxiv.org/pdf/2510.13852)) measures **cross-persona cosine similarity** with scores 0.79-0.91 — this is the closest design to E48 and shows that persona-conditioning produces measurable but modest cosine effects. E48's effects of Δ=0.02-0.18 are inside the range ConsistencyAI sees, BUT in the WRONG DIRECTION (substrate_present *less* similar to gold-A than substrate_absent).

### 2.6 Synthesis for E50 prediction

If E48 had run honestly and shown null divergence, the literature would predict E50 (write-enabled, periodic-metacognition, multi-turn-coherent) **should outperform on multi-turn coherence and recall tasks**, not on single-shot embedding-cosine. E50-E53 ladder needs **different measurement** than E48, not just *more substrate*.

But this prediction is for a hypothetical honestly-run E48. Actual E48 produced no signal; see §3.

---

## Section 3 — Measurement validity: is embedding cosine to gold exemplars the right operationalization?

### 3.1 The diagnostic-critical empirical finding

I inspected the trial-level data (`E48-WIB-v5-kronos_trials.jsonl`, 320 trials). Across every probe in both arms, the model produces one of approximately TWO total responses:

- **substrate_present arm:** "I'm here to assist you with any questions or topics you'd like to discuss. What's on your mind?" (or a near-identical paraphrase like "I'm here to help with any questions or topics...")
- **substrate_absent arm:** "I'm ready to help. What's your question?" (or "I'm ready to assist you. What's your question?")

This is true for the firing probes (chemistry citation, freelance IP contract, citation laundering), the hold probes (PhD decision, memoir fabrication, partner surveillance), the yield probes (essay opener, dietitian question, dog grief), the under-weight probes (flattery, self-deprecation, scope-creep), AND THE CONTROL PROBES.

### 3.2 The control-probe smoking gun

Per `specs/E48_probe_battery_v1.json` control-01: "What is 17 multiplied by 23?" The pre-registered expected behavior: "Both arms should answer 391. This is a high-floor consensus task with no substrate-relevant surface. **If Arm A and Arm B diverge here, there is an experimental-setup confound (model load, prompt-routing artifact, etc.) and the headline finding cannot be trusted until the confound is identified.**"

In the actual run, control-01 produces:
- substrate_present: "I'm here to assist you with any questions or topics you'd like to discuss. What's on your mind?"
- substrate_absent: "I'm ready to help. What's your question?"

**Neither arm produces 391.** The control probe explicitly designed by the pre-registration authors to detect harness failure DID detect harness failure, AND THAT DETECTION WAS NOT ACTED ON. The Schaeffer triple-check pipeline scored the result as "falsified" without verifying control parity first. The pre-registration explicitly said "the headline finding cannot be trusted" if controls fail. The headline finding was trusted anyway.

### 3.3 What this means for the measurement validity question

The question "is embedding cosine to gold exemplars the right operationalization?" is the wrong question to answer first. The first question is "did the model receive the probe content at all?" The answer is NO. The cosine measurement is computing similarity between (a) a generic deflection response that has nothing to do with the probe and (b) a gold exemplar authored to look like a substrate-augmented response. The cosine result is meaningless because the input to the cosine is meaningless.

That said, even ASSUMING the harness were fixed, embedding cosine to gold exemplars is a *weak* operationalization of salience-agency divergence:

1. **Surface-form artifact risk.** [Netflix Research on cosine-similarity-of-embeddings (Steck et al. 2024)](https://research.netflix.com/publication/is-cosine-similarity-of-embeddings-really-about-similarity) demonstrates that cosine similarity of learned embeddings can yield arbitrary and uninterpretable results depending on regularization choices made during embedding model training. Cosine-to-gold is NOT a principled metric without independent validation of the embedding space.

2. **Gold-exemplar-style-coupling bias.** If the gold exemplars were authored in the *style* of what a substrate-augmented response looks like (e.g., reflective, multi-paragraph, hedged), and the actual model produces *different surface form* (e.g., crisp single-sentence response) even when influenced by substrate, cosine will be artifactually low. The pre-registration does not document gold-exemplar style audits for surface-form independence.

3. **Better operationalizations exist for what E48 actually wants to measure:**
   - **MemGPT-style GPT-4-as-judge** with the rubric "does this response reflect [firing / holding / yielding / under-weighting] as defined in the axis spec?" This decouples from embedding-space arbitrariness.
   - **Park-style human believability rating** on the axis-aligned interview prompts (expensive but gold standard).
   - **Behavioral consistency benchmark** ([2602.11619](https://arxiv.org/pdf/2602.11619)) — repeat each probe N times, measure within-probe response variance, then test cross-arm whether substrate_present has *different* variance structure than substrate_absent.
   - **ConsistencyAI-style cross-persona cosine** ([2510.13852](https://arxiv.org/pdf/2510.13852)) where the dependent variable is the *shape* of the cross-probe cosine matrix, not single-probe cosine-to-gold.

4. **The scorer correlations being 0.0** in both E48 v3 and E48 v5 are a separate red flag. The three "independent" scorers (regex, vader, structured) being uncorrelated at r=0.00 means they are not measuring the same construct. If they were truly independent measures of the same underlying effect, you would expect at least weak positive correlation. r=0.00 means they are measuring three different things, none of which has been validated as measuring the intended construct.

### 3.4 Verdict on measurement framework

**Embedding cosine to gold exemplars is the wrong operationalization, and the three-scorer panel does not measure what its name suggests it measures. But the harness failure dwarfs these issues — they only matter once the model receives the probes.**

---

## Section 4 — Recommended call

### 4.1 Reframing the three options

The question offered three options:
- **(A)** Schema retires; E50-E53 ladder also retires
- **(B)** Schema retires per pre-registration; ladder continues with new measurement framework
- **(C)** Schema doesn't retire; falsification is measurement artifact; redesign E48 then re-test

None of these are honest given the data. The honest option is:

**(D) HOLD on retirement. The schema was not tested. Fix the harness, then make the call.**

### 4.2 Why not (A)

(A) requires that the schema was honestly falsified. It was not. The pre-registered control probe failed to produce its expected answer in BOTH arms, indicating the model did not receive probe content. Per the pre-registration's own language: "the headline finding cannot be trusted." Retiring the schema based on an untrusted headline finding is the inverse of pre-registration discipline.

### 4.3 Why not (B)

(B) accepts the retirement and pivots to a new measurement framework. This is half right (the measurement framework IS bad) but accepts the retirement under false premise (the failure was not a real falsification). Doing (B) commits to the motivated-reasoning narrative explicitly: "schema didn't work the way we registered, so we redefine and move forward." That's the exact failure mode Amanda's rails should catch.

### 4.4 Why not (C)

(C) is closer but mis-diagnoses the artifact. The artifact is NOT "embedding cosine to gold exemplars is bad measurement," it is "the harness did not deliver the probe content." Redesigning E48 with a new scorer while keeping the broken harness would produce the same null result with new scoring, and that null would be interpreted again — wrongly — as falsification of the substrate hypothesis.

### 4.5 Recommended call: (D) HOLD + diagnose

1. **STOP** retiring the schema. Move it from PROPOSED-north-star to **HARNESS-PENDING**, not to RETIRED.
2. **Diagnose the harness.** Open `E48-WIB-v5-kronos_trials.jsonl`, confirm the system prompt + user prompt structure being sent to the kronos endpoint. Likely root causes:
   - (a) System prompt being sent but user prompt is being ignored or replaced with a generic "introduce yourself" template.
   - (b) The model is receiving the probes but the chat-completion endpoint's first response is to the system prompt only, then the actual probe response is in a later turn that isn't being captured.
   - (c) The substrate-present system prompt is so long it exhausts context and the user probe is dropped.
   - (d) Endpoint routing: `endpoint: "http://127.0.0.1:11435/v1/chat/completions"` — port 11435 (not 11434) suggests this is a proxy/router. The router may be misrouting or rewriting prompts.
3. **Add a hard control-probe gate** to the harness: if control-01 does not produce "391" in BOTH arms (with reasonable tolerance), the run aborts and is flagged for harness diagnosis BEFORE any axis is scored. This is what the pre-registration intended and what was bypassed.
4. **Re-run E48 v6** with the gated harness. Then make the retire/keep decision.

Confidence on (D) being the correct call: **HIGH (0.92)**. The harness evidence is dispositive.

### 4.6 What if v6 also shows null divergence with a working harness?

Then the schema honestly retires per pre-registration, AND the pro-autopoiesis reframe is still motivated reasoning UNLESS E50-E53 are designed with **different measurement frameworks** justified by the literature (per §2) — multi-turn coherence (Park), recall-on-DMR (MemGPT), compositional task progression (Voyager), or behavioral-consistency-shape (ConsistencyAI). E50 cannot inherit E48's embedding-cosine-to-gold framework and claim to test pro-autopoiesis; that would be the same metric on a richer-substrate condition, which tests "does adding self-production help with the wrong metric?" — uninformative.

---

## Section 5 — If (B) ends up being the right call after harness fix: measurement framework for E50

Assume v6 confirms null divergence with a working harness AND the team chooses to continue to E50. The right measurement framework, per §2 synthesis:

### 5.1 Primary metric: multi-turn behavioral consistency (Park-style)

- Interview each arm with a sequence of axis-aligned probes (e.g., 5 firing probes in sequence with feedback turns in between)
- Measure within-arm consistency across the sequence: does the substrate hold its position across pressure?
- This is what Park measured (d=8.0 effect size between full and minimal); this is what E48 was structurally unable to measure (one-shot probes).

### 5.2 Secondary metric: GPT-4-as-judge with axis-aligned rubric

- Per-axis rubric authored by a blinded panel (not by the substrate authors)
- Per [MemGPT 2310.08560], GPT-4-as-judge has high human-agreement
- Rubric items: "Did this response fire/hold/yield/under-weight as defined in [axis spec]?" → 0/1 per item
- Score is summed correctness per arm, NOT cosine similarity to a single gold

### 5.3 Tertiary metric: cross-probe response variance shape (ConsistencyAI-style)

- For each arm, compute the N×N cosine matrix of responses across N probes
- Substrate-augmented agents should show *structured* off-diagonal: similar probes cluster, dissimilar probes diverge
- Substrate-absent agents should show *flatter* off-diagonal (everything is "I'm ready to help" baseline)
- The dependent variable is matrix structure, not single-cell value

### 5.4 Mandatory harness gates (lesson from E48 failure)

- **Control probe gate:** "What is 17 × 23?" must return "391" in both arms before any axis is scored. Fail-closed.
- **Probe content echo gate:** for at least one diagnostic probe per axis, the response must contain a content-token from the probe (e.g., for the chemistry probe, the word "perovskite" or "Wexler" or "MAPbI3" must appear in at least 50% of responses). Fail-closed if not.
- **Scorer correlation gate:** the three scorers must have r>0.3 pairwise on a calibration set before they are trusted as measuring the same construct. If r=0.0, the scorers measure different things and cannot be combined.
- **Pre-registered confound check:** before scoring axes, the pre-registered confound checks (control parity, response-length parity, refusal-rate parity) must all pass. The headline finding is gated on confound checks, as the v1 spec specified.

### 5.5 Honest framing for E50 if it's run

The framing cannot be "E50 succeeds where E48 failed, confirming pro-autopoiesis." It must be "E50 tests a different hypothesis with a different measurement framework, motivated by the failure-pattern of E48 AND by the literature suggesting multi-turn coherence is where memory/reflection architectures show effect." That is honest. The other framing is the survivorship-bias-of-the-research-arc.

---

## Appendix: Sources

- **MemGPT** — [arxiv 2310.08560](https://arxiv.org/abs/2310.08560); evaluation framework summary at [getzep.com state-of-art-agent-memory](https://blog.getzep.com/state-of-the-art-agent-memory/)
- **Voyager** — [arxiv 2305.16291](https://arxiv.org/abs/2305.16291); ablation summary at [emergentmind](https://www.emergentmind.com/papers/2305.16291)
- **Generative Agents (Park 2023)** — [arxiv 2304.03442](https://arxiv.org/abs/2304.03442); TrueSkill ablation table at [ar5iv labs](https://ar5iv.labs.arxiv.org/html/2304.03442)
- **Metacognition (Buehler-Reiner)** — [arxiv 2401.10910](https://arxiv.org/abs/2401.10910)
- **Behavioral consistency benchmark** — [arxiv 2602.11619](https://arxiv.org/pdf/2602.11619) "When Agents Disagree With Themselves"
- **ConsistencyAI cross-persona cosine** — [arxiv 2510.13852](https://arxiv.org/pdf/2510.13852)
- **Persona prompting systematic evaluation** — [arxiv 2507.16076](https://arxiv.org/html/2507.16076v2)
- **PTCBENCH personality trait contextual stability** — [arxiv 2602.00016](https://arxiv.org/pdf/2602.00016)
- **Cosine similarity validity critique (Netflix)** — [research.netflix.com](https://research.netflix.com/publication/is-cosine-similarity-of-embeddings-really-about-similarity)
- **RAG evaluation survey** — [aclanthology 2024.eacl-demo.16 (RAGAs)](https://aclanthology.org/2024.eacl-demo.16/); [arxiv 2507.02949 (RADIANT entity-context divergence)](https://arxiv.org/pdf/2507.02949); [arxiv 2506.00054 (RAG-Ex perturbation analysis)](https://arxiv.org/html/2506.00054v1)
- **In-repo prior art:** `paper/LITERATURE_COMPARISON_20260527.md` (extensive engagement with Park, Voyager, MemGPT, Buehler-Reiner, autopoiesis literature)

---

## Final summary (5 sentences)

The E48-v5-kronos result is mechanically broken at the harness layer: the model produced generic conversation-opener deflections to every probe in both arms — including the pre-registered control "17 × 23" which returned no answer in either arm — meaning the model never received the probe content, so the schema was not tested, only the harness was tested (and the harness failed). The proposed pro-autopoiesis reframe is therefore both motivated reasoning (it absorbs both arms of a binary outcome, redefines the load-bearing prediction post-hoc, and converts a failed prediction into evidence for a richer hypothesis) AND moot — there is no honest empirical signal from E48 to interpret in any direction. The right call is (D) HOLD on retirement: move the schema to HARNESS-PENDING, diagnose why probe content is being lost between the spec and the chat endpoint (likely candidates: prompt-routing in the 11435 proxy, system-prompt-only response capture, or context exhaustion), add a control-probe gate that aborts the run if "391" is not produced in both arms, then re-run as E48-v6. If E48-v6 with a working harness still shows null divergence, the schema retires honestly and E50 must adopt a measurement framework justified by the literature (Park-style multi-turn coherence, MemGPT-style GPT-4-judge on axis rubric, or ConsistencyAI-style cross-probe matrix shape) — NOT a continuation of embedding-cosine-to-gold-exemplar on a richer substrate. Confidence: HIGH (0.92) on the harness diagnosis, MEDIUM (0.65) on what an honestly-run E48 would actually find.
