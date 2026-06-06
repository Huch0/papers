# Reading-site requirements

Status: Agreed via grilling session (2026-06-06). Companion to `CONTEXT.md` (glossary)
and `docs/adr/0001–0003`. Implementation-level; decisions live in the ADRs.

## 1. Goal & scope
A human-friendly **Website** to search/filter/sort and *read* paper **Summaries** across
computers and phones, for a small lab whose members add papers to one git repo. The site
is a **read-only Derived view** over the existing **Harness** (ADR-0001) — it adds no
paper data of its own. Public readership on GitHub Pages.

## 2. Guiding principles
- **Harness/YAML stays authoritative; the site is derived & disposable.** (ADR-0001)
- **Summaries are curated-component MDX — no per-paper bespoke code.** (ADR-0002)
- **Derived artifacts are generated in CI, never committed; `main` always builds via PR gate.** (ADR-0003)
- **Concise, core-first Summaries**; depth is available but collapsed.
- **Claude Code is a power-tool, not a requirement** — Python + a text editor suffices to contribute.

## 3. Repository layout (monorepo)
```
papers/                       ← the one repo colleagues clone
  config/  library/  registry/  knowledge/  scripts/  .claude/   ← Harness (authoritative)
  config/summary_template.mdx        ← canonical Summary structure
  config/summary_components.md        ← component cheat-sheet (agents + humans author against this)
  site/                       ← Astro app (the Website)
    src/{components,layouts,pages,content.config.ts,styles}
    package.json (Bun)  astro.config.mjs
  docs/{website-requirements.md, adr/}
  .github/workflows/          ← PR gate + deploy
  CONTEXT.md
```

## 4. Data flow
```
metadata.yaml (authoritative)
   ├─ harness generates ─▶ registry/papers.jsonl ──▶ site Catalog (search/filter/sort)
   └─ harness generates ─▶ summary.mdx frontmatter (display subset)
summary.mdx body (human/agent authored) ─▶ Astro content collection ─▶ Summary page
Catalog entry ── join on canonical_key ──▶ Summary page
```

## 5. Functional requirements
### 5.1 Catalog (R-CAT)
- R-CAT-1: List all papers from `registry/papers.jsonl` (single metadata feed).
- R-CAT-2: **Faceted filter** by venue, year, authors, tags, topic groups, triage label; **sort** by date / score / year / title — a single client-side island over the JSON (no backend).
- R-CAT-3: **Full-text search** over rendered Summary content via **Pagefind** (lazy-loaded, chunked WASM index; no full corpus in the browser). Composes with facets.
- R-CAT-4: Each entry links to its Summary page; shows triage badge, venue/year, tags, source link.

### 5.2 Summary rendering (R-REND)
- R-REND-1: Render `summary.mdx` (and legacy `summary.md`) from a content collection globbing `../library/**/summary.{md,mdx}` (Astro 5 Content Layer; no copy step).
- R-REND-2: **Core-first layout** — visible by default: `<Meta>`+`<TriageBadge>`, TL;DR, Motivation, Contribution, Research questions, Methodology, Main result, Implications, Limitations, Critiques & Questions.
- R-REND-3: **Depth collapsed** — full results table, claim→evidence mapping, method internals behind `<Pass>`/`<Tabs>`/expanders.
- R-REND-4: **Self-contained** — non-universal terms defined via inline hover `<Term def="…">` (zero added visible length).
- R-REND-5: Mobile-friendly, fast (ship ~zero JS on reading pages except hydrated islands).

### 5.3 Summary authoring (R-AUTH)
- R-AUTH-1: Canonical structure in `config/summary_template.mdx`; sections per R-REND-2.
- R-AUTH-2: `summarize_paper.py --format mdx --prepare` scaffolds frontmatter (generated from `metadata.yaml`) + section skeleton; author writes only the body.
- R-AUTH-3: **Two paths, same output:** (a) Claude Code `summarize-paper` skill; (b) human writes MDX against `config/summary_components.md`. CI validates both identically.
- R-AUTH-4: Keep the rigor — Motivation **≠** Contribution(novelty: delta + mechanistic why); claims separated from evidence; figure scrutiny — but written tersely and demoted behind disclosure.

### 5.4 Component library (R-COMP) — ADR-0002
- R-COMP-1: Curated, globally auto-provided to all MDX (no per-file imports → low token/boilerplate).
- R-COMP-2: v1 set: structural (`<Meta>`, `<TriageBadge>`, `<Pass>`, `<Tabs>`, `<Glossary>`/`<Term>`, `<ResultsTable>`, `<ClaimEvidence>`); epistemic marks (`<Claim>`, `<Evidence src>`, `<Weak>`, `<Limit>`); data-driven interactive primitives (`<Stepper>`, `<Chart kind data>`, `<Figure zoom>`, `<MathBlock>`, `<Compare>`, `<SelfCheck>`).
- R-COMP-3: New interactions are added to the **shared library via PR** (reusable), never as per-paper code.
- R-COMP-4: Maintain `config/summary_components.md` as the authoritative cheat-sheet for agents + humans.

