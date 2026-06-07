# Summary component cheat-sheet

The curated vocabulary for authoring `summary.mdx` (ADR-0002 — no per-paper bespoke
components; to add a new one, PR it into `site/src/components/summary/` and document it
here). Components are provided **globally** — never import them in a summary. Render-time
behavior lives in the site; here is the authoring contract.

## Layout-rendered (you don't write these — the page renders them from frontmatter)
- **Metadata card + triage badge** — title, authors, venue, year, tags, `source_link`,
  triage label/confidence. Driven entirely by frontmatter, which the harness generates.

## Core blocks
| Component | Use | Example |
|---|---|---|
| `<TLDR>` | one-sentence takeaway (top of every summary) | `<TLDR>SWE-bench evaluates LLMs on real GitHub issues via hidden tests.</TLDR>` |
| `<WhyItMatters>` | 1–2 lines of relevance | `<WhyItMatters>Foundational for my SWE-agent track.</WhyItMatters>` |
| `<Pass title="…">` | collapsible depth (collapsed by default) | wrap method internals / full results |

## Semantic highlights — one colour per meaning (consistent across all summaries)
Use these for their MEANING, not decoration. Colours work in light + dark mode.

| Component | Colour | Meaning | Example |
|---|---|---|---|
| `<Problem>` | red | the problem the paper tackles / a prior-work limitation | `<Problem>prior benchmarks test only self-contained functions</Problem>` |
| `<Novelty>` | green | a novel module/approach/insight the paper introduces | `<Novelty>tests touched by the PR become an objective grader</Novelty>` |
| `<Finding src="Tab.X">` | teal | a finding / claim / result of THIS paper (+ anchor) | `<Finding src="Fig.5">difficulty correlates with context length</Finding>` |
| `<FollowUp>` | blue | a notion/thread the reader should follow up | `<FollowUp>how later scaffolds fix localization</FollowUp>` |
| `<Caveat>` | orange | a limitation of THIS paper | `<Caveat>Python-only, 12 repos</Caveat>` |
| `<Related>` | violet | related work / lineage | `<Related>enabled the SWE-agent line</Related>` |
| `<Term def="plain definition">term</Term>` | chip + hover tooltip | self-contained inline glossary | `<Term def="fail→pass tests gate success">execution-based</Term>` |

Legacy aliases still work: `<Claim>`→finding, `<Evidence src>`→finding, `<Limit>`→caveat,
`<Weak>`→amber (uncertain). Prefer the semantic names above.

## Data-driven interactive primitives (you supply data/props, not code)
| Component | Props | Use |
|---|---|---|
| `<KeyStats items={[{value,label,sub}]} />` | objects | scannable headline-number strip (put near the top) |
| `<SortableTable columns={[…]} rows={[[…]]} />` | string[] / (string\|number)[][] | **interactive** results table — click a header to sort (React island) |
| `<ResultsTable columns={[…]} rows={[[…]]} />` | string[] / string[][] | small static results table |
| `<ClaimEvidence rows={[{claim, evidence, verdict}]} />` | objects | claim→evidence→verdict map |
| `<Stepper steps={[{title, body}]} />` | objects | walk an algorithm/method |
| `<Chart kind="bar\|line" data={[{label, value}]} />` | objects | re-plot an extracted result |
| `<Figure src="…" caption="…" zoom />` | strings | a diagram/figure (image hosted in the version dir or remote) |
| `<MathBlock>…</MathBlock>` | KaTeX | a key equation |
| `<Compare a={…} b={…} />` | nodes | A/B contrast |
| `<SelfCheck q="…" a="…" />` | strings | a quick comprehension check |

## Rules
- **Concise + core-first:** the visible body is TL;DR → Motivation → Contribution →
  Research questions → Methodology → Main result → Implications → Limitations →
  Critiques. Push detail into `<Pass>`.
- **Self-contained:** define every non-universal term with `<Term>`.
- **Declarative English**, specific numbers + anchors, "Not reported"/"Unclear" for gaps.
- **Motivation ≠ Contribution** — keep them distinct.
- Preserve the `{/* NOTES_START */} … {/* NOTES_END */}` block (personal notes).
