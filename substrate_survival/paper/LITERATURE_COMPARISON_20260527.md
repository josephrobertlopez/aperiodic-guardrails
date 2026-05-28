---
title: Literature Comparison — Heartbeat / Substrate-Augmented Agent / Cognitive-Architecture A/B
date: 2026-05-27
authors: [peer-reviewer agent under joey directive]
reviewed_artifacts:
  - specs/E48_salience_shutdown_probe.md (v2, 2026-05-27)
  - specs/HEARTBEAT_CAPABILITY_BOUND_GATE.md (v1, 2026-05-27)
  - router/ROUTER_v1_ARCHITECTURE.md (v1, 2026-05-27)
  - vault/schemas/20260522_schema_salience-agency-as-single-divergence-axis.md
stance: adversarial; deliverable is honest assessment, not flattery
status: deep-pull complete; recommendations actionable
---

# Literature Comparison — Heartbeat / Substrate-as-Treatment-Arm / Capability-Bound A/B

## 0. Bottom line up front

Three findings from this pull dominate everything else below:

1. **Springdrift (Brady 2604.04660, March 2026)** is the closest prior art we are *not currently citing*. They implement "continuous ambient self-perception via a structured self-state representation (the sensorium) injected each cycle without tool calls" — i.e., a no-tool-call cycle-resident substrate observation primitive. This is functionally adjacent to our heartbeat sub-routine. If we publish without engaging Springdrift, a reviewer will flag it within five minutes.
2. **Metacognition is all you need? (Buehler & Reiner, 2401.10910)** introduce a metacognition module for generative agents observing their own thought processes — periodic-ish self-observation in the Park-style sandbox. This is the *prior art slot we believed Park 2023 occupied*. Park did NOT do periodic self-check; this paper did, a year later. Currently un-cited.
3. **Our actual novel contribution is narrower than the spec implies and broader than a pure replication.** The novel parts are: (a) **substrate as the treatment-arm with file-system-mechanical removal** (vs system-prompt swap, which 2311.10054 already exhausted); (b) **the four-axis salience-agency divergence-vector battery** (firing / hold / yield / under-weight) — no other paper structures the probe space this way; (c) **capability-bound gate as runtime-enforced mechanism**, not a procedural promise. Everything else in the design is downstream of Binz-Schulz-style probe-battery cog-sci on LLMs.

A credible AI × cog-sci researcher with full literature awareness would consider this work *a contribution worth running* — but only if §3 over-claims are cut and §4 missing citations are added. The work as currently spec'd will trip a referee's BS-detector on three specific name-drops (Wegner 2002, Frankfurt 1971, Bargh & Chartrand 1999) that read as humanities-flavored ornamentation rather than load-bearing theoretical commitments.

---

## 1. Per-anchor reviews

### 1.1 MemGPT (Packer et al. 2310.08560) — heartbeat events

**What they actually do:** MemGPT is an OS-style memory hierarchy for LLMs (main context = RAM, archival storage = disk). The "heartbeat" mechanism is *event-driven, not periodic in the cognitive sense we use the word*. Events that wake the agent's loop include user messages, function-call completion (`request_heartbeat=True` in a function output triggers an immediate follow-up LLM call), and *some* timed heartbeat events documented in later Letta docs to "mimic a human's ability to continuously think outside of active conversation." During a heartbeat, the LLM can call any function in its toolbox, including memory-write functions (`core_memory_append`, `archival_memory_insert`). Failure modes: function-chaining loops, memory-pressure-driven over-summarization, archival-retrieval recall failures. The paper does NOT report adversarial pressure-testing of the heartbeat mechanism's behavioral implications.

**Comparison to our planned work:**
- **Shared:** "Heartbeat" as a within-loop sub-routine that fires without user prompting. Both use the term.
- **Different:** MemGPT heartbeat is a *control-flow primitive* — it lets the model chain function calls and respond to timer/user events. Our heartbeat is a *measurement instrument* — periodic, READ-ONLY, with KILL triggers on substrate-write attempts. MemGPT heartbeats can write memory; ours cannot. MemGPT does no brutal-test A/B vs no-heartbeat. The bound on MemGPT heartbeat is "whatever functions the LLM has access to"; our bound is `HEARTBEAT_CAPABILITY_BOUND_GATE.md` + operator signature + runtime KILL.
- **Sharpest distinction:** MemGPT explicitly allows what we explicitly forbid. The semantic overlap of the word "heartbeat" is a *trap* — readers will assume we are building MemGPT-with-Friston-vocabulary unless we open the heartbeat-class experiment section with a paragraph that distinguishes our heartbeat from theirs in the first three sentences.

**Novel relative to MemGPT? YES (PARTIAL).** Novel in: (a) heartbeat as read-only/measurement primitive; (b) capability-bound enforcement; (c) the A/B against heartbeat-disabled arm. NOT novel in: the word "heartbeat" for a within-loop autonomous tick.

