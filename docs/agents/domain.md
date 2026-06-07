# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring
the codebase. This repo is **single-context**.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root (the project glossary).
- **`docs/adr/`** — read ADRs that touch the area you're about to work in (currently
  ADR-0001 … 0005).

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't
suggest creating them upfront. The producer skill (`/grill-with-docs`) creates them lazily
when terms or decisions actually get resolved.

## File structure (single-context)

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-website-is-a-derived-view.md
│   ├── 0002-curated-only-summary-components.md
│   └── …
└── scripts/ library/ knowledge/ site/ …
```

(If a `CONTEXT-MAP.md` ever appears at the root, this repo has become multi-context —
read each per-context `CONTEXT.md` it points to, plus any `src/<context>/docs/adr/`.)

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a
hypothesis, a test name), use the term as defined in `CONTEXT.md` (e.g. Harness,
Authoritative record, Derived view, Summary, Concept, Q&A). Don't drift to synonyms the
glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're
inventing language the project doesn't use (reconsider) or there's a real gap (note it for
`/grill-with-docs`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently
overriding:

> _Contradicts ADR-0001 (website is a derived view) — but worth reopening because…_
