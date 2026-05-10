---
name: research-doc-targeting
description: Pick the spine for a technical research doc based on who reads it. Practitioner-facing (CACM-Practice spine) and policy-maker-facing (CAIS-Policy-Brief spine) are worked-example templates; the deltas between them transfer to any technical-result-to-stakeholder communication problem in industry, academia, or regulatory contexts.
user_invocable: true
arguments: optional — "audience: practitioner|policymaker|academic|exec" or topic
---

# Research Doc Audience Targeting

You have a technical result. You need to write it for a specific audience. The same result lands differently for an engineer, a regulator, a peer reviewer, and an executive. This skill picks the **spine** — the section structure and tonal anchors — based on who pays the cost of inaction.

Audience targeting is **deeper than tone-shift**. It changes the section order, the math treatment, the number framing, and the action verb. Tone-shift alone (re-vocabularize for the audience) is a junior-writer trap that produces unreadable hybrid documents.

## When to use

- A single result needs to ship to multiple audiences (one paper for peer review, one brief for the regulator, one Practice piece for the architect).
- A draft is bouncing between reviewers because the spine is wrong for the reader, not because the content is wrong.
- A team has a technical result and is debating "venue fit" — this skill makes the venue-fit question concrete.

## The audience-spine table

| Audience | Pays cost of inaction | Pick |
|---|---|---|
| Engineer / architect | Architectural risk in production | Template A — Practitioner |
| Regulator / compliance / board | Fines, lawsuits, jurisdictional exposure | Template B — Policy-maker |
| Peer reviewer / academic | Reputation, citation, publication record | Standard IMRaD (not in this skill) |
| Executive / non-technical decision-maker | Budget, vendor selection, headline risk | Hybrid — see "Picking the spine" |

Ask: **who pays the cost of inaction?** That picks the spine.

## Template A — Practitioner spine

Use when: the target reader is an engineer or architect deciding what to change in production.

```
1.  Title — name the structural problem (not the framework)
2.  Author + venue line
3.  The argument in one paragraph (concrete claim + measurable outcome)
4.  Who this is for, why now (audience identification + context)
5.  Quick glossary (plain English for any required term)
6.  The concrete demonstration (canonical example walked through)
7.  Why this is structural (formal apparatus in PLAIN ENGLISH; citations parenthetical)
8.  Why the formalism matters (operational stakes — what the reader gains by having it)
9.  The measurement (corpus + numbers; reproducible)
10. Extensions to adjacent domains (where else the argument applies)
11. Composition does not save you (or equivalent — extending the architectural argument)
12. The action checklist (numbered, answerable from artifacts the reader already has)
13. What this does NOT solve (honest scope — LOAD-BEARING)
14. Closing (architectural principle, one sentence)
15. Notes and references
16. AI-methodology disclosure (if AI-assisted)
```

Tonal anchors:

- **Lead with a symptom** the reader recognizes from incident logs.
- **Math behind a paywall**: cite the formal result, don't derive it. Plain-English chain plus parenthetical citations is the convention.
- **Numbers are operational**: pattern counts, detection rates, audit runtimes, deployment percentages.
- **The action checklist is non-decorative**: every item must be answerable from configuration the reader has access to.
- **Honesty section is non-optional** — it's the part that survives peer review and earns reader trust.

## Template B — Policy-maker spine

Use when: the target reader is a regulator, compliance officer, or board member deciding policy text or enforcement action.

```
1. Title — name the impossibility / framework / governance gap
2. Authors + venue line (with collaborator credit if any)
3. Abstract (with a quantitative threshold — e.g., correlation >= acceptance threshold)
4. Keywords
5. Executive Summary
   - The reality (mathematical or empirical, framed for non-technical reading)
   - Business and regulatory implications
   - Implementation timeline (typically 90-day phased framework)
6. Formal foundation (theorem statement, proof sketch, complexity classification)
7. Empirical validation (incident dossier with $ impact and correlation)
8. Recommendations (draft regulatory text; agency training; vendor certification)
9. International coordination / cross-jurisdictional alignment
10. Limitations (often skipped; INCLUDE for credibility)
```

Tonal anchors:

