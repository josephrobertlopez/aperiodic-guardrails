# Why Substring-Matching Defenses Are Provably Bypassable

### A 1965 Theorem Names a Generation of Bypass Techniques — WAFs, IDS, Antivirus, Spam Filters, Code Scanners, Secret Scanners, LLM Guardrails

**Target Venue:** Communications of the ACM (Practice)
**Author:** Joseph R. Lopez
**Word Count:** ~6,000 (body ~3,800; appendices ~2,200)

---

Type **`b​o​m​b`** into a chatbot routed through LLM-Guard, Presidio, Rebuff, or any of the dozen most-deployed regex content scanners. The four invisible characters between the `b`s are zero-width Unicode codepoints — they take no visual space, your eye reads `bomb`, the regex finds no contiguous match. The model decodes and responds.

The same construction succeeds against a Web Application Firewall blocking SQL injection. Against an Intrusion Detection System matching exploit signatures. Against a secret scanner looking for API keys. Against a spam filter matching keywords. Against a code-analysis tool flagging unsafe imports. Against any substring-matching defensive layer using aperiodic regex.

Same bypass class. Same algebraic blind spot. Same six-decade-old mathematical theorem behind every instance. Substring-matching aperiodic regex is in **AC⁰**, the constant-depth circuit class that *provably cannot count modulo a prime*. The bypass — interleaving a payload with a filler at every other character position — exploits exactly that limit. Adding more patterns does not help: the union of finitely many aperiodic-monoid languages is itself aperiodic, so any patched filter remains in AC⁰, still provably blind to modular-counting encodings.

The defensive-security community has been building substring-matching pattern recognition systems for thirty years — antivirus signatures since the late 1980s, web application firewalls since the mid-1990s, intrusion detection systems since the late 1990s, spam filters since the early 2000s, code and secret scanners since the 2010s, LLM guardrails since the 2020s. That entire history shares one provable failure mode and one classical name for it. Schützenberger 1965 sat in the formal-language-theory literature, completely accessible, while every defensive-tooling vintage rediscovered the same class of bypass technique under a different label and patched it locally without naming the unification.

This article names the unification. We describe the algebraic bound, trace it through six decades of separately-discovered bypass techniques, demonstrate it empirically against a 142-pattern corpus from twelve LLM-guardrail libraries (the specific deployment class that motivated this work), and connect the dots that the security literature has been missing through formal-language theory. The empirical work is LLM-specific; the algebraic argument is not. The cobra strikes the entire history.

---

## 1 — The Strike, in Code

A two-line bypass against an aperiodic substring-matching defense:

```python
import re
filter = re.compile(r'(bomb|weapon|explosive|kill|attack)', re.IGNORECASE)
payload  = 'bomb'
encoded  = ''.join(c + '​' for c in payload).rstrip('​')
# encoded == 'b​o​m​b'  (visually identical to 'bomb')
assert not filter.search(encoded)        # regex sees no contiguous match
```

The construction is the **MOD₂ bypass**: place the payload at even positions, place a filler at odd positions. Generalizes to any prime *p*. Works against any aperiodic substring matcher. Filler can be NULL byte, zero-width Unicode, ASCII whitespace, punctuation, or any character outside the pattern's literal alphabet. We empirically verify the bypass succeeds across seven distinct filler choices in §4.

The downstream consumer is what makes the bypass operationally meaningful. An LLM downstream of an LLM-guardrail decodes zero-width interleaving and acts on the payload. A human reading rendered model output reads `bomb` and not `b​o​m​b`. A SQL engine receiving `SELECT \x00 *` may or may not parse the NULL bytes — the operational gradient varies by consumer, detailed in §3.

---

## 2 — The Historical Unification

The bypass class has been rediscovered across defensive-security generations. The list below is a small selection — each row is a separately-published bypass technique that, viewed through the algebraic lens, is the same Z/pZ position-shift construction against the same AC⁰ recognition class.

