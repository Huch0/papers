# Contributing

How to contribute to **papers** — for humans and for their coding agents. Read
[CLAUDE.md](CLAUDE.md) for the non-negotiable data-integrity rules; this file is the
practical workflow.

---

## 0. Before you start

- **Prereqs:** Python 3.11+, Node 20+ (or Bun), `gh` CLI (authenticated), Claude Code
  (for the skills). `pip install -r requirements.txt` for the Python side; `cd site &&
  npm install` for the website.
- **Add yourself for attribution.** Edit `config/contributors.yaml`:
  ```yaml
  by_email:
    you@example.com: { github: your-gh-login, name: Your Name }
  ```
  Find your git email with `git config user.email`. Your GitHub login (never your email)
  is stamped into anything you author (`curated_by` / `asked_by`) and shown on the site
  with your avatar. This is the only place raw emails live; it is not published.
- **Track your reading.** The site has a per-reader read/unread tracker — mark summaries
  read, filter the catalog to your unread, and optionally sync across devices via a private
  Gist (needs a `gist`-scoped token). See **README → "Reading tracker"**. It's per-browser
  and never committed.

---

## 1. Golden rules (see CLAUDE.md for the full list)

- **Authoritative data** is the per-paper YAML + colocated MDX under `library/` and the
  concepts under `knowledge/`. `registry/`, `indexes/`, `knowledge/{INDEX,BY_*}.md`, and
  `site/dist/` are **derived** — regenerate, never hand-edit.
- **Never overwrite a PDF or summary for a new version** — a new arXiv version / changed
  PDF / changed venue is a **new `vN` directory** (use `scripts/ingest.py`).
- **Summaries are English, analytical, and grounded** (claim vs evidence vs unclear; page
  anchors). Use `"Not reported"` / `"Unclear"` instead of guessing.
- **User notes are sacred** — append/refine, never overwrite prose in summaries/concepts.
- **Route preferences into `config/`** (via `/evolve-paper-system`), not into hidden
  behavior.

---

## 2. Branch & PR workflow (required)

`main` is **branch-protected**: no direct pushes, a pull request is required to merge
(**no reviewer required — you merge your own PR**). This applies to everyone, including
admins and agents.

```bash
git checkout -b feat/short-description        # or summaries/…, docs/…, fix/…
# … make your changes …

# validate before pushing:
python3 scripts/validate_registry.py          # exit 0 = no errors
python3 scripts/knowledge.py validate         # if you touched knowledge/
python3 scripts/update_indexes.py             # refresh derived indexes
(cd site && npm run build)                     # must be green

git add -A && git commit -m "summary: add Foo et al. (arxiv-XXXX)"
git push -u origin feat/short-description
gh pr create --fill
gh pr merge --merge --delete-branch            # or use the GitHub UI
```

End commit messages with the trailer the repo uses:
`Co-Authored-By: …`. CI builds the site and deploys to GitHub Pages on merge to `main`.

> Agents: you **cannot** `git push origin main`. Always branch → PR → merge.

---

## 3. Add a summary

**With Claude Code (preferred):**
```
/summarize-paper <paper>        # canonical key, arXiv id/url, version dir, or title
```
The skill prepares extraction, writes `library/<slug>/vN/summary.mdx` from
`config/summary_template.mdx`, **self-verifies with `check-mdx`**, stamps `curated_by`,
and finalizes.

**By hand:**
```bash
python3 scripts/summarize_paper.py <version_dir> --prepare --format mdx   # extract + scaffold
# write the body in summary.mdx using config/summary_template.mdx + config/summary_components.md
node site/scripts/check-mdx.mjs "$PWD/<version_dir>/summary.mdx"          # must print OK
python3 scripts/summarize_paper.py <version_dir> --finalize --format mdx
```
Keep it **concise, core-first**, with a mandatory `## Key findings` section, semantic
highlights (`<Problem>/<Novelty>/<Finding>/<FollowUp>/<Caveat>/<Related>`), and a
self-contained `<Term>` glossary. Verify every number against `extraction.txt`. See
`.claude/skills/summarize-paper/SKILL.md` for the authoritative checklist.

---

## 4. Add Q&A (paper-scoped, shows on the paper page)

Use `/paper-tutor <paper>` — discuss the paper and it records the questions you asked +
intuitive answers. Or directly:
```bash
python3 scripts/knowledge.py qa-add --paper <canonical_key> \
  --question "Why does X happen?" --answer "Because … (MDX-safe text)" \
  --concepts "concept-slug-a,concept-slug-b"
```
This appends a `<QA asked_by=… concepts=…>` to `library/<slug>/vN/qa.mdx`, links the paper
to the cited concepts, and renders in the **"Questions & Discussion"** panel. Run
`check-mdx` on the `qa.mdx` afterward.

---

## 5. Add knowledge (global, cross-paper concepts)

Concepts live in `knowledge/concepts/<slug>.mdx` and are reused across papers. Easiest via
`/paper-tutor`; or directly:
```bash
python3 scripts/knowledge.py search "agent-computer interface"   # reuse if it exists
python3 scripts/knowledge.py ensure-concept --title "Agent-Computer Interface" \
  --aliases ACI --tags agent-harness --paper <canonical_key>
# edit the .mdx body (## Intuition / Details / Q&A / See also); <Term> for jargon
python3 scripts/knowledge.py link --concept <slug> --related <other-slug>
node site/scripts/check-mdx.mjs "$PWD/knowledge/concepts/<slug>.mdx"   # OK
python3 scripts/knowledge.py index && python3 scripts/knowledge.py validate
```
Links are **bidirectional** and validated; the concept page shows **Linked papers**,
**Related concepts**, and build-time **Referenced by** backlinks.

---

## 6. Add or use a skill

- **Use:** in Claude Code, type the slash command (e.g. `/triage-papers`). The available
  skills are in `.claude/skills/` (see the table in [README.md](README.md)).
- **Add:** create `.claude/skills/<name>/SKILL.md` with frontmatter:
  ```markdown
  ---
  name: my-skill
  description: One line — what it does and when to use it (this is how it's discovered).
  ---
  # /my-skill — …
  …procedure…
  ```
  Put **deterministic work in `scripts/`** (import `scripts/paperlib.py`; don't re-derive
  keys/paths) and let the skill orchestrate; the agent does the reading/judgment. If the
  skill changes scoring/tagging/layout behavior, put that in `config/` instead of
  hard-coding it. Test it, then PR.

---

## 7. The validation gates (run before every PR)

| Command | Checks |
|---|---|
| `python3 scripts/validate_registry.py` | Metadata integrity (required after any data/script change) |
| `python3 scripts/knowledge.py validate` | Concept/Q&A frontmatter, link reciprocity, dangling links |
| `node site/scripts/check-mdx.mjs <file>` | Each summary/concept/`qa.mdx` compiles (no MDX errors) |
| `python3 scripts/update_indexes.py` | Regenerate `registry/` + `indexes/` + `knowledge/` indexes |
| `(cd site && npm run build)` | The whole site builds green |

If validation reports **ERRORS**, fix them — don't open the PR claiming success. A
PostToolUse hook also runs validation automatically after edits under `library/`,
`config/`, `registry/`.

---

## 8. What not to commit

Derived artifacts and PDFs are git-ignored and regenerated by CI: `registry/papers.jsonl`,
`registry/catalog.sqlite`, `registry/contributors.json`, `site/dist/`, and `*.pdf`. The
site **links** to sources; it never hosts PDFs.