- **Lead with the regulatory pressure** the reader is already under (existing compliance frameworks they must reconcile).
- **Math is upfront and formal** — regulators expect rigor, not plain-English. The proof sketch belongs in the body, not the appendix.
- **Numbers are stakes**: dollar impact, correlation percentages, court judgments, compliance thresholds, sample-rate gaps.
- **Action is regulatory text + timeline + training** — not architectural diagrams.
- **Limitations section is often missing** in policy briefs. INCLUDE one. It is the only thing that distinguishes a serious brief from advocacy.

## The deltas (what actually changes between A and B)

| Aspect | Practitioner (A) | Policy-maker (B) |
|---|---|---|
| Hook | Symptom from incident logs | Compliance pressure from existing frameworks |
| Opening claim | One paragraph, measurable | Abstract + Executive Summary, regulatory-threshold-framed |
| Math treatment | Plain English; citations parenthetical | Formal theorem + proof sketch in body |
| Empirics | Pattern counts, bypass rates, runtime | $ impact, correlation %, incident dossier |
| Action verb | "Run the audit", "Change the topology" | "Adopt the rule", "Train the agency", "Certify the vendor" |
| Honesty section | Required, named explicitly | Often skipped; INCLUDE for credibility |
| Vocabulary | Algebraic class, composition, audit, pipeline | Compliance, due diligence, jurisdiction, enforcement |
| Length | ~4,000–8,000 words | ~3,000–10,000 words; structured by phase, not section |

## Picking the spine

The spine question is not "what's the venue?" — venues accept both spines. The question is **who pays the cost of inaction**, which determines what evidence and what action the reader needs.

- If the reader will *change a system*: Template A.
- If the reader will *change a rule*: Template B.
- If both at once (e.g., enterprise compliance officer with engineering staff): write A and B as **separate documents**. Hybrids fail because the spine is one or the other; tone-shifting between sections produces a doc that satisfies neither audience.

For an executive / non-technical decision-maker who is choosing between vendors or budgeting: a one-page summary derived from Template A's section 1+3+12, OR Template B's Executive Summary, depending on whether the decision is technical or governance-flavored.

## Honest-labeling discipline (the load-bearing rule)

Both templates require an explicit scope-limit section. If you cannot write three sentences honestly stating what the argument does NOT cover, you do not yet have an argument — you have a sales pitch.

This section is the only one peer reviewers, regulators, and practitioners all respect equally. Skipping it is the most common failure mode in industry technical writing. Including it earns trust faster than any other rhetorical move.

The standard form: "We claim X. We do not claim Y. The argument's reach extends to A but not to B because [structural reason]."

## Anti-patterns

1. **Formal apparatus in the practitioner template.** Loses the reader by paragraph two. Cite, parenthesize, move on.
2. **Plain-English math in the policy template.** Loses credibility with regulators who read formal mathematics regularly. Use the formal statement.
3. **Skipping the honesty section in either template.** Reader stops trusting the document; reviewer rejects.
4. **Anchoring numbers without citation source.** Any technical reader spot-checks. A number without an artifact (file path, dataset, court judgment) is a number that won't survive review.
5. **Treating audience-targeting as tone-shift.** Vocabulary swap on top of the wrong spine produces a worse document, not a better one.
6. **Writing both audiences into one document.** The hybrid satisfies neither. Two documents, one shared appendix of evidence.
7. **Putting the action verb in the wrong template.** "Adopt the rule" in a Practice piece is jarring; "Change the topology" in a Policy Brief reads as out-of-scope.

## Reuse outside research papers

The two spines transfer to other artifact types:

- **Practitioner spine** also fits: postmortems for engineering audiences, RFCs, architectural decision records, runbooks for incident response.
- **Policy-maker spine** also fits: compliance reports, board memos, vendor due-diligence summaries, regulatory comment letters.

The deltas table is the portable asset; the templates are starting points.

## Pre-flight check before drafting

Before opening a blank doc, answer these three questions out loud:

1. Who pays the cost of inaction? (picks the spine)
2. What artifact will they cite back to me? (picks the evidence form)
3. What action verb completes the sentence "After reading, the reader will ___"? (picks the action section)

If you cannot answer all three in one sentence each, the targeting is not yet decided. Write the answers down before the doc, not in the doc.