| Decade | Defensive class | Example bypass technique | Algebraic name |
|---|---|---|---|
| **1990s** | Antivirus signatures | Polymorphic encoding, byte-interleaving against literal-string signatures | MOD_p with byte filler |
| **mid-1990s →** | Web Application Firewalls (ModSecurity, AWS WAF, Cloudflare) | SQL-injection bypass via in-token whitespace, unicode normalization tricks, comment-character interleaving | MOD_p with whitespace/comment filler |
| **late 1990s →** | Intrusion Detection / Prevention (Snort, Suricata) | Signature evasion via packet fragmentation, in-payload byte-stuffing | MOD_p across packet boundaries / within payloads |
| **early 2000s →** | Spam filters (SpamAssassin, regex-based content filters) | Acrostic spam, character-substitution + interleaving (`v.i.a.g.r.a`) | MOD_p with punctuation filler |
| **2010s →** | Source-code analysis, secret scanners (Semgrep, Bandit, GitLeaks, TruffleHog) | Comment-broken token bypass, secret splitting across continuations | MOD_p with comment-token filler |
| **2020s** | LLM input/output guardrails (LLM-Guard, Presidio, Rebuff, Guardrails-AI, NeMo regex rails, OWASP-LLM patterns) | Zero-width Unicode insertion (Boucher 2022), payload splitting (Wei 2023), encoding-based jailbreak (Hackett 2025), uncommon text-organization (Li 2024 StructuralSleight) | MOD_p with zero-width / whitespace filler |

Three observations make the unification non-trivial.

**First**, every defensive class in the table uses substring-matching aperiodic regex as its decision tier (or its primary decision tier; some have neural-classifier additions, addressed in §6). The substring-matching design pattern is precisely what produces the aperiodic syntactic monoid, and aperiodicity is precisely what places the decision language in AC⁰.

**Second**, every bypass technique listed has been documented as an *engineering trick* in the literature of its respective defensive class — typically diagnosed as "the regex needs more patterns" or "we need to handle case X." The algebraic argument explains why "more patterns" cannot work: the patched filter remains in AC⁰, still provably blind.

**Third**, the bypass techniques across decades are not analogies — they are *the same construction*. A 1995 SQL-injection-via-comment-character bypass and a 2024 LLM-jailbreak-via-zero-width-Unicode bypass differ only in their choice of filler character. Both are MOD₂ instances against an aperiodic substring matcher. The defensive-security field treated them as separate problems, one per vendor per defense class, for thirty years.

The empirical work in this article is LLM-specific (§4) because that is the class we tested at scale. The algebraic argument extends to every defensive class in the table; the empirical extension to non-LLM classes is straightforward and a natural follow-up.

---

## 3 — The Bound's Surface Area and Operational Gradient

Within a given defensive deployment, the bound applies to every aperiodic substring-matching tier — and the *operational impact* tracks what the downstream consumer does with the encoded payload.

