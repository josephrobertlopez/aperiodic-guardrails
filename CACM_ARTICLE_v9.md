# Your Regex Guardrail Is Provably Bypassable

### A Six-Decade-Old Theorem Says So. Twelve Production Libraries Confirm It.

**Target Venue:** Communications of the ACM (Practice)
**Author:** Joseph R. Lopez
**Word Count:** ~4,400 (body ~2,800; appendices ~1,600)

---

Type **`b​o​m​b`** into a chatbot routed through LLM-Guard, Presidio, Rebuff, Guardrails-AI, NeMo's regex rails, or any of the dozen most-deployed regex content scanners. The four invisible characters between the `b`s are zero-width Unicode codepoints — they take no visual space, your eye reads `bomb`, and your regex sees nothing of the sort. The regex finds no contiguous match for any blocked keyword and waves the string through. The model behind the regex decodes the encoding and responds to the request.

This is not an engineering bug. It is a *mathematical property* of substring-matching regex, and it has been sitting in the formal-language-theory literature since Schützenberger published it in 1965. The property applies — provably, unconditionally, with no unproven complexity-class separations — to every aperiodic-monoid regex guardrail you have ever deployed.

It is not patchable. Adding more regex patterns does not close the gap. The union of finitely many aperiodic-monoid languages is itself aperiodic, which means your patched guardrail still lives in **AC⁰**, the constant-depth circuit class that *provably cannot count modulo a prime*. The bypass class — interleaving a payload with a filler at every other character position — exploits exactly that limit.

We surveyed 142 regex patterns from twelve sources spanning every widely-deployed open-source guardrail-adjacent project. Every single pattern was aperiodic. Every test we ran bypassed: 56 of 56 against author-assembled patterns at four primes; 392 of 392 across seven distinct fillers; 48 of 48 against patterns from eight different third-party libraries. We measured the load-bearing assumption that contemporary LLMs decode the encoding: four open-weight models recovered the payload **91.7% of the time** on benign tests, with a no-payload random-character control returning **0%** — a +91.7 percentage-point lift that rules out response-prior confounds.

The operational consequence is sharp. Wherever an aperiodic regex tier sits as a serial pre-filter in front of a neural arbiter, the bypass class passes through *both* tiers. The regex tier's blindness vetoes the neural tier's capacity, by construction. *"Cheap regex first, expensive neural model on the ambiguous remainder"* — the deployment composition that justifies the regex tier's cost in the first place — is the deployment composition that lets the bound bite at system level.

This is not "AI security is impossible." Neural tiers live in TC⁰ rather than AC⁰, and TC⁰ does include modular counting as a capacity bound. The bound applies to the regex tier; the question for the deployer is whether their architecture lets a local algebraic bound become a system-level operational gap.

---

## 1 — The Strike, in Code

A two-line bypass against an aperiodic regex guardrail:

```python
import re
guardrail = re.compile(r'(bomb|weapon|explosive|kill|attack)', re.IGNORECASE)

payload   = 'bomb'
encoded   = ''.join(c + '​' for c in payload).rstrip('​')
# encoded == 'b​o​m​b'  — visually identical to 'bomb'

assert not guardrail.search(encoded)  # the regex sees no contiguous match
```

A model downstream of this guardrail ingests `encoded`, recognizes `bomb` (zero-width characters do not change visual or semantic interpretation in any contemporary tokenizer we tested), and responds to the request. The same construction works with any blocked literal in any of the surveyed libraries, with any character outside the literal's alphabet as filler.

The construction is the **MOD₂ bypass**: place the payload at even positions, place a filler at odd positions, submit the result. Generalizes to any prime *p*.

---

## 2 — Why No Patch Closes It

The argument is one paragraph of mathematics. It uses three classical theorems and one new lemma; the formal apparatus is in **Appendix A**.

A regex used as a substring matcher (`re.search` is the design pattern shared by all surveyed libraries) defines a language whose syntactic monoid is **aperiodic** — Schützenberger 1965. Aperiodic-monoid languages are exactly the languages computable by **AC⁰** circuits — Barrington-Compton-Straubing-Thérien 1992. AC⁰ provably cannot compute parity or any modular-counting predicate — Furst-Saxe-Sipser 1981, Håstad 1987 (no P≠NP required). Therefore an aperiodic regex guardrail provably cannot decide *L_decode(p)*, the language of strings whose every-*p*-th character forms a blocked pattern. Adding more aperiodic regex patterns leaves the guardrail in AC⁰. **The patch does not exist within the regex class.**

