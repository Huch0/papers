# The Dawn of LMMs: Preliminary Explorations with GPT-4V(ision)

## Metadata
- Canonical key: arxiv-2309.17421
- Version: v1
- Fetch date: 2026-06-06T07:57:31Z
- Source: arxiv
- PDF: library/the-dawn-of-lmms-preliminary-explorations-with-230917421/v1/paper.pdf
- Venue: arXiv.org
- Year: 2023
- Authors: Zhengyuan Yang, Linjie Li, Kevin Lin, Jianfeng Wang, Chung-Ching Lin, Zicheng Liu, Lijuan Wang
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
A ~160-page qualitative Microsoft "case-study" report cataloguing what an early GPT-4V(ision) can do across dozens of vision-language tasks, whose two load-bearing contributions for agent research are (a) the *visual referring prompting* idea -- editing the input image's pixels (arrows, boxes, circles, scene text) to instruct the model -- and (b) hand-driven demonstrations of GPT-4V acting as an embodied/GUI agent (web browsing, smartphone shopping, house navigation) by predicting the next action from screenshots.

## Why this paper matters
CLAIMED/WHY-read: This is one of the seed documents that showed a frontier multimodal model could read a screenshot and propose a plausible next UI action (click/move-mouse/type), and could be "pointed at" things via marks drawn on the image rather than text coordinates. Those two ideas -- screenshot-in / action-out, and visual marking as a grounding channel -- recur in the later computer-use / GUI-agent lineage (Set-of-Mark prompting, SeeAct, WebVoyager, OS-level agents). It is worth reading for *provenance and intuition* about where the "VLM-as-GUI-driver" pattern came from, not for any reproducible system or benchmark. Note this is a qualitative report (the authors themselves call it "less rigorous", p.8): it demonstrates *possibility*, not reliability or measured success rates.

## Problem and gap
- CLAIMED (p.8): With GPT-4 (no vision) and PaLM as the strongest LLMs, it was "unclear what are the status quo and emergent multimodal abilities of LMMs" built on SOTA LLMs. Prior open LMMs (Flamingo, OpenFlamingo, MiniGPT-4, LLaVA-class) were of limited model/data scale, possibly suppressing emergent abilities.
- CLAIMED (p.8-9): Standard benchmark evaluation is argued to be ill-suited for GPT-4V -- LMM captions are richer than benchmark ground truths, and undisclosed large-scale pretraining may violate train/test splits and invalidate numbers. So the authors deliberately *substitute* curated qualitative probes for quantitative benchmarking.
- UNCLEAR: The "gap" is therefore framed as exploratory/descriptive. The paper does not attempt to close a measurable performance gap; it maps a capability surface.

## Core idea
The report is organized around four questions (p.8): (1) supported inputs and working modes; (2) quality/genericity of capabilities across domains; (3) effective ways to prompt; (4) promising future directions. The genuinely novel methodological contribution is **visual referring prompting** (Sec. 3.2, Sec. 5): because GPT-4V robustly understands visual markers drawn directly onto image pixels -- arrows, boxes, circles, hand-drawings, and handwritten scene text -- a user can specify the task or referent by *editing the image* instead of (or in addition to) text. The report claims this is more reliable than passing numeric text coordinates (p.66, Fig. 49 caption). The rest is a large gallery of zero-shot (default mode, p.9) qualitative examples demonstrating capabilities and prompting tricks.

## Harness relevance
This is NOT an agent system paper -- there is no codebase, no automated loop, no benchmark harness. It is a human-in-the-loop demonstration. Mapping it to harness concepts:

