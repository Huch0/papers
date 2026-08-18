# System changes log

Append-only record of changes made via /evolve-paper-system or manual maintenance.
Each entry: date, trigger, change, files touched, migration status.

---

## 2026-06-06 — System bootstrapped

- Trigger: initial build request.
- Change: created full paper-harness skeleton (config, scripts, skills, hooks, indexes).
- Files: entire papers/ tree.
- Migration: none (green-field directory).

---

## 2026-06-06 — Added milestone discovery + global knowledge base

- Trigger: user feature request — (1) a skill to fetch milestone papers of a field from
  emergence to recent without duplicating existing papers; (2) a tutor/lab-colleague
  chat skill that captures learned knowledge into a global, cross-paper knowledge base.
- Change:
  - New config `config/milestones.yaml` (curated landmark seeds per field; titles + era
    + significance, resolved to real records at fetch time).
  - New scripts `scripts/fetch_milestones.py` (resolve + dedupe + `--discover` +
    `--mark-existing`) and `scripts/knowledge.py` (global concept notes: ensure-concept,
    link, search, session, index, validate).
  - New skills `.claude/skills/milestone-papers/` and `.claude/skills/paper-tutor/`.
  - Schema additions to `paper.yaml`: `milestone` block + `knowledge_concepts` (backfilled
    via migrate_registry); new `indexes/MILESTONES.md`; new `knowledge/` tree with
    generated INDEX/BY_TAG/BY_PAPER.
  - Scoring: `foundational_floor` (READ_SOON) so curated/foundational papers stay visible
    despite age; ingest carries the `milestone` block through and tags `foundational`.
  - Hooks/docs: auto_update_index + validate_metadata now watch `knowledge/`; sync skill
    rebuilds+validates the KB; README/CLAUDE.md/metadata_schema updated; SessionStart
    dashboard shows milestone + KB-concept counts.
- Migration: `migrate_registry.py` backfills the two new paper fields (idempotent, makes
  backups). Ran on the existing library (1 paper updated at time of change).
- Backwards compatibility: preserved — new fields default to null/[]; existing records
  validate unchanged.

---

## 2026-06-06 — Exhaustive milestone search: computer_use_agents

- Trigger: user request to exhaustively search milestone papers in the computer-use-agent field.
- Method: 5 parallel expert sweeps (web, gui_grounding, os_desktop, mobile,
  enabler_benchmark_survey) using web search + the harness's discover pass; merged and
  deduped by arXiv id then normalized title; flagged against the existing library.
- Result: 95 unique milestones (88 new, 7 already in library), spanning 4 eras.
- Durable capture: config/milestones.yaml `computer_use_agents` field restructured with
  sub-areas and expanded from 8 to 95 curated seeds (each title/year/era/arxiv/subarea/
  significance). Ingestion remains on-demand via /milestone-papers (dedup-protected).
- Note: a few late-2025 entries are tech reports/blogs without arXiv ids (Claude Computer
  Use, OpenAI Operator/CUA, Project Mariner, OSWorld-Verified); arXiv ids are validated at
  ingest time, so any imperfect id resolves by title search or is flagged unresolved.

## 2026-06-06 — Ingested all 88 new computer_use_agents milestones

- Ingested all 88 new milestones from the exhaustive search (records + metadata via a
  Semantic Scholar batch call to avoid arXiv rate limits; 84 arXiv PDFs downloaded with
  0 failures; 4 product reports kept as PDF-less records).
- Deep-summarized all 29 new emergence + foundational papers via parallel subagents,
  each grounded in its own PDF extraction with verified numbers and claim/evidence/
  unclear separation (several flagged abstract-vs-table discrepancies).
- Expansion (39) + recent (23) milestones remain as complete records (metadata + abstract
  + READ_SOON triage), summarizable on demand via /summarize-paper.
- Library: 11 -> 99 papers; 96 computer_use_agents milestones (91 with PDF, 36 with full
  summaries). Validation clean (0 errors/warnings); indexes + MILESTONES.md regenerated.

## 2026-06-06 — Revised the summary template (three-pass + Motivation≠Novelty + FOCUS)

- Trigger: user request to revise config/summary_template.md, referring to Keshav
  "How to Read a Paper", Kim "Motivation ≠ Novelty", and the AI@UVA "FOCUS" prompt.
- Change: restructured config/summary_template.md into Keshav's three passes
  (Triage → Content → Critique). Pass 1 adds the Five Cs. Pass 2 splits MOTIVATION
  (the problem) from NOVELTY (the genuine delta + the mechanistic reason the design must
  take its form), with Kim's litmus tests ("survives deleting 'we propose'?", "verify
  novelty vs merely confirm motivation", 30-second novelty test). FOCUS adds a
  declarative-voice / specific-numbers-with-anchors extraction rule and figure-scrutiny
  (axes/error-bars/significance, abstract-vs-table mismatches).
- Preserved script contracts: the `# <Paper Title>` header, the 12 `## Metadata` bullets
  (filled by summarize_paper.py --prepare), and the `## Personal notes`/`Free-form notes
  for later.` anchor (note preservation). Verified prepare fills metadata and preserves
  an injected note.
- Propagated to .claude/skills/summarize-paper/SKILL.md (requirements) and README
  ("Summary template & rules"). No metadata migration needed.
- Backwards compatibility: the ~37 existing summaries used the prior structure and remain
  valid (the template guides generation; it is not an enforced schema). Re-run
  /summarize-paper on any paper to regenerate it in the new format.

## 2026-06-06 — Self-contained rule + HTML summary format (experiment)

- Self-contained rule added to config/summary_template.md (+ skill): define every
  non-universal term/acronym/dataset/metric/method inline AND in a new Glossary section.
- Added an experimental rich HTML format: config/summary_template.html (CSS + color-coded
  claim/evidence/weak/limit callouts, results & claim→evidence tables, collapsible Pass 3,
  <dfn> glossary). summarize_paper.py gained `--format {md,html}` (prepare fills placeholders;
  finalize wires summary.html; status.summary_format recorded). Indexes/validate handle .html.
- Experiment: summarized 5 new CUA milestones in HTML (WebVoyager, OS-Atlas, AndroidWorld,
  Agent S2, UI-TARS-2). Measured vs last turn's 5 MD summaries (same paper types):
  same content (words 1.00x), artifact 1.27x bytes, generation cost ~1.03x — NOT 2-4x.
  Decision on default format pending user review.

## 2026-07-18 — `collections` tag group + icml2026-picks

- Added a `collections` group to config/tag_taxonomy.yaml with the first entry
  `icml2026-picks`: a curated reading list of agent papers the user picked up while
  attending ICML 2026 (10 papers ingested with this tag in the same change).
  The pattern is reusable for future conferences (e.g. `neurips2026-picks`).
- Requested by user: "Add a special tag for this list."

## 2026-07-19 — tde-related-work collection + robotics/SE/FM venue tiers

- Added `tde-related-work` to the `collections` tag group: the related-work corpus
  for the user's "Test-Driven Execution" (TDE) research (51 papers ingested from the
  user's novelty survey; 1 survey entry — WebArena Verified — has no fetchable source
  and was logged to errors.jsonl instead).
- Extended config/venues.yaml A_star tiers + aliases with CoRL, ICRA, IROS, CAV, and
  IEEE TSE so the robotics/formal-methods/SE anchors in this corpus are credited
  correctly (previously they would have landed in workshop_or_minor).
- Requested by user: "Add this papers to the library and write the summaries."

## 2026-08-15 — embodied-agent + world-model tags

- Added `embodied-agent` (domain) and `world-model` (method) to
  config/tag_taxonomy.yaml. First robotics/VLA paper in the library
  ("World Action Models are Zero-shot Policies", arXiv 2602.15922) had no
  applicable tag; both are reusable for future embodied/world-model work.

## 2026-08-18 — FlowMatch + AttnMask interactive components; inline-SVG diagram convention

- Added two reusable interactive summary components (ADR-0002 path: PR'd into
  site/src/components/summary/ and documented in config/summary_components.md):
  `<FlowMatch />` (toy 2-D flow-matching transport: t-slider, straight-line paths,
  velocity arrows, generate/train views) and `<AttnMask />` (chunked/causal DiT
  attention-mask explorer: training window, block-causal, KV-cache + observation-
  overwrite toggle). Both are dependency-free React islands hydrated client:visible.
- Documented the inline-SVG mechanism-diagram convention (currentColor + var(--accent),
  figure/figcaption, aria-label, unique marker ids).
- Trigger: user asked for background on Causal DiT / flow matching / robot action
  encoders with intuitive interactive diagrams to understand DreamZero's Figure 4;
  the components are generic so future diffusion/transformer papers reuse them.

## 2026-08-18 — background material moves to the knowledge base; figure ids

- User rule: general background/tutorial material belongs in knowledge/concepts/,
  not inside a single paper's summary; summaries link to the concept pages and keep
  only paper-specific background. Recorded in config/summary_components.md Rules.
- Applied to DreamZero: created concepts `flow-matching` (definition, velocity
  semantics, constant-velocity derivation, parameterization equivalence, history,
  drawbacks; Fig. FM-1 interactive) and `causal-dit` (latents/VAE, DiT block+adaLN
  Fig. DIT-1, chunk-causality/KV-cache/teacher-forcing, Fig. DIT-2 interactive),
  reciprocally linked to arxiv-2602.15922; summary background slimmed to primers +
  paper-notation objective + real-time loop (Fig. DZ-1) + Figure-4 walkthrough
  (Fig. DZ-2). All figures now carry stable ids.
- FlowMatch island gained a same-space view (noise overlaid on data) after the user
  correctly objected that the side-by-side layout hides that transport directions
  point every way.

## 2026-08-18 — KB self-containment rule + Glossary sections

- User rule: the knowledge base must be self-contained — define every
  academic/technical term (Term chips at first use) and end each concept page
  with a ## Glossary. Recorded in config/summary_components.md Rules.
- Applied to flow-matching (new vocabulary section defining field / velocity
  field / probability path / generates; new "marginal field" section resolving
  what u_theta(x_t, t) converges to — the conditional expectation E[x1 − x0 |
  x_t = x] — with new Fig. FM-2 showing crossing conditional targets averaging;
  named "rectified flow" + reflow; 15-entry Glossary) and causal-dit (15-entry
  Glossary).

## 2026-08-18 — Definition component for formal mathematical definitions

- User rule: every formal, mathematical definition is written inside an explicit
  <Definition term="..."> block (textbook register); intuition stays in prose.
  Component added via the ADR-0002 path (site/src/components/summary/Definition.astro,
  registered in map.ts, documented + rule recorded in config/summary_components.md).
- Applied: flow-matching (Probability path, Generating velocity field, Conditional
  flow matching, Marginal velocity field, Rectified flow — 5 blocks), causal-dit
  (Block-causal attention mask), DreamZero summary (Eq. 2 corruption/velocity,
  Eq. 3 objective).

## 2026-08-18 — visualizing u(x, t): field view + spacetime + filmstrip

- User asked for the best way to visualize a time-dependent velocity field and
  whether a 3-D time-axis plot is workable. Added to knowledge/flow-matching:
  a "How do you picture u(x, t)?" section presenting the three honest views —
  (1) FlowMatch island gained a third tab, "Field: the marginal wind", drawing
  the toy's EXACT marginal field (closed form: softmax-weighted data mean minus
  position over remaining time; formula + derivation Pass on the page) as an
  arrow grid under the t-slider; (2) new static Fig. FM-3, a 1-D spacetime slope
  field with exact integrated marginal trajectories (conditional lines cross,
  marginal ODE curves cannot — computed, not sketched); (3) new static Fig. FM-4,
  a probability-path filmstrip. Text explains why a literal 3-D rendering is
  avoided (projection ambiguity) — a slider is the 3-D plot, sliced.

## 2026-08-18 — causal-dit page: VAE pipeline, detailed DiT block, chunk clocks, denoising loop

- Six user questions while reading /knowledge/causal-dit/ drove four figures and
  three text sections: Fig. DIT-3 (causal 3-D conv VAE: 33 raw -> 8 latent with
  the anchor-frame arithmetic 1 + 4x8 = 33, then patchify -> tokens), a fully
  detailed redraw of Fig. DIT-1 (QKV attention internals, both adaLN sites,
  adaLN-Zero gates, residuals, and the complete timestep pathway t -> sinusoidal
  -> MLP -> per-block heads -> six modulation signals), an adaLN <Definition>
  with the modulation equation, Fig. DIT-4 (one 1.6 s chunk as three aligned
  clocks: 8 raw frames at 5 FPS, K=2 latent frames, H=48 action ticks at 30 Hz —
  all denoised in one pass, streamed sequentially), and a new "From velocity to
  a finished chunk" section with Fig. DIT-5 (the integrator loop: DiT outputs
  velocities, the loop generates; 16 -> 4 -> 1 steps) cross-linked to the
  flow-matching page. Glossary +4 (causal video VAE, patchify, adaLN-Zero,
  action chunk); +1 SelfCheck (why 33 not 32).

## 2026-08-18 — causal-dit deep detail: causal 3-D conv mechanics, real dimensions, adaLN intent, Fourier features

