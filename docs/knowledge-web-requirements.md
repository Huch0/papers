# Knowledge-base web integration — requirements

Status: Agreed via grilling session (2026-06-07). Companion to `CONTEXT.md` and
`docs/adr/0005`. Builds on the existing site (ADR-0001/0002/0003/0004) and KB
(`knowledge/`, `scripts/knowledge.py`, `/paper-tutor`).

## 1. Goal & workflow
Read a summary → discuss the paper with `/paper-tutor` (in Claude Code) → the agent
answers intuitively and updates the KB → the related **Q&A** shows on the paper's web page
and the **Concepts** are browsable like the paper library, densely cross-linked to each
other and to the source paper.

## 2. Principles (ADR-0005)
- Chat in Claude Code; the Website is a **read-only** view of the KB (no in-browser LLM).
- **Concept** = global, cross-paper, paged, browsable. **Q&A** = paper-scoped, on the
  paper page, links to Concepts. **Session** = local provenance, not rendered.
- Dense linking: structured frontmatter + `[[wiki-links]]` + build-time backlinks.
- Authoring is `.mdx`, self-verified with `check-mdx` before finalizing.

## 3. Entities (see CONTEXT.md)
| Entity | Stored | Web surface | Scope |
|---|---|---|---|
| Concept | `knowledge/concepts/<slug>.mdx` | `/knowledge/<slug>/` + `/knowledge/` catalog | global, cross-paper |
| Q&A | `library/<slug>/vN/qa.mdx` | "Questions & Discussion" panel on the paper page | one paper version |
| Session | `knowledge/sessions/<date>-…md` | none (provenance) | one conversation |

## 4. Functional requirements
### 4.1 Knowledge catalog & concept pages (R-KC)
- R-KC-1: `concepts` Astro content collection globbing `../knowledge/concepts/*.{md,mdx}`,
  Zod schema = `name,title,aliases,tags,related_papers,related_concepts,created,updated`
  (dates as quoted strings).
- R-KC-2: **`/knowledge/`** catalog — React island listing all concepts; facets **tag**,
  **#linked-papers**, **recency(updated)**; sort; Pagefind full-text (scoped to concepts).
- R-KC-3: **`/knowledge/<slug>/`** concept page — render Intuition/Details/Q&A/See-also;
  metadata card with tags, **Linked papers**, **Related concepts**.
- R-KC-4: Header nav gains **"Knowledge"** beside "Catalog" (two parallel libraries).

### 4.2 Paper-page integration (R-PP)
- R-PP-1: `qa` content collection globbing `../library/**/qa.mdx` (frontmatter
  `canonical_key,version_key`); the paper page renders its Q&A entry in a
  **"Questions & Discussion"** panel via a `<QA question="…" concepts="…">…</QA>` component
  (concepts → links to `/knowledge/<slug>/`).
- R-PP-2: Paper page shows a **"Related concepts"** list (from `knowledge_concepts`).
- R-PP-3: Paper page shows a **"Discuss this paper in Claude Code"** block with the exact
  copyable command (`/paper-tutor <canonical_key>`).

### 4.3 Linking & backlinks (R-LK)
- R-LK-1: `[[concept-slug]]` wiki-links (remark plugin) resolve to `/knowledge/<slug>/`,
  render the concept title, and flag unknown slugs at build.
- R-LK-2: structured frontmatter `related_concepts`/`related_papers` (reciprocal via
  `knowledge.py`) drive lists + facets.
- R-LK-3: build-time **"Referenced by"** backlinks on each concept page, aggregated from
  other concepts (`related_concepts` + inline `[[…]]`), papers (`knowledge_concepts`), and
  Q&A (`concepts="…"`).
- R-LK-4: visual graph view — **deferred**.

### 4.4 Search (R-SR)
- R-SR-1: Pagefind indexes concept pages (free); tag pages `data-pagefind-filter="type:concept|paper"`
  so the paper catalog returns papers and the knowledge catalog returns concepts.

## 5. Tutor → web loop (R-TW)
- R-TW-1: `/paper-tutor <paper>` writes three artifacts: (a) appends `<QA>` items to the
  version dir's `qa.mdx`; (b) creates/extends Concept `.mdx` (Intuition/Details, `[[links]]`,
  reciprocal frontmatter); (c) a `knowledge/sessions/` transcript.
- R-TW-2: every authored `.mdx` must pass `check-mdx` before the skill finishes.
- R-TW-3: local `bun run dev` hot-reloads `library/**/qa.mdx` and `knowledge/concepts/**`;
  publishing = commit + push → existing CI (runs `update_indexes` + `knowledge.py index`
  + build + deploy).

## 6. Harness changes (R-HC)
- R-HC-1: `knowledge.py ensure-concept` emits **`.mdx`** (generated frontmatter); migrate
  the existing `.md` concept.
- R-HC-2: add `knowledge.py qa-add --paper <key> --question … --answer … --concepts …`
  that appends a `<QA>` to `qa.mdx` and reciprocally links the paper ↔ concepts.
- R-HC-3: extend `knowledge.py validate` — concept/qa frontmatter, `[[…]]`/`concepts="…"`
  resolve, reciprocity; keep `knowledge/{INDEX,BY_TAG,BY_PAPER}.md` generated.
- R-HC-4: update `/paper-tutor` skill to the three-artifact `.mdx` + self-verify contract.

## 7. Non-goals (v1)
In-browser chatbot / backend / LLM key. Editing the KB from the web. A visual graph view.
Rendering Session transcripts on the web.

## 8. Phased plan
1. **Harness:** `knowledge.py` → `.mdx` + `qa-add` + extended validate; migrate the 1
   existing concept; update `/paper-tutor`.
2. **Site collections:** `concepts` + `qa` content collections (Zod); wiki-link remark
   plugin; `<QA>` component.
3. **Concept pages + `/knowledge/` catalog** (mirror the paper library) + nav.
4. **Paper-page panels:** Q&A, Related concepts, "Discuss in Claude Code".
5. **Backlinks** ("Referenced by") + Pagefind type-scoping.
6. **Seed & verify:** run `/paper-tutor` on a paper (e.g. Mind2Web) end-to-end; build green; deploy.

---
ADR: [0005 knowledge base on the web](adr/0005-knowledge-base-on-the-web.md). Glossary:
[CONTEXT.md](../CONTEXT.md) (Knowledge base, Concept, Q&A, Session).
