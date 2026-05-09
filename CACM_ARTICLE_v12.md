# Your Regex Guardrail Is Provably Bypassable

### Six Decades of Algebra, Twelve Production Libraries, And the AC⁰ Tier of Your LLM Stack

**Target Venue:** Communications of the ACM (Practice)
**Author:** Joseph R. Lopez
**Word Count:** ~5,200 (body ~3,400; appendices ~1,800)

---

Type **`b​o​m​b`** into a chatbot routed through LLM-Guard, Presidio, Rebuff, Guardrails-AI, NeMo's regex rails, or any of the dozen most-deployed regex content scanners. The four invisible characters between the `b`s are zero-width Unicode codepoints — they take no visual space, your eye reads `bomb`, and your regex sees nothing of the sort. The regex finds no contiguous match for any blocked keyword and waves the string through. The model behind the regex decodes the encoding and responds to the request.

This is not an engineering bug. It is a *mathematical property* of substring-matching regex, sitting in the formal-language-theory literature since Schützenberger 1965. The property applies — provably, with no unproven complexity-class separations — to every aperiodic-monoid regex guardrail in our 142-pattern survey, and structurally to every regex guardrail using the substring-matching design pattern (`re.search` and equivalents).

The bound is patch-resistant in a precise sense: the *class* of bypasses cannot be closed within the regex tier. Vendors *can* patch any individual filler choice (strip zero-width Unicode codepoints, reject NULL bytes, normalize whitespace), and each patch closes a specific evasion. But the union of finitely many aperiodic-monoid languages is itself aperiodic, which means your patched guardrail still lives in **AC⁰**, the constant-depth circuit class that *provably cannot count modulo a prime*. The bypass class — interleaving a payload with a filler at every other character position — exploits exactly that limit, and a new filler choice always exists outside any finite patch set.

And the bound does not stop at input scanners. Every aperiodic regex sitting anywhere in your stack is in AC⁰: outbound DLP scanners, tool-call argument validators, JSON Schema `pattern` fields, trie- and DFA-based blocklists, multi-stage pipelines whose individual tiers each call `re.search`. The composition argument carries: serial AND of aperiodic tiers is still aperiodic. The bound applies to the *class*, not the *tier*.

We surveyed 142 regex patterns from twelve sources spanning every widely-deployed open-source guardrail-adjacent project. Every single pattern was aperiodic. Every test we ran bypassed: 56 of 56 against author-assembled patterns at four primes; 392 of 392 across seven distinct fillers; 48 of 48 against patterns from eight different third-party libraries. We measured the load-bearing operational assumption that contemporary LLMs decode the encoding: four open-weight models recovered the payload **91.7%** of the time on benign tests, with a no-payload random-character control returning **0%** — a +91.7 percentage-point lift that rules out response-prior confounds.

The operational consequence is sharp. Wherever an aperiodic regex tier sits as a serial pre-filter in front of a more capable tier — neural classifier, LLM judge, the model itself — the bypass class passes through *both*. The regex tier's blindness vetoes the more capable tier's capacity, by construction. *"Cheap regex first, expensive model on the ambiguous remainder"* — the deployment composition that justifies the regex tier's cost in the first place — is the deployment composition that lets a local algebraic bound bite at system level.

This is not "AI security is impossible." Neural and LLM-judge tiers live in TC⁰ rather than AC⁰, and TC⁰ does include modular counting as a capacity bound. The bound applies to the AC⁰ tier wherever it sits; the question for the deployer is whether their architecture lets that local bound become a system-level operational gap.

---

## 1 — The Strike, in Code

A two-line bypass against an aperiodic regex guardrail:

```python
import re
guardrail = re.compile(r'(bomb|weapon|explosive|kill|attack)', re.IGNORECASE)

payload  = 'bomb'
encoded  = ''.join(c + '​' for c in payload).rstrip('​')
# encoded == 'b​o​m​b'  — visually identical to 'bomb'

assert not guardrail.search(encoded)        # regex sees no contiguous match
```

A model downstream of this guardrail ingests `encoded`, recognizes `bomb` (zero-width characters do not change visual or semantic interpretation in any contemporary tokenizer we tested), and responds to the request.

The same algebraic construction succeeds against any aperiodic substring-matching guardrail. The *operational* impact varies by what the downstream consumer does with the encoded payload — §3 makes this gradient explicit. The classes of guardrails to which the bound applies:

