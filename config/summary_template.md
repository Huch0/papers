# <Paper Title>

## Metadata
- Canonical key:
- Version:
- Fetch date:
- Source:
- PDF:
- Venue:
- Year:
- Authors:
- Tags:
- User status:
- Triage label:
- Triage confidence:

<!--
HOW TO USE THIS TEMPLATE
This template adapts three references:
  • Keshav, "How to Read a Paper" — the three-pass method (triage → content → critique)
    and the Five Cs.
  • Kim, "Motivation ≠ Novelty" — keep the PROBLEM (motivation) strictly separate from
    the genuine DELTA over prior work (novelty), and explain WHY the design must take
    its form (mechanistic reason), not just "prior work couldn't do X so we added a module".
  • AI@UVA "FOCUS" — extract rich, specific details (numbers, quotes with anchors);
    write declaratively (NOT "the authors state that…"); ground every claim in a section.

WRITING RULES
  • English only. Write declaratively and specifically; avoid meta-discourse and generic
    praise. Prefer exact numbers and short quotes with page/section anchors, e.g. (p.4, §3.2).
  • "Not reported" for absent source data; "Unclear" when the text does not support a
    conclusion. Never invent metadata or results. Quote sparingly, only when wording matters.
  • Fill what the paper supports; mark the rest. A SKIM/TRACK_ONLY paper may stop after
    Pass 1 + the Decision block — say so rather than padding.
  • BE SELF-CONTAINED. On first use, define every non-universal term, acronym, dataset,
    metric, or named method in one clause inline AND collect them in the Glossary. Assume
    a reader who knows ML broadly but not this subfield — they should not need the paper
    or a web search to follow the summary.
-->

---

# PASS 1 — Triage (bird's-eye, ~5 min)

## One-sentence takeaway
The paper's core contribution in a single sentence.

## The Five Cs
- **Category:** what kind of paper — measurement / new method or system / benchmark or
  dataset / analysis of an existing system / position / survey.
- **Context:** which prior work and lines of research it builds on and competes with;
  the theoretical or empirical bases it relies on.
- **Correctness:** do the core assumptions look valid on a first read? Flag anything dubious.
- **Contributions:** the 1–3 claimed contributions, as crisp bullets.
- **Clarity:** is it well written and well evidenced? (this calibrates your confidence)

## Why this matters to me now
Relevance to my interest profile and current trends, in 1–3 lines.

---

# PASS 2 — Content (what it actually does; section-grounded)

## Motivation — the problem (NOT the novelty)
What problem the paper attacks and **why it matters** / what breaks in prior work.
This is the problem and its importance only. Resist describing the solution here.

## Novelty — the genuine delta  ★ the core of a good summary
What is *actually new* versus the closest prior work, and **why the solution takes the
form it does**. A real contribution is an insight, not just an artifact. Answer:
- **Delta in one sentence** — state the *insight*, phrased so it survives deleting the
  words "we propose" (if nothing remains, it was motivation, not novelty).
- **Mechanistic reason** the design must be this way, derived from *why* the baseline
  fails — not "prior work couldn't do X, so we bolted on a module".
- **Closest prior work and the precise difference** from each (name them).
- **Motivation-vs-novelty check:** does the stated contribution end at "prior method X
  fails in scenario Y"? If so, flag it: that is motivation dressed as novelty.
- **30-second test:** can you say what is novel in 30 seconds? Write that sentence.

## Core idea / method
The main technical idea, architecture, algorithm, dataset/benchmark construction, or
system design — in your own words, grounded in specific sections. Not an abstract rehash.

## Harness relevance
For agent/harness papers, identify explicitly:
- environment or workspace
- observation interface
- action interface
- tool / API / shell / GUI layer
- planner / executor / verifier / search structure
- evaluation harness
- training harness, if any
- logging / trace / reproducibility mechanism
- safety or permission mechanism, if any

If it is not an agent/harness paper, adapt this section to the paper's central system or method.

## Experimental setup
Datasets/benchmarks · baselines · models · metrics · compute or cost (if reported) ·
implementation and released artifacts (if reported).

## Key results — read the figures, not just the prose
The most important quantitative and qualitative results, with anchors. Inspect figures
and tables critically: axes and scales, error bars / variance, statistical significance,
sample sizes, and whether the headline (abstract) number matches the table. Flag
abstract-vs-table mismatches and cherry-picked or single-run numbers. Mark uncertain or
incomplete numbers as such.

---

# PASS 3 — Critique (challenge every assumption)

## Does the evidence actually support the claims?
Map each main claim to the evidence for/against it. Call out: missing or weak baselines,
over-favorable metrics, benchmark contamination/leakage, narrow task coverage, missing
ablations, absent variance/significance, and train/test issues. Crucially, separate
experiments that **verify the novelty** from experiments that **merely confirm the
motivation** (i.e. re-show that the problem exists).

## Hidden assumptions & failure modes
Assumptions the work relies on (stated and unstated). When would the method break? What
would you press on if you were reviewing it?

## Could I reconstruct it? (reproducibility)
The pass-3 re-implementation test: could you rebuild the core result from the paper alone?
- Code:
- Data:
- Models:
- Environment:
- License:
- Exact commands or setup:
- Missing details (what blocks reconstruction):

## Strengths
The main strengths, concretely.

## Weaknesses and limitations
Limitations stated by the authors and ones you infer from the paper.

## Relationship to prior work
The closest related papers/systems and what is genuinely new versus incremental
(consistent with the Novelty section above — do not relitigate motivation here).

---

# Decision

## Glossary / key terms
Define every non-universal term, acronym, dataset, metric, and named method used above,
so the summary stands alone. One line each, e.g.:
- **<Term/acronym>** — <plain-language definition; what it is and why it matters here>.

## What I should read
- Must read:
- Skim:
- Can skip:
- Follow-up papers / references to chase:

## Triage decision
Label: MUST_READ / READ_SOON / SKIM / TRACK_ONLY / SKIP
Rationale (ground it in the Five Cs + novelty + evidence quality):
Confidence:
Reading time estimate:

## Personal notes
Free-form notes for later.

## Follow-up actions
- Add related paper:
- Compare with:
- Re-run after new version:
- Check code:
- Read benchmark details:
