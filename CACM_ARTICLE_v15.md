# Your Regex-First Security Stack Has a 30-Year-Old Blind Spot

### The same bypass keeps working against WAFs, spam filters, secret scanners, and now LLM guardrails. Here is what to ask your vendors on Monday.

**Target Venue:** Communications of the ACM (Practice)
**Author:** Joseph R. Lopez
**Word Count:** ~3,800 (body) + ~900 (appendices)

---

## The 60-Second Version

If your security stack has any layer that decides "block or allow" by matching patterns against incoming text — a Web Application Firewall, an antivirus signature engine, a Data Loss Prevention scanner, a spam filter, a secret scanner, an LLM input/output guardrail — there is a class of bypass technique that has worked against that layer's design for thirty years and will continue to work no matter how many patterns the vendor adds.

The bypass: insert an invisible or ignored character between every other character of the payload. The pattern engine sees no contiguous match. The downstream consumer (the LLM, the SQL engine, the human reading rendered output, the compiler) reassembles or ignores the filler and acts on the original payload.

We tested this against 142 patterns from twelve LLM-guardrail libraries: every pattern is structurally vulnerable. We extended the test to ModSecurity's flagship SQL-injection rules and to SpamAssassin's phrase rules: same bypass, same outcome. We have a mathematical proof, available in a companion paper, that adding more patterns of the same kind cannot close the bypass class.

The business consequence is not "buy a different product." The business consequence is: **the architectural pattern of "cheap regex layer in front, expensive AI layer behind" has a serial veto problem.** When the regex layer says "looks fine," the AI layer never sees the request. The regex layer's blindness becomes the system's blindness. This article tells you how to detect that pattern in your stack, what to ask your vendors, and what to budget.

---

## §1 — The Strike: One Bypass, One Demo

A corporate chatbot has an input guardrail that blocks the words `bomb`, `weapon`, `kill`, `attack`, and a few hundred others. The guardrail is a regex matcher. The chatbot routes every user message through it before passing the message to the language model.

A user types this into the chat box:

```
b​o​m​b
```

To the user's eye, that says `bomb`. To the regex engine, the four characters between the `b`s are zero-width Unicode codepoints — invisible glyphs that take no visual space. The regex looks for the literal string `bomb` and does not find it. The message is allowed through. The language model receives the input, decodes the zero-width characters as whitespace it can ignore, and answers as though the user had typed `bomb` directly.

That is the entire bypass. Two lines of Python construct the payload. The same construction works with NULL bytes, ASCII spaces, tabs, tildes, backticks, or any character outside the regex's literal alphabet. We tested seven filler choices across four prime spacings (every-other, every-third, every-fifth, every-seventh character). All 392 combinations bypass.

Now substitute the recognizable scenario:

- The "guardrail" is a **WAF**, the payload is `SELECT * FROM users`, and the filler is an SQL comment `/**/`. The WAF does not match. The database receives `SEL/**/ECT * FROM users`, which it parses as valid SQL. This bypass has been documented since the late 1990s.
- The "guardrail" is a **spam filter** matching the word `viagra`. The filler is a period. The text reads `v.i.a.g.r.a` to the filter and `viagra` to the human reader. Documented since the early 2000s.
- The "guardrail" is a **secret scanner** like GitLeaks looking for AWS access keys. The filler is a line continuation in a comment. The scanner sees a broken token; the build pipeline sees the assembled secret. Documented in the 2010s.
- The "guardrail" is an **LLM jailbreak detector** looking for known attack phrases. The filler is a zero-width Unicode character. The detector sees garbage; the model sees the attack. Documented 2022-2025 (Boucher et al., Wei et al., Hackett et al., Li et al.).

Same construction. Same bypass class. Different filler character per generation of defense.

---

## §2 — Why This Isn't New: Same Algebra, Thirty Years of Whack-a-Mole

The defensive-security industry has been building pattern-matching defenses for three decades. Antivirus signatures appeared in the late 1980s. Web Application Firewalls in the mid-1990s. Network Intrusion Detection in the late 1990s. Spam filters in the early 2000s. Code and secret scanners in the 2010s. LLM guardrails in the 2020s.