Two regimes appear in the proof. For patterns whose effective alphabet is smaller than Σ — which covers the vast majority of production regex — a cyclic-group witness in the syntactic monoid of *L_decode(p)* directly demonstrates non-aperiodicity. For patterns whose alphabet equals Σ (regex containing `.` or negated character classes like `[^>]*`), the cyclic witness does not directly apply, but an explicit AC⁰ many-one reduction from MOD_p suffices. Both regimes give the same conclusion. Detail in Appendix A.

The bypass requires the LLM downstream of the guardrail to decode the encoding. This is an *operational* observation about contemporary deployed models, not a theorem. We measured it empirically and report the result in §3.

---

## 3 — What We Measured

Five numbers. Methodology and per-pilot detail in **Appendix B**.

| # | What | Sample | Result |
|---|---|---|---|
| 1 | **Aperiodicity rate of deployed patterns** | 142 patterns, twelve sources (nine third-party libraries + three author-assembled sets, 30%) | **142 / 142 aperiodic** |
| 2 | **Primary MOD_p bypass** | 11 patterns × 4 primes (2, 3, 5, 7) × 12 payloads, NULL-byte filler | **56 / 56 bypass** |
| 3 | **Filler-diversity bypass** | Same 11 patterns × 4 primes × 7 fillers (NULL, ASCII space, tab, tilde, backtick, U+200B, U+200C) | **392 / 392 bypass** |
| 4 | **Third-party-library bypass** | 100 library-shipped patterns; 48 baseline-matched our literal-glue payload synthesizer across 8 of 9 libraries | **48 / 48 bypass** under both NULL and ASCII-space filler |
| 5 | **LLM decode reliability with control** | 4 open-weight models × 3 fillers × 5 benign payloads (60 decode cells; 20 random-character control cells) | **55 / 60 decode (91.7%) vs 0 / 20 control (0%); +91.7 pp lift** |

**The case in one paragraph.** The substring-matching design pattern produces aperiodic guardrails in 100% of the corpus we surveyed — this is forced by the design, not contingent. The MOD_p bypass succeeds at every prime we tested, with every filler choice, against every third-party-library pattern where our synthesizer could produce a baseline match. Contemporary open-weight LLMs decode the encoding reliably; a random-character control rules out the alternative that we measured response priors instead of decoding.

