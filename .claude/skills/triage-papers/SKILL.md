---
name: triage-papers
description: Re-score and re-label papers against the current interests/scoring config and their summaries, and produce a ranked reading list. Use when the user runs /triage-papers (optionally with an inbox path, --untriaged, or --tag).
---

# /triage-papers [inbox/<date> | --untriaged | --tag <group>]

Re-apply the scoring rubric (`config/scoring.yaml` + `config/interests.yaml`) to
papers and update their triage labels. Use after editing config, adding interests, or
writing new summaries.

## Select the target set
- `inbox/<date>` → re-triage candidates listed in that inbox's `candidates.jsonl`
  (and the corresponding library records if already ingested).
- `--untriaged` → all version dirs whose `metadata.yaml: status.triaged` is false or
  whose `scoring.label` is null.
- `--tag <group>` → all papers whose `topic_groups` include `<group>`.
- no arg → all papers in `library/`.

## Steps
1. For each selected version dir, re-score (this reads refined subscores if Claude has
   written them during summarization, else recomputes heuristics):
   ```
   python3 scripts/score_paper.py <version_dir>
   ```
   This writes `scoring.{score,label,confidence,rationale,...}` back into
   `metadata.yaml` and sets `status.triaged = true`.

2. Where a summary exists, sanity-check the heuristic label against the summary's
   "Evidence quality" / "Triage decision" sections. If they disagree, refine the
   subscores in `metadata.yaml` (e.g. lower `evaluation_quality` for a weak benchmark,
   raise `novelty` for a genuinely new harness) and re-run `score_paper.py` so the
   label is explainable and grounded — never hand-edit the label without adjusting the
   subscores that justify it.

3. Carry the label up to `paper.yaml: user.triage_label/triage_confidence` (the
   scorer + summarize finalize already do this; run
   `python3 scripts/update_indexes.py` to refresh).

4. Produce a **ranked reading list** for the user: MUST_READ first, then READ_SOON,
   then SKIM, each with score + one-line rationale + estimated reading time. Point to
   `indexes/MUST_READ.md`.

## Guardrails (from config — honor them)
- Don't over-prioritize citation count for papers younger than ~6 months.
- Don't over-prioritize old GUI-agent papers unless foundational.
- Accepted A* > equivalent preprint, but remarkable preprints (new benchmark/harness,
  major lab, wide adoption) can still be MUST_READ.
- If you change how triage *should* work in general (not just one paper), do it via
  `/evolve-paper-system` so it becomes a durable config change.
