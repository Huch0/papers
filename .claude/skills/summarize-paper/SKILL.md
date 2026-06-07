---
name: summarize-paper
description: Generate or refresh a detailed-yet-concise English MDX summary for a paper version directory or a PDF, using the project's MDX template and semantic component vocabulary. Use when the user runs /summarize-paper <version_dir|pdf>.
---

# /summarize-paper <version_dir | pdf> [--overwrite-notes]

Produce a **concise, core-first, self-contained** English analysis of a paper as an
**MDX** file — readable in 60 seconds at the top, with depth available on demand. This is
the canonical instruction for both Claude and human authors. The format is `summary.mdx`
(MDX is the default); `config/summary_template.mdx` is the skeleton and
`config/summary_components.md` is the component vocabulary.

## Procedure
1. Resolve the target to a version dir `library/<slug>/vN` (a bare `.pdf` → ingest via
   **add-paper** first so it gets a version dir).
2. `python3 scripts/summarize_paper.py <version_dir> --prepare --format mdx`
   — ensures `extraction.txt` exists and writes `summary.scaffold.mdx` (frontmatter
   generated from `metadata.yaml`; never hand-edit frontmatter).
3. **Read `extraction.txt` in full** (it has `=== PAGE n ===` anchors), then write
   `<version_dir>/summary.mdx` from the scaffold, following the rules below.
4. **Self-verify the MDX compiles BEFORE finalizing (mandatory).** Run:
   `(cd site && node scripts/check-mdx.mjs <ABSOLUTE path to summary.mdx>)`.
   If it prints `FAIL … (line L:C)`, fix that exact spot and re-run until it prints `OK`.
   You MUST output a completed, error-free summary — never hand off a summary that fails
   this check. (Common causes: a bare `{` or `<` in prose or inside `<MathBlock>` — wrap
   code/math in backticks; e.g. `` `{cell:value}` ``, `` `p<0.05` ``, `` `\beta_1=0.1` ``.)
5. `python3 scripts/summarize_paper.py <version_dir> --finalize --format mdx`
   then `python3 scripts/update_indexes.py`.

## What a good summary is (our preferences — follow exactly)
- **English, declarative.** State findings directly; never "the authors state that…".
- **Concise + core-first.** The visible body reads top-to-bottom as: TL;DR → why it
  matters → KeyStats → Motivation → Contribution → Research questions → Methodology →
  Main result → **Key findings** → Implications → Limitations → Critiques → Glossary.
  Push granular detail into `<Pass>` collapsibles. A SKIM/TRACK_ONLY paper may stop after
  the Main result and say so.
- **Keep the key points — this is the #1 failure mode.** Do NOT report only the headline
  number. Read the analysis/discussion section and capture the real takeaways in a
  **`## Key findings`** section: ablations, scaling/sensitivity trends, failure analyses,
  surprising results. (E.g. SWE-bench: "difficulty correlates with context length",
  "finetuned models are sensitive to context-distribution shift".) A short summary that
  omits these is wrong.
- **Motivation ≠ Contribution.** Keep the problem (`<Problem>`) separate from the genuine
  delta (`<Novelty>`). In Contribution, state the insight that survives deleting "we
  propose" and the *mechanistic reason* the design must take its form.
- **Self-contained.** Define every non-universal term/acronym/dataset/metric on first use
  with `<Term def="plain definition">term</Term>` (a hover chip) — assume a reader who
  knows ML broadly but not this subfield.
- **Verify every number against `extraction.txt`** and cite an anchor (`Tab.3`, `§5`,
  `p.7`). Mark "Not reported" / "Unclear" for gaps. Read figures/tables critically (error
  bars, variance, significance); flag abstract-vs-table mismatches and single-run numbers.

## Semantic highlights (use for MEANING — colors are consistent across all summaries)
- `<Problem>` 🔴 — the problem the paper tackles / a prior-work limitation
- `<Novelty>` 🟢 — a novel module/approach/insight the paper introduces
- `<Finding src="Tab.X">` 🟦 — a finding/claim/result of THIS paper (+ anchor)
- `<FollowUp>` 🔵 — a notion/thread the reader should follow up on
- `<Caveat>` 🟠 — a limitation of THIS paper
- `<Related>` 🟣 — related work / lineage
Structural/interactive components: `<TLDR>`, `<WhyItMatters>`, `<KeyStats>`, `<Pass>`,
`<SortableTable>` (interactive), `<Stepper>`, `<Chart>`, `<SelfCheck>`, `<Figure>`,
`<MathBlock>`. Full reference: `config/summary_components.md`. Components are provided
globally — never import them. Preserve the `{/* NOTES_START */}…{/* NOTES_END */}` block.

## MDX gotchas
- A bare `{` or `<` in prose breaks MDX — wrap code-ish text in backticks (e.g. `` `{k:v}` ``).
- Frontmatter is generated; don't touch it. Keep `summary_date` quoted.

## Type-specific checks
SWE agents → execution-based eval & test-validated patches. Computer-use → interface type
(GUI/CLI/API/shell/browser/OS/IDE). Document agents → artifact type, editing granularity,
evaluator, structural validation. Benchmarks → task construction, evaluator reliability,
contamination risk, aging.

Preserve the user's `## Personal notes` unless `--overwrite-notes` is given.
