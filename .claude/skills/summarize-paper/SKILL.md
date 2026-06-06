---
name: summarize-paper
description: Generate or refresh a detailed English summary for a paper version directory or a PDF, using the project summary template. Use when the user runs /summarize-paper <version_dir|pdf>.
---

# /summarize-paper <version_dir | pdf> [--overwrite-notes]

Produce a triage-grade English analysis of a paper — not an abstract paraphrase.

## Steps
1. Resolve the target:
   - `library/<slug>/vN` → a version dir (preferred).
   - a `.pdf` path → first ingest it via **add-paper** (so it gets a version dir), or
     extract ad hoc with `scripts/extract_pdf_text.py <pdf>` for a one-off read.

2. Prepare:
   ```
   python3 scripts/summarize_paper.py <version_dir> --prepare
   ```
   This ensures `extraction.txt` exists (running PyMuPDF extraction if needed),
   writes a metadata-filled `summary.scaffold.md`, and prints the extraction path,
   character count, and whether existing personal notes were preserved.

3. Read `extraction.txt` **in full** (it has `=== PAGE n ===` anchors). Then write
   the analysis into `<version_dir>/summary.md`, starting from `summary.scaffold.md`.
   Follow `config/summary_template.md`, which is built on three references — Keshav's
   three-pass method, Kim's "Motivation ≠ Novelty", and the FOCUS extraction discipline.
   Requirements:
   - **English only. Write declaratively** — state findings directly, never "the authors
     state that…". Prefer exact numbers and short quotes with anchors over generic praise.
   - **Do not paraphrase the abstract.** Ground every claim in a specific section.
   - **Three passes** (mirror the template): Pass 1 = triage (one-line takeaway + the
     **Five Cs**: Category, Context, Correctness, Contributions, Clarity). Pass 2 =
     content. Pass 3 = critique. For a SKIM/TRACK_ONLY paper it's fine to do Pass 1 +
     the Decision block and say so, rather than padding the rest.
   - **Motivation ≠ Novelty — the most important rule.** Keep the *Motivation* section
     (the problem and why it matters) strictly separate from the *Novelty* section. In
     Novelty, state the genuine **delta** over the closest prior work AND the
     **mechanistic reason** the design must take its form (derived from *why* the
     baseline fails) — not "prior work couldn't do X so they added a module". Apply the
     checks: does the contribution survive deleting "we propose" (insight vs artifact)?
     does it merely end at "prior method fails in case Y" (that's motivation, not
     novelty)? what is novel in 30 seconds?
   - **Separate claims from evidence.** Map each claim to its support; distinguish
     experiments that *verify the novelty* from those that *merely confirm the
     motivation*. **Read the figures/tables critically** — axes, error bars, variance,
     significance, sample size — and flag abstract-vs-table mismatches and single-run /
     cherry-picked numbers.
   - Use "Not reported" for absent data; "Unclear" when text doesn't support a claim.
   - Fill the **Harness relevance** section for agent/harness papers (environment,
     observation/action interface, tool/API/shell/GUI layer, planner/executor/verifier,
     eval harness, training harness, logging/trace, safety/permissions). Adapt it for
     non-agent papers to the paper's central system.
   - Apply the type-specific checks from the README "Summary rules" (SWE agents →
     execution-based eval & test-validated patches; computer-use → interface type;
     document agents → artifact type/granularity/validation; benchmark/harness →
     task construction, evaluator reliability, contamination risk, aging).
   - Preserve the user's `## Personal notes` block unless `--overwrite-notes` is given
     (the scaffold already carries forward existing notes).

4. Finalize:
   ```
   python3 scripts/summarize_paper.py <version_dir> --finalize --status full
   python3 scripts/update_indexes.py
   ```
   For a quick triage-only pass (no deep read), use `--status triage_only`.

5. Report the summary path and the triage label/rationale. If your reading changes the
   triage judgment, note it and (optionally) refine `metadata.yaml: scoring.subscores`
   then re-run `scripts/score_paper.py <version_dir>` so the label reflects your read.
