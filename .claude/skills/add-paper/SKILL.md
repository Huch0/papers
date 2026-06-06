---
name: add-paper
description: Ingest a specific paper into the harness from an arXiv link/id, PDF URL, local PDF, DOI/venue page, OpenReview/Semantic Scholar page, or manual metadata. Use when the user runs /add-paper <url|arxiv_id|doi|pdf_path>. Also supports adding a new version of an existing paper.
---

# /add-paper <ref>

Ingest one paper into the same library/registry as `/daily-papers`.

## Step 1 — classify the reference
Run: `python3 scripts/paperlib.py` is not needed; instead classify with the helper:
```
python3 -c "import sys; sys.path.insert(0,'scripts'); import paperlib as pl; print(pl.classify_source(sys.argv[1]))" "<ref>"
```
Possible types: `arxiv`, `pdf_url`, `local_pdf`, `doi`, `openreview`,
`semantic_scholar`, `openalex`, `url`, `unknown`.

## Step 2 — resolve metadata into a normalized candidate (JSON)
- **arxiv**: `python3 scripts/fetch_arxiv.py --id <id-or-url>` → one candidate JSON line.
- **doi**: `python3 scripts/fetch_openalex.py --doi <doi>` (and/or `fetch_semantic_scholar.py --doi`).
- **openreview**: `python3 scripts/fetch_openreview.py --forum <id>` (extract id from the `?id=` param).
- **semantic_scholar / openalex page**: pull the id from the URL and use the matching fetcher.
- **pdf_url**: build a minimal candidate (title from the page or PDF after download);
  set `source=pdf_url`, `pdf_url=<url>`.
- **local_pdf**: build a minimal candidate; you'll attach the file via `--pdf <path>`.
- **manual metadata**: if the user supplied `title=...` etc., construct the candidate JSON by hand.
- Optionally enrich any candidate:
  `python3 scripts/fetch_openalex.py --enrich '<cand json>'` then
  `python3 scripts/fetch_semantic_scholar.py --enrich '<cand json>'`.

If you cannot resolve a title, still proceed — create the record with what's known
and mark missing fields "Not reported".

## Step 3 — ingest
```
python3 scripts/ingest.py --candidate '<candidate json>' [--pdf <url-or-local-path>]
```
- For arXiv with a `pdf_url`, pass `--pdf <pdf_url>` to download it.
- For a local PDF, pass `--pdf ./path.pdf` (it is copied into the version dir).
- ingest.py decides automatically whether this is a **new paper**, a **new version**
  (changed arXiv version / PDF sha256 / venue), or **unchanged**. To force a new
  version, add `--force-new-version`.
- It prints JSON with `canonical_key`, `version_dir`, `action`, `label`, `score`, and
  any `duplicate_candidates`.

## Step 4 — summarize
Follow the **summarize-paper** procedure on the returned `version_dir`:
```
python3 scripts/summarize_paper.py <version_dir> --prepare
# read the extraction, write <version_dir>/summary.md from the scaffold (English)
python3 scripts/summarize_paper.py <version_dir> --finalize --status full
```

## Step 5 — indexes + report
```
python3 scripts/update_indexes.py
python3 scripts/validate_registry.py
```
Report the created paper path, version, triage label + rationale, and flag any
duplicate candidates for the user to resolve (they are recorded in
`registry/duplicate_candidates.jsonl`; resolve via `registry/aliases.yaml` or
`/evolve-paper-system`).

## Updating to a new version
If the user points at a newer arXiv version (or a changed PDF) of a paper already in
the library, ingest.py will detect it and create `vN+1` automatically — never
overwriting the previous version's PDF/summary.