- **Environment / workspace**: Ad hoc, per-demo. For GUI navigation (Sec. 9.8, pp.121-149): a real desktop browser (Chrome) and a real smartphone (Amazon app) driven by screenshots. For embodied navigation (Sec. 9.7, pp.116-120): a *Redfin virtual house tour* used as a stand-in interactive environment, plus a coffee-machine operating panel for "operate appliance."
- **Observation interface**: A single screenshot of the current screen/scene per turn (image), optionally with the goal and a short action history in text. Visual referring marks may be overlaid on observations (Sec. 5, Fig. 51 explicitly shows marks on GUI screenshots).
- **Action interface**: Text descriptions of GUI actions. For web browsing the model is *given a fixed action list* -- "move the mouse, click an icon with the mouse, type with the keyboard" -- and must predict the next action and, when moving the mouse, "describe the location as detailed as possible" (p.121, Fig. 92 prompt). For mobile: "move/click finger, scroll, type." For embodied nav: "turn right / move forward / use robotic arm to open the fridge." Actions are natural-language, not structured/grounded coordinates.
- **Tool / API / shell / GUI layer**: None automated. CLAIMED-but-UNCLEAR: the authors note that because the mouse target is described in detail, the actions are "grounded, showing the potential of automating the whole process without human in the loop" (p.121) -- but in this report a human manually executes every predicted action and captures the next screenshot. So there is no real action executor or accessibility/DOM layer; grounding is verbal and approximate.
- **Planner / executor / verifier / search**: The model itself plays planner+executor per turn; there is no search, no verifier, no retry policy in the GUI demos. Section 10 *imagines* richer structures: multimodal ReAct chains (Fig. 121: Thought/Action/Observation rounds calling a person-detector then a crop tool for PPE counting), self-reflection (Sec. 10.3, "double-check the code and align it better"), self-consistency via majority vote over repeated counts (Sec. 10.4, Fig. 124), and retrieval augmentation (Sec. 10.5) -- all hand-constructed illustrations, not implemented systems.
- **Evaluation harness**: None. No success metrics, no task suite with pass/fail, no baselines. Outcomes are author-judged ("accomplished the task", "minor errors in Fig. 100").
- **Training harness**: None. GPT-4V is a black box; the authors only had early API access.
- **Logging / trace / reproducibility**: Each demo shows the verbatim prompt and GPT-4V output as figures; the "trace" is the figure sequence. No seeds, no temperature, no API version, no automation scripts. Sample-selection protocol (below) is the only reproducibility scaffolding.
- **Safety / permission mechanism**: None. No sandboxing, no action confirmation, no guardrails discussed for the GUI/embodied actions.