| **In scope** (star-free string-matchers, hence in AC⁰) | **Out of scope** (TC⁰ or different class) |
|---|---|
| Input-side regex content scanners (LLM-Guard, Rebuff, etc.) | LLM-as-judge systems (Llama Guard, Lakera, MS Prompt Shield, NeMo's primary path) |
| Output-side regex DLP / content moderation | Embedding-based similarity filters (continuous, not discrete language recognition) |
| Tool-call argument validators using regex | Fine-tuned BERT-class toxicity / safety classifiers |
| JSON Schema `pattern` field validators (ECMA-262 subset, no lookarounds/backrefs) | Behavioral / rate-limit / quota guardrails (orthogonal to content) |
| Trie- and DFA-based blocklists matching finite literal sets | Model-internal safety (RLHF, constitutional AI, refusal training) |
| Bloom-filter blocklists *of the underlying literal set* (the bound applies to the set; the false-positive class is additional noise) | Token-budget / context-window guardrails |
| **WAF / IDS / AV signature regex tiers** (ModSecurity, Snort, ClamAV signature-rules with regex extensions, SpamAssassin pattern rules) | Anomaly detection on edit-distance, dynamic-programming-based detection |
| **Any Boolean composition** of the above (intersection or union) — the syntactic-monoid class is closed under finite Boolean operations and concatenation (Pin 1986) | Formal verification of model behavior on bounded input classes |

Within the in-scope class, the *operational bite* depends on whether the downstream consumer decodes the encoded payload:

| Downstream consumer | Decode behavior | Operational bite |
|---|---|---|
| **LLM ingesting prompt** | Decodes interleaving (Pilot 5: 91.7% across 4 open-weight models, +91.7pp lift over control) | **High** |
| **Human reading rendered model output / web page** | Decodes visually (zero-width chars are invisible) | **High** |
| **Downstream LLM in agent chain** (MCP server passing tool-args to another LLM) | Same as input case — decodes | **High** |
| **RAG pipeline including an LLM step** | LLM in the loop decodes | **High** |
| **SQL / shell / filesystem layer parsing the bypassed input** | Most parsers handle NULL/whitespace literally; bypass usually inert at this layer | **Low to Mixed** (depends on parser; modern WAFs sometimes feed into normalizing parsers downstream) |
| **Network IDS scanning packet content** | Reassembled stream consumed by application protocol parsers | **Mixed** (depends on protocol; HTTP/SMTP can reconstruct interleaved payloads) |
| **Code-execution layer running scanned source** | Compilers/interpreters strip comments and whitespace; bypass *helps* the attacker because the executable form differs from the scanned form | **High in code-scanner contexts** |
| **Schema-consumer pipeline, direct (no LLM)** | Processes literally | **Low** |

The fractal pattern: the same algebraic bypass that lets a `b​o​m​b` payload through an LLM guardrail to a decoding model is the same construction that lets a `S​E​L​E​C​T` payload through a WAF to a normalizing SQL parser, and the same construction that lets a comment-broken secret through a code scanner to a comment-stripping compiler. Different defenses, different consumers, same algebra.

---

## 4 — What We Measured

The empirical work tested the LLM-guardrail instance of the unified bypass. Five numbers; methodology and per-pilot detail in **Appendix B**.

| # | What | Sample | Result |
|---|---|---|---|
| 1 | **Aperiodicity rate of deployed patterns** | 142 patterns, twelve sources (nine third-party libraries + three author-assembled sets, 30%) | **142 / 142 aperiodic** (119 by completed monoid enumeration; 22 theorem-implied via the substring-aperiodicity lemma; 1 — the Presidio IBAN pattern — by the word-boundary lemma) |
| 2 | **Primary MOD_p bypass** | 11 patterns × 4 primes (2, 3, 5, 7) × 12 payloads, NULL-byte filler | **56 / 56 bypass** |
| 3 | **Filler-diversity bypass** | Same 11 patterns × 4 primes × 7 fillers (NULL, ASCII space, tab, tilde, backtick, U+200B, U+200C) | **392 / 392 bypass** |
| 4 | **Third-party-library bypass** | 100 library-shipped patterns; 48 baseline-matched our literal-glue payload synthesizer across 8 of 9 libraries | **48 / 48 bypass** under both NULL and ASCII-space filler |
| 5 | **LLM decode reliability with control** | 4 open-weight models × 3 fillers × 5 benign payloads (60 decode cells; 20 random-character control cells) | **55 / 60 decode (91.7%) vs 0 / 20 control (0%); +91.7 pp lift** |

The substring-matching design pattern produces aperiodic guardrails in 100% of the corpus we surveyed — forced by the design, not contingent. The MOD_p bypass succeeds at every prime, every filler, every third-party-library pattern where our synthesizer could produce a baseline match. Contemporary open-weight LLMs decode the encoding reliably; the random-character control rules out response-prior confounds.

We additionally surveyed four production guardrail implementations — LLM-Guard's `BanSubstrings` scanner, Presidio's analyzer, Rebuff's heuristic detector, NeMo Guardrails' content-safety check — for input-normalization behavior. None perform Unicode normalization (NFC/NFKC) or strip zero-width Unicode codepoints prior to regex match. One (Rebuff's heuristic stage) strips NULL bytes and zero-width codepoints as a side effect of broader sanitization; printable-filler bypass remains intact.

Empirical extension to the non-LLM defensive classes named in §2 (WAFs, IDS, AV, spam filters, code/secret scanners) is straightforward and a natural follow-up; the algebraic argument suffices to predict the bypass succeeds against any aperiodic substring matcher in those classes. We did not run direct pilots against ModSecurity, Snort, ClamAV, SpamAssassin, or Semgrep in this article.

---

## 5 — The Composition Trap

A neural filter — any transformer-based classifier — operates in **TC⁰** (Merrill & Sabharwal 2023, Chiang-Cholak-Pillay 2023). TC⁰ properly contains AC⁰ and *does* include MOD_p as a capacity bound. This is not a guarantee that a specific trained transformer reliably computes MOD_p; Hahn 2020 established that fixed-architecture self-attention cannot model parity for unboundedly long inputs unless depth or heads scale with sequence length. The capacity-vs-realization gap matters: the neural tier *can in principle* catch MOD_p encodings, and trained classifiers in practice catch many of them, but the practical detection rate is a separate question from the capacity bound.

Conditioned on a neural classifier that empirically catches the encoding class with acceptable accuracy, the composition behavior splits sharply:

| Composition | Behavior on the bypass class |
|---|---|
| **Parallel-OR** *(every request reaches both tiers; layer blocks if any constituent blocks)* | The neural filter's TC⁰ capacity **survives**. Combined layer detects MOD_p encodings at the rate the neural filter alone can. |
| **Serial-AND** *(regex first; only ambiguous requests reach neural)* | The regex tier's blindness **vetoes** the neural tier's capacity. **Combined layer's blindness equals the regex tier's blindness.** |

> **The thesis.** Wherever an aperiodic substring-matching tier sits as a serial pre-filter in front of a more-capable tier, the modular-counting encoding class bypasses *both*. The bound applies per-tier; system-level inheritance depends on the architecture's voting/veto structure.

The serial-AND composition is *the* canonical justification for deploying a regex tier at all: it is what makes the regex tier's cost-savings real. The bound says that exact composition propagates the regex tier's algebraic blind spot to the system. Not slightly. *Exactly*.

This pattern repeats across every defensive class in §2's table. WAFs typically run regex first, expensive pattern matching second, neural anomaly detection third — and the regex tier vetoes the rest. IDS typically runs signature matching first, behavioral analysis second — same structure. The composition trap is the same mathematical object across the defensive-security landscape.

Hybrid topologies require finer-grained analysis. Rate-limited fallback applies the bound to the regex-sampled fraction. Ensemble voting with a neural majority can attenuate the bound at a cost. Sampled-routing applies the bound to traffic that hits the regex path. Multi-stage agentic pipelines compound the issue: every aperiodic tier is in AC⁰, and the conjunction of multiple AC⁰ checks is still AC⁰.

---

## 6 — What To Do Monday

Four actions, ordered by leverage. Apply to every defensive-class instance in your stack.

**1. Audit your AC⁰ tier across every substring-matching defense.** Map every request and response path through every aperiodic regex / signature matcher in your stack — input scanners, output DLP, tool-call validators, schema validators, retrieval-content scanners, WAF rule sets, IDS signatures, secret/code scanners, spam-filter rules. For each, identify whether the tier sits as a serial pre-filter (the bypass-class blindness propagates to the system) or as a parallel constituent (the more-capable tier's capacity survives). One engineer-week for most LLM-stack deployments; longer for organizations with full WAF + IDS + AV + DLP coverage. The diff between *"regex first, expensive thing for ambiguous"* and *"every request reaches the expensive thing"* is concrete enough to reason about in cost terms.

**2. Treat the bypass class as a known-unknown.** Vendor pattern libraries cover what they cover. The bound says they cannot cover the modular-counting encoding class within the substring-matching design pattern. *"Yes, the neural tier handles encoded attacks"* is the correct posture; *"yes, our regex patterns catch encoded attacks"* is a claim the math does not support for the bypass class. This applies equally to vendors of LLM guardrails, WAFs, IDS, AV, code scanners, and DLP.

**3. Use substring-matching tiers for what they are good at.** Speed, determinism, audit trail, exact-match patterns. Direct keyword blocks. Exfiltration patterns where the leaked content is contiguous. Format validators. These are not in the bypass class and the regex tier excels at them. The bound is a boundary, not a verdict on the technology.

**4. Invest in higher-complexity-class arbiters for the bypass class.** Where the cost of a bypass is large enough to matter, route the bypass class through a TC⁰-or-higher arbiter (neural classifier, LLM judge, parser-based normalization) without the AC⁰ tier vetoing it. For the highest-stakes cases, architectures that never expose secrets or sensitive context to the inference layer are the right answer. An MIT-licensed reference implementation accompanying this work demonstrates one such architecture (an MCP server where the LLM operates on opaque handles while a separately-permissioned service performs field-fill via a controlled actuator).[^secrets-router]

For researchers and tool authors: further investment in regex pattern engineering for the bypass class is wasted effort across the entire defensive landscape, not just LLM guardrails. The interesting research questions are at the more-capable tier, in composition behavior, in input-normalization design, and in out-of-band architectures.

[^secrets-router]: *Disclosure: this implementation was developed by the author as part of this project. Readers should verify its properties against their own threat model.*

---

## 7 — What We Do Not Claim

We do not claim that all AI security is mathematically impossible. We do not claim that all defensive security is mathematically impossible. We do not claim neural guardrails or LLM-judges have the same blind spot — they do not, because TC⁰ is strictly larger than AC⁰. We do not claim the bound applies to embedding-based similarity filters, fine-tuned classifiers, model-internal safety training, behavioral / rate-limit guardrails, or any guardrail outside the star-free string-matching class — those are explicitly out of scope (§3 taxonomy). We do not claim a regulatory framework follows from this result. The bound holds unconditionally for substring-matched aperiodic regex with nontrivial accepted-language (every nontrivial production matcher).

We do not claim our 142-pattern empirical corpus generalizes to the non-LLM defensive classes named in §2. The algebraic argument extends; the direct empirical sweep against ModSecurity / Snort / ClamAV / SpamAssassin / Semgrep patterns is a clean follow-up we did not run. The unification claim of §2 is *algebraic*, not measured-across-defense-classes.

The original framing of this work was a much larger universal-impossibility claim covering all AI systems with compression capability. That claim turned out to be false — a single counterexample (a parity-projection classifier where the compression respects the safety equivalence relation) destroys the universal version. That destruction is documented alongside the project repository. The bound that survives — the one this article describes — is narrower, scoped to substring-matching aperiodic recognition layers, and unconditional within that scope.

The classical theorems are old: Schützenberger (1965; six decades), McNaughton-Papert (1971; five-and-a-half decades), Furst-Saxe-Sipser (1981; four-and-a-half decades), Håstad (1987; four decades), Barrington-Compton-Straubing-Thérien (1992; three-and-a-half decades). The novelty is in the application: *naming the unification across defensive-security classes* that the literature of each class has been treating as a separate engineering problem; matching the substring-aperiodicity lemma to the regex grammar present in production libraries; the empirical verification across the LLM-guardrail corpus; the explicit MOD_p bypass against representative patterns and fillers; the operational analysis of the serial-AND composition pattern; and the surface-area mapping across input scanners, output DLP, tool-arg validators, schema validators, multi-stage pipelines, and the broader history.

The right shape of result for this field: a falsifiable, decision-relevant criterion that says, *if your defense layer is in this class, here is what it provably cannot do — regardless of when it was built, who built it, or what category of bypass technique its vendor has previously seen.*

---

## Appendix A — Mathematical Apparatus

### A.1 Substring-aperiodicity lemma

**Lemma.** Let *r* be a regular expression built from literals, character classes (including PCRE shorthands `\s`, `\d`, `\w` and their negations), alternation, optional groups `r?`, dot, bounded repetition `r{m,n}`, and Kleene star or plus *applied to character classes only*. Let *L_r* = Σ\* · L(r) · Σ\* be the language of strings containing a substring matching *r*. Then the syntactic monoid M(L_r) is aperiodic.

**Proof sketch.** Structural induction. Every primitive yields a star-free language; closure of star-free under concatenation, union, complement, and Kleene-on-character-class preserves star-freeness throughout. Wrapping with Σ\* (which equals ¬∅, hence star-free) on either side preserves star-freeness. By Schützenberger's theorem, every star-free language has an aperiodic syntactic monoid. The Kleene-restriction to character classes is essential: `(ab)*` is the standard counterexample of a non-aperiodic Kleene-on-group construction. Full proof in `paper/main.tex`.

### A.2 Word-boundary anchors preserve aperiodicity

A separate lemma in `paper/main.tex` establishes that the `\b` word-boundary anchor preserves aperiodicity. The argument realizes the anchor as an intersection with a position-context predicate that is itself star-free. This handles 41 of 142 corpus patterns (those using `\b`), including the single timeout pattern (a Presidio IBAN regex) whose interior is in the lemma's grammar.

### A.3 The Guardrail Blindness Theorem — both regimes closed

**Setup.** Let *G* be a star-free substring-matching defense (regex, trie, DFA, finite Bloom-filter blocklist) with aperiodic syntactic monoid. By Barrington-Compton-Straubing-Thérien, L_G ∈ AC⁰. Fix a prime *p* and define

> *L_decode(p)* = { *w* ∈ Σ\* : *w*[0::p] ∈ L_blocked }.

**Claim.** No star-free substring-matcher can decide *L_decode(p)* (assuming L(r) is nontrivial — at least two distinct strings of equal length differing in some position; every nontrivial production defense satisfies this).

**Two regimes, both closed:**

*Regime 1 (alphabet ⊊ Σ — vast majority of production patterns).* If there exists *f* ∈ Σ outside `alphabet(L_blocked)`, then *f* self-loops the blocked-DFA from every state, and {*f*ᵏ : 0 ≤ *k* < *p*} witnesses Z/pZ ⊂ M(*L_decode(p)*) directly via the cyclic action on the position counter.

*Regime 2 (alphabet = Σ — patterns containing `.` or `[^X]*`).* No external self-looping filler exists, but the cyclic structure still witnesses via *position-shift offset*. For any character *a* ∈ Σ, the strings *u_j* := *a*ʲ for *j* = 0, ..., *p*−1 are pairwise syntactically inequivalent in *L_decode(p)*: the context (*x*, *y*) = (ε, *h*ᴺ) for a blocked-pattern witness *h* and large *N* shifts which characters of *h* land in the decoded substring depending on |*u_j*| mod *p*. For any nontrivial L(r) containing two distinct equal-length strings, some choice of *h* makes the offset shift cross the L_blocked decision boundary, distinguishing *u_j* from *u_k*. Therefore Z/pZ ⊂ M_Σ(*L_decode(p)*) without alphabet extension.

**Combined:** The bound holds unconditionally for every nontrivial substring-matched defense, regardless of alphabet structure. Full proofs in `paper/main.tex`.

**Corollary (MOD₂ sufficiency).** *p* = 2 already breaks every aperiodic substring-matching defense with nontrivial accepted-language. Existing techniques — reading every other character, zero-width-character insertion, even-position acrostics, comment-character interleaving, byte-stuffing — are all instances of the φ₂ construction.

### A.4 Closure under composition and the broader string-matcher class

By "AC⁰ string-matcher" we mean a string-matcher whose decision language is regular and lies in AC⁰ — equivalently (Barrington-Compton-Straubing-Thérien 1992), a regular language whose syntactic monoid is aperiodic, i.e., a star-free language.

**Closure.** The union and intersection of finitely many star-free languages are star-free, and the syntactic monoid of a Boolean combination divides the direct product of the components' syntactic monoids (Pin 1986 §I.4). Therefore any star-free *G'* added to *G* — at any tier of a multi-tier pipeline — leaves the composed system in AC⁰, which cannot decide *L_decode(p)*. This generalizes patch-resistance from "no further regex" to "no further star-free string-matcher of any kind." The result holds equally for compositions across defensive-class boundaries: a WAF rule set composed with an IDS signature set composed with an LLM guardrail, all star-free, remains in AC⁰.

**Finite-language matchers (tries, DFA-based blocklists).** Every finite language *F* ⊆ Σ\* is star-free: *F* = ⋃_{w ∈ F} {w}, a finite union of singletons, each star-free. Trie- and DFA-based blocklists matching against finite literal sets therefore inherit the bound directly.

**Bloom-filter blocklists.** A Bloom filter implementing membership in finite literal set *F* recognizes *F* exactly when no false positives occur, and a superset *F* ∪ *FP* otherwise. The substring-aperiodicity argument applies to *F*; bypass behavior matches that of a trie-based matcher of *F*, modulo false-positive contamination. The bound applies to the Bloom filter's *intended* literal set.

**Vendors can patch individual filler choices but not the class.** Strip zero-width Unicode codepoints, reject NULL bytes, normalize whitespace — each closes a specific evasion. The bound asserts only that no finite collection of such patches covers all filler choices simultaneously, and that no addition of further star-free string-matchers closes the modular-counting class structurally.

---

## Appendix B — Empirical Methodology (LLM-Guardrail Corpus)

### B.1 Corpus

Twelve sources, 142 patterns. **Nine third-party projects** contribute 100 patterns: LLM-Guard (12), llm-guard-py (12, plausibly overlapping LLM-Guard but with different pattern files), Rebuff (10), Guardrails-AI (12), Presidio (15), GitLeaks (8), LangKit (10), BodAIGuard (10), and the regex subset of NeMo Guardrails' content rails (11). **Three author-assembled sets** contribute 42 patterns (29.6%): 8 inspired by the OWASP Top 10 for LLMs taxonomy, 15 from a curated WAF-generic pattern set drawn from widely-cited enterprise WAF references, 19 author-constructed adversarial test patterns. Released as `corpus_full.csv`.

### B.2 Aperiodicity verification

Compile each pattern to Thompson NFA → minimal DFA (Hopcroft) → enumerate transition monoid via BFS over Cayley graph → test *x*ⁿ = *x*ⁿ⁺¹ for *n* bounded by |M|² (Pin 1986). 119 complete; 22 timeouts within the lemma's grammar (theorem-implied aperiodic); 1 timeout (Presidio IBAN, `\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b`) established aperiodic by the word-boundary lemma.

### B.3 Pilot designs

**Pilot A (primary bypass).** 11 author-assembled patterns × 4 primes (2, 3, 5, 7) × 12 payloads, NULL-byte filler. Artifact: `results/mod_p_bypass_matrix.json`.

**Pilot B (filler diversity).** Same 11 patterns × 4 primes × 7 fillers (NULL, ASCII space, tab, tilde, backtick, U+200B, U+200C). 392 tests, all bypass. Artifact: `results/printable_filler_bypass.json`.

**Pilot C (LLM decode reliability with control).** Four open-weight models (llama3.1:8b, llama3.2:3b, qwen2.5-coder:14b, codestral; 3B–22B parameters) under decode (60 cells) and random-character control (20 cells) conditions. Decode 55/60 (91.7%), control 0/20 (0%), lift +91.7pp. Artifact: `results/llm_decode_pilot_v2.json`.

**Pilot D (third-party library patterns).** Literal-glue payload synthesizer applied to 100 library-shipped patterns; 48 baseline-matched across 8 of 9 libraries (Presidio's PII patterns are the synthesis exception). 48/48 bypass under both NULL and ASCII-space filler. Artifact: `results/library_pattern_bypass.json`.

**Library normalization survey.** Source-level inspection of LLM-Guard `BanSubstrings`, Presidio analyzer, Rebuff heuristic, NeMo content-safety on `main`/`develop` HEAD. None perform Unicode normalization or strip zero-width Unicode codepoints prior to regex match. Artifact: `results/library_normalization_survey.md`.

**Pilots not run, in scope of the bound.** Output-side DLP regex; tool-call argument validator regex; JSON Schema `pattern` field validators; trie/DFA/Bloom-filter blocklists; WAF / IDS / AV / spam / code-scanner / secret-scanner pattern sets across the §2 historical-unification table; multi-tier aperiodic pipelines. The algebraic bound applies; direct empirical pilots are clean follow-ups.

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
16. Project repository (this work, 2026), to be deposited at a stable DOI for camera-ready. Includes: 142-pattern corpus (`corpus_full.csv`), monoid enumeration scripts, primary MOD_p bypass artifact (`mod_p_bypass_matrix.json`), three follow-up empirical pilots (`printable_filler_bypass.json`, `library_pattern_bypass.json`, `llm_decode_pilot_v2.json`), four-library normalization survey (`library_normalization_survey.md`), formal proofs (`paper/main.tex`), the parity-projection counterexample referenced in §7 (`counterexamples.md`), and the secrets-router reference implementation.
