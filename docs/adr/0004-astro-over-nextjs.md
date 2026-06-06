# 4. Astro (with React islands available) over Next.js for the reading site

Status: Accepted (2026-06-06)

## Context
The site framework (originally chosen in the planning session) was questioned: a
colleague suggested Next.js. The relevant constraints are fixed by earlier ADRs and the
requirements: the site is a **static, public** view (GitHub Pages), **content/reading-first**,
with a **low-JS / concise** goal, MDX summaries + a curated component library, and several
lab contributors. Two concerns were raised in favor of Next: React familiarity, and
React being "more interactive/customizable."

Key clarifications reached during the discussion:
- Astro is not an alternative to React — it **runs React** (and other UI frameworks) as
  **islands**. The interactivity/customizability ceiling inside Astro is identical to a
  React app; the difference is *where* JS is shipped.
- React component libraries (e.g. **shadcn/ui** = React + Radix + Tailwind) work in Astro
  via `@astrojs/react`, rendered as islands (coordinated interactive pieces grouped into a
  single island).
- On a **static** host, Next.js requires `output: 'export'`, which disables its main
  advantages (SSR, ISR, API routes, runtime data fetching) — so Next would add client
  weight without the server payoff.

## Decision
Stay on **Astro**. When richer interactivity is wanted, author those components in
**React via `@astrojs/react`** (and shadcn/Radix/Tailwind if desired) as islands — keeping
near-zero JS on reading pages while giving React DX. The site is already built and verified
on Astro (catalog + facet/sort + Pagefind + MDX component library, 48 pages).

## Consequences
- (+) Reading pages ship ~0 KB JS (islands); concise goal preserved.
- (+) Native content collections + MDX + Zod validation; Pagefind integration trivial.
- (+) React familiarity is satisfied *inside* Astro (React islands, shadcn) — the "React
  shop" concern does not require Next.
- (−) Contributors touch some `.astro` (layouts/static components); interactive parts can
  be pure React to limit this.
- **Revisit if** the project becomes app-like / needs server features (auth-gated access,
  a runtime search API, ISR, accounts) — that would favor Next *and* change the hosting
  decision (ADR-0003). For a static public reading library, it does not apply.
- **Overriding factor acknowledged:** if the team genuinely will not maintain Astro, that
  maintainability concern could reverse this; mitigated by writing interactive components
  in React.