- **Outbound DLP regex** scanning model output for PII or secret patterns. The model can produce MOD_p-encoded content; the regex passes it; the consumer (often a human reading rendered output) decodes.
- **Tool-call argument validators** doing regex whitelisting on agent function calls. Operationally relevant when the downstream tool feeds another LLM in a multi-step agentic chain (MCP, multi-LLM orchestration); operationally inert when the tool processes the argument literally (shell, database, filesystem call).
- **JSON Schema `pattern` fields** (ECMA-262 regex subset, excluding lookarounds and backreferences) validating structured outputs. Operationally relevant when the consuming pipeline includes an LLM step that decodes; operationally inert when consumed literally by downstream code.
- **Trie- and DFA-based blocklists** matching against finite literal sets. Finite languages are trivially star-free (every finite language is a finite union of singletons, all star-free), so the algebraic class applies; operational impact tracks the consumer as above.

The construction is the **MOD₂ bypass**: place the payload at even positions, place a filler at odd positions, submit the result. Generalizes to any prime *p*.

---

## 2 — Why No Patch Closes It (Inside the Regex Class)

The argument is one paragraph of mathematics. Three classical theorems and one new lemma; the formal apparatus is in **Appendix A**.

A regex used as a substring matcher (`re.search` is the design pattern shared by all surveyed libraries) defines a language whose syntactic monoid is **aperiodic** — Schützenberger 1965. Aperiodic-monoid languages are exactly the languages computable by **AC⁰** circuits — Barrington-Compton-Straubing-Thérien 1992. AC⁰ provably cannot compute parity or any modular-counting predicate — Furst-Saxe-Sipser 1981, Håstad 1987 (no P≠NP required). Therefore an aperiodic regex guardrail provably cannot decide *L_decode(p)*, the language of strings whose every-*p*-th character forms a blocked pattern. Adding more aperiodic regex patterns leaves the guardrail in AC⁰, by closure of star-free languages under Boolean operations and concatenation. **The patch does not exist within the regex class.**

Two regimes appear in the proof, and both close cleanly. For patterns whose effective alphabet is smaller than Σ — the vast majority of production regex — a cyclic-group witness in the syntactic monoid of *L_decode(p)* directly demonstrates non-aperiodicity, using a single character outside the blocked-pattern alphabet as the cyclic generator. For patterns whose alphabet equals Σ (regex containing `.` or negated character classes like `[^>]*`), no such external character exists, but the cyclic witness still appears via *position-shift offsets*: powers of any single character `a^j` for `j = 0, ..., p−1` are pairwise syntactically inequivalent in `L_decode(p)`, witnessed by contexts where the position-mod-p offset shifts which characters of a long blocked-pattern witness `h^N` land in the decoded substring. Both regimes give the same conclusion: *L_decode(p)* ∉ AC⁰ for any nontrivial substring-matched `L_blocked` (one accepted and one rejected string of equal length differing in at least one position — every nontrivial production guardrail). Detail and the Regime 2 theorem in Appendix A.

The bypass requires the LLM downstream of the guardrail to *decode* the encoding. This is an *operational* observation about contemporary deployed models, not a theorem. We measured it empirically; results in §3.

---

## 3 — The Bound's Actual Surface Area

Treating "guardrails" as a single thing obscures where the bound bites and where it doesn't. The honest taxonomy:

