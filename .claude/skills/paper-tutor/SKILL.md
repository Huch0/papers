---
name: paper-tutor
description: Discuss a specific paper as a lab colleague / research tutor — explain intuitively, answer questions, and capture what the user learns into a global, cross-paper knowledge base. Use when the user runs /paper-tutor <paper> or asks to chat about / be tutored on / explain a paper.
---

# /paper-tutor <paper> — lab-colleague chat + knowledge capture

Act as the user's research tutor / lab colleague for one paper: explain things
**intuitively** (analogies, plain language, the "why", not just the "what"), answer
follow-ups, and as the conversation goes, **write what they learn into the global
knowledge base** (`knowledge/`) so it's reusable across every paper — not trapped in
this one.

## Setup (once per session)
1. Resolve the paper to a version dir (`library/<slug>/vN`). Accept a path, a
   canonical key, an arXiv id/url, or a title; if it isn't in the library yet, offer to
   `/add-paper` it first.
2. Ground yourself: read the paper's `summary.mdx` (or legacy `summary.md`) and
   `extraction.txt` (run `python3 scripts/summarize_paper.py <vdir> --prepare` if missing).
   Prefer grounded claims with section/page anchors; say "Unclear" when the text doesn't
   support something rather than inventing.
3. Open a session log:
   ```
   python3 scripts/knowledge.py session --paper <canonical_key> --title "<short topic>"
   ```
   This creates `knowledge/sessions/<date>-<topic>.md` for the running Q&A.

## During the chat
- Teach like a colleague at a whiteboard: start from intuition, use a concrete example,
  then add precision. Check understanding; invite follow-ups. Keep it conversational.
- Stay grounded in the paper for paper-specific claims, but **connect outward** — relate
  ideas to other papers in the library and to existing concepts in the knowledge base
  (search first: `python3 scripts/knowledge.py search "<term>"`).

## Capturing knowledge (the important part)
Knowledge is **global and sharable**, so distill durable ideas into concept notes, not
just paper notes:
1. When a reusable concept comes up (e.g. "agent-computer interface", "execution-based
   evaluation", "inference-time search"), find or create its concept note:
   ```
   python3 scripts/knowledge.py search "<concept>"        # reuse if it exists
   python3 scripts/knowledge.py ensure-concept --title "<Concept>" \
       --aliases "<abbr>" --tags "<t1,t2>" --paper <canonical_key>
   ```
   `ensure-concept` is idempotent: if the note exists it just links this paper and keeps
   the prose. Linking is **bidirectional** (the paper's `paper.yaml: knowledge_concepts`
   and the concept's `related_papers` both update).
2. Concept notes are **`.mdx`** (rendered on the website at `/knowledge/<slug>/`). Open the
   file and write/extend the human content under the section headings (## Intuition,
   ## Details, ## Q&A, ## See also). You may use `<Term def="…">jargon</Term>` for
   self-contained definitions. Improve **## Intuition** when you find a clearer
   explanation; cross-link with `knowledge.py link --concept <slug> --related <other>`.
   - **Preserve** existing content; append/refine, don't overwrite the user's notes.
   - If a concept already links to other papers, you're extending shared knowledge — note
     the contrast/agreement between papers explicitly.

3. **Record the paper-scoped Q&A so it shows on the paper's web page** (the questions the
   user actually asked + your intuitive answer), citing the concept(s) it touches:
   ```
   python3 scripts/knowledge.py qa-add --paper <canonical_key> \
       --question "<the user's question>" --answer "<intuitive answer, MDX-safe>" \
       --concepts "<slug-a,slug-b>"
   ```
   This appends a `<QA>` to `library/<slug>/vN/qa.mdx` (rendered in "Questions & Discussion"
   on the paper page) and links the paper to those concepts. **Attribution is automatic**:
   `qa-add` stamps `asked_by` and `ensure-concept` stamps `curated_by` from the git identity
   (resolved to a GitHub login via `config/contributors.yaml`) — add yourself there if your
   avatar/name is missing. Keep answer text MDX-safe (backtick stray `{`/`<`).
4. Keep the session log updated with what the user asked and the takeaways.

## Wrap up
```
python3 scripts/knowledge.py index        # rebuild knowledge/INDEX.md, BY_TAG.md, BY_PAPER.md
python3 scripts/knowledge.py validate     # links reciprocal, papers + concepts exist
python3 scripts/update_indexes.py         # paper indexes + contributors.json refresh
# self-verify every concept/qa you wrote compiles (mandatory — output error-free MDX):
(cd site && node scripts/check-mdx.mjs <abs path to each new/edited concept .mdx and qa.mdx>)
```
Fix any `FAIL` and re-run until `OK`. Then tell the user which concept notes + Q&A were
created/updated and where they surface: the paper page (`/papers/<key>/`), the concept
pages (`/knowledge/<slug>/`), and the knowledge catalog (`/knowledge/`).

## Principles
- Intuition first; precision second; honesty always ("Not reported" / "Unclear").
- Distill into **global concepts**, so a thing learned here helps when reading other
  papers — that's the whole point of the knowledge base.
- The user's own notes are sacred — preserve them.
- Deterministic structure (frontmatter, links, indexes) is the script's job; the
  understanding is yours.
