---
name: research-paper
description: End-to-end research paper pipeline. Literature search, draft, adversarial peer review, fix, re-review until accepted, LaTeX compile, ship. Makes AI researchers homeless.
user_invocable: true
arguments: topic or thesis statement
---

# Research Paper Pipeline

You are orchestrating a full research paper from thesis to submission-ready PDF.

## Pipeline Stages

### Stage 1: SCOPE (5 min)
Ask the user exactly 3 questions:
1. What's the claim? (one sentence)
2. What evidence exists? (code, experiments, intuition?)
3. Target venue? (security: USENIX/S&P/CCS | theory: STOC/FOCS/ICALP | ML: NeurIPS/ICML | safety: CSF/AAAI)

### Stage 2: LITERATURE (Agent: Explore)
Search arXiv for prior art. Use WebSearch for:
- Direct keyword matches for the claim
- Known authors in the area
- Recent surveys covering the topic

Produce a 5-entry "must cite and distinguish" list. If someone already published this, STOP and tell the user.

### Stage 3: PILOT (if empirical claims exist)
Before writing a single word, run a 5-task pilot:
- Define 5 concrete test cases for the core claim
- Run them
- If <2/5 pass: KILL the direction, tell the user why
- If >=2/5 pass: proceed with honest scope

This is the KILL GATE. Most bad papers die here. That's the point.

### Stage 4: DRAFT (Agent: general-purpose, opus)
Write the paper following venue conventions:
- Security venue: threat model → attacks → formal analysis → PoC → case studies → defense
- Theory venue: definitions → theorems → proofs → applications
- ML venue: method → experiments → ablations → related work

Rules:
- Lead with empirical results, math as backing (unless pure theory venue)
- Acknowledge when math is "known tools, new domain" — don't oversell
- Honest limitations section
- ~4000 words for workshop, ~8000 for full paper

### Stage 5: PEER REVIEW (Agent: peer-reviewer, opus)
Launch the peer-reviewer agent. It will:
- Search arXiv for prior art
- Verify every theorem line by line
- Check for circular reasoning, inverted arrows, vacuous definitions
- Score Novelty/Rigor/Clarity (1-10 each)
- Produce verdict: Accept / Weak Accept / Borderline / Reject
- List critical errors with fixes

### Stage 6: FIX
Apply all critical and major fixes from the review. For each fix:
1. Read the error description
2. Apply the correction
3. Verify it doesn't break adjacent claims

DO NOT skip fixes. DO NOT argue with the reviewer. Fix or cut.

### Stage 7: RE-REVIEW (Agent: peer-reviewer, opus)
Run the reviewer again on the fixed version. Compare scores.

Loop Stage 6-7 until:
- All scores >= 6
- No critical errors remain
- Verdict is at least Weak Accept

Maximum 3 review rounds. If still Reject after 3 rounds, the thesis needs rethinking, not more polish.

### Stage 8: ADVERSARIAL MATH AUDIT (if paper has theorems)
Launch a separate agent specifically to attack the proofs:
- Check every quantifier
- Check every reduction
- Verify definitions are consistent
- Look for circularity
- Check if "theorems" are actually propositions or observations

### Stage 9: LaTeX
Convert to LaTeX with:
- Proper theorem/proposition/definition environments
- booktabs tables
- natbib references with .bib file
- lstlisting for code
- Compile with tectonic or pdflatex

### Stage 10: SHIP
- Compile PDF
- Zip everything (paper + code + supplementary)
- Copy to ~/Sync/
- Print final scores and verdict

## When to STOP

- After Stage 2 if prior art already covers the claim
- After Stage 3 if pilot fails (<2/5)
- After Stage 7 round 3 if still Reject
- After Stage 9 if PDF compiles clean and scores are Accept

## Key Principles

1. **Kill early.** A killed paper saves weeks. The pilot gate exists for this.
2. **Reviewer is always right about errors.** If the reviewer says the proof is wrong, it's wrong. Fix it.
3. **Reviewer is sometimes wrong about significance.** If the reviewer says "not novel" but you have evidence it IS novel (empty arXiv search), push back with evidence.
4. **Honest framing beats overclaiming.** "Known tools applied to new domain" is a valid contribution. "Novel impossibility theorem" when it's the pigeonhole principle is not.
5. **Empirics first, theory as backing.** Unless targeting a pure theory venue, lead with what you built and measured. The math explains why it works.
6. **The meta-contribution matters.** "Nobody pointed X at Y" is a real contribution if X+Y produces actionable results. You don't need new math to have a new paper.

## Agent Delegation

| Stage | Agent | Model | Why |
|-------|-------|-------|-----|
| Literature | Explore | haiku | Fast search, breadth |
| Draft | general-purpose | opus | Needs deep reasoning for theorem statements |
| Peer review | peer-reviewer | opus | Needs to verify proofs |
| Math audit | general-purpose | opus | Adversarial proof checking |
| LaTeX | general-purpose | sonnet | Mechanical conversion |
| Fix application | (you) | (main) | Stay in main context for coherence |