## 6. Non-functional requirements
- R-NF-1 (Security): no agent/colleague executable code in summaries; only curated components run.
- R-NF-2 (Determinism): index/feed generation deterministic (stable sort; drop the `INDEX.md` generated-at timestamp from the site feed).
- R-NF-3 (Resilience): a malformed paper fails its PR, never `main`.
- R-NF-4 (Performance): Pagefind lazy-loaded; reading pages near-zero JS; catalog island only.
- R-NF-5 (Accessibility/mobile): responsive layout; keyboard-navigable facets/search.

## 7. Build, CI & deploy (ADR-0003)
- R-BD-1: Local dev under **Bun** (`bun run dev`); a `predev`/`prebuild` hook runs `update_indexes.py` first.
- R-BD-2: CI build under **Node 20** (Astro/Pagefind/MDX validated on Node).
- R-BD-3: PR gate (required checks, in order): `validate_registry.py` → `knowledge.py validate` → `update_indexes.py` → `astro build` (+ Pagefind). Any red ⇒ PR blocked.
- R-BD-4: Publish via the **`gh-pages` branch**; production at root.
- R-BD-5: **Free PR previews** at `/pr-preview/pr-<N>/` via `rossjrw/pr-preview-action`; auto-cleanup on close. Requires correct Astro `base`/relative URLs. Fork PRs get no preview → colleagues are repo collaborators.

## 8. Collaboration & git policy (ADR-0003)
- R-COL-1: **Committed (authoritative):** `config/`, `library/**/{paper.yaml, vN/metadata.yaml, vN/summary.{md,mdx}}`, `knowledge/`, `site/src/`, `docs/`, `CONTEXT.md`.
- R-COL-2: **Git-ignored (derived/local):** `registry/papers.jsonl`, `indexes/*.md`, `registry/catalog.sqlite`, `library/**/paper.pdf`, `library/**/extraction.txt`, `site/dist/`, `node_modules/`.
- R-COL-3: PDFs are **not shared** — the site links to **Source links** (arXiv/venue); downloaded PDFs stay local-only Harness inputs.
- R-COL-4: PR-based workflow; conflict-free adds (each paper is its own folder).

## 9. Frontmatter & schema (R-FM)
- R-FM-1: `summary.mdx` frontmatter = join keys (`canonical_key`, `version_key`) + display subset (`title`, `triage_label`, `triage_confidence`, `venue`, `year`, `tags`, `authors`, `source_link`, `summary_date`), all generated from `metadata.yaml`.
- R-FM-2: Astro content-collection **Zod schema** mirrors that frontmatter; validates at build. Contract is one-directional (YAML → frontmatter → Zod); mismatch fails CI.

## 10. Migration plan (R-MIG)
- R-MIG-1: Render `.md` and `.mdx` side-by-side; the 42 legacy `.md` show immediately as plain summaries. **No bulk rename** (`<`/`{` break MDX).
- R-MIG-2: **Lazy migration** — `.mdx` is default for new + regenerated summaries; corpus migrates as papers are revisited.
- R-MIG-3: **Regenerate the 5 experimental `.html` → `.mdx`** in the new concise template (removes the HTML render path); retire `summary_template.html`.
- R-MIG-4: Retire the long `summary_template.md`; `summary_template.mdx` is canonical.

## 11. Harness changes required
- `git init` + GitHub remote; add `.gitignore` per R-COL-2.
- `summarize_paper.py`: add `--format mdx` (frontmatter scaffold from YAML); make `update_indexes.py` site-deterministic (drop generated-at line for the feed); extend `papers.jsonl` with `abstract`, full `authors`, `source_link`.
- New `config/summary_template.mdx` + `config/summary_components.md`.
- Update `summarize-paper` skill to author MDX in the concise structure.

## 12. Non-goals (v1)
- Hosting/redistributing PDFs. Server-side rendering or a database. Auth/private access. User accounts/comments in-app (use PRs/issues). Editing paper data through the website.

## 13. Open / deferred decisions
- Exact v1 component prop APIs; charting lib for `<Chart>`; KaTeX vs MathML.
- Theming / dark mode; catalog visual design.
- Whether the knowledge base (`knowledge/concepts`) also gets a site view (likely v2).
- Analytics (privacy-respecting, optional).

## 14. Phased delivery
1. **Harness prep:** git init + `.gitignore`; `--format mdx`; deterministic feed; extend `papers.jsonl`; templates + cheat-sheet.
2. **Site skeleton:** Astro app under `site/`; content collection glob + Zod; render one `.mdx` end-to-end.
3. **Component library v1** (R-COMP-2) + concise template; regenerate the 5 `.html`.
4. **Catalog:** JSON facet/sort island + Pagefind.
5. **CI + deploy:** PR gate, gh-pages publish, PR previews.
6. **Docs:** contributor guide (both paths); link from README.

---
ADR index: [0001 website is a derived view](adr/0001-website-is-a-derived-view.md) ·
[0002 curated-only components](adr/0002-curated-only-summary-components.md) ·
[0003 derived-in-CI + Pages previews](adr/0003-derived-in-ci-and-pages-branch-previews.md).
Glossary: [CONTEXT.md](../CONTEXT.md).