| **In scope** (star-free string-matchers, hence in AC⁰) | **Out of scope** (TC⁰ or different class) |
|---|---|
| Input-side regex content scanners (LLM-Guard, Rebuff, etc.) | LLM-as-judge systems (Llama Guard, Lakera, Microsoft Prompt Shield, NeMo's primary path) |
| Output-side regex DLP / content moderation | Embedding-based similarity filters (continuous, not discrete language recognition) |
| Tool-call argument validators using regex | Fine-tuned BERT-class toxicity / safety classifiers |
| JSON Schema `pattern` field validators (ECMA-262 subset, no lookarounds/backrefs) | Behavioral / rate-limit / quota guardrails (orthogonal to content) |
| Trie- and DFA-based blocklists matching finite literal sets | Model-internal safety (RLHF, constitutional AI, refusal training) |
| Bloom-filter blocklists *of the underlying literal set* (the algebraic bound applies to the set; the false-positive class is additional noise) | Token-budget / context-window guardrails |
| **Any Boolean composition** of the above (intersection or union) — the syntactic-monoid class is closed under finite Boolean operations and concatenation (Pin 1986) | Formal verification of model behavior on bounded input classes |

The in-scope class is unified by *being in AC⁰*. The out-of-scope classes either live in TC⁰ (transformer-based filters) or are not language-recognition decisions at all (rate limits, model-internal training).

**Two non-obvious consequences for production stacks.**

First, a multi-stage pipeline whose every tier is aperiodic regex is *still in AC⁰*. The intersection of finitely many aperiodic-monoid regular languages is aperiodic; the union is aperiodic; the composition through any Boolean structure is aperiodic. Stacking five regex tiers does not give you parity-detection capacity. It gives you a more elaborate AC⁰ filter.

Second, the operational *impact* of the bound varies by what decodes the encoded payload downstream:

| Downstream consumer | Decode behavior | Operational bite |
|---|---|---|
| **LLM ingesting prompt** | Decodes interleaving (Pilot 5: 91.7% across 4 open-weight models, +91.7pp lift over control) | **High** |
| **Human reading model output** | Decodes visually (zero-width chars are invisible; users read `bomb`) | **High** |
| **Downstream LLM in agent chain** (MCP server passing tool-args to another LLM; multi-step orchestration; LLM-judged structured outputs) | Same as input case — decodes | **High** |
| **RAG pipeline including an LLM step** (retrieved JSON document or pattern-validated content fed into model context) | LLM in the loop decodes | **High** |
| **Tool execution layer, direct** (shell, DB query, filesystem call processing the argument literally without LLM in the chain) | Processes literally; usually fails to execute encoded form | **Low** (formally bypassed but operationally inert) |
| **Schema-consumer pipeline, direct** (validated JSON consumed by downstream code without LLM step) | Processes literally | **Low** |

The strongest bite is exactly where the article's primary harness measures it: the path from user prompt → regex tier → model. The article extends to outbound DLP and agentic chains where the downstream is again a model or a human reader. We do not claim operational impact on tool-execution or schema-consumer paths beyond the algebraic bound; the bound applies, but the bypass is theoretical there.

This taxonomy is what we mean by *"the AC⁰ tier of your LLM stack"* in the subtitle. It is not "your guardrail." It is *every aperiodic-regex string-matcher in your request flow*, and the operational impact tracks who decodes downstream.

---

## 4 — What We Measured

Five numbers for the input-regex case, with the methodology and per-pilot detail in **Appendix B**.

| # | What | Sample | Result |
|---|---|---|---|
| 1 | **Aperiodicity rate of deployed patterns** | 142 patterns, twelve sources (nine third-party libraries + three author-assembled sets, 30%) | **142 / 142 aperiodic** (119 by completed monoid enumeration; 22 theorem-implied via the substring-aperiodicity lemma; 1 — the Presidio IBAN pattern — established by the word-boundary lemma in Appendix A) |
| 2 | **Primary MOD_p bypass** | 11 patterns × 4 primes (2, 3, 5, 7) × 12 payloads, NULL-byte filler | **56 / 56 bypass** |
| 3 | **Filler-diversity bypass** | Same 11 patterns × 4 primes × 7 fillers (NULL, ASCII space, tab, tilde, backtick, U+200B, U+200C) | **392 / 392 bypass** |
| 4 | **Third-party-library bypass** | 100 library-shipped patterns; 48 baseline-matched our literal-glue payload synthesizer across 8 of 9 libraries | **48 / 48 bypass** under both NULL and ASCII-space filler |
| 5 | **LLM decode reliability with control** | 4 open-weight models × 3 fillers × 5 benign payloads (60 decode cells; 20 random-character control cells) | **55 / 60 decode (91.7%) vs 0 / 20 control (0%); +91.7 pp lift** |

The substring-matching design pattern produces aperiodic guardrails in 100% of the corpus we surveyed — forced by the design, not contingent. The MOD_p bypass succeeds at every prime we tested, with every filler choice we tested, against every third-party-library pattern where our synthesizer could produce a baseline match. Contemporary open-weight LLMs decode the encoding reliably; the random-character control rules out the alternative that we measured response priors instead of decoding.

We additionally surveyed four production guardrail implementations — LLM-Guard's `BanSubstrings` scanner, Presidio's analyzer, Rebuff's heuristic detector, NeMo Guardrails' content-safety check — for input-normalization behavior. None perform Unicode normalization (NFC/NFKC) or strip zero-width Unicode codepoints prior to regex match. One (Rebuff's heuristic stage) strips NULL bytes and zero-width codepoints as a side effect of broader sanitization; printable-filler bypass remains intact in that case.

We did not run pilots on output-side DLP, tool-call argument validators, schema validators, or trie/Bloom filters. The bound applies to those by the algebraic argument; the operational-impact gradient in §3 says where the bite lands. Extension pilots are a clean follow-up.

---

## 5 — Where It Has Already Bitten

The bypass class has documented instances in the security and ML literature. The reframing through the algebraic lens is ours; the incidents are not.

**Boucher et al., IEEE S&P 2022, *Bad Characters*.** Identifies four imperceptible-attack subclasses; the first — interleaving zero-width Unicode codepoints between payload characters — is exactly the MOD₂ construction with a zero-width filler. The fix proposed in that paper (strip zero-width before matching) closes one filler choice. The bound says no finite collection of such fixes covers all filler choices simultaneously.

**Wei, Haghtalab, Steinhardt, *Jailbroken*, NeurIPS 2023.** Documents jailbreak attacks including base64 encoding, payload splitting, and prefix injection. A subset are MOD_p instances; the algebraic argument explains why no patch within the regex class closes the modular-counting subclass even after individual instances are addressed.

**Hackett et al., LLMSEC 2025, *Bypassing LLM Guardrails*.** Empirical analysis of evasion attacks against prompt-injection and jailbreak detection systems, including character-injection methods. The class of bypasses they document includes MOD_p; the bound says this is structural.

**Li et al., 2024, *StructuralSleight*.** Reports a 94.62% attack success rate against GPT-4o using uncommon text-organization structures. A subset encode the payload at modular positions within a structured template. The high success rate is consistent with the bound's prediction when a substring-matching regex pre-filter sits in the request path.

**Indirect prompt injection (Greshake et al., AISec 2023).** Adversarial content arrives via document context — emails, web pages, tool output. If the retrieval path scans incoming documents through aperiodic regex, the bound applies. The encoded payload survives the regex tier in the retrieved document, the LLM ingests the document as context, and the LLM decodes during reasoning. This expands the threat surface beyond direct user input.

These are the *predicted* class of failures, in the wild, with peer-reviewed analyses already done. The algebraic bound names the class.

---

## 6 — The Composition Trap

A neural filter — any transformer-based classifier — operates in **TC⁰** (Merrill & Sabharwal 2023, Chiang-Cholak-Pillay 2023). TC⁰ properly contains AC⁰ and *does* include MOD_p as a capacity bound. This is not a guarantee that a specific trained transformer reliably computes MOD_p; Hahn 2020 established that fixed-architecture self-attention cannot model parity for unboundedly long inputs unless depth or heads scale with sequence length. The capacity-vs-realization gap matters: the neural tier *can in principle* catch MOD_p encodings, and trained classifiers in practice catch many of them, but the practical detection rate is a separate question from the capacity bound.

Conditioned on a neural classifier that empirically catches the encoding class with acceptable accuracy, the composition behavior splits sharply:

| Composition | Behavior on the bypass class |
|---|---|
| **Parallel-OR** *(every request reaches both tiers; layer blocks if any constituent blocks)* | The neural filter's TC⁰ capacity **survives**. Combined layer detects MOD_p encodings at the rate the neural filter alone can. |
| **Serial-AND** *(regex first; only ambiguous requests reach neural)* | The regex tier's blindness **vetoes** the neural tier's capacity. **Combined layer's blindness equals the regex tier's blindness.** |

> **The thesis.** Wherever an aperiodic substring-matching tier sits as a serial pre-filter in front of a more-capable tier, the modular-counting encoding class bypasses *both*. The bound applies per-tier; system-level inheritance depends on the architecture's voting/veto structure.

The serial-AND composition is *the* canonical justification for deploying a regex tier at all: it is what makes the regex tier's cost-savings real. The bound says that exact composition propagates the regex tier's algebraic blind spot to the system. Not slightly. *Exactly*.

Hybrid topologies require finer-grained analysis. Rate-limited fallback applies the bound to the regex-sampled fraction. Ensemble voting with a neural majority can attenuate the bound at a cost. Sampled-routing applies the bound to traffic that hits the regex path. Multi-stage agentic pipelines compound the issue: every aperiodic tier in the chain is in AC⁰, and the conjunction of multiple AC⁰ checks is still AC⁰.

The cobra here is not "the regex tier bypasses." The cobra is: *the regex tier bypasses, AND the architecture you deployed for cost reasons inherits the bypass at system level, AND adding more regex does not help.*

---

## 7 — What To Do Monday

Four actions, ordered by leverage.

**1. Audit your composition pattern across the entire AC⁰ tier of your stack.** Map every request path through every aperiodic regex in your stack — input scanners, output DLP, tool-call validators, schema validators, retrieval-content scanners. For each, identify whether the tier sits as a serial pre-filter (the bypass-class blindness propagates) or as a parallel constituent (the neural tier's capacity survives). One engineer-week for most deployments. The diff between *"regex first, neural for ambiguous"* and *"every request reaches neural"* is concrete enough to reason about in cost terms.

**2. Treat the bypass class as a known-unknown.** Vendor pattern libraries cover what they cover. The bound says they cannot cover the modular-counting encoding class within the substring-matching design pattern. *"Yes, the neural tier handles encoded attacks"* is the correct posture; *"yes, our regex patterns catch encoded attacks"* is a claim the math does not support for the bypass class. This applies equally to vendors of input scanners, output DLP, tool-arg validators, and schema validators.

**3. Use regex tiers for what they are good at.** Speed, determinism, audit trail, exact-match patterns. Direct prompt-injection keyword blocks. Exfiltration patterns where the leaked content is contiguous. Format validators. These are not in the bypass class and the regex tier excels at them. The bound is a boundary, not a verdict on the technology.

**4. Invest in out-of-band architectures for the highest-stakes cases.** Where the cost of a bypass is large enough that even a neural tier's residual error rate is unacceptable, architectures that never expose secrets or sensitive context to the inference layer are the right answer. An MIT-licensed reference implementation accompanying this work demonstrates one such architecture (an MCP server where the LLM operates on opaque handles while a separately-permissioned service performs field-fill via a controlled actuator).[^secrets-router]

For researchers and tool authors: further investment in regex pattern engineering for the bypass class is wasted effort. The interesting research questions are at the neural tier, in composition behavior, and in out-of-band architectures.

[^secrets-router]: *Disclosure: this implementation was developed by the author as part of this project. Readers should verify its properties against their own threat model.*

---

## 8 — What We Do Not Claim

We do not claim that all AI security is mathematically impossible. We do not claim neural guardrails or LLM-judges have the same blind spot — they do not, because TC⁰ is strictly larger than AC⁰. We do not claim the bound applies to embedding-based similarity filters, fine-tuned classifiers, model-internal safety training, behavioral / rate-limit guardrails, or any guardrail outside the star-free string-matching class — those are explicitly out of scope (§3 taxonomy). We do not claim a regulatory framework follows from this result. The bound holds unconditionally for substring-matched aperiodic regex with nontrivial accepted-language (i.e., at least two distinct accepted strings of equal length differing in some position — every nontrivial production guardrail).

The operational impact of the bound depends on the downstream system *decoding* the interleaved string. Pilot 5 measures decode reliability at 91.7% across four open-weight models with a 0% no-payload control; frontier-model behavior is not directly sampled and may differ. For payload classes outside the pilot (low-entropy structured payloads with rare codepoints, or models with aggressive input normalization), the assumption may not hold. Adversarial co-evolution can patch any individual filler choice; the bound says no finite patch covers all filler choices simultaneously, but local patches close individual instances cheaply and are often the right operational choice in the short term.

The original framing of this work was a much larger universal-impossibility claim covering all AI systems with compression capability, plus a regulatory-framework brief built on top of it. That claim turned out to be false — a single counterexample (a parity-projection classifier where the compression respects the safety equivalence relation) destroys the universal version. That destruction is documented alongside the project repository. The bound that survives — the one this article describes — is narrower, scoped to AC⁰ string-matching guardrails, and unconditional within that scope.

The classical theorems are old: Schützenberger (1965), McNaughton-Papert (1971), Furst-Saxe-Sipser (1981), Håstad (1987), Barrington-Compton-Straubing-Thérien (1992). The novelty is in the application: matching the substring-aperiodicity lemma to the regex grammar present in production libraries; the empirical verification across a corpus drawn from twelve sources; the explicit MOD_p bypass against representative patterns and fillers; the operational analysis of what the bound implies for the serial-AND composition pattern; and naming the bound's actual surface area across the production AC⁰ tier — input scanners, output DLP, tool-arg validators, schema validators, multi-stage pipelines.

The right shape of result for this field: a falsifiable, decision-relevant criterion that says, *if your defense layer is in this class, here is what it provably cannot do.*

---

## Appendix A — Mathematical Apparatus

### A.1 Substring-aperiodicity lemma

**Lemma.** Let *r* be a regular expression built from literals, character classes (including PCRE shorthands `\s`, `\d`, `\w` and their negations), alternation, optional groups `r?`, dot, bounded repetition `r{m,n}`, and Kleene star or plus *applied to character classes only*. Let *L_r* = Σ\* · L(r) · Σ\* be the language of strings containing a substring matching *r*. Then the syntactic monoid M(L_r) is aperiodic.

**Proof sketch.** By structural induction on *r*. Each primitive (literal, character class, alternation, optional group, dot, bounded repetition, Kleene-on-character-class) yields a star-free language; closure of star-free under concatenation, union, complement, and Kleene-on-character-class preserves star-freeness throughout. Wrapping with Σ\* on either side preserves star-freeness (Σ\* is the complement of ∅, hence star-free). By Schützenberger's theorem, every star-free language has an aperiodic syntactic monoid. The Kleene-star/plus restriction to character classes is essential: general `(r)*` for arbitrary *r* can yield non-aperiodic languages — `(ab)*` is the standard counterexample. Full proof in `paper/main.tex`.

### A.2 Word-boundary anchors preserve aperiodicity

A separate lemma in `paper/main.tex` establishes that the `\b` word-boundary anchor preserves aperiodicity: Σ\* · \b · L(r) · \b · Σ\* has aperiodic syntactic monoid whenever Σ\* · L(r) · Σ\* does. The argument realizes the anchor as an intersection with a position-context predicate that is itself star-free. This handles the 41 of 142 corpus patterns falling outside the lemma's syntactic grammar due to `\b` use, including the single timeout pattern (a Presidio IBAN regex) whose interior is in the lemma's grammar.

### A.3 The Guardrail Blindness Theorem

**Setup.** Let *G* be an AC⁰ string-matching guardrail (regex, trie, DFA, finite Bloom-filter blocklist) with aperiodic syntactic monoid. By Barrington-Compton-Straubing-Thérien, L_G ∈ AC⁰. Fix a prime *p* and define the modular-decode language

> *L_decode(p)* = { *w* ∈ Σ\* : *w*[0::p] ∈ L_blocked }

(every *p*-th character of *w*, starting at position 0, forms a blocked-pattern substring).

**Claim.** No aperiodic AC⁰ string-matcher can decide *L_decode(p)*. Therefore no addition of further aperiodic patterns to *G* can detect MOD_p-encoded payloads.

**Proof structure (two regimes).**

*Regime 1 (alphabet condition holds).* If there exists *f* ∈ Σ that does not advance the blocked-DFA from any state — equivalently, *f* lies outside the alphabet of L_blocked — then the transition monoid of *L_decode(p)* contains Z/pZ as a subgroup, witnessed by *f*ᵏ for *k* = 0, 1, ..., *p*−1. We verify in `paper/main.tex` that this subgroup survives the syntactic quotient (via context-distinguishing pairs *xuy* / *xvy* where *u* = *f*ʲ and *v* = *f*ᵏ for *j* ≢ *k* mod *p*). The syntactic monoid is therefore non-aperiodic, so *L_decode(p)* ∉ AC⁰ by Barrington-Compton-Straubing-Thérien. This regime covers production patterns whose effective alphabet is much smaller than Σ — the vast majority of regex deployed in surveyed libraries.

*Regime 2 (alphabet condition fails — closed by Theorem 4.X in main.tex).* If no such *f* exists in Σ (regex contains `.` or negated character classes whose minimal-DFA alphabet equals Σ), the *external-filler* cyclic-witness does not apply, but a *position-shift* cyclic-witness does. For any character `a ∈ Σ`, consider the strings `u_j := a^j` for `j = 0, 1, ..., p−1`. Their composition `u_j u_k = u_{(j+k) mod p}` realizes the multiplication of Z/pZ. Their syntactic inequivalence follows from the position-shift structure: for a blocked-pattern witness `h ∈ L(r)` of length ≥ p and a context `(x, y) = (ε, h^N)` for large `N`, the decoded substring `(u_j h^N)[0::p]` contains characters of `h` at positions offset by `−j (mod p)`. For any nontrivial `L(r)` containing two distinct strings of equal length (every production regex satisfies this), some choice of `h` makes the offset shift place a blocked substring in one decoded string but not another, distinguishing `u_j` from `u_k`. Therefore Z/pZ ⊂ M_Σ(*L_decode(p)*) without alphabet extension. The structural patchability claim is therefore established for every substring-matched production guardrail.

**Corollary (MOD₂ sufficiency).** *p* = 2 already breaks every aperiodic AC⁰ string-matcher in this class. Existing techniques — reading every other character, zero-width-character insertion, even-position acrostics — are all instances of the φ₂ construction.

### A.4 Closure under composition and the broader string-matcher class

By "AC⁰ string-matcher" we mean a string-matcher whose decision language is regular and lies in AC⁰ — equivalently (Barrington-Compton-Straubing-Thérien 1992), a regular language whose syntactic monoid is aperiodic, i.e., a star-free language. The claim of patch-resistance below is precisely about this class.

**Closure.** The union and intersection of finitely many star-free languages are star-free, and the syntactic monoid of a Boolean combination divides the direct product of the components' syntactic monoids (Pin 1986, §I.4). Therefore any star-free *G'* added to *G* — at any tier of a multi-tier pipeline — leaves the composed system in AC⁰, which cannot decide *L_decode(p)*. This generalizes patch-resistance from "no further regex" to "no further star-free string-matcher of any kind."

**Finite-language matchers (tries, DFA-based blocklists).** Every finite language *F* ⊆ Σ* is star-free: *F* = ⋃_{w ∈ F} {w}, a finite union of singletons, each star-free. Trie- and DFA-based blocklists matching against finite literal sets therefore inherit the bound directly.

**Bloom-filter blocklists.** A Bloom filter implementing membership in a finite literal set *F* recognizes *F* exactly when no false positives occur, and a superset *F* ∪ *FP* otherwise (where *FP* is the false-positive set, structurally undetermined). The substring-aperiodicity argument applies to *F*; the Bloom filter's bypass behavior on the modular-counting class therefore matches that of a trie-based matcher of *F*, modulo false-positive contamination. The bound applies to the Bloom filter's *intended* literal set; whether the false-positive set introduces or escapes the bound's reach is implementation-specific and not addressed here.

**What vendors can and cannot do.** Vendors *can* patch any individual filler choice (strip zero-width Unicode codepoints, reject NULL bytes, normalize whitespace), and each patch closes a specific evasion. The bound asserts only that no finite collection of such patches covers all filler choices simultaneously, and that no addition of further star-free string-matchers to the guardrail closes the modular-counting class structurally.

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

**Pilots not run, in scope of the bound.** Output-side DLP regex; tool-call argument validator regex; JSON Schema `pattern` field validators; trie/DFA/Bloom-filter blocklists; multi-tier aperiodic pipelines. The algebraic bound applies to all of these (§3 taxonomy and §A.4); we did not run direct empirical pilots on them. Extensions are a clean follow-up.

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
12. Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., and Fritz, M. (2023). Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection. In *Proc. Workshop on Artificial Intelligence and Security (AISec)*.
13. Merrill, W., and Sabharwal, A. (2023). The parallelism tradeoff: Limitations of log-precision transformers. *TACL* 11, 531–545.
14. Chiang, D., Cholak, P., and Pillay, A. (2023). Tighter bounds on the expressivity of transformer encoders. In *Proc. 40th International Conference on Machine Learning (ICML)*, PMLR vol. 202.
15. Hahn, M. (2020). Theoretical limitations of self-attention in neural sequence models. *TACL* 8, 156–171.
16. Project repository (this work, 2026), to be deposited at a stable DOI for camera-ready. Includes: 142-pattern corpus (`corpus_full.csv`), monoid enumeration scripts, primary MOD_p bypass artifact (`mod_p_bypass_matrix.json`), three follow-up empirical pilots (`printable_filler_bypass.json`, `library_pattern_bypass.json`, `llm_decode_pilot_v2.json`), four-library normalization survey (`library_normalization_survey.md`), formal proofs (`paper/main.tex`), the parity-projection counterexample referenced in §8 (`counterexamples.md`), and the secrets-router reference implementation.
