# arXiv cs.CR Endorsement Outreach
**Paper:** "Algebraic and Computational Limits of LLM Guardrails" — Joseph Robert Lopez
**Endorsement code:** `3YEWSA`
**Endorsement link:** https://arxiv.org/auth/endorse?code=3YEWSA

---

## All Cited Authors — arXiv Status

| Author | Paper Cited | arXiv Activity | cs.CR Papers | Reachability | Score |
|--------|-------------|----------------|--------------|--------------|-------|
| **Andy Zou** | `zou2023universal` — GCG adversarial attacks | 30+ papers, active 2026 | Yes — multiple (prompt injection, adversarial LLMs) | andyzou@cmu.edu — PhD student at CMU, co-founder Gray Swan AI | ★★★★★ |
| **Nicolas Papernot** | `boucher2021badchars` (co-author) | 127+ papers, very active | Yes — 13+ cs.CR papers | nicolas.papernot@utoronto.ca — Associate Prof, U of Toronto | ★★★★★ |
| **Nicholas Boucher** | `boucher2021badchars` — Bad Characters NLP attacks | 8 papers, all cs.CR | Yes — 100% cs.CR | ndb40@cl.cam.ac.uk — Now at Microsoft, still Cambridge affiliate | ★★★★☆ |
| **Kai Greshake** | `greshake2023injection` — Indirect Prompt Injection | 1 paper on arXiv | Yes — cs.CR, cs.AI | Public: greshake.github.io — Saarland/sequire technology | ★★★☆☆ |
| **Alexander Wei** | `wei2023jailbroken` — Jailbroken NeurIPS 2023 | ~5 papers | Likely cs.CR (safety/adversarial) | awei@berkeley.edu — PhD student UC Berkeley | ★★★☆☆ |
| **Jacob Steinhardt** | `wei2023jailbroken` (advisor) | Active, Berkeley faculty | Has certified defense / poisoning papers (cs.CR adjacent) | jsteinhardt@berkeley.edu — Professor UC Berkeley | ★★★☆☆ |
| **William Merrill** | `merrill2023saturated`, `merrill2024survey`, `strobl2024formal` | 40+ papers, very active | No cs.CR — primarily cs.CL/cs.FL/cs.LG | willm@allenai.org — AI2/TTIC researcher | ★★☆☆☆ |
| **David Chiang** | `chiang2024tighter`, `strobl2024formal` | 66+ papers | No cs.CR — primarily cs.CL/cs.FL | dchiang@nd.edu — Professor, Notre Dame | ★★☆☆☆ |
| **Lena Strobl** | `strobl2024formal` | Several papers cs.CL/cs.FL | No cs.CR | strobl@uni-trier.de | ★★☆☆☆ |
| **Gail Weiss** | `strobl2024formal`, `weiss2022extracting` | Several papers cs.LG/cs.FL | No cs.CR | — | ★★☆☆☆ |
| D. A. M. Barrington | `barrington1992` | Classic TCS (1992) | No — retired/historical | — | ✗ |
| H. Straubing | `straubing1994`, `barrington1992` | Classic TCS | No | — | ✗ |
| J.-E. Pin | `pin1986`, `pin2021` | Lecture notes only | No | IRIF, Paris — emeritus | ✗ |
| D. Angluin | `angluin1987`, `strobl2024formal` | Classic — emeritus Yale | No active arXiv | — | ✗ |
| M. Ball et al. | `ball2025impossibility` | arXiv 2507.07341 | Likely cs.CR/cs.CC | Anonymous "and others" — unclear | ✗ |
| T. Hagendorff et al. | `reasoning_jailbreak2026` | Nature Comms 2026 | cs.AI adjacent | — | ★★☆☆☆ |
| Y. Dong et al. | `nfl_guardrails2025` | arXiv 2504.00441 | cs.CR likely | "and others" — unclear lead author | ★★☆☆☆ |
| A. Kumar et al. | `certifying_safety2023` | arXiv 2309.02705 | cs.CR (certified LLM safety) | — | ★★★☆☆ |

**Note on endorser verification:** The `/auth/show-endorsers/{paper_id}` endpoint requires arXiv login and cannot be scraped. The cs.CR status above is inferred from each author's primary submission category history on arXiv. Authors submitting to cs.CR are automatically eligible to endorse once they have a published paper there.

---

## Top 3 Candidates — Ranked

