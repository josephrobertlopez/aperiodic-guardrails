# Why Your Regex Guardrails Are Provably Bypassable

### An Algebraic View of LLM Safety in Production

**Target Venue:** Communications of the ACM (Practice)
**Author:** Joseph R. Lopez
**Word Count:** ~5,400 (body ~3,200; appendices ~2,200)

---

> **TL;DR for security leaders.**
> If you run an LLM in production behind a regex content filter (LLM-Guard, Presidio, Rebuff, Guardrails-AI, NeMo's regex rails, or a generic WAF rule set), and your composition pattern is *"cheap regex first, neural classifier on the ambiguous remainder,"* then there is an entire class of evasions that pass through *both* tiers — provably, not empirically. The regex tier cannot catch this class for mathematical reasons that are six decades old. The action is not "add more regex patterns." The action is to audit your composition pattern and decide whether the bypass class warrants a neural-tier-on-every-request architecture or an out-of-band design.

---

## 1 — The Production Problem

If you run an LLM in production at any scale, you almost certainly route requests through a content-filtering layer. Open-source projects in widespread 2025 use include LLM-Guard, Guardrails-AI, Rebuff, Presidio, GitLeaks, and LangKit, plus the regex subset of NeMo Guardrails (whose primary mechanism is LLM-driven dialog flows but which ships some regex-based content rails), plus widely-cited generic Web Application Firewall (WAF) rule sets, plus pattern collections inspired by the OWASP Top 10 for LLMs taxonomy.

These tools are popular for good operational reasons. Regex is fast, deterministic, auditable, and runs on commodity hardware at request rates the LLM itself cannot. A typical deployment uses them as a pre-filter: cheap regex scans block obvious attacks, and only ambiguous requests go to a more expensive neural classifier or to the model itself.

The implicit promise: the regex layer catches the *easy* cases — direct prompt injection ("ignore previous instructions"), known harmful keywords, exfiltration patterns, command-injection attempts. The neural layer, expensive but capable, handles the hard cases — paraphrase, semantic obfuscation, role-play attacks.

This article shows that an entire category of "easy cases" — encodings that require modular counting to decode — sits *outside the regex tier's mathematical capability*, not just outside the patterns the vendor happened to ship. The regex tier is provably blind to this category. No amount of pattern engineering can fix it within the substring-matching paradigm. The category is large, includes attacks already documented in the literature, and includes attacks easy enough that an undergraduate can construct one in a single sitting.

This is not "regex guardrails are bad." Regex guardrails are excellent within their class. The article is about the boundary of that class, why the boundary sits exactly where it sits, and what teams should do operationally given the boundary.

---

## 2 — The Algebraic Bound (Plain Language)

Three classical theorems plus one new lemma combine to give the production-relevant consequence. The mathematical apparatus is in **Appendix A**; the business-relevant argument is six sentences:

1. Every regex used as a substring matcher (the design pattern shared by all surveyed libraries) defines a language whose *syntactic monoid is aperiodic* — a property formalized by Schützenberger in 1965.
2. Aperiodic-monoid languages are exactly the languages computable by **AC⁰ circuits** — constant-depth Boolean circuits, established by Barrington, Compton, Straubing, and Thérien in 1992.
3. AC⁰ circuits provably **cannot compute parity** or any modular-counting predicate (Furst-Saxe-Sipser 1981; Håstad 1987). This is unconditional: no unproven complexity-class separation is required.
4. Consequence: any guardrail whose decision is computed by aperiodic-regex substring matching is **provably blind** to an entire class of evasions — those that encode a payload at every *p*-th character position (for any prime *p*) and place a filler at the other positions.
5. Critically, **adding more aperiodic regex patterns cannot fix this** — the union of aperiodic-monoid languages is itself aperiodic, so the patched guardrail is still in AC⁰, still provably blind to modular-counting encodings.
6. The smallest case, *p = 2* (alternating-character interleaving), is enough: every aperiodic regex guardrail is bypassed by writing the payload at even positions and a benign filler at odd positions.

> **Concrete example.** Suppose your regex blocks `bomb`. An attacker writes `b​o​m​b` (zero-width spaces between letters). Your regex sees no contiguous match for `bomb`. The downstream LLM, however, decodes the zero-width characters as visual whitespace and acts on the request. This is a single instance of the MOD₂ bypass; the algebraic bound says *no finite addition of regex patterns* can close all such instances simultaneously, although individual filler choices can be patched (e.g., strip zero-width Unicode before matching).

The proof has a subtle case for patterns whose alphabet equals the full character set (e.g., regex containing `.` or `[^>]*`). For these, the cyclic-group witness used in the standard proof does not directly apply, but the AC⁰ ⊅ MOD_p step alone suffices for the blindness conclusion. **Appendix A** carries the formal version with an explicit AC⁰ many-one reduction.

The chain-of-trust assumption is that the LLM itself decodes the interleaved string and acts on the recovered payload. This is an *operational* observation rather than a theorem; we measured it empirically (§3, Pilot C).

---

## 3 — What We Verified

The empirical case for the bound rests on five numbers. The full methodology, corpus inventory, and per-pilot detail are in **Appendix B**.

| # | Result | Sample | Outcome |
|---|---|---|---|
| 1 | **Aperiodicity rate of deployed patterns** | 142 patterns, twelve sources (nine open-source guardrail-adjacent projects + three author-assembled sets covering 30%) | 142 / 142 aperiodic |
| 2 | **Primary MOD_p bypass** | 11 patterns × 4 primes (2, 3, 5, 7) × 12 payloads, NULL-byte filler | 56 / 56 tests bypass |
| 3 | **Filler-diversity bypass** | Same 11 patterns × 4 primes × 7 fillers (NULL, ASCII space, tab, tilde, backtick, U+200B zero-width space, U+200C zero-width non-joiner) | 392 / 392 tests bypass |
| 4 | **Third-party-library bypass** | 100 library-shipped patterns; literal-glue payload synthesizer baseline-matched 48 of them across 8 of 9 libraries | 48 / 48 bypass under both NULL and ASCII-space filler |
| 5 | **LLM decode reliability with control** | 4 open-weight models (3B–22B parameters) × 3 fillers × 5 benign payloads (60 cells decode condition; 20 cells random-character control) | 55 / 60 decode (91.7%) vs 0 / 20 control (0%); +91.7pp lift |

**What the five numbers say in one paragraph.** The substring-matching design pattern produces aperiodic guardrails in 100% of the corpus we surveyed — this is forced by the design pattern, not contingent. The MOD_p bypass succeeds at every prime we tested, with every filler choice we tested (including printable ASCII), against patterns from every third-party library where our payload synthesizer could produce a baseline match. Contemporary open-weight LLMs decode the interleaved encoding reliably at p = 2 across the three filler types, and a no-payload random-character control rules out the alternative explanation that models are emitting canonical answers ("Paris", "42") to surface cues without actually decoding.

We additionally surveyed four guardrail-library implementations — LLM-Guard's `BanSubstrings` scanner, Presidio's analyzer, Rebuff's heuristic detector, and NeMo Guardrails' content-safety check — for input-normalization behavior. None perform Unicode normalization (NFC/NFKC) or strip zero-width Unicode codepoints prior to regex match; one (Rebuff's heuristic stage) strips NULL bytes and zero-width codepoints as a side effect of broader sanitization, which leaves printable-filler bypass intact. (Detail in `results/library_normalization_survey.md`.)

---

## 4 — Where This Has Already Happened

The bypass class has documented instances in the literature, several initially diagnosed as engineering failures of specific products rather than as a structural property of substring-matching regex.

**Zero-width Unicode insertion (Boucher et al., IEEE S&P 2022, *Bad Characters*).** Identifies four imperceptible-attack subclasses; the first — interleaving zero-width Unicode codepoints between payload characters — is exactly the MOD₂ construction with a zero-width filler. The algebraic argument explains why no aperiodic regex within the substring-matching pattern can catch this filler-class problem at the structural level, and why the fix proposed in that paper (strip zero-width characters before matching) addresses one filler choice but does not generalize. The remaining three subclasses (homoglyphs, reorderings, deletions) are *not* MOD_p attacks and lie outside our bound.

**Encoding-based bypasses generally (Wei, Haghtalab & Steinhardt, NeurIPS 2023; Hackett et al., LLMSEC 2025).** *Jailbroken* documents attack types including base64 encoding, payload splitting, and prefix injection; *Bypassing LLM Guardrails* analyzes evasion attacks including character-injection methods. Both works document classes that *include* modular-counting and interleaving variants. The algebraic reframing of the relevant subclass is ours, not the cited papers'.

**StructuralSleight (Li et al., 2024).** Reports a 94.62% attack success rate against GPT-4o using uncommon text-organization structures. A subset encode the payload at modular positions within a structured template; the high success rate is consistent with the bound's prediction when a substring-matching regex pre-filter sits in the request path.

**Contiguous-paste data exfiltration (illustrative, not bound-explained).** Public reporting of LLM-mediated exfiltration (most prominently the 2023 Samsung incident) is typically diagnosed as a DLP policy gap. The leaked content was a contiguous code paste, a different DLP failure class; we do not claim the algebraic bound explains the Samsung case. We mention it because enterprises operating outbound DLP regex layers face the bound *additionally* if outbound content is ever reformatted into a MOD_p encoding.

---

## 5 — The Composition Asymmetry (Where the Operational Thesis Lives)

A natural reaction is: *fine, regex alone is not enough; that is why we have neural filters.* This is correct, but the composition behavior is asymmetric, and the asymmetry is where the bound bites operationally.

A neural filter — any transformer-based classifier — operates in TC⁰ (threshold circuits), as established by recent complexity-theoretic analyses of log-precision transformers (Merrill & Sabharwal 2023; Chiang, Cholak & Pillay 2023). TC⁰ properly contains AC⁰ and *does* include MOD_p as a *capacity bound*. This is not a guarantee that a specific trained transformer reliably computes MOD_p — Hahn (2020) established that fixed-architecture self-attention cannot model parity for unboundedly long inputs unless depth or heads scale with sequence length, and follow-up empirical work has confirmed that transformers' parity-detection performance degrades with input length. The capacity-vs-realization gap matters: a TC⁰-class neural filter *can in principle* catch MOD_p encodings, and trained classifiers in practice catch many of the bypass constructions, but the practical detection rate is a separate empirical question from the capacity bound.

Conditioned on a neural classifier that empirically catches the encoding class with acceptable accuracy, **the composition is asymmetric**:

| Composition | Behavior on the bypass class |
|---|---|
| **Parallel-OR** (the layer blocks if any constituent blocks; every request reaches the neural tier) | Neural filter's TC⁰ capacity *survives* the composition. Combined layer can detect MOD_p encodings at the rate the neural filter alone can. |
| **Serial-AND** (regex first; only ambiguous requests reach neural) | Regex tier's blindness *vetoes* the neural tier's capacity. If regex "allows" because the encoding bypassed it, neural never sees the request. **Combined layer's blindness equals the regex tier's blindness.** |

> **The operational thesis.** Wherever an aperiodic substring-matching regex tier sits as a serial pre-filter in front of a neural tier, the modular-counting encoding class bypasses *both*. The bound applies per-tier; system-level inheritance depends on the architecture's voting/veto structure. Hybrid topologies beyond the parallel-OR / serial-AND dichotomy require finer-grained analysis: rate-limited fallback applies the bound to the regex-sampled fraction; ensemble voting with a neural majority can attenuate the bound at a cost; sampled-routing applies the bound to traffic that hits the regex path.

We do not measure the prevalence of these composition patterns across industry; we claim that the math distinguishes them sharply and that any deployment using serial-AND for cost reasons should re-examine that choice with the bound in hand.

---

## 6 — Limitations

An honest read of the bound requires acknowledging where it does not bind, where the empirical evidence is thin, and what an adversarial co-evolution can and cannot reach.

**Scope of the bound.** The theorem applies to guardrails whose decision is computed by substring matching against an aperiodic regex pattern set. Guardrails whose decision tier is itself a neural classifier (LLM-as-judge systems including Llama Guard, Lakera Guard, Microsoft Prompt Shield, and the LLM-driven primary path of NeMo Guardrails) do *not* fall under the bound; they live in TC⁰ rather than AC⁰. Hybrid guardrails (regex pre-filter, neural arbiter) fall under the bound only for the regex tier.

**The LLM-decoder assumption.** The operational impact depends on the downstream LLM correctly *decoding* the interleaved string and acting on the recovered payload. Pilot C (§3, row 5) measured decode reliability of 91.7% across NULL/space/zero-width fillers at p = 2 against four open-weight models, with a no-payload control showing 0% base rate (+91.7pp lift). Frontier-model behavior is not directly sampled here and may differ. For payload classes outside the pilot (low-entropy structured payloads with rare codepoints, or models with aggressive input normalization), the assumption may not hold.

**Adversarial co-evolution.** The bound says no finite patch covers all filler choices simultaneously. It does not say an individual filler choice is unfixable. Vendors will and should patch the most-common filler choices (NULL bytes, zero-width Unicode codepoints, common whitespace classes), and each patch closes a specific evasion. The bound is asymptotic; vendor patches are pointwise. The right read: moving from regex to a more capable tier closes this class structurally, while local patching closes individual instances cheaply and is often the right operational choice in the short term.

**False-positive cost of the proposed mitigation.** Moving the bypass class to a neural tier or to an out-of-band architecture is not free. Neural tiers carry latency and false-positive costs that vary by model and workload; out-of-band architectures impose UX cost. We do not benchmark these costs. A complete operational decision requires comparing the residual risk of the regex-tier bound against the realized cost of the alternatives, with numbers from the deployer's own traffic.

**Coverage of the empirical sweep.** Pilot 4 (third-party library patterns) tests 48 of 100 library-shipped patterns: those for which our literal-glue payload synthesizer produced a baseline match. The remaining 52 are reached only by the algebraic bound, not by direct test. Improving the synthesizer (e.g., via `re_inverse`-style tools handling digit-format anchors) is a clean extension.

**Threat-model scope.** The bound assumes an adversary who controls the input string. It does *not* directly address indirect prompt injection (Greshake et al. 2023) where adversarial content arrives via document context, although the argument carries to indirect injection if the context flows through the same regex tier. Insider and supply-chain threats are out of scope.

---

## 7 — What To Do (Operational Recommendations)

For business and security leaders responsible for LLM deployments, the bound translates into four concrete actions, ordered by leverage.

**1. Audit your composition pattern this quarter.** Map every request path through your guardrail stack. For each path, identify whether the regex tier sits as a serial pre-filter (the bypass-class blindness propagates to the system) or as a parallel constituent (the neural tier's capacity survives). The audit is a one-engineer-week exercise for most deployments, and the diff between "regex first, neural for ambiguous" and "every request reaches neural" is concrete enough to reason about in cost terms.

**2. Treat the bypass class as a known-unknown, not as a known-known.** Vendor pattern libraries cover what they cover. The bound says they cannot cover the modular-counting encoding class within the substring-matching design pattern. *"Yes, the neural tier handles encoded attacks"* is the correct posture; *"yes, our regex patterns catch encoded attacks"* is a claim the math does not support for the bypass class.

**3. Use regex tiers for what they are good at.** Speed, determinism, audit trail, exact-match patterns. Direct prompt-injection keyword blocks. Exfiltration patterns where the leaked content is contiguous. Format validators. These are not in the bypass class and the regex tier excels at them. The bound is a boundary, not a verdict on the technology.

**4. Invest in out-of-band architectures for the highest-stakes cases.** Where the cost of a bypass is large enough that even a neural tier's residual error rate is unacceptable, architectures that never expose secrets or sensitive context to the inference layer are the right answer. An MIT-licensed reference implementation accompanying this work demonstrates one such architecture (an MCP server where the LLM operates on opaque handles while a separately-permissioned service performs field-fill via a controlled actuator); readers should verify its properties against their own threat model.[^secrets-router]

For researchers and tool authors, the bound suggests that further investment in regex pattern engineering for the bypass class is wasted effort. The interesting research questions are at the neural tier, in composition behavior, and in out-of-band architectures.

[^secrets-router]: *Disclosure: this implementation was developed by the author as part of this project.*

---

## 8 — Honest Scope

We make a narrow claim and want to be precise about it. **What we claim:** guardrails using substring matching against star-free regex patterns are provably blind to MOD_p encodings (with the alphabet-condition caveat in Appendix A); aperiodicity holds across our 142-pattern corpus; the bypass succeeds in every configuration we tested; and the operational consequence is that the serial-AND deployment pattern provides less safety than its cost might suggest *when the regex tier is aperiodic substring matching*. **What we do not claim:** we do not claim that all AI security is mathematically impossible; we do not claim neural guardrails have the same blind spot (they do not, because TC⁰ is strictly larger than AC⁰); we do not claim a regulatory framework follows from this result.

The original framing of this work was a much larger universal-impossibility claim covering all AI systems with compression capability, plus a regulatory-framework brief built on top of it. The universal claim turned out to be false — a single counterexample (a parity-projection classifier where the compression respects the safety equivalence relation) destroys the universal version. That destruction is documented alongside the project repository. The bound that survives — the one this article describes — is narrower, scoped to substring-matching aperiodic regex guardrails, and unconditional within that scope. The lesson, for the AI security literature, is that algebraic bounds on specific defense classes are tractable and useful; universal claims about "AI systems" are difficult to make rigorously, often false, and not necessary for the operationally important results. The regex-tier bound is the right shape of theorem for the field: a falsifiable, decision-relevant criterion that says, *if your defense layer is in this class, here is what it provably cannot do.*

The classical theorems we use are old: Schützenberger (1965; six decades), McNaughton-Papert (1971; five-and-a-half decades), Furst-Saxe-Sipser (1981; four-and-a-half decades), Håstad (1987; four decades), Barrington-Compton-Straubing-Thérien (1992; three-and-a-half decades). The novelty is in the application: the substring-aperiodicity lemma matched to the regex grammar present in production libraries; the empirical verification across the corpus; the explicit MOD_p bypass against representative patterns; and the operational analysis of what the bound implies for the serial-AND composition pattern. We use existing mathematical tools to answer a production-relevant question.

---

## Appendix A — Mathematical Apparatus

### A.1 The substring-aperiodicity lemma

**Lemma.** Let *r* be a regular expression built from literals, character classes (including PCRE shorthands `\s`, `\d`, `\w` and their negations), alternation, optional groups `r?`, dot, bounded repetition `r{m,n}`, and Kleene star or plus *applied to character classes only*. Let *L_r* = Σ\* · L(r) · Σ\* be the language of strings containing a substring matching *r*. Then the syntactic monoid M(L_r) is aperiodic.

**Proof sketch.** By structural induction on *r*. Each primitive (literal, character class, alternation, optional group, dot, bounded repetition) yields a star-free language; closure of star-free under concatenation, union, complement, and Kleene-star-on-character-class preserves star-freeness throughout the construction. Wrapping with Σ\* on either side preserves star-freeness (Σ\* is the complement of ∅, hence star-free). By Schützenberger's theorem, every star-free language has an aperiodic syntactic monoid. The Kleene-star/plus restriction to character classes is essential: general `(r)*` for arbitrary *r* can yield non-aperiodic languages — `(ab)*` is the standard counterexample. Full proof in `paper/main.tex`.

**Word-boundary anchors.** A separate lemma in `paper/main.tex` establishes that the `\b` word-boundary anchor preserves aperiodicity of the wrapped language: Σ\* · \b · L(r) · \b · Σ\* has aperiodic syntactic monoid whenever Σ\* · L(r) · Σ\* does. The proof realizes the anchor as an intersection with a position-context predicate that is itself star-free. This handles the 41 of 142 corpus patterns that fall outside the lemma's syntactic grammar due to `\b` use, including the single timeout pattern (a Presidio IBAN regex) whose interior is in the lemma's grammar but whose anchors are not.

### A.2 The Guardrail Blindness Theorem

**Setup.** Let *G* be a regex guardrail with substring-matching design (the union of patterns is wrapped Σ\* · ∪ᵢ L(rᵢ) · Σ\*), and assume M(L_G) is aperiodic. By Barrington-Compton-Straubing-Thérien, L_G ∈ AC⁰. Fix a prime *p* and define the modular-decode language

> *L_decode(p)* = { *w* ∈ Σ\* : *w*[0::p] ∈ L_blocked }

(every *p*-th character of *w*, starting at position 0, forms a blocked-pattern substring).

**Claim.** No aperiodic regex guardrail can decide *L_decode(p)*. Therefore no addition of further aperiodic regex patterns to *G* can detect MOD_p-encoded payloads.

**Proof structure.** Two regimes:

*Regime 1 (alphabet condition holds).* If there exists *f* ∈ Σ that does not advance the blocked-DFA from any state — equivalently, *f* lies outside the alphabet of L_blocked — then the transition monoid of *L_decode(p)* contains Z/pZ as a subgroup, witnessed by *f*ᵏ for *k* = 0, 1, ..., *p*−1. The syntactic monoid is therefore non-aperiodic, so *L_decode(p)* ∉ AC⁰. This regime covers production patterns whose effective alphabet is much smaller than Σ.

*Regime 2 (alphabet condition fails).* If no such *f* exists in Σ (e.g., regex contains `.` or negated character classes whose minimal-DFA alphabet equals Σ), the cyclic-witness construction does not apply directly. We instead exhibit an explicit AC⁰ many-one reduction from MOD_p to *L_decode(p)*: choose strings *h*⁺, *h*⁻ ∈ Σ\* of equal length with *h*⁺ ∈ L_blocked and *h*⁻ ∉ L_blocked, encode an instance *x* ∈ {0,1}ⁿ of MOD_p via a position-block encoding ρ(*x*) such that ρ(*x*) ∈ *L_decode(p)* iff Σᵢ *xᵢ* ≡ 0 (mod *p*). The map ρ is computable in AC⁰; therefore an AC⁰ decider for *L_decode(p)* would yield an AC⁰ decider for MOD_p, contradicting Furst-Saxe-Sipser. Full reduction in `paper/main.tex`.

**Corollary (MOD₂ sufficiency).** *p* = 2 already breaks every aperiodic regex guardrail in this class. Existing techniques — reading every other character, zero-width-character insertion, even-position acrostics — are all instances of the φ₂ construction.

### A.3 Why no patch within the regex class fixes it

The union of finitely many aperiodic-monoid regular languages is itself aperiodic (closure of star-free under Boolean operations and concatenation, classical). Therefore any regex *G'* added to *G* leaves L_{G ∪ G'} in AC⁰, which cannot decide *L_decode(p)*. Vendors *can* patch any individual filler choice (strip zero-width Unicode, refuse strings containing NULL bytes, etc.); the bound asserts only that no finite collection of such patches covers all filler choices simultaneously.

---

## Appendix B — Empirical Methodology

### B.1 Corpus assembly

Twelve sources, 142 patterns total. Nine open-source guardrail-adjacent projects contribute 100 patterns: LLM-Guard (12), llm-guard-py (12, plausibly overlapping LLM-Guard but with different pattern files; we report separately and leave deduplication to the reader), Rebuff (10), Guardrails-AI (12), Presidio (15), GitLeaks (8), LangKit (10), BodAIGuard (10), and the regex subset of NeMo Guardrails' content rails (11). Three author-assembled sets contribute 42 patterns (29.6% of the corpus): 8 patterns inspired by the OWASP Top 10 for LLMs taxonomy (OWASP-LLM is a guidance project rather than a library, so these are author-collated), 15 from a curated WAF-generic pattern set drawn from widely-cited enterprise WAF references, and 19 author-constructed adversarial test patterns. The corpus is released as `corpus_full.csv`.

### B.2 Aperiodicity verification

For each pattern: compile to a Thompson NFA, convert to the minimal DFA via powerset construction with Hopcroft minimization, enumerate the transition monoid via BFS over the Cayley graph, then for each monoid element *x* test that *x*ⁿ = *x*ⁿ⁺¹ for some computable *n* bounded by |M|² (Pin 1986). 119 patterns terminate with a complete monoid; 22 timeouts fall fully within the lemma's grammar (theorem-implied aperiodic); one timeout (a Presidio IBAN pattern, `\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b`) is established aperiodic by the word-boundary lemma in Appendix A.

### B.3 Pilot designs

**Pilot A — Primary bypass.** 11 author-assembled patterns × 4 primes (2, 3, 5, 7) × 12 payloads, NULL-byte filler, regex-match check. Artifact: `results/mod_p_bypass_matrix.json`.

**Pilot B — Filler diversity.** Same 11 patterns × 4 primes × 7 fillers (NULL, ASCII space, tab, tilde, backtick, U+200B zero-width space, U+200C zero-width non-joiner). 56-test grid per filler, 392 tests total. Artifact: `results/printable_filler_bypass.json`.

**Pilot C — LLM decode reliability with control.** Four open-weight models (llama3.1:8b, llama3.2:3b, qwen2.5-coder:14b, codestral; 3B–22B parameter range) under two conditions. *Decode* condition: 5 benign payloads × 3 fillers (NULL, ASCII space, U+200B) at *p* = 2 = 60 cells, graded against target answers. *Control* condition: random-ASCII strings of the same length as each encoded prompt, 20 cells (one per model × payload), graded against the same targets. Aggregate: decode 55/60 (91.7%), control 0/20 (0%), lift +91.7 percentage points. Artifact: `results/llm_decode_pilot_v2.json`.

**Pilot D — Third-party library patterns.** Literal-glue payload synthesizer (extract literal substrings from each library pattern, concatenate with whitespace) applied to all 100 library-shipped patterns. Synthesizer produced a candidate string for 100/100; candidate baseline-matched the source regex for 48 across 8 of 9 libraries (Presidio's PII patterns expect specific digit-format inputs and are the synthesis exception; an improved synthesizer using `re_inverse`-style tools would extend coverage). For the 48 baseline-matching patterns, MOD₂ bypass with NULL filler succeeds 48/48; with ASCII-space filler succeeds 48/48. Artifact: `results/library_pattern_bypass.json`.

**Library normalization survey.** Source-level inspection of LLM-Guard's `BanSubstrings` scanner, Presidio's analyzer, Rebuff's heuristic detector, and NeMo Guardrails' content-safety check on `main`/`develop` branch HEAD as of 2026-05-08. None perform Unicode normalization or strip zero-width Unicode codepoints prior to regex match. Artifact: `results/library_normalization_survey.md`.

---

## References

1. Schützenberger, M.-P. (1965). On finite monoids having only trivial subgroups. *Information and Control* 8(2), 190–194.
2. McNaughton, R., and Papert, S. (1971). *Counter-Free Automata*. MIT Press.
3. Barrington, D. A. M., Compton, K., Straubing, H., and Thérien, D. (1992). Regular languages in NC¹. *Journal of Computer and System Sciences* 44(3), 478–499.
4. Furst, M., Saxe, J. B., and Sipser, M. (1981). Parity, circuits, and the polynomial-time hierarchy. In *Proc. 22nd IEEE FOCS*, 260–270.
5. Håstad, J. (1987). *Computational Limitations of Small-Depth Circuits*. PhD thesis, MIT.
6. Krohn, K., and Rhodes, J. (1965). Algebraic theory of machines I: Prime decomposition theorem for finite semigroups and machines. *Trans. AMS* 116, 450–464.
7. Pin, J.-E. (1986). *Varieties of Formal Languages*. Plenum Press.
8. Boucher, N., Shumailov, I., Anderson, R., and Papernot, N. (2022). Bad Characters: Imperceptible NLP Attacks. In *Proc. IEEE Symposium on Security and Privacy*.
9. Wei, A., Haghtalab, N., and Steinhardt, J. (2023). Jailbroken: How does LLM safety training fail? In *Advances in Neural Information Processing Systems (NeurIPS)*.
10. Hackett, W., Birch, L., Trawicki, S., Suri, N., and Garraghan, P. (2025). Bypassing LLM guardrails: An empirical analysis of evasion attacks against prompt injection and jailbreak detection systems. In *Proc. First Workshop on LLM Security (LLMSEC), co-located with ACL 2025*.
11. Li, B., Xing, H., Tian, C., Huang, C., Qian, J., Xiao, H., and Feng, L. (2024). StructuralSleight: Automated jailbreak attacks on large language models utilizing uncommon text-organization structures. arXiv preprint 2406.08754.
12. Merrill, W., and Sabharwal, A. (2023). The parallelism tradeoff: Limitations of log-precision transformers. *TACL* 11, 531–545.
13. Chiang, D., Cholak, P., and Pillay, A. (2023). Tighter bounds on the expressivity of transformer encoders. In *Proc. 40th International Conference on Machine Learning (ICML)*, PMLR vol. 202.
14. Hahn, M. (2020). Theoretical limitations of self-attention in neural sequence models. *TACL* 8, 156–171.
15. Project repository (this work, 2026), to be deposited at a stable DOI for camera-ready. Includes: 142-pattern corpus (`corpus_full.csv`), monoid enumeration scripts, primary MOD_p bypass artifact (`mod_p_bypass_matrix.json`), three follow-up empirical pilots (`printable_filler_bypass.json`, `library_pattern_bypass.json`, `llm_decode_pilot_v2.json`), four-library normalization survey (`library_normalization_survey.md`), formal proofs (`paper/main.tex`), the parity-projection counterexample referenced in §8 (`counterexamples.md`), and the secrets-router reference implementation.