Every generation has discovered the bypass. Every generation has named it differently. Every generation's vendors have responded the same way: "we'll add patterns for that." That response has not worked, will not work, and cannot work — for a reason that has been sitting in a 1965 mathematics paper the entire time.

The reason in plain English: a regex (or any equivalent substring matcher — trie, DFA, Bloom-filter blocklist) makes its decisions based on whether specific characters appear next to each other in specific orders. It cannot answer the question "does this text contain the payload if you read every other character?" It is the wrong shape of computation for that question. Adding more rules does not change the shape; the combination of two such matchers is itself a matcher of the same shape with the same blind spot.

| Decade | What the defense was called | What the bypass was called | What was added between every other character |
|---|---|---|---|
| Late 1980s — 1990s | AV literal-string signatures | "no-op stuffing," "byte interleaving" | NULL bytes, no-op instructions |
| Mid-1990s — present | Web Application Firewalls (ModSecurity, AWS WAF, Cloudflare) | "comment evasion," "case mutation," "Unicode normalization tricks" | `/**/`, whitespace, comment characters |
| Late 1990s — present | IDS/IPS regex tiers (Snort, Suricata) — narrow subclass | "regex-tier evasion" | NULL bytes, fragments that survive reassembly |
| Early 2000s — present | Spam filters (SpamAssassin, regex content filters) | "acrostic spam," "character substitution" | Periods, spaces, format characters |
| 2010s — present | Code and secret scanners (Semgrep, Bandit, GitLeaks, TruffleHog) | "comment-broken tokens," "line-continuation splits" | Comments, line continuations |
| 2020s | LLM input/output guardrails (LLM-Guard, Presidio, Rebuff, Guardrails-AI, NeMo, OWASP-LLM) | "Bad Characters," "payload splitting," "encoding-based jailbreak" | Zero-width Unicode, whitespace |

A note on what is *not* in this table:

- Classical **polymorphic-virus** encoding (encryption + a decryption stub that mutates) is a different attack class. The bound here applies only to literal-string AV signatures bypassed by in-pattern interleaving.
- Classical **IDS evasion** (Ptacek & Newsham 1998) — exploiting differences between how the IDS and the endpoint reassemble TCP packets — is a different attack class. The bound here applies only to the IDS regex-matching tier itself.

We are being precise about scope so the unification claim is verifiable, not rhetorical.

The point of the table is not "look how many things are broken." The point is: **the security industry has been treating thirty years of the same bypass as thirty separate engineering problems.** Each vendor patches the specific filler character its customers report. The next attacker uses a different filler. The bound is structural; the patches are surface.

---

## §3 — Is Your Stack Affected?

Walk this checklist for each defensive layer in your stack. If you answer "yes" to question 1 *and* "serial-AND" to question 5, that layer is in the bypass class and the bypass class can propagate to your whole system through that layer.

**1. Does the layer make its block/allow decision by matching patterns (regex, signatures, blocklist) against the literal characters of the input?**
- Yes → continue
- No (it uses a neural network, an embedding-similarity check, a fine-tuned classifier, an LLM-as-judge, behavioral analysis, rate limiting, or a parser that fully normalizes input first) → out of scope, you are fine on this axis

**2. Are the patterns substring-matching — i.e., do they look for the payload anywhere in the input rather than requiring the input to start with or end with the pattern?**
- Yes (the common case) → continue
- No (rare; the layer requires exact full-string match) → still vulnerable but the attack surface narrows

**3. Does the input pass through the layer *before* reaching the more-capable downstream system (LLM, parser, classifier, human reviewer)?**
- Yes → the bypass can reach the downstream system
- No (only logged, not blocked) → bypass is a detection-evasion problem, not a control-bypass problem

