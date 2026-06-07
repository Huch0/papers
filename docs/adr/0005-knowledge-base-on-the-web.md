# 5. Knowledge base on the web — read-only view, Claude-Code chat, Concept/Q&A split

Status: Accepted (2026-06-07)

## Context
We want the knowledge base in the web interface and this workflow: read a summary →
discuss the paper with an agent → the agent answers and updates the KB → the related
knowledge is reachable from the paper's web page and browsable like the paper library,
densely cross-linked to other knowledge and the source paper.

Constraints: the Website is a static, public, read-only Derived view (ADR-0001, ADR-0003)
— no server. The KB already exists locally: `knowledge/concepts/*.md` (bidirectionally
linked to papers), `knowledge/sessions/`, `scripts/knowledge.py`, and the `/paper-tutor`
skill that already chats about a paper and writes concepts.

## Decision
- **Chat happens in Claude Code** (`/paper-tutor`), not in the browser. The Website renders
  a **read-only view** of the KB. No in-browser LLM/backend (that would need a server, an
  API key, per-user cost, and auth — out of scope; revisit only with an authenticated,
  non-static deployment).
- **Two distinct entities:**
  - **Concept** — reusable, cross-paper understanding; `.mdx` under `knowledge/concepts/`;
    its own `/knowledge/<slug>/` page; browsable in a knowledge catalog (`/knowledge/`,
    parallel to the paper library) with tag / linked-count / recency facets + Pagefind.
  - **Q&A** — paper-scoped questions+answers; `library/<slug>/vN/qa.mdx`; rendered on the
    paper page in a "Questions & Discussion" panel; each item links out to Concept(s).
  - **Session** — raw transcript under `knowledge/sessions/`; local provenance, not rendered.
- **Dense linking:** structured frontmatter (`related_concepts`/`related_papers`,
  reciprocal) + inline `[[wiki-links]]`; build-time **"Referenced by" backlinks** from all
  sources (concepts, papers, Q&A). Visual graph view deferred.
- **Authoring:** `.mdx` for concepts and `qa.mdx`, self-verified with `check-mdx` before
  the tutor finishes; `knowledge.py` emits `.mdx` and gains a `qa-add` helper.

## Consequences
- (+) Reuses `/paper-tutor` and the static pipeline; stays free/public; coherent with
  ADR-0001/0003. Delivers the dense paper⇄Q&A⇄Concept⇄paper graph + backlinks.
- (−) The "talk to the agent" step is in the terminal; the web reflects it after a rebuild
  (local `dev` hot-reloads; deploy via push).
- (−) Lab-mates without Claude Code can *read* the KB but cannot chat to extend it — that
  would require the deferred in-browser-chatbot + backend.