### Rank 1: Andy Zou — andyzou@cmu.edu
**Why:** Most directly aligned. His GCG paper (`zou2023universal`) is a primary reference in this work — it's the canonical adversarial attack benchmark the V5 bypass supersedes in the monoid sense. He posts actively in cs.CR, has 30+ arXiv papers with confirmed cs.CR tags, and as a PhD student + startup founder is reachable and likely responsive to peer outreach. His very recent paper on indirect prompt injection (arXiv:2603.15714, cs.CR) confirms current activity.

### Rank 2: Nicolas Papernot — nicolas.papernot@utoronto.ca
**Why:** 127 papers, 13+ in cs.CR, Associate Professor — almost certain established endorser. Papernot co-authored `boucher2021badchars` which is directly cited. His research sits at the intersection of security + ML, exactly the paper's domain. Faculty are typically willing to endorse legitimate academic work. Most likely to be a formal cs.CR endorser.

### Rank 3: Nicholas Boucher — ndb40@cl.cam.ac.uk (or via https://nickboucher.com)
**Why:** Every one of his 8 arXiv papers is cs.CR. Now at Microsoft Security Research — a practitioner who will understand the paper's relevance immediately. `boucher2021badchars` is the most thematically related citation (encoding-level attacks on NLP systems). Short, practitioner-friendly email will resonate.

---

## Draft Emails

---

### Email 1 — Andy Zou (Warmest Lead)

**To:** andyzou@cmu.edu
**Subject:** arXiv endorsement request — algebraic impossibility of regex guardrails

Hi Andy,

I'm working on a paper titled "Algebraic and Computational Limits of LLM Guardrails" that builds directly on your GCG work — we prove that all substring-matching regex guardrails have aperiodic syntactic monoids, making them provably blind to modular-counting encodings, and demonstrate 100% bypass rates empirically across 11 tools. Your universal adversarial attack result is a central reference, and this work provides the algebraic explanation for why such attacks succeed structurally, not just empirically.

I'd be grateful if you'd consider endorsing my arXiv submission to cs.CR: https://arxiv.org/auth/endorse?code=3YEWSA — it takes about 30 seconds. Happy to share a draft if useful.

Best,
Joey Lopez

---

### Email 2 — Nicolas Papernot (Highest Endorser Probability)

**To:** nicolas.papernot@utoronto.ca
**Subject:** arXiv cs.CR endorsement — formal proof that regex guardrails are algebraically bypassable

Dear Professor Papernot,

I'm an independent researcher and I'd like to request a cs.CR arXiv endorsement for a paper on the algebraic limits of LLM guardrails. The paper proves — via syntactic monoid theory and Schützenberger's theorem — that all regex-based guardrails are structurally blind to a class of encodings, and quantifies the information-theoretic and computational barriers using Fano's inequality and NP-hardness reductions. We cite your work with Boucher et al. on imperceptible NLP attacks as a key empirical predecessor to these algebraic results.

If you're willing to endorse, the link is: https://arxiv.org/auth/endorse?code=3YEWSA — I'm happy to send a preprint draft on request.

Thank you for your time,
Joey Lopez

---

### Email 3 — Nicholas Boucher (Most Thematically Aligned)

**To:** ndb40@cl.cam.ac.uk
**Subject:** arXiv endorsement — algebraic proof of NLP guardrail bypass (builds on Bad Characters)

Hi Nicholas,

Your "Bad Characters" paper on imperceptible encoding attacks is a central citation in a paper I'm finalizing on the algebraic limits of LLM guardrails. We prove formally that all substring-matching regex defenses have aperiodic syntactic monoids — meaning they are provably blind to modular-counting encodings — and achieve 100% bypass rates empirically. Your encoding-attack framing was a direct precursor to this algebraic generalization.

I'd appreciate an arXiv cs.CR endorsement if you're willing: https://arxiv.org/auth/endorse?code=3YEWSA — takes 30 seconds. Happy to share the draft.

Thanks,
Joey Lopez

---

## Notes on Sending Order

1. Send all three simultaneously — endorsements are one-and-done, first response wins.
2. Andy Zou is the fastest path: PhD student, active on Twitter (@andyzou_jiaming), can also DM him there if email bounces.
3. If none of these three respond within 5 days, next batch: Kai Greshake (greshake.github.io contact form), Anshuman Kumar (certifying_safety2023 lead), and Jacob Steinhardt (jsteinhardt@berkeley.edu).
4. The endorsement link https://arxiv.org/auth/endorse?code=3YEWSA is single-use per endorser session but can be sent to multiple people — only one needs to click it.
