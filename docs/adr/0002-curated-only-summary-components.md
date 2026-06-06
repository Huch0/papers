# 2. Summaries use a curated, shared interactive component library only

Status: Accepted (2026-06-06)

## Context
Summaries are authored in MDX (ADR-0001) and we want rich, paper-specific interactivity,
authored largely by Claude Code summarization sub-agents (and human colleagues). MDX is
code: it executes JSX at build and ships JavaScript to every visitor of a public static
site, and Astro builds all pages together (one bad component fails the whole build).

Options considered:
- (a) Free-form per-paper components — sub-agents/colleagues write arbitrary component
  code colocated with each summary.
- (b) Two-tier — curated library + a guard-railed bespoke escape hatch (client-only,
  allowlisted deps, error-boundaried, PR-reviewed).
- (c) Curated-only — a rich, globally-provided set of data-driven interactive primitives;
  no per-paper component code.

## Decision
Adopt **(c)**. The Website provides a rich, curated, globally-auto-provided component
vocabulary (epistemic marks, structural blocks, and data-driven interactive primitives
such as tabs, steppers, charts-from-extracted-data, math, compare, self-check). Authors —
human or agent — get paper-specific expressiveness by **composing primitives with
paper-specific data/props**, never by authoring new executable code per summary. A
genuinely new interaction is added to the **shared library via PR** and is then reusable.

## Consequences
- (+) No agent- or colleague-authored executable code is ever published; the per-paper
  code-injection / supply-chain / build-fragility surface is eliminated.
- (+) Consistent UX, low token + maintenance cost, library value compounds.
- (−) Expressiveness ceiling: a novel interaction waits on a (reviewed) library addition
  rather than being produced per paper.
- (−) Requires a maintained **component reference** that the `summarize-paper` skill and
  human contributors author against, and a lightweight governance path for additions.