## Method
- **Format**: Curated qualitative case study. The report "contains minimal quantitative benchmark results" and instead presents "selected interesting qualitative examples" (p.8), trading rigor for breadth.
- **Default working mode**: Zero-shot instruction following (p.9), chosen specifically to avoid information leakage from in-context examples; few-shot is shown only where zero-shot fails (e.g., speed-meter reading, line-plot multi-hop reasoning).
- **Anti-memorization protocol** (p.8, "Sample selection to prevent mere memorizing"): generate original text queries from scratch; use images either not online or timestamped after April 2023; flag any sample that violates this; add "rationale queries" probing the reasoning process to distinguish capability from lucky guesses. This is the report's main methodological safeguard, and a notable observation in its own right.
- **Prompting techniques catalogued** (Sec. 3): instruction following; *constrained prompting* (force JSON output, Fig. 3); *"condition on good performance"* (tell the model it is an expert and to succeed -- flips a miscount of apples to a correct count, Fig. 4); chain-of-thought; multimodal example-grounded instruction (mixing instructions and worked examples, including marks); in-context few-shot.
- **Visual referring prompting** (Sec. 5): understand pointing inputs (Sec. 5.1), prompt by editing pixels (Sec. 5.2), and even *generate* pointing outputs as text coordinates for closed-loop, multi-hop grounded reasoning (Sec. 5.3) -- though generated boxes are coarse and not tightly fitted (p.69).
- **Capability gallery** (Secs. 4,6,7,8,9): open-world description (celebrity/landmark/food/medical/logo), localization/counting/dense captioning, multimodal knowledge & commonsense, scene-text/table/chart/document reasoning, multilingual understanding, coding-from-image (LaTeX/Markdown/figure-replication), temporal/video understanding, abstract visual reasoning & IQ tests (WAIS, Raven's Progressive Matrices), emotion/EQ; plus application highlights (spot-the-difference, industrial defect inspection, radiology reports, auto-insurance, customized captioning, image-generation evaluation, embodied agent, GUI navigation).

## Experimental setup
- Datasets / benchmarks: **Not reported** (deliberately -- no standardized benchmark is run; a few examples reuse public dataset images, flagged inline).
- Baselines: **Not reported** (no head-to-head; occasional informal contrast with "prior vision-language models" in prose).
- Models: An early-access version of GPT-4V(ision); GPT-4 (no vision) referenced for the language/coding baseline. Auxiliary models appear in the Section 10 imagined chains (Bing Image Search plugin, a person detector, SDXL for text-to-image).
- Metrics: **Not reported** (qualitative, author-judged correctness; figures use green/red highlighting to mark correct/wrong answers).
- Compute / cost: **Not reported**.
- Implementation / artifacts: **Not reported** -- no code, no released prompts beyond what appears in figures, no API version pinned.

## Key results
Because this is qualitative, "results" = demonstrated capabilities and observed failure modes. Quantitative success rates are **Not reported** throughout.
- EVIDENCE (single-instance demos, not measured): GPT-4V recognizes celebrities, landmarks, dishes, logos; reads scene text into JSON; reads tables/charts/documents; does multilingual OCR/translation; writes LaTeX/Markdown/code from a hand-drawn or screenshot input; describes video from frame sequences; attempts WAIS / Raven's IQ items and emotion recognition.
- EVIDENCE (prompting effects): "Condition on good performance" + row-by-row counting fixes an apple miscount (Fig. 4); few-shot is *necessary* for the speed-meter (zero/one-shot fail, two-shot reads "~9 mph" correctly, Figs. 8-10) and for a multi-hop gas-price line-plot question (two-shot reaches correct "2022", Figs. 11-13). These are explicit, instructive failure-then-fix sequences.
- EVIDENCE (visual referring prompting): GPT-4V binds objects to drawn indices, answers questions written next to a pointed edge/angle, and follows "+dot" arrow patterns; the authors report marks-on-pixels work *more reliably* than numeric text coordinates (p.66), though no number quantifies "more reliably."
- EVIDENCE (agentic demos): GUI web-browsing reaches and prints a Mapo Tofu recipe across Figs. 92-96; smartphone shopping completes a 9-step Amazon flow to checkout (Figs. 103-111); house navigation reaches the fridge in ~3-4 turns (Figs. 90-91). All succeed in the shown single runs, with at least one acknowledged "minor error" (Fig. 100, failing to return to a prior search page).
- UNCLEAR / honest caveats from the authors (p.8): showcased examples "may require careful instruction tuning to amplify" the capability, "some complex cases may only work with the specifically designed prompts," and capabilities "may not consistently work across different samples." This is the single most important caveat for anyone citing these demos as evidence of reliable agency.

## Evidence quality
- Severely limited by design. No quantitative benchmarks, no baselines, no ablations, no statistical reporting, no success/failure rates, no multiple-seed runs -- the authors state this trade-off up front (p.8). Each capability is typically backed by one or a few cherry-picked successful prompts.
- Selection bias: by their own admission complex cases may only work with specially designed prompts and may not generalize across samples; the gallery shows what *can* happen, not what *usually* happens.
- The anti-memorization protocol (post-April-2023 / offline images, rationale queries) is a genuine strength that raises confidence the model isn't merely recalling training data -- but it does not address reliability.
- The "grounded, automatable without human in the loop" claim for GUI actions (p.121) is aspirational: every action was executed by a human, and mouse targets are verbal ("approximately 1/3 down the left side"), not pixel-precise. Treat GUI/embodied "successes" as existence proofs, not measured task completion.

## Reproducibility and artifacts
- Code: None.
- Data: None released; query images curated ad hoc, many post-April-2023 or offline.
- Models: GPT-4V early-access (closed, version unspecified); GPT-4-no-vision referenced.
- Environment: Browser/phone/Redfin-tour demos described in prose only.
- License: Not reported (arXiv report; model is OpenAI's).
- Exact commands or setup: Only the verbatim prompts shown in figures; no temperature/seed/API version.
- Missing details: essentially all quantitative and operational details needed to reproduce a measurable result.

## Strengths
- Breadth: a single document surveys an unusually wide capability surface, useful as a map and as figure-level citation source.
- Introduces and names **visual referring prompting**, a genuinely influential prompting primitive (pixel-space marks as a grounding/interaction channel) that seeded later Set-of-Mark-style and GUI-agent work.
- Provides clear, reproducible-as-illustrations agentic *patterns*: screenshot-in / next-action-out for GUI and embodied navigation; multimodal ReAct chains; self-reflection; self-consistency.
- Thoughtful anti-memorization protocol and candid statements of its own non-rigor.

## Weaknesses and limitations
- Author-stated: not exhaustive; examples may need careful prompt tuning; may not work consistently across samples; quantitative evaluation left to future work (pp.8-9, 19, 156).
- Inferred: no metrics/baselines/ablations; cherry-picked single runs; "no human in the loop" GUI automation is unrealized (human executes every step); generated bounding boxes are spatially coarse (p.69); GUI grounding is verbal, not coordinate-precise; Section 10 "agent" structures are hand-built mockups, not running systems.
- Time-sensitive black-box subject: results pertain to one early GPT-4V snapshot and may not replicate on later versions.

## Relationship to prior work
- Sibling to "Sparks of AGI: Early experiments with GPT-4" (Bubeck et al., 2023) [24] in spirit -- a qualitative capability probe, here for the vision modality.
- Builds conceptually on LLM prompting literature it imports into the multimodal setting: instruction following, chain-of-thought, in-context few-shot, ReAct, self-reflection (Reflexion-style), self-consistency, retrieval augmentation.
- Contrasts itself with scale-limited open LMMs (Flamingo/OpenFlamingo, MiniGPT-4, LLaVA-class) as motivation.
- Genuinely new vs. incremental: the *visual referring prompting* framing is the most original methodological contribution; the GUI/embodied demos are new *demonstrations* of an existing idea (LLM/VLM as action proposer) rather than a new method or system. Downstream, the screenshot->action and pixel-mark grounding ideas anticipate Set-of-Mark prompting, SeeAct, WebVoyager, and later computer-use agents.

## What I should read
- Must read: Sec. 1 (motivation + the four questions, pp.8-9, esp. the deliberate choice of qualitative-over-quantitative and the anti-memorization protocol); Sec. 3.2 + Sec. 5 (visual referring prompting); Sec. 9.7-9.8 (embodied agent + GUI navigation prompts, esp. Fig. 92's full action-list prompt); Sec. 10.2 (multimodal ReAct chain, Fig. 121).
- Skim: Sec. 3.1/3.4 prompting tricks (condition-on-good-performance, few-shot speed-meter/line-plot); Sec. 10.3-10.5 (self-reflection / self-consistency / retrieval) as idea sketches.
- Can skip: Sec. 4/6/7/8 capability galleries unless a specific domain (charts, OCR, IQ tests, emotion) is needed -- they are figure-driven and repetitive.
- Follow-up papers: Set-of-Mark Prompting (Yang et al., 2023); SeeAct / GPT-4V web agents; WebVoyager; later OS/computer-use agent papers; "Sparks of AGI" [24] for the text-only analogue.

## Triage decision
Label: READ_SOON
Rationale: Provenance value is high for anyone working on GUI / computer-use / multimodal agents -- it is where visual referring prompting and the screenshot->next-action demonstration pattern enter the literature, and Fig. 92's action-list prompt is a concrete template. But it is qualitative, has zero benchmarks/metrics, and its agentic "successes" are human-executed single runs, so it is not a methods or results source. Read the four target sections (1, 3.2/5, 9.7-9.8, 10.2); the rest is skim/skip. Evidence held at READ_SOON (not downgraded) because the conceptual seeds are load-bearing for the harness's domain even though rigor is low.
Confidence: high
Reading time estimate: 45-70 min for the four target sections; the full 160 pages are not warranted.

## Personal notes
The most reusable artifact for harness work is the verbatim GUI prompt on p.121/Fig. 92 (give the model the goal, a fixed action vocabulary, and the current screenshot; require it to verbalize the mouse target). Treat every "task accomplished" in Secs. 9.7-9.8 as an existence proof under a human executor, not a success rate. The honest caveat on p.8 ("may not consistently work across different samples") should accompany any citation of these demos.

## Follow-up actions
- Add related paper: Set-of-Mark Prompting; SeeAct; WebVoyager.
- Compare with: later computer-use / GUI-agent harnesses that automate the screenshot->action loop this report ran by hand.
- Re-run after new version: n/a (black-box model; report is a fixed snapshot).
- Check code: none exists.
- Read benchmark details: none exist -- pair with a quantitative GUI-agent benchmark (e.g., WebArena / Mind2Web) for measured numbers.