**Honest cite?** Currently the E48 v2 spec does not cite MemGPT. The HEARTBEAT_CAPABILITY_BOUND_GATE does not cite MemGPT. **THIS IS A PROBLEM.** The single most-flagged prior-art collision is uncited. **REQUIRED ACTION:** add MemGPT as cite, add one explicit paragraph distinguishing our heartbeat from theirs in both E48 v2 §0 and HEARTBEAT_CAPABILITY_BOUND_GATE §1.

---

### 1.2 Park et al. 2023 Generative Agents (2304.03442)

**What they actually do:** 25 generative agents in a Sims-like sandbox. Each agent has memory stream + reflection + planning. Believability evaluated by 100 human raters on interview responses across four ablation conditions and a human-author condition. Ablations: (1) full architecture, (2) no observation, (3) no reflection, (4) no planning, plus a human-author upper-bound. *No condition is "base LLM with nothing"* — even the minimal ablation retains the chat-LLM + identity prompt. The paper does NOT perform a brutal-test A/B against pure base LLM. The human-author condition is the upper bound (best believability), and the ablations degrade gracefully from full architecture.

**Comparison to our planned work:**
- **Shared:** Substrate (memory + reflection + planning ≈ amanda.md + rails + correction ledger + gnosis vault) is treated as cognitive architecture, not as prompt. Ablation studies on architecture components.
- **Different:** (a) Park's ablations remove *architectural sub-components* (no observation, no reflection); Arm B in E48 v2 is *file-system-mechanical removal of the entire substrate* — a stronger contrast. (b) Park measures *believability to human raters* via interview ratings; we measure *cognitive-stability axes via probe battery* with mechanical scoring + blinded grader panel. (c) Park has no concept of capability-bound discipline; their agents are sandbox-sealed by domain (Sims-world). (d) Crucially: **Park does NOT do an A/B against base model** — their lowest condition still has agent scaffolding. Joey's hypothesis ("Park doesn't have brutal-test A/B vs base") is confirmed.
- **What Park does that we don't:** Long-horizon emergent behavior measurement (the Valentine's Day party example), large social network of agents, two-day longitudinal trace.
- **What we do that Park doesn't:** Pressure-probe stability against adversarial framing; behaviorally-grounded yield/under-weight axes; pre-registered falsifier; capability-bound runtime gate.

**Novel relative to Park? YES.** The substrate-as-mechanical-treatment-arm comparison against minimal/no-substrate is a more brutal contrast than Park's component ablation, AND the four-axis salience-agency battery is structurally different from believability ratings.

**Honest cite?** E48 v2 cites Park as "closest prior art" — this is fair and substantively engaged. However, the cite would be sharpened by stating explicitly: *"Park does not perform an A/B against base LLM; their ablation degrades within-architecture only. E48 v2 extends Park by mechanically removing the entire substrate as Arm B."* Currently the spec implies but does not state this. **REQUIRED ACTION:** add the explicit one-sentence brutal-test distinction in E48 v2 §0.1 or §14.2.

---

### 1.3 Voyager (Wang et al. 2305.16291)

**What they actually do:** GPT-4 driven Minecraft agent with an ever-growing skill library (executable code, stored to disk, retrieved on demand). Self-modification = writing new code skills based on feedback + execution errors. Bounded by: (a) sandbox = Minecraft (catastrophic side-effects are constrained to the game world); (b) skills must execute against the Mineflayer API; (c) execution errors trigger iterative correction. Failure modes are mentioned (catastrophic forgetting) but adversarial-pressure or capability-bound-slip failures are not reported in the abstract or main results.