- Follow-up to five "you are skipping details" questions: Fig. DIT-3 fully redrawn
  as two panels — (a) WaveNet-style time-unrolled causal convolution (left-padding,
  backward-leaning edges, stride-2 stages giving the ÷4, accent anchor path,
  centered-kernel contrast inset) and (b) the dimension pipeline with Wan2.1's
  public config (3×33×480×832 raw → 16×(1+8)×60×104 latents → 60×104 grid of
  16-dim vectors → 1×2×2 patch = 64 numbers → d=5120 tokens, 1,560/latent frame,
  ~48× compression). Formal <Definition> for causal temporal convolution.
- Reconciled the 8↔33 arithmetic precisely: anchor rides alongside the 8 chunked
  latent frames (1 + 8×4 = 33); SelfCheck answer updated.
- New "Why scaling-and-shifting?" section: token-vs-concat-vs-FiLM comparison,
  LN as the natural injection site, adaLN-Zero identity-init stability, DiT
  ablation result. New "Why sinusoidal features?" section with a formal
  <Definition> + equation and new Fig. DIT-6 (sample-the-wave-bank picture);
  spectral-bias rationale. Glossary +4 (receptive field, strided convolution,
  FiLM, sinusoidal features); +1 SelfCheck (why inject t at all 40 blocks).

## 2026-08-18 — causal-dit fully rewritten as a taught narrative

- User verdict: figures stated shapes without showing transformations; page had
  grown by accretion. Complete rewrite around one running example (1.6 s of one
  832×480 view) traced pixels → cells → latent frames → tiles → 64-number rows →
  5120-wide tokens, organized as Parts 1–5 with a map. New Fig. DIT-7 (an 8×8
  pixel block of 192 numbers visibly becoming one 16-number cell; frame → 60×104
  cell grid; 4-frames→1 merge; K=2 slabs), new Fig. DIT-8 (patchify exploded:
  the 2×2 tile cut out, its 4×16=64 numbers flattened, ×W(5120×64) → one token;
  the 3,120+48+text/state token list), the "becomes-what" ledger table with the
  key insight (patchify regroups 199,680 numbers unchanged; the embedding then
  EXPANDS into working width — compression was the VAE's job), Fig. DIT-1
  regenerated with shapes on every wire (n×5120 lane, 40 heads × 128, n×n
  weights, 5120→13824→5120 MLP, t→256→5120→6×5120 conditioning lane), Fig. DIT-3
  reduced to the causality unroll alone, and an un-patchify paragraph closing
  the loop in Part 5. All prior Definitions, DIT-2/4/5/6 figures, Glossary and
  SelfChecks carried into the new structure.

## 2026-08-18 — Fig. DIT-1 redrawn vertically in the DIT-7 style

- User liked Fig. DIT-7's structure but found DIT-1 overlapped and unintuitive
  (twelve ops crammed into one horizontal ribbon). Regenerated vertically:
  token list in at top → two dashed containers making the anatomy visible
  ("sub-block 1 · mix the tokens (attention)" / "sub-block 2 · transform each
  token alone (MLP)"), each = normalize → scale-shift → operate → gate → add;
  a visible dashed residual bypass lane on the left; the timestep as its own
  right-hand column (t → 256 → c:5120 → block head → 6×5120) feeding an accent
  bus with four labeled taps. Every label owns its own row/gutter by
  construction; plain-words sublines on every op; shapes on the wires.
  Surrounding Part-3 prose updated to the same-wrapper-applied-twice framing.

## 2026-08-18 — figure text size floor + per-figure zoom (FigZoom)

- User: figure text too small; wants paragraph-comparable size and per-figure
  resizing. Added <FigZoom> (ADR-0002 path): a wrapper island giving every
  figure −/+/reset controls (60–300%), scrolling horizontally inside its own
  viewport when enlarged. All 12 inline-SVG figures across causal-dit,
  flow-matching and the DreamZero summary wrapped; all SVG label fonts bumped
  mechanically (×1.4, floor 13px at 880-wide viewBox ≈ body-comparable once
  scaled) — 141 attributes across the three docs plus both interactive islands.
  Convention recorded in config/summary_components.md (wrap sizable SVG figures
  in FigZoom; keep labels ≥13px).

## 2026-08-18 — FigZoom gains drag-to-pan

- Panning added to the per-figure zoom wrapper: while zoomed past 100% the
  viewport locks to its 100% height, and the figure pans by pointer drag
  (mouse and touch, via pointer capture; touch-action disabled so the page
  does not scroll instead) or native scrollbars; reset also clears the pan.
  "drag to pan" hint shown in the control bar when active.
