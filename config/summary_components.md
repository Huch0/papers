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
| `<Definition term="…">` | formal, mathematical definition (textbook register) | `<Definition term="Marginal velocity field"><MathBlock>…</MathBlock></Definition>` |

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
| `<MathBlock>…</MathBlock>` | KaTeX | a key **display** equation |
| `<M tex="…" />` | KaTeX | **inline** math inside prose (`<M tex="q_t" />`, `<M tex="\pi(a \mid o)" />`) |
| `<FlowMatch />` | none | **interactive** flow-matching explainer: toy 2-D noise→data transport with a t-slider; generate/train views plus a **field view** rendering the toy's exact marginal field as an arrow grid (convention t=0 noise → t=1 data) |
| `<AttnMask />` | none | **interactive** attention-mask explorer for chunked/causal DiTs: training window, block-causal-over-chunks, and KV-cache views with an observation-overwrite toggle; hover a query row to read its receptive field |
| `<Compare a={…} b={…} />` | nodes | A/B contrast |
| `<SelfCheck q="…" a="…" />` | strings | a quick comprehension check |

## Math
Both math components render with KaTeX **at build time** (no client JS, no CDN). Two
authoring forms, chosen to survive MDX escaping:
- `tex="…"` prop — preferred for inline. JSX attribute strings are literal, so single
  backslashes are safe: `<M tex="\pi(o_{t:t+H} \mid o_{0:t},\, c,\, q_t)" />`. The only
  character you cannot use inside is a double quote.
- Template-literal child — preferred for long display equations, and what existing
  summaries use: <code>&lt;MathBlock&gt;&#123;`\\pi(x) = \\sum_i w_i`&#125;&lt;/MathBlock&gt;</code>
  (backslashes doubled inside the JS string).

Never write math as a plain backtick code span — it renders as monospace text, not math.
If KaTeX cannot parse an expression the component falls back to the raw source (styled
`.mathblock-raw` / `.math-raw`) instead of breaking the page, so a bad equation is visible
but harmless.

## Diagrams
Inline `<svg>` mechanism diagrams are allowed directly in the MDX body (they are markup,
not bespoke components). Follow the house style: size via `viewBox` + `style="width:100%;height:auto"`,
strokes/text in `currentColor` so both themes work, reserve `var(--accent)` for the one
element that carries meaning, label the arrows, wrap in `<figure>` + `<figcaption>`, give the
svg `role="img"` + an `aria-label`, and keep marker/gradient ids unique per page.

## Rules
- **Formal definitions are explicit.** Every formal, mathematical definition goes inside a
  `<Definition term="…">` block — never plain prose. Intuition and analogy stay outside the
  block; the block holds the precise statement (equations welcome).
- **Knowledge concepts are self-contained.** A concept page assumes no prior exposure:
  define every academic/technical term at first use with `<Term def="…">` and end the
  page with a `## Glossary` section collecting those definitions (same convention as
  summaries). A reader should never need to leave the page to parse a sentence.
- **General background belongs in the knowledge base.** Tutorial material reusable across
  papers (e.g. flow matching, DiT architectures) lives in `knowledge/concepts/*.mdx`
  (authored via `knowledge.py ensure-concept` + `link` for reciprocal paper links); the
  summary links to those pages (relative `../../knowledge/<slug>/`) and keeps only
  paper-specific background. Give every figure a stable id (`Fig. FM-1`, `Fig. DZ-2`, …)
  in its caption and reference figures by id.
- **Concise + core-first:** the visible body is TL;DR → Motivation → Contribution →
  Research questions → Methodology → Main result → Implications → Limitations →
  Critiques. Push detail into `<Pass>`.
- **Self-contained:** define every non-universal term with `<Term>`.
- **Declarative English**, specific numbers + anchors, "Not reported"/"Unclear" for gaps.
- **Motivation ≠ Contribution** — keep them distinct.
- Preserve the `{/* NOTES_START */} … {/* NOTES_END */}` block (personal notes).
