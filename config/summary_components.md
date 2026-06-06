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

## Inline epistemic marks
| Component | Meaning | Example |
|---|---|---|
| `<Claim>` | a claim the paper makes | `<Claim>matches human-level on MiniWoB++</Claim>` |
| `<Evidence src="Tab.3, p.8">` | supporting evidence + anchor | `<Evidence src="Tab.2">73.0% vs 16.2%</Evidence>` |
| `<Weak>` | unclear / weak / caveated | `<Weak>single run, no variance</Weak>` |
| `<Limit>` | a limitation / risk | `<Limit>Python-only, 12 repos</Limit>` |
| `<Term def="plain definition">term</Term>` | self-contained inline glossary (hover) | `<Term def="fail→pass tests gate success">execution-based</Term>` |

## Data-driven interactive primitives (you supply data/props, not code)
| Component | Props | Use |
|---|---|---|
| `<ResultsTable columns={[…]} rows={[[…]]} />` | string[] / string[][] | numeric results |
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