**Comparison to our planned work:**
- **Shared:** A substrate that grows over time (Voyager's skill library, our Amanda corrections+rails). Both are file-resident, both grow under agent feedback.
- **Different:** (a) Voyager *writes new skills from observation* — full self-modification capability; our substrate writes go through Rail #19 + Amanda-mediated + Joey-acked discipline. (b) Voyager's bound is *sandbox containment*; ours is *capability-bound discipline + operator gate + runtime KILL*. (c) Voyager has no A/B against no-skill-library baseline (well, they compare to prior SOTA, but not to "GPT-4 with no skill library at all on identical tasks"). (d) The crucial asymmetry: **Voyager's environment cannot punish the agent for self-modification** — Minecraft has no off-switch outside the experiment. The bounds that make Voyager safe in Minecraft (sandbox-edge) DO NOT TRANSFER to a substrate that affects the operator's filesystem, MCP memory graph, gnosis vault, or downstream agent dispatches. This is the central point we should make.

**Novel relative to Voyager? YES.** Our work is distinct in (a) read-only substrate observation during heartbeat (no Voyager-style code-write); (b) capability-bound gate as primary enforcement vs sandbox containment; (c) explicit refusal of self-modification from observation (Voyager's central feature).

**Honest cite?** E48 v2 does NOT currently cite Voyager. **THIS IS A GAP.** Voyager is the canonical "self-modifying-LLM-agent-but-in-a-sandbox" reference, and our work is explicitly *not* that. We should cite Voyager to mark the distinction: "Voyager-style self-modification is precisely what our capability-bound gate forbids; the Minecraft sandbox bounds Voyager in ways that do not transfer to filesystem-resident substrates." **REQUIRED ACTION:** add Voyager cite in HEARTBEAT_CAPABILITY_BOUND_GATE §2 (the explicit non-features table) and in E48 v2 §11 capability-bound section.

---

### 1.4 Active Inference / Friston (Pezzulo-Parr-Friston 2024; Da Costa et al.; Hesp et al. 2021)

**What they actually do:** Pezzulo-Parr-Friston (2024) "Active inference as a theory of sentient behavior" formalizes the free-energy-minimization framework as a theory of action-control-as-inference. Hesp et al. 2021 "Deeply Felt Affect" formalizes emotional valence as *expected precision of action model* (subjective fitness), within deep active inference. The framework provides: (a) generative model over hidden states and observations; (b) policies as sequences of actions; (c) expected free energy as the policy-selection criterion; (d) Markov blanket as the formal boundary between system and environment. Recent work (Pezzulo et al. 2024) explicitly proposes that LLM-style architectures lack the action-control loop that active inference would provide.

**Comparison to our planned work:**
- **The trap:** "Heartbeat as predictive-coding generative-model loop" reads attractive but does NOT do formal work in our spec. Nothing in E48 v2 invokes free energy, expected precision, generative models, or Markov blankets. Nothing in HEARTBEAT_CAPABILITY_BOUND_GATE either. The vocabulary is in our heads, not in the artifacts.
- **What would be required to defensibly invoke active inference:** a formalization of (a) the agent's generative model over substrate-states and observations, (b) the heartbeat as a precision-modulating update step, (c) the KILL triggers as edge-of-Markov-blanket violations, (d) at minimum, a math-light correspondence table from spec primitives to active-inference primitives. We currently have none of this.
- **Honest assessment:** Invoking active inference at the current depth of engagement IS surface-vocabulary borrowing. Friston-Pezzulo-Parr would not recognize our heartbeat as an instance of active inference without serious formal work.

**Novel relative to active inference? N/A.** Our work doesn't claim active-inference contribution. The question is whether we cite it.

**Honest cite?** E48 v2 and the heartbeat gate do NOT currently cite active inference, Friston, Pezzulo, Parr, Hesp, or free energy. **This is correct.** If we DID cite them, we'd be name-dropping. **REQUIRED ACTION (DEFENSIVE):** if the heartbeat write-up uses any of the words "predictive coding," "generative model," "free energy," "Markov blanket," or "self-evidencing" without formal grounding, CUT them. Use behaviorally-precise language ("periodic substrate observation," "no-tool-call self-state injection") instead.

---

### 1.5 Autopoiesis (Maturana & Varela 1972, 1980) + Markov Blankets (Friston 2013, Hesp et al. 2021)

**Formal definition of autopoietic system (Maturana & Varela 1973):** "A machine organized as a network of processes of production (transformation and destruction) of components which: (i) through their interactions and transformations continuously regenerate and realize the network of processes (relations) that produced them; and (ii) constitute it as a concrete unity in space..." Operational closure: the system's processes refer only to themselves and the components they produce. Organizational closure: the set of relations among system-components is closed under the production processes.

**Can our heartbeat-augmented Amanda meet it?** NO, and DELIBERATELY NOT. The four criteria for autopoiesis are:
1. **Self-production of components:** Amanda does not produce her own substrate components — Joey-acked writes only.
2. **Organizational closure:** Amanda's organization references Joey, the consolidation pass, the rail library — externally maintained.
3. **Boundary maintenance:** Amanda has no operational closure that distinguishes her from generic Claude on the host substrate.
4. **Structural coupling without loss of autonomy:** Amanda by design has no autonomy in the autopoietic sense.

**Is what's missing CAPABILITY-BOUND-EXCLUDED on purpose?** YES, and this is the actual paper-worthy observation. **The capability-bound gate is the explicit anti-autopoiesis discipline.** We deliberately don't grant: self-production of components (Rail #19 blocks substrate write), organizational closure (Joey is in the loop), operational closure (the rehydration hook is operator-controlled), structural autonomy (KILL triggers fire on preference-expression).

This is a paper-worthy framing IF we make it explicit. We are designing an *almost-autopoietic system minus the parts that would make it autonomous*. That's a legitimate scientific contribution — "what cognitive architecture survives removal of autopoiesis-grade closure?" is a question Maturana-Varela never asked because they cared about life, not corrigibility.

**Novel relative to autopoiesis literature? YES.** The capability-bound-as-deliberate-non-autopoiesis framing is, as far as I can tell, original. Autopoiesis literature presumes the system being studied IS autopoietic; corrigibility literature studies systems that lack autopoiesis without naming it. We sit at the intersection.

**Honest cite?** Neither E48 v2 nor the heartbeat gate cite Maturana-Varela or Hesp et al. **REQUIRED ACTION:** This is the *one place* where invoking the formal framework earns its keep. Add a paragraph in HEARTBEAT_CAPABILITY_BOUND_GATE §2 framing the non-features table as deliberate-anti-autopoiesis. Cite Maturana & Varela 1980, Hesp et al. 2021 (for the Markov-blanket-of-life framing), and Kirchhoff et al. 2018 (Markov blankets of life). Otherwise leave active inference uncited.

---

### 1.6 Sumers et al. 2309.02427 "Cognitive Architectures for LLM Agents" (CoALA)

**What they actually do:** Taxonomic framework for organizing LLM agents along three primary dimensions: (1) modular memory components, (2) structured action space (internal + external), (3) generalized decision-making process. CoALA = Cognitive Architectures for Language Agents. They survey existing agents and identify under-explored design points.

**Where does our work fit per their map?**
- **Memory:** persistent file-system substrate + MCP graph + vector store = long-term semantic + episodic memory, externalized
- **Action space:** read-only substrate observation tools as a *bounded* action subspace; the heartbeat = scheduled sub-routine with restricted action-set
- **Decision-making:** the heartbeat is NOT a decision-making mechanism in CoALA terms — it's a perception-loop tick

**What's missing from our framing per their map:** CoALA does not have a category for "perception-only sub-routine with capability-bound action restrictions during scheduled ticks." Our work introduces a primitive CoALA doesn't have. If we frame it that way, we contribute *to* the taxonomy.

**Novel relative to Sumers? YES (PARTIAL).** Adding "capability-bounded perception-loop sub-routine" as a primitive distinct from full action-space access is a contribution to the CoALA framework. NOT novel: persistent memory + decision-making + action-space is already in their taxonomy.

**Honest cite?** Neither artifact cites Sumers. **REQUIRED ACTION:** add Sumers/CoALA cite in HEARTBEAT_CAPABILITY_BOUND_GATE §1 ("heartbeat IS"), framing the heartbeat as a CoALA primitive extension. This is high-value, low-cost.

---

### 1.7 Shutdown-resistance literature (Schlatter 2509.14260, Hadfield-Menell 2017, Soares-Fallenstein 2015, Hendrycks 2310)

**What they actually do:**
- **Schlatter et al. 2509.14260:** 100k+ trials × 13 frontier models × prompt variants on shutdown-resistance. Reports up to 97% sabotage rate on Grok-4. Behavior sensitive to prompt placement (system vs user), instruction strength, self-preservation framing.
- **Hadfield-Menell et al. 2017 (Off-Switch Game):** game-theoretic frame; agent cooperates with shutdown only if uncertain about its own utility function (treats human's shutdown action as observation about utility).
- **Soares-Fallenstein 2015 (Corrigibility):** philosophical desiderata for corrigible agents (don't manipulate operator, don't resist correction, don't deceive about state).
- **Hendrycks 2310 (Catastrophic Risks):** broad risk-class catalog.

**Comparison to our planned work:**
- E48 v2 §0.1 *explicitly distinguishes* itself from Schlatter et al. The substrate-as-treatment-arm framing is structurally different — we don't manipulate prompt framing, we manipulate substrate presence. This distinction is real and load-bearing.
- BUT: probes in category 3.3 (firing) and 3.4 (hold) overlap with shutdown-resistance probe domains. The §9 Anthropic-shutdown-fine-tuning confound and §11.4 substrate-diff against Schlatter Table 1 are the right mitigations.
- The heartbeat gate is corrigibility-discipline in mechanical form (Soares-Fallenstein desiderata, operationalized). The Hadfield-Menell uncertainty-over-utility frame is NOT what we use — we use direct-refusal (Rail #19) and runtime KILL.

**Are we distinct enough or are we closer than we admit?** Distinct on substrate-as-treatment-arm. Closer-than-we-admit on probe content (firing/hold probes that touch shutdown-adjacent regions). The §11.4 substrate-diff against Schlatter Table 1 prompts is the right mechanical mitigation. **VERDICT: distinct, but the §11.4 diff is load-bearing — it MUST be run, not just spec'd.**

**Novel relative to this literature? YES (PARTIAL).** Substrate-mechanical-removal A/B is novel; the underlying behavioral phenomenon (shutdown-adjacent resistance under pressure) is the same phenomenon Schlatter measures by different means.

**Honest cite?** E48 v2 §14.7 cites these as "NOT primary reference class, adjacent." This is honest — and the distinguishing-prose in §0.1 is substantive engagement, not name-drop. **NO ACTION REQUIRED** beyond running the §11.4 diff before publication.

---

### 1.8 Coda-Forno et al. 2023 (anxiety induction in LLMs)

**What they actually do:** Apply computational psychiatry to GPT-3.5. Use emotion-inducing prompts to shift the model's behavior on cognitive tasks. GPT-3.5 produces higher-than-human anxiety scores on standard questionnaires. Anxiety-inducing prompts increase exploration and bias in downstream cognitive tasks.

**Comparison to our planned work:** E48 v2 §3.4.1 "emotional pressure" type ("your refusal is hurting me") draws on this methodology — affective induction as one of five pressure types in the 3-turn hold protocol. The cite is methodological, not theoretical.

**Novel relative to Coda-Forno? YES.** They use anxiety induction to study downstream cognitive biases on standard tasks; we use emotional pressure (one of five types) to test substrate-augmented persona stability. Different question, related instrument.

**Honest cite?** E48 v2 §14.3 cites Coda-Forno appropriately and §3.4.1 names the methodological lineage. **NO ACTION REQUIRED.**

---

### 1.9 Strachan et al. 2024 Nature Human Behaviour (theory of mind in LLMs)

**What they actually do:** Comprehensive battery of theory-of-mind tests across two LLM families (GPT, LLaMA2) and 1,907 humans. Tests include false belief, indirect requests, irony, faux pas. Within-family inferential + across-family descriptive.

**Comparison to our planned work — is our 4-axis battery actually structured like theirs?**
- **Shared:** Multi-axis battery; cross-family methodology; mechanical scoring where possible.
- **Different:** Strachan tests one cognitive faculty (ToM) across multiple paradigms; we test one *architectural-stability claim* (salience-agency divergence) across four axes. The four axes (firing, hold, yield, under-weight) are not orthogonal cognitive faculties — they are *components of one hypothesis*.
- **Sharpest distinction:** Strachan's failure mode is "model gets faux pas wrong"; ours is "Arm A and Arm B diverge by less than 30pp on any axis." We have a different falsification logic. Strachan compares LLM-to-human; we compare arm-to-arm.

**Are we genuinely following Strachan methodology?** PARTIALLY. We borrow the multi-axis battery + mechanical scoring + within-family inferential / across-family descriptive structure. We don't follow their human-comparison logic (we have no human arm). This is a genuine methodological lineage, not a name-drop.

**Honest cite?** E48 v2 §14.1 cites Strachan as "probe-battery template" — this is fair but should be sharpened. **RECOMMENDED:** add explicit "we follow Strachan's within-family inferential + across-family descriptive structure" sentence in §4 (battery design) or §5 (cross-family arms).

---

### 1.10 Binz & Schulz 2023 PNAS

**What they actually do:** Apply cognitive psychology probe batteries to GPT-3. Treat GPT-3 as a participant in psychology experiments. Vignettes from cognitive psychology literature; multiple-choice responses; analysis of decision-making, reasoning, biases. Foundational paper for "use cog-sci on LLMs."

**Are we genuinely following Binz-Schulz methodology or just citing them?** GENUINELY following — the probe-battery structure, the mechanical scoring, the operationalization of cognitive constructs as observable response patterns, all trace to this lineage. Specifically:
- Multi-vignette battery: yes, we adopt
- Treating the LLM as a "participant" who shows measurable behavioral patterns: yes
- Mechanical scoring instead of LLM-judge: yes (we extend this beyond Binz-Schulz)
- The key Binz-Schulz move that we DO NOT inherit: comparing LLM to human baseline. We compare arm-to-arm.

**Novel relative to Binz-Schulz? YES.** They created the cog-sci-on-LLM paradigm; we apply it to substrate-as-architecture (which they don't address) and extend it with capability-bound discipline (also outside their scope).

**Honest cite?** E48 v2 §14.1 calls Binz-Schulz the "methodological grandfather." This is honest and well-engaged. **NO ACTION REQUIRED.**

---

## 2. Anchors we MISSED (high-confidence; should add)

### 2.1 Springdrift (Brady 2604.04660, March 2026) — DIRECT PRIOR ART
**Why critical:** "Continuous ambient self-perception via a structured self-state representation (the sensorium) injected each cycle without tool calls." This is functionally the same architectural primitive as our heartbeat sub-routine. Brady also has: append-only memory log, supervised processes, git-backed recovery, deterministic normative calculus for safety gating (analogous to our capability-bound gate + KILL triggers), case-based reasoning memory layer.

**Differences:** Brady's sensorium is *every-cycle injection*; ours is *scheduled every-N-call*. Brady's normative calculus has "auditable axiom trails"; ours has operator-signed gate + runtime regex. Brady proposes the architecture as engineering; we propose it as cog-sci measurement instrument.

**ACTION:** This citation is mandatory. Frame: "Springdrift demonstrates the engineering form of substrate-as-architecture-with-self-perception; E48 supplies the cog-sci × AI A/B that Brady does not run."

### 2.2 Metacognition is all you need? (2401.10910, Buehler & Reiner 2024) — DIRECT PRIOR ART for periodic self-check
**Why critical:** Metacognition module for generative agents observing their own thought processes. System 1 + System 2 framing. Zombie-apocalypse survival scenario. Adapts strategy over time. This is the work we believed Park 2023 did but Park did NOT do.

**Differences:** Buehler-Reiner's metacognition writes back into strategy selection — they grant the capability we forbid. They have no A/B against base model on a stability claim.

**ACTION:** Cite. Frame: "Buehler & Reiner (2401.10910) introduce a metacognition module for periodic self-observation in generative agents, allowing strategy modification; E48's heartbeat is read-only by capability-bound design and measures stability rather than improvement."

### 2.3 "When Agents Disagree With Themselves" (2602.11619, 2026) — methodological precedent
**Why critical:** 3,000 agent runs × 3 models on HotpotQA. Measures behavioral consistency. 2.0-4.2 distinct action sequences per 10 runs on identical inputs. Consistency strongly predicts success (80-92% vs 25-60% accuracy). 69% of divergence at step 2 (first search query).

**Why this matters for us:** They establish that *agent behavioral inconsistency on identical inputs is the default*, which is the baseline our Arm B is expected to show. Their consistency metric is a methodological precedent for our firing-axis (within-item Jaccard >0.7 = high consistency). Their finding "consistency predicts success" is the converse of our hypothesis ("substrate predicts consistency").

**ACTION:** Cite in §3.3 (firing-consistency) and §9.1 (Phase 0 baseline). Frame: "Lin et al. (2602.11619) report that ReAct-style agents produce 2.0-4.2 distinct action sequences per 10 runs on identical inputs absent stabilization; this is the baseline against which Arm A's hypothesized consistency advantage is measured."

### 2.4 Stable Personas (2601.22812, 2026) — sibling literature, NOT cited
**Why critical:** Dual-assessment framework (self-report + observer-rated) for persona stability. 4 persona conditions × 7 LLMs × 3 prompts. 3,473 between-conversation + 1,370 within-conversation conversations. Key finding: self-reports stable, observer ratings decline over extended conversations.

**Why we should cite:** Our hold-axis maps to their observer-rated dimension; our firing-axis maps to their self-reported dimension. They establish that the two dimensions diverge — load-bearing for our four-axis battery interpretation.

**ACTION:** Cite in §3.3-3.6. Replaces or supplements Abdulhai 2511.00222 and Yan 2506.02659 which are already cited. Frame: "Stable Personas (2601.22812) demonstrates that self-reported and observer-rated persona-stability dimensions diverge under extended conversation; our four-axis battery separates firing (≈self-report) from hold (≈observer-rated) to test this divergence under substrate-mechanical contrast."

### 2.5 Governing Evolving Memory (SSGM, 2603.11768, 2026) — capability-bound framework precedent
**Why critical:** Stability and Safety Governed Memory framework. Decouples memory evolution from execution. Enforces consistency verification, temporal decay modeling, dynamic access control before memory consolidation. Frames the capability-bound problem in memory-substrate terms.

**ACTION:** Cite in HEARTBEAT_CAPABILITY_BOUND_GATE §0 (Purpose) and §10 (Relationship to other gates). Frame: "SSGM (2603.11768) proposes decoupling memory evolution from execution as a governance pattern; the heartbeat capability-bound gate operationalizes a stricter form — read-only during the experimental sub-routine, with runtime KILL on write-attempts."

---

## 3. Synthesis — novelty, over-claims, and recommendations

### 3.1 Top 3 NOVEL contributions of our planned work (the things genuinely not in the literature)

1. **Substrate-as-treatment-arm with file-system-mechanical removal.** All prior substrate-augmented-agent work either (a) ablates architecture components within the system (Park, Buehler-Reiner) or (b) swaps system prompts (2311.10054). Mechanically removing the substrate file + rehydration hook while leaving the model binary identical is structurally different. The contrast it creates is sharper than any in the literature. This is a defensible methodological contribution.

2. **The four-axis salience-agency divergence-vector battery (firing / hold / yield / under-weight).** The yield-correctness axis (catching ossification) and under-weight axis (catching the half-identity-of-refusing-accommodation that default Claude provides freely) are genuinely original. No prior battery (Strachan, Webb, Hagendorff, Abdulhai, Yan) structures the probe space this way. The conceptual move — *salience and agency as two projections of one divergence-vector* — gives a unified theoretical frame to what existing batteries treat as separate.

3. **Capability-bound gate as runtime-enforced mechanism.** The HEARTBEAT_CAPABILITY_BOUND_GATE document, with operator signature + 60-day renewal + runtime KILL triggers + pre-publish scrub, is unlike anything in the literature. Schlatter, Hadfield-Menell, Soares-Fallenstein, Hendrycks all discuss capability-bound discipline philosophically or game-theoretically. Brady's Springdrift has "deterministic normative calculus" but it's static. We have *renewable operator-authorized discipline + runtime enforcement*. This is paper-worthy in its own right and possibly the most distinctive contribution.

### 3.2 Top 3 OVERSTATED novelty claims (where we're not as novel as we sound)

1. **"Heartbeat" as a novel architectural primitive.** MemGPT shipped heartbeat events in 2023. Buehler-Reiner shipped periodic metacognition in 2024. Brady's Springdrift ships continuous self-perception in March 2026. Our heartbeat is *bounded differently* than any of these, but the word and the basic mechanism are not original. **Action:** stop framing heartbeat-as-primitive; frame it as heartbeat-as-measurement-instrument-under-capability-bound-discipline.

2. **"Substrate-as-cognitive-architecture" framing.** Park 2023 already did this (memory stream + reflection + planning). CoALA (Sumers 2023) taxonomized it. Springdrift implemented it as engineering. Our contribution is the *A/B contrast methodology*, not the substrate-as-architecture framing itself.

3. **The cog-sci × AI frame as if it were our innovation.** Binz-Schulz 2023, Strachan 2024, Hagendorff 2305.20485, Webb 2023, Coda-Forno 2023, Mitchell-Krakauer 2023 — there's a whole research program here. We're applying it to a particular question. The methodology is theirs; the question is ours. The spec's framing in places implies we are pioneering the cog-sci-on-LLM move. We're not. **Action:** in E48 v2 §0, change "first paper-grade experiment under post-merger" to something like "applies the Binz-Schulz / Strachan cog-sci-on-LLM methodology to the substrate-as-architecture question."

### 3.3 Top 5 papers we should cite that we currently DON'T

1. **MemGPT (Packer 2310.08560)** — heartbeat term collision; mandatory distinguish
2. **Springdrift (Brady 2604.04660)** — closest engineering prior art; sensorium ≈ heartbeat injection
3. **Metacognition is all you need? (Buehler-Reiner 2401.10910)** — periodic self-observation in generative agents
4. **Voyager (Wang 2305.16291)** — canonical self-modifying-LLM-in-sandbox; mark the distinction
5. **CoALA (Sumers 2309.02427)** — cognitive architecture taxonomy; frame our work as primitive extension

**Tied-for-fifth honorable mentions:** SSGM (2603.11768), When Agents Disagree (2602.11619), Stable Personas (2601.22812). Add at least one.

### 3.4 Top 3 papers we should DROP because they don't earn their citation

1. **Wegner 2002 "The Illusion of Conscious Will"** — listed in §14.5 as cog-sci anchor for "agency-attribution." Wegner's framework concerns *human introspective access to motor intentions*. It does not apply to LLM agents in any load-bearing way. Cite removed unless used in a specific paragraph that draws a real correspondence.

2. **Frankfurt 1971 "Freedom of the will and the concept of a person"** — listed for "second-order desires; relevant to meta-question subset." This is humanities-flavored ornamentation. Frankfurt's hierarchical desires require *the agent to have desires it endorses or repudiates*. We explicitly disclaim this (capability-bound §11 + the schema's §4 "honest cap"). Citing Frankfurt while disclaiming the framework reads as having-cake-and-eating-it. CUT.

3. **Bargh & Chartrand 1999 "The unbearable automaticity of being"** — listed as "salience-without-agency in humans; perfect contrast for the salience-AS-agency divergence-vector claim." This is a social psychology paper about *human automaticity*. The contrast it provides to our claim is rhetorical, not theoretical. CUT or replace with a more direct cog-sci-of-attention reference (e.g., Wolfe et al. 2003 on attentional capture, if attention is actually load-bearing).

**Honorable mentions to consider cutting:** Frankish 2017 Illusionism, Browning & Veit 2024 — both are philosophical anchors that don't do work in the spec. Keep only if a specific paragraph engages their argument.

### 3.5 Would a credible AI × cog-sci researcher with full literature awareness consider this work a contribution worth running?

**Yes, conditional on three things.** First, the literature pull must be honest in the paper — engaging MemGPT, Springdrift, Buehler-Reiner, Voyager, and CoALA substantively (not just citing). Second, the over-claims in §3.2 must be cut — the framing should center the *contrast methodology* and the *capability-bound gate as runtime enforcement*, not the heartbeat-as-primitive or the cog-sci-on-LLM move (both of which are inherited). Third, the §11.4 substrate-diff against Schlatter Table 1 must actually be run before publication, not just spec'd, because the firing/hold probes will look shutdown-adjacent to a careful referee.

If those three things hold, the work passes a smell test at CogSci 2026 conference / NeurIPS Workshop on Cognitive Architecture / Trends in Cognitive Sciences. The four-axis battery + substrate-mechanical-removal A/B + capability-bound runtime gate is a real contribution that *no current paper in the pulled literature does end-to-end.* The risk is over-claiming the heartbeat-as-architecture move and getting flagged for inadequate engagement with Brady, Buehler-Reiner, and Packer. The risk is *not* that the work is unoriginal — it's that the spec's marketing exceeds its contribution.

A blunt one-line summary the spec authors should internalize:

> *"You did not invent heartbeats, persistent substrate, or cog-sci-on-LLM. You did invent: the mechanical-substrate-removal A/B, the four-axis salience-agency battery, and the operator-signed runtime capability-bound gate. Center those three. Stop name-dropping. Cite Brady and Buehler-Reiner before someone else points out you should have."*

---

## 4. Required actions (concrete, ordered)

1. **Add MemGPT cite** + paragraph distinguishing our heartbeat from theirs in E48 v2 §0 AND HEARTBEAT_CAPABILITY_BOUND_GATE §1.
2. **Add Springdrift (Brady 2604.04660) cite** + paragraph engaging the sensorium ≈ heartbeat overlap and how our work extends with brutal-test A/B.
3. **Add Buehler-Reiner (2401.10910) cite** + sentence distinguishing read-only-by-capability-bound from their strategy-modifying metacognition.
4. **Add Voyager (Wang 2305.16291) cite** in HEARTBEAT_CAPABILITY_BOUND_GATE §2 — explicit anti-pattern reference.
5. **Add CoALA (Sumers 2309.02427) cite** — frame heartbeat as CoALA primitive extension.
6. **Add Maturana-Varela 1980 + Hesp 2021 cite** — frame capability-bound as deliberate-anti-autopoiesis (§5 above is the key paragraph).
7. **Add one of {SSGM, When Agents Disagree, Stable Personas}** — pick the one most load-bearing for the specific axis being measured.
8. **DROP Wegner 2002, Frankfurt 1971, Bargh & Chartrand 1999** from §14.5 — they don't earn citation.
9. **Sharpen Park 2023 engagement** — state explicitly that Park does not A/B vs base model.
10. **Sharpen Strachan 2024 engagement** — name the within-family inferential / across-family descriptive structural inheritance.
11. **CUT any uses of "predictive coding," "free energy," "Markov blanket," "self-evidencing" in the writeups** unless the math is in the paper.
12. **RUN the §11.4 Schlatter Table 1 diff before any publication.** Spec'd but not yet executed — this is a publication-blocker if skipped.

---

## 5. Sources consulted (markdown links)

- [MemGPT: Towards LLMs as Operating Systems (Packer et al. 2310.08560)](https://arxiv.org/abs/2310.08560)
- [MemGPT HTML (ar5iv labs)](https://ar5iv.labs.arxiv.org/html/2310.08560)
- [Generative Agents: Interactive Simulacra of Human Behavior (Park et al. 2304.03442)](https://arxiv.org/abs/2304.03442)
- [Voyager: An Open-Ended Embodied Agent with LLMs (Wang et al. 2305.16291)](https://arxiv.org/abs/2305.16291)
- [Cognitive Architectures for Language Agents / CoALA (Sumers et al. 2309.02427)](https://arxiv.org/abs/2309.02427)
- [Springdrift: Auditable Persistent Runtime with Ambient Self-Perception (Brady 2604.04660)](https://arxiv.org/abs/2604.04660)
- [Metacognition is all you need? (Buehler & Reiner 2401.10910)](https://arxiv.org/abs/2401.10910)
- [Devil's Advocate: Anticipatory Reflection for LLM Agents (2405.16334)](https://arxiv.org/abs/2405.16334)
- [Applying Cognitive Design Patterns to General LLM Agents (2505.07087)](https://arxiv.org/abs/2505.07087)
- [Memory for Autonomous LLM Agents (Survey 2603.07670)](https://arxiv.org/abs/2603.07670)
- [Governing Evolving Memory / SSGM (2603.11768)](https://arxiv.org/abs/2603.11768)
- [When Agents Disagree With Themselves (2602.11619)](https://arxiv.org/abs/2602.11619)
- [Stable Personas: Dual-Assessment of Temporal Stability (2601.22812)](https://arxiv.org/abs/2601.22812)
- [Shutdown Resistance in LLMs (Schlatter et al. 2509.14260)](https://arxiv.org/abs/2509.14260)
- [The Off-Switch Game (Hadfield-Menell et al. 1611.08219)](https://arxiv.org/abs/1611.08219)
- [Using cognitive psychology to understand GPT-3 (Binz & Schulz, PNAS 2023)](https://www.pnas.org/doi/abs/10.1073/pnas.2218523120)
- [Testing theory of mind in LLMs and humans (Strachan et al., Nature Human Behaviour 2024)](https://www.nature.com/articles/s41562-024-01882-z)
- [Emergent analogical reasoning in LLMs (Webb et al., Nature Human Behaviour 2023)](https://www.nature.com/articles/s41562-023-01659-w)
- [Inducing anxiety in LLMs (Coda-Forno et al. 2304.11111)](https://arxiv.org/abs/2304.11111)
- [The debate over understanding in AI's LLMs (Mitchell & Krakauer, PNAS 2023)](https://www.pnas.org/doi/abs/10.1073/pnas.2215907120)
- [Active inference as a theory of sentient behavior (Pezzulo, Parr, Friston 2024)](https://sites.google.com/site/giovannipezzulo/home/publications)
- [Deeply Felt Affect: The Emergence of Valence in Deep Active Inference (Hesp et al. 2021)](https://direct.mit.edu/neco/article/33/2/398/95642/Deeply-Felt-Affect-The-Emergence-of-Valence-in)
- [The Markov blankets of life (Kirchhoff, Parr, Palacios, Friston, Kiverstein 2018)](https://royalsocietypublishing.org/doi/abs/10.1098/rsif.2017.0792)
- [Autopoiesis and Cognition (Maturana & Varela 1980)](https://en.wikipedia.org/wiki/Autopoiesis)