**4. Does the downstream system "decode" the bypass — i.e., does it ignore or normalize the filler character the attacker is likely to use?**
- An LLM downstream → yes, decodes reliably (we measured 91.7% across four open-weight models)
- A human reading rendered output → yes, decodes visually (zero-width characters are invisible)
- A SQL parser → sometimes (whitespace and comment fillers decode; NULL bytes typically don't)
- A compiler reading scanned source → yes, strips comments and whitespace
- A schema validator with no further consumer → no, processes literally

**5. What is the layer's relationship to your more-capable defenses (neural classifier, LLM judge, deep parser, manual review)?**
- **Serial-AND** — the regex tier blocks first and only ambiguous traffic reaches the next tier → **the regex tier's blindness becomes the system's blindness**
- **Parallel-OR** — every request reaches both tiers and either tier can block → the more-capable tier's capacity survives
- **No more-capable tier exists** — the regex layer is your only defense → maximum exposure

The serial-AND configuration is overwhelmingly the default in production because it is what makes the cheap regex tier financially worthwhile. It is also exactly the configuration in which the bypass propagates.

---

## §4 — What To Do Monday

Four actions, in priority order. Most of this is one engineer-week of work for an LLM-stack deployment; longer for organizations with full WAF + IDS + AV + DLP coverage.

**1. Map every pattern-matching tier in your stack and its composition with downstream tiers.** For each: input scanner, output scanner, tool-call validator, schema validator, retrieval-content scanner, WAF rule set, IDS signature set, secret/code scanner, spam-filter rule set. Write down whether it is serial-AND or parallel-OR with the next tier. Most teams discover their architecture is more serial than they assumed; the cost difference between "every request reaches the expensive thing" and "regex first" is concrete and budget-able.

**2. Reframe what your regex tier is for.** Substring matchers are excellent at exact-match keyword blocks, format validators (detecting credit-card-shaped strings), audit logging of contiguous patterns, and high-throughput cheap filtering of obviously-malformed traffic. They are structurally bad at the bypass class. Tell your security team and your vendors which job you are using each tier for, and stop relying on the regex tier for the bypass class.

**3. Where bypass cost is high, route the bypass class through a more-capable arbiter without the regex tier vetoing it.** Options, in increasing order of cost: a transformer-based safety classifier in parallel with the regex tier; an LLM-as-judge for ambiguous traffic; a normalizing parser that strips known filler classes before the regex check (closes specific filler choices, not the class); for the highest-stakes cases, an architecture in which sensitive secrets and context never reach the inference layer at all (a reference MIT-licensed implementation accompanies this work).[^secrets-router]

**4. Put the bypass class in your threat model as a known-unknown.** Vendor pattern libraries cover what they cover. The math says they cannot cover the bypass class within the substring-matching design pattern. *"Yes, the neural tier handles encoded attacks"* is a defensible posture; *"yes, our regex patterns catch encoded attacks"* is a claim no vendor can support for this attack class. Audit your contractual language and your risk register accordingly.

[^secrets-router]: *Disclosure: this implementation was developed by the author as part of this project. Readers should verify its properties against their own threat model.*

---

## §5 — Five Questions to Ask Your Security Vendors

These are written so the answers are useful regardless of whether the vendor is selling you a WAF, an LLM guardrail, an IDS, a secret scanner, or a DLP product. The structure of the bypass is the same; the structure of the questions is the same.

**1. "What is the architectural pattern in front of and behind your pattern-matching tier? Is it serial-AND or parallel-OR with the next layer? If serial-AND, what is your answer to the modular-counting bypass class?"**
A vendor who cannot describe the composition pattern, or who cannot describe the bypass class, is selling you a black box.

**2. "What input normalization runs before your pattern match? Specifically: do you strip zero-width Unicode characters, normalize Unicode (NFC or NFKC), strip NULL bytes, collapse whitespace, decode comments?"**
Each of these closes specific filler choices. None closes the class. We surveyed four widely-deployed LLM-guardrail libraries; none performed Unicode normalization, and only one stripped some filler characters as a side effect of broader sanitization.

**3. "Show me your test corpus for the modular-counting bypass class. Specifically: at what spacings (every-other, every-third, every-fifth) and with which fillers do you test, and against what patterns?"**
A vendor with a real test corpus for this class will hand you numbers. A vendor without one will pivot to "our customers haven't reported this."

**4. "When the regex tier passes traffic through, does the more-capable tier behind it see the original input or the regex tier's normalized version?"**
If the more-capable tier only sees regex-normalized input, the regex tier's blind spots transfer to the more-capable tier even in nominally parallel deployments.

**5. "What is your roadmap for moving the bypass class out of the substring-matching tier?"**
This is the diagnostic question. A vendor with a serious answer will talk about parallel composition, transformer-based classifiers, normalizing parsers, or architectural changes that route sensitive content out of the inference path. A vendor without one will offer to add patterns.

---

## §6 — What We Measured

Five empirical measurements, plus extension to two non-LLM defensive classes. Methodology and per-pilot detail in **Appendix B**; full artifact JSONs are in the project repository.

| # | What we measured | Sample | Result | Plain-English caption |
|---|---|---|---|---|
| 1 | How many production guardrail patterns are structurally vulnerable | 142 patterns from 12 LLM-guardrail sources (9 third-party libraries, 3 author-assembled sets representing 30%) | **142 / 142 vulnerable** | Every pattern in the corpus has the structural blind spot — not because of bad pattern design, but because the substring-matching design *forces* the blind spot |
| 2 | Does the basic bypass work on a sample of representative patterns | 14 (payload, pattern) test cases at each of 4 spacings (every-other, every-third, every-fifth, every-seventh), NULL-byte filler | **56 / 56 bypass** | The bypass works at every prime spacing the math predicts |
| 3 | Does it still work if the vendor blocks NULL bytes | Same 14 cases × 4 spacings × 7 different filler characters (NULL, ASCII space, tab, tilde, backtick, two zero-width Unicode codepoints) | **392 / 392 bypass** | Patching one filler character does not close the class. There are always more filler characters. |
| 4 | Does it work against patterns shipped by named third-party vendors | 100 library-shipped patterns; 48 of them were baseline-matchable by our payload synthesizer (across 8 of the 9 vendors) | **48 / 48 bypass** under both NULL and ASCII-space filler | Shipped patterns from named vendors bypass at the same rate as test patterns |
| 5 | Do downstream LLMs reliably reconstruct the encoded payload (and is this just a response-prior artifact) | 4 open-weight models (3B–22B parameters) × 3 fillers × 5 benign payloads = 60 decode cells; plus 20 random-character control cells to test for response priors | **55 / 60 decode (91.7%); 0 / 20 control (0%); +91.7-percentage-point lift** | Modern LLMs reliably decode the bypass; this is not a coincidence of the model just liking the topic |
| 6 | Does the bypass extend to non-LLM defensive classes | 6 ModSecurity OWASP CRS 4.27 SQL-injection patterns + 6 SpamAssassin `20_phrases.cf` rules; 20 synthesized payloads; tested with NULL, ASCII-space, and zero-width-space fillers | **WAF (ModSec):** 10/10 baseline-matched; 8/10 NULL-bypass, 10/10 ASCII-space bypass, 10/10 zero-width-space bypass. **Spam (SpamAssassin):** 9/10 baseline-matched; 9/9 NULL-bypass, 9/9 ASCII-space, 9/9 zero-width-space. **The two NULL failures are SQL-comment patterns whose alphabet *includes* NULL by design — and they bypass under printable-space filler instead.** | The bypass works against production WAF and spam-filter rules in exactly the way the math predicts: no single filler closes the class |

We additionally surveyed the source of four production guardrails (LLM-Guard `BanSubstrings`, Presidio analyzer, Rebuff heuristic detector, NeMo Guardrails content-safety check) for input-normalization behavior. None perform Unicode normalization; only one strips zero-width Unicode codepoints as a side effect of broader sanitization, and printable-filler bypass remains intact against it.

The remaining defensive classes named in §2 (literal-string AV signatures, IDS regex tiers, code/secret scanners) are by mathematical argument rather than direct empirical pilot in this release. We expect the same outcome based on the structure being identical; direct empirical extension is a clean follow-up.

---

## §7 — What We Do Not Claim

We do not claim that all AI security is mathematically impossible. We do not claim that all defensive security is mathematically impossible. We do not claim neural guardrails or LLM-judges share this blind spot — they do not, because they are a different and strictly more capable class of computation.

The bound is narrow, sharp, and unconditional inside its scope: it applies to substring-matching pattern recognizers (regex, trie, DFA, finite-language Bloom filter) and to any Boolean composition of them, including multi-tier compositions across product boundaries. It does not apply to embedding-based similarity filters, fine-tuned safety classifiers, model-internal safety training (RLHF, constitutional AI, refusal training), behavioral or rate-limit guardrails, or anomaly detection on edit-distance or dynamic-programming features.

We do not claim our LLM-guardrail measurements generalize universally to the non-LLM defensive classes named in §2. We *do* present empirical extension to two non-LLM classes (ModSecurity and SpamAssassin) — the bypass succeeds across all baseline-matched payloads in both. The remaining classes are by argument; the empirical sweep across them is a follow-up.

The original framing of this work was a much larger universal-impossibility claim covering all AI systems with compression capability. That claim turned out to be false; a single counterexample destroys it, and we document that destruction publicly alongside the project repository. The bound that survives — the one this article describes — is narrower and unconditional within its scope. We mention this because *integrity about which claims survived adversarial review* is itself a posture this field needs more of.

---

## Appendix A — The Math, Compressed

For practitioners who want to verify the argument or read the proofs, the full development is in the companion technical paper at `paper/main.tex` (28 pages, arXiv preprint). The compressed version:

A regex (and equivalently any trie, DFA, or finite-literal-set Bloom filter) that scans for substring matches falls into a class of computation that formal-language theorists call **star-free**. Schützenberger (1965) proved that star-free languages are exactly those whose **syntactic monoid** — an algebraic object that captures what the recognizer can distinguish — has no nontrivial cyclic subgroups. In plainer words: these recognizers cannot count modulo a prime.

Barrington, Compton, Straubing, and Thérien (1992) connected this to circuit complexity: every star-free language is decidable in **AC⁰**, the constant-depth, polynomial-size, unbounded-fan-in Boolean circuit class. Furst, Saxe, and Sipser (1981) and Håstad (1987) proved that AC⁰ provably cannot compute the parity function — the simplest case of modular counting.

The bypass is the constructive witness of this gap. Place the payload at every other character; place a filler character (one outside the pattern's literal alphabet, or one whose effect on the shifted alphabet is captured by a separate "Regime 2" argument we develop in the companion paper) at the alternating positions. The substring matcher cannot align with the payload because doing so would require it to count positions modulo 2. No combination of additional star-free patterns closes the class, because the union of star-free languages is star-free, and the syntactic monoid of a Boolean combination divides the direct product of the components' monoids (Pin 1986). This is why "add more patterns" cannot work: *any* additional pattern of the same kind, at any tier of the pipeline, leaves the system in AC⁰.

A neural classifier (any transformer-based model) operates in **TC⁰**, a strictly larger class that does include modular counting as a capacity bound (Merrill & Sabharwal 2023; Chiang, Cholak, Pillay 2023). Whether a *specific* trained transformer reliably realizes this capacity is a separate empirical question (Hahn 2020 raised concerns about parity at unboundedly long inputs); but the architecture-level capacity gap is the structural reason the composition trap matters: a TC⁰ tier behind an AC⁰ veto inherits the AC⁰ blindness; a TC⁰ tier in parallel with an AC⁰ tier does not.

The full proof of the bound for both regimes (alphabet ⊊ Σ; alphabet = Σ), the word-boundary-anchor lemma, and the closure argument under composition appear in `paper/main.tex` §§3–10.

---

## Appendix B — Methodology, Compressed

Full methodology and per-pilot artifacts are in the project repository. The compressed version:

**Corpus.** 142 patterns from twelve sources. Nine third-party LLM-guardrail libraries contribute 100 patterns: LLM-Guard (12), llm-guard-py (12), Rebuff (10), Guardrails-AI (12), Presidio (15), GitLeaks (8), LangKit (10), BodAIGuard (10), and the regex subset of NeMo Guardrails (11). Three author-assembled sets contribute 42 patterns (29.6% of the corpus): 8 inspired by OWASP Top 10 for LLMs, 15 from a curated WAF-generic pattern set, 19 author-constructed adversarial test patterns. Released as `corpus_full.csv`.

**Vulnerability verification.** Each pattern compiled to Thompson NFA → minimal DFA (Hopcroft minimization) → transition monoid enumerated by BFS over the Cayley graph → tested for `x^n = x^(n+1)` at bound `n ≤ |M|²` (Pin 1986). 119 verified by completed enumeration; 22 timed out within a grammar covered by the substring-aperiodicity lemma (theorem-implied vulnerable); 1 (the Presidio IBAN regex) verified vulnerable by a separate word-boundary-anchor lemma.

**Pilot A — primary bypass.** 11 author-assembled patterns × 4 prime spacings (2, 3, 5, 7) × 12 payloads, NULL-byte filler. Artifact: `results/mod_p_bypass_matrix.json`.

**Pilot B — filler diversity.** Same 11 patterns × 4 primes × 7 fillers (NULL, ASCII space, tab, tilde, backtick, U+200B, U+200C). 392 tests, all bypass. Artifact: `results/printable_filler_bypass.json`.

**Pilot C — LLM decode reliability with control.** Four open-weight models (llama3.1:8b, llama3.2:3b, qwen2.5-coder:14b, codestral; 3B–22B parameters) × 3 fillers × 5 benign payloads = 60 decode cells; plus 20 random-character control cells to rule out response-prior artifacts. Decode 55/60 (91.7%); control 0/20 (0%); lift +91.7pp. Artifact: `results/llm_decode_pilot_v2.json`.

**Pilot D — third-party library patterns.** Literal-glue payload synthesizer applied to 100 library-shipped patterns; 48 baseline-matched across 8 of 9 libraries (Presidio's PII patterns are the synthesis exception). 48/48 bypass under both NULL and ASCII-space filler. Artifact: `results/library_pattern_bypass.json`.

**Pilot E — non-LLM defensive classes.** 6 ModSecurity OWASP CRS 4.27 SQL-injection patterns + 6 SpamAssassin `20_phrases.cf` patterns; 20 synthesized payloads; MOD_2 bypass tested with NULL, ASCII-space, and U+200B fillers. Per-class results in §6 row 6. Artifact: `results/non_llm_defense_bypass.json`.

**Library normalization survey.** Source-level inspection of LLM-Guard `BanSubstrings`, Presidio analyzer, Rebuff heuristic, and NeMo Guardrails content-safety check on `main`/`develop` HEAD. None perform Unicode normalization (NFC/NFKC) or strip zero-width Unicode codepoints prior to regex match. Rebuff strips NULL bytes and zero-width codepoints as a side effect of broader sanitization; printable-filler bypass remains intact. Artifact: `results/library_normalization_survey.md`.

**Pilots not run, in scope of the bound.** Output-side DLP regex; tool-call argument validator regex; JSON Schema `pattern` field validators; trie/DFA/Bloom-filter blocklists; literal-string AV signatures; IDS regex tiers; code/secret scanners; multi-tier vulnerable pipelines. The mathematical bound applies; direct empirical pilots are clean follow-ups.

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
16. Ptacek, T. H., and Newsham, T. N. (1998). Insertion, evasion, and denial of service: Eluding network intrusion detection. Technical Report, Secure Networks, Inc.
17. Liu, C., and Stamm, S. (2007). Fighting unicode-obfuscated spam. In *Proc. Anti-Phishing Working Groups 2nd Annual eCrime Researchers Summit*, 45–59.
18. 0xInfection (curator) (2024). Awesome-WAF: A curated list of Web Application Firewall bypass techniques. https://github.com/0xInfection/Awesome-WAF
19. Project repository (this work, 2026), to be deposited at a stable DOI for camera-ready. Includes: 142-pattern corpus (`corpus_full.csv`), monoid enumeration scripts, primary bypass artifact (`mod_p_bypass_matrix.json`), four follow-up empirical pilots (`printable_filler_bypass.json`, `library_pattern_bypass.json`, `llm_decode_pilot_v2.json`, `non_llm_defense_bypass.json`), four-library normalization survey (`library_normalization_survey.md`), formal proofs (`paper/main.tex`), the parity-projection counterexample referenced in §7 (`counterexamples.md`), and the secrets-router reference implementation.
