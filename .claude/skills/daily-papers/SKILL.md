---
name: daily-papers
description: Fetch, triage, and record recent AI papers in my interest areas for a day or date range, then summarize the top ones. Use when the user runs /daily-papers (optionally with a date, --since, --tags, or --dry-run).
---

# /daily-papers

Discover recent papers from configured sources, triage them, store records, and
summarize the above-threshold ones. The mechanical work is done by
`scripts/daily.py`; you (Claude) write the English summaries for high-scoring papers.

## Arguments (parse from the user's invocation)
- no arg / `today` → default window (`config/sources.yaml: defaults.since_days`)
- a date `YYYY-MM-DD` → pass as `--date` and `--from <date> --to <date>`
- `--since 3d|1w|12h|YYYY-MM-DD`
- `--tags a,b` → restrict to those topic groups
- `--dry-run` → fetch + score only, write nothing into `library/`
- `--enrich` → also pull OpenAlex/Semantic Scholar signals (slower)

## Steps
1. Run the orchestrator from `scripts/`:
   ```
   python3 scripts/daily.py [--since ...] [--from ... --to ...] [--tags ...] [--dry-run] [--enrich]
   ```
   It fetches (arXiv primary), dedupes against the registry, scores every candidate,
   ingests non-SKIP papers (creating a record even when the PDF can't be fetched),
   downloads PDFs for papers at/above the SKIM threshold, regenerates indexes, and
   writes `inbox/<date>/{candidates.jsonl,rejected.jsonl,daily_report.md}`.
   It prints JSON including a `needs_summary` list.

2. If `--dry-run`, just summarize the JSON/report back to the user and stop.

3. For each entry in `needs_summary` (these are MUST_READ / READ_SOON / SKIM papers
   with a downloaded PDF), generate a full summary by following the
   **summarize-paper** procedure on its `version_dir`:
   - `python3 scripts/summarize_paper.py <version_dir> --prepare`
   - Read the printed `extraction` file fully, then write the analysis into
     `<version_dir>/summary.md` using `<version_dir>/summary.scaffold.md` as the
     skeleton. English only; analyze, don't paraphrase the abstract.
   - `python3 scripts/summarize_paper.py <version_dir> --finalize --status full`
   For papers below the PDF threshold, the deterministic triage record is enough
   (no full summary); the metadata already carries a scored triage label + rationale.

4. Regenerate indexes once more after summaries: `python3 scripts/update_indexes.py`.

5. Report to the user: counts (fetched/new/updated/duplicates/errors), the top
   MUST_READ and READ_SOON titles with one-line rationales, any duplicate candidates
   to review, source coverage, and a pointer to `inbox/<date>/daily_report.md`.

## Notes
- Never invent metadata. Missing data stays "Not reported".
- If a source errors, the candidate/record is preserved with the error logged to
  `logs/errors.jsonl`; mention failures rather than hiding them.
- Respect the user's interests/scoring config — do not hand-tune labels here. If the
  user disagrees with triage, route that to `/evolve-paper-system`.
- arXiv can be briefly slow; the fetcher retries with backoff. If it fully fails,
  report it and suggest re-running.