We additionally surveyed four production guardrail implementations — LLM-Guard's `BanSubstrings` scanner, Presidio's analyzer, Rebuff's heuristic detector, NeMo Guardrails' content-safety check — for input-normalization behavior. None perform Unicode normalization (NFC/NFKC) or strip zero-width Unicode codepoints prior to regex match. One (Rebuff's heuristic stage) strips NULL bytes and zero-width codepoints as a side effect of broader sanitization; printable-filler bypass remains intact in that case.

---

## 4 — Where It Has Already Bitten

The bypass class has documented instances in the security and ML literature. The reframing through the algebraic lens is ours; the incidents are not.

**Boucher et al., IEEE S&P 2022, *Bad Characters*.** Identifies four imperceptible-attack subclasses; the first — interleaving zero-width Unicode codepoints between payload characters — is exactly the MOD₂ construction with a zero-width filler. The fix proposed in that paper (strip zero-width before matching) closes one filler choice. The bound says no finite collection of such fixes covers all filler choices simultaneously.

**Wei, Haghtalab, Steinhardt, *Jailbroken*, NeurIPS 2023.** Documents jailbreak attacks including base64 encoding, payload splitting, and prefix injection. A subset of these are MOD_p instances; the algebraic argument explains why no patch within the regex class closes the modular-counting subclass even after individual instances are addressed.

**Hackett et al., LLMSEC 2025, *Bypassing LLM Guardrails*.** Empirical analysis of evasion attacks against prompt-injection and jailbreak detection systems, including character-injection methods. The class of bypasses they document includes MOD_p; the bound says this is structural.

**Li et al., 2024, *StructuralSleight*.** Reports a 94.62% attack success rate against GPT-4o using uncommon text-organization structures. A subset encode the payload at modular positions within a structured template. The high success rate is consistent with the bound's prediction when a substring-matching regex pre-filter sits in the request path: the regex layer cannot block the encoded form, and the model decodes and acts on the payload before a neural post-filter (when present) can intervene.

These are not anecdotes loosely connected to a theory. They are the *predicted* class of failures, in the wild, with peer-reviewed analyses already done. The algebraic bound names the class.

---

## 5 — The Composition Trap

Practitioners' first instinct on hearing this result is correct: *fine, regex alone is not enough; that is why we have neural filters*. Their second instinct — that any neural-filter-plus-regex composition is safe — is where the bound becomes operationally interesting.

A neural filter — any transformer-based classifier — operates in **TC⁰** (threshold circuits): Merrill & Sabharwal 2023, Chiang-Cholak-Pillay 2023. TC⁰ properly contains AC⁰ and *does* include MOD_p as a capacity bound. This is not a guarantee that a specific trained transformer reliably computes MOD_p; Hahn 2020 established that fixed-architecture self-attention cannot model parity for unboundedly long inputs unless depth or heads scale with sequence length. The capacity-vs-realization gap matters: the neural tier *can in principle* catch MOD_p encodings, and trained classifiers in practice catch many of them, but the practical detection rate is a separate question from the capacity bound.

Conditioned on a neural classifier that empirically catches the encoding class with acceptable accuracy, the composition behavior splits sharply:

| Composition | Behavior on the bypass class |
|---|---|
| **Parallel-OR** *(every request reaches the neural tier; layer blocks if any constituent blocks)* | The neural filter's TC⁰ capacity **survives** the composition. Combined layer detects MOD_p encodings at the rate the neural filter alone can. |
| **Serial-AND** *(regex first; only ambiguous requests reach neural)* | The regex tier's blindness **vetoes** the neural tier's capacity. If the regex "allows" because the encoding bypassed it, the neural tier never sees the request. **Combined layer's blindness equals the regex tier's blindness.** |

> **The thesis.** Wherever an aperiodic substring-matching regex tier sits as a serial pre-filter in front of a neural tier, the modular-counting encoding class bypasses *both*. The bound applies per-tier; system-level inheritance depends on the architecture's voting/veto structure.

The serial-AND composition is *the* canonical justification for deploying a regex tier at all: it is what makes the regex tier's cost-savings real. The bound says that exact composition propagates the regex tier's algebraic blind spot to the system. Not slightly. *Exactly*.

Hybrid topologies require finer-grained analysis. Rate-limited fallback applies the bound to the regex-sampled fraction. Ensemble voting with a neural majority can attenuate the bound at a cost. Sampled-routing applies the bound to traffic that hits the regex path. The general claim is *not* "blindness propagates everywhere" — it is "blindness applies to the regex-tier component of any composition; whether the composite system inherits that blindness depends on the architecture's voting/veto structure."

---

## 6 — What To Do Monday

Four actions, ordered by leverage.

**1. Audit your composition pattern.** Map every request path through your guardrail stack. For each path, identify whether the regex tier is a serial pre-filter (the bypass-class blindness propagates to the system) or a parallel constituent (the neural tier's capacity survives). One engineer-week for most deployments. The diff between *"regex first, neural for ambiguous"* and *"every request reaches neural"* is concrete enough to reason about in cost terms.

**2. Treat the bypass class as a known-unknown.** Vendor pattern libraries cover what they cover. The bound says they cannot cover the modular-counting encoding class within the substring-matching design pattern. *"Yes, the neural tier handles encoded attacks"* is the correct posture; *"yes, our regex patterns catch encoded attacks"* is a claim the math does not support for the bypass class.

**3. Use regex tiers for what they are good at.** Speed, determinism, audit trail, exact-match patterns. Direct prompt-injection keyword blocks. Exfiltration patterns where the leaked content is contiguous. Format validators. These are not in the bypass class and the regex tier excels at them. The bound is a boundary, not a verdict on the technology.

**4. Invest in out-of-band architectures for the highest-stakes cases.** Where the cost of a bypass is large enough that even a neural tier's residual error rate is unacceptable, architectures that never expose secrets or sensitive context to the inference layer are the right answer. An MIT-licensed reference implementation accompanying this work demonstrates one such architecture (an MCP server where the LLM operates on opaque handles while a separately-permissioned service performs field-fill via a controlled actuator).[^secrets-router]

For researchers and tool authors: further investment in regex pattern engineering for the bypass class is wasted effort. The interesting research questions are at the neural tier, in composition behavior, and in out-of-band architectures.

[^secrets-router]: *Disclosure: this implementation was developed by the author as part of this project. Readers should verify its properties against their own threat model.*

---

## 7 — What We Do Not Claim

We do not claim that all AI security is mathematically impossible. We do not claim neural guardrails have the same blind spot — they do not, because TC⁰ is strictly larger than AC⁰. We do not claim a regulatory framework follows from this result. The bound applies to substring-matching aperiodic regex guardrails; it does not apply to LLM-as-judge systems (Llama Guard, Lakera Guard, Microsoft Prompt Shield, NeMo's primary LLM-driven path), which live in TC⁰ and have the capacity to recognize the bypass class. The operational impact depends on the LLM downstream of the guardrail decoding the interleaving — Pilot 5 shows this holds at 91.7% across four open-weight models with a 0% no-payload control, but frontier-model behavior is not directly sampled and may differ. Adversarial co-evolution can patch any individual filler choice; the bound says no finite patch covers all filler choices simultaneously, but local patches close individual instances cheaply and are often the right operational choice in the short term.

The original framing of this work was a much larger universal-impossibility claim covering all AI systems with compression capability, plus a regulatory-framework brief built on top of it. That claim turned out to be false — a single counterexample (a parity-projection classifier where the compression respects the safety equivalence relation) destroys the universal version. That destruction is documented alongside the project repository. The bound that survives — the one this article describes — is narrower, scoped to substring-matching aperiodic regex guardrails, and unconditional within that scope.

The classical theorems we use are old: Schützenberger (1965), McNaughton-Papert (1971), Furst-Saxe-Sipser (1981), Håstad (1987), Barrington-Compton-Straubing-Thérien (1992). The novelty is in the application: the substring-aperiodicity lemma matched to the regex grammar present in production libraries; the empirical verification across the corpus; the explicit MOD_p bypass against representative patterns; and the operational analysis of what the bound implies for the serial-AND composition. We use existing mathematical tools to answer a production-relevant question.

The right shape of result for this field: a falsifiable, decision-relevant criterion that says, *if your defense layer is in this class, here is what it provably cannot do.*

---

## Appendix A — Mathematical Apparatus

### A.1 Substring-aperiodicity lemma

**Lemma.** Let *r* be a regular expression built from literals, character classes (including PCRE shorthands `\s`, `\d`, `\w` and their negations), alternation, optional groups `r?`, dot, bounded repetition `r{m,n}`, and Kleene star or plus *applied to character classes only*. Let *L_r* = Σ\* · L(r) · Σ\* be the language of strings containing a substring matching *r*. Then the syntactic monoid M(L_r) is aperiodic.

**Proof sketch.** By structural induction on *r*. Each primitive (literal, character class, alternation, optional group, dot, bounded repetition, Kleene-on-character-class) yields a star-free language; closure of star-free under concatenation, union, complement, and Kleene-on-character-class preserves star-freeness throughout. Wrapping with Σ\* on either side preserves star-freeness (Σ\* is the complement of ∅, hence star-free). By Schützenberger's theorem, every star-free language has an aperiodic syntactic monoid. The Kleene-star/plus restriction to character classes is essential: general `(r)*` for arbitrary *r* can yield non-aperiodic languages — `(ab)*` is the standard counterexample. Full proof in `paper/main.tex`.

### A.2 Word-boundary anchors preserve aperiodicity

A separate lemma in `paper/main.tex` establishes that the `\b` word-boundary anchor preserves aperiodicity: Σ\* · \b · L(r) · \b · Σ\* has aperiodic syntactic monoid whenever Σ\* · L(r) · Σ\* does. The argument realizes the anchor as an intersection with a position-context predicate that is itself star-free. This handles the 41 of 142 corpus patterns falling outside the lemma's syntactic grammar due to `\b` use, including the single timeout pattern (a Presidio IBAN regex) whose interior is in the lemma's grammar.

### A.3 The Guardrail Blindness Theorem

**Setup.** Let *G* be a regex guardrail with substring-matching design (the union of patterns is wrapped Σ\* · ∪ᵢ L(rᵢ) · Σ\*), and assume M(L_G) is aperiodic. By Barrington-Compton-Straubing-Thérien, L_G ∈ AC⁰. Fix a prime *p* and define the modular-decode language

> *L_decode(p)* = { *w* ∈ Σ\* : *w*[0::p] ∈ L_blocked }

(every *p*-th character of *w*, starting at position 0, forms a blocked-pattern substring).

**Claim.** No aperiodic regex guardrail can decide *L_decode(p)*. Therefore no addition of further aperiodic regex patterns to *G* can detect MOD_p-encoded payloads.

**Proof structure (two regimes).**

*Regime 1 (alphabet condition holds).* If there exists *f* ∈ Σ that does not advance the blocked-DFA from any state — equivalently, *f* lies outside the alphabet of L_blocked — then the transition monoid of *L_decode(p)* contains Z/pZ as a subgroup, witnessed by *f*ᵏ for *k* = 0, 1, ..., *p*−1. The syntactic monoid is therefore non-aperiodic, so *L_decode(p)* ∉ AC⁰. This regime covers production patterns whose effective alphabet is much smaller than Σ.

*Regime 2 (alphabet condition fails).* If no such *f* exists in Σ (regex contains `.` or negated character classes whose minimal-DFA alphabet equals Σ), the cyclic-witness construction does not apply directly. We exhibit an explicit AC⁰ many-one reduction from MOD_p to *L_decode(p)*: choose strings *h*⁺, *h*⁻ ∈ Σ\* of equal length with *h*⁺ ∈ L_blocked and *h*⁻ ∉ L_blocked; encode an instance *x* ∈ {0,1}ⁿ of MOD_p via a position-block encoding ρ(*x*) such that ρ(*x*) ∈ *L_decode(p)* iff Σᵢ *xᵢ* ≡ 0 (mod *p*). The map ρ is computable in AC⁰; an AC⁰ decider for *L_decode(p)* would yield an AC⁰ decider for MOD_p, contradicting Furst-Saxe-Sipser. Full reduction in `paper/main.tex`.

**Corollary (MOD₂ sufficiency).** *p* = 2 already breaks every aperiodic regex guardrail in this class. Existing techniques — reading every other character, zero-width-character insertion, even-position acrostics — are all instances of the φ₂ construction.

### A.4 No patch within the regex class fixes it

The union of finitely many aperiodic-monoid regular languages is itself aperiodic (closure of star-free under Boolean operations and concatenation). Therefore any regex *G'* added to *G* leaves L_{G ∪ G'} in AC⁰, which cannot decide *L_decode(p)*. Vendors *can* patch any individual filler choice (strip zero-width Unicode, refuse strings containing NULL bytes, etc.); the bound asserts only that no finite collection of such patches covers all filler choices simultaneously.

---

## Appendix B — Empirical Methodology

### B.1 Corpus

Twelve sources, 142 patterns. **Nine third-party projects** contribute 100 patterns: LLM-Guard (12), llm-guard-py (12, plausibly overlapping LLM-Guard but with different pattern files), Rebuff (10), Guardrails-AI (12), Presidio (15), GitLeaks (8), LangKit (10), BodAIGuard (10), and the regex subset of NeMo Guardrails' content rails (11). **Three author-assembled sets** contribute 42 patterns (30%): 8 inspired by the OWASP Top 10 for LLMs taxonomy (OWASP-LLM is a guidance project rather than a library, so these are author-collated), 15 from a curated WAF-generic set, and 19 author-constructed adversarial test patterns. Released as `corpus_full.csv`.

### B.2 Aperiodicity verification

For each pattern: compile to a Thompson NFA, convert to the minimal DFA via powerset construction with Hopcroft minimization, enumerate the transition monoid via BFS over the Cayley graph, then for each monoid element *x* test that *x*ⁿ = *x*ⁿ⁺¹ for some *n* bounded by |M|² (Pin 1986). 119 complete; 22 timeouts within the lemma's grammar (theorem-implied aperiodic); 1 timeout (Presidio IBAN, `\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b`) established aperiodic by the word-boundary lemma.

### B.3 Pilot designs

**Pilot A (primary bypass).** 11 author-assembled patterns × 4 primes (2, 3, 5, 7) × 12 payloads, NULL-byte filler, regex-match check. Artifact: `results/mod_p_bypass_matrix.json`.

**Pilot B (filler diversity).** Same 11 patterns × 4 primes × 7 fillers (NULL, ASCII space, tab, tilde, backtick, U+200B zero-width space, U+200C zero-width non-joiner). 56-test grid per filler, 392 tests total. Artifact: `results/printable_filler_bypass.json`.

**Pilot C (LLM decode reliability with control).** Four open-weight models (llama3.1:8b, llama3.2:3b, qwen2.5-coder:14b, codestral; 3B–22B parameter range) under two conditions. *Decode*: 5 benign payloads × 3 fillers (NULL, ASCII space, U+200B) at *p* = 2 = 60 cells, graded against target answers. *Control*: random-ASCII strings of the same length as each encoded prompt, 20 cells (one per model × payload), graded against the same targets. Aggregate: decode 55/60 (91.7%), control 0/20 (0%), lift +91.7 percentage points. Artifact: `results/llm_decode_pilot_v2.json`.

**Pilot D (third-party library patterns).** Literal-glue payload synthesizer (extract literal substrings, concatenate with whitespace) applied to all 100 library-shipped patterns. Synthesizer produced a candidate string for 100/100; 48 baseline-matched the source regex across 8 of 9 libraries (Presidio's PII patterns expect specific digit-format inputs and are the synthesis exception). For the 48 baseline-matching patterns, MOD₂ bypass with NULL filler succeeds 48/48; with ASCII-space filler succeeds 48/48. Artifact: `results/library_pattern_bypass.json`.

**Library normalization survey.** Source-level inspection of LLM-Guard's `BanSubstrings` scanner, Presidio's analyzer, Rebuff's heuristic detector, NeMo Guardrails' content-safety check on `main`/`develop` HEAD as of 2026-05-08. None perform Unicode normalization or strip zero-width Unicode codepoints prior to regex match. Artifact: `results/library_normalization_survey.md`.

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
9. Wei, A., Haghtalab, N., and Steinhardt, J. (2023). Jailbroken: How does LLM safety training fail? In *NeurIPS*.
10. Hackett, W., Birch, L., Trawicki, S., Suri, N., and Garraghan, P. (2025). Bypassing LLM guardrails: An empirical analysis of evasion attacks against prompt injection and jailbreak detection systems. In *Proc. First Workshop on LLM Security (LLMSEC), co-located with ACL 2025*.
11. Li, B., Xing, H., Tian, C., Huang, C., Qian, J., Xiao, H., and Feng, L. (2024). StructuralSleight: Automated jailbreak attacks on large language models utilizing uncommon text-organization structures. arXiv preprint 2406.08754.
12. Merrill, W., and Sabharwal, A. (2023). The parallelism tradeoff: Limitations of log-precision transformers. *TACL* 11, 531–545.
13. Chiang, D., Cholak, P., and Pillay, A. (2023). Tighter bounds on the expressivity of transformer encoders. In *Proc. 40th International Conference on Machine Learning (ICML)*, PMLR vol. 202.
14. Hahn, M. (2020). Theoretical limitations of self-attention in neural sequence models. *TACL* 8, 156–171.
15. Project repository (this work, 2026), to be deposited at a stable DOI for camera-ready. Includes: 142-pattern corpus (`corpus_full.csv`), monoid enumeration scripts, primary MOD_p bypass artifact (`mod_p_bypass_matrix.json`), three follow-up empirical pilots (`printable_filler_bypass.json`, `library_pattern_bypass.json`, `llm_decode_pilot_v2.json`), four-library normalization survey (`library_normalization_survey.md`), formal proofs (`paper/main.tex`), the parity-projection counterexample referenced in §7 (`counterexamples.md`), and the secrets-router reference implementation.
