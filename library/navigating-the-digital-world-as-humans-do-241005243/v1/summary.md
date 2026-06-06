# Navigating the Digital World as Humans Do: Universal Visual Grounding for GUI Agents

## Metadata
- Canonical key: arxiv-2410.05243
- Version: v1
- Fetch date: 2026-06-06T07:57:34Z
- Source: arxiv
- PDF: library/navigating-the-digital-world-as-humans-do-241005243/v1/paper.pdf
- Venue: International Conference on Learning Representations (ICLR 2025, Oral)
- Year: 2024 (arXiv v1 Oct 2024; published version ICLR 2025)
- Authors: Boyu Gou, Ruohan Wang, Boyuan Zheng, Yanan Xie, Cheng Chang, Yiheng Shu, Huan Sun, Yu Su
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

---

# PASS 1 — Triage (bird's-eye, ~5 min)

## One-sentence takeaway
A 7B LLaVA-derived visual grounding model (UGround), trained on a 10M-element web-synthesized grounding dataset, lets GUI agents act from pixels alone via the SeeAct-V planner/grounder split, beating prior grounding models by ~20% absolute on ScreenSpot and matching or beating SOTA agents that additionally read HTML/a11y trees.

## The Five Cs
- **Category:** New method/system + dataset. Two coupled artifacts: a grounding model (UGround) and a vision-only agent framework (SeeAct-V). Also carries a position argument (human-like, pixel-only embodiment).
- **Context:** Builds on SeeAct (Zheng et al., 2024) for the planner/grounder decomposition; LLaVA-NeXT (Liu et al., 2024b) + AnyRes for the architecture; SeeClick (Cheng et al., 2024) and CogAgent (Hong et al., 2024) as the closest grounding baselines; ScreenSpot, Multimodal-Mind2Web, AndroidControl, OmniACT, Mind2Web-Live, AndroidWorld for evaluation. Competes with text-based GUI agents (HTML Choice / a11y-tree selection, Set-of-Mark labeling).
- **Correctness:** Core assumptions look sound: pixel renderings are information-complete; a11y trees are noisy (cites WebAIM 2024: 95.9% of top-1M home pages have accessibility errors, avg 56.8/page, p.2). The cross-platform transfer claim (web-only training → desktop/mobile) is the riskiest assumption but is empirically supported (UGround scores well on desktop despite zero desktop training data, p.6). The "vision-only beats text-input agents" headline holds for element/step accuracy under a fixed-planner setup, not for every online success-rate cell.
- **Contributions (claimed, p.2-3):** (1) A reasoned case + generic framework (SeeAct-V) for pixel-only GUI agents adapted from SeeAct; (2) a simple recipe (web-synthetic data + light LLaVA adaptation) yielding the largest GUI grounding dataset to date (10M elements / 1.3M screenshots) and the UGround model; (3) the most comprehensive GUI-agent evaluation to date — six benchmarks, three settings — showing UGround beats grounding baselines by up to ~20% absolute and SeeAct-V matches/beats text-input SOTA agents.
- **Clarity:** Strong. Clear separation of grounding vs. agent settings, explicit baselines, ablations (data sources, resolution, RE types, backbone), error analysis, and full prompts in the appendix. Well evidenced.

## Why this matters to me now
Directly central to computer-use / GUI-agent harness design: it argues for and validates a pure-pixel observation + coordinate-action interface and a clean planner/grounder module split. The grounding model is a pluggable component for any MLLM planner, and the data-synthesis recipe is a reusable blueprint. This is a foundational reference for the "vision-only agent" line.

---

# PASS 2 — Content (what it actually does; section-grounded)

## Motivation — the problem (NOT the novelty)
GUI agents overwhelmingly perceive via text representations (HTML, accessibility trees) and act by *selecting from a candidate list* (HTML elements or Set-of-Mark labels) rather than by direct pixel operations (p.2, §1). These extra requirements have real costs:
- **Noise/incompleteness:** Full HTML carries large amounts of irrelevant content; a11y trees are compact but rely on voluntary annotation and are widely wrong/incomplete — WebAIM 2024 finds 95.9% of top-1M home pages have accessibility conformance errors, avg 56.8 per page (p.2, fn.3). Visual renderings are by design information-complete and user-relevant.
- **Latency/cost:** HTML can take up to ~10× more tokens than the corresponding screenshot to encode (Zheng et al., 2024, cited p.2); obtaining a11y trees is itself slow on desktop/mobile. These costs compound over long-horizon tasks.
- **The bottleneck:** Prior pixel-only attempts (Shaw et al. 2023; Hong et al. 2024; Cheng et al. 2024) exist but are "rarely adopted in state-of-the-art solutions" (p.2). The diagnosed reason is *grounding* — mapping a textual plan to precise on-screen coordinates — which must be (1) high-accuracy (one error can fail a whole task), (2) cross-platform, and (3) pluggable into different MLLMs. Existing grounding models meet none of these three desiderata well (p.2).

This section is the problem only: text representations are a leaky, costly crutch, and the missing piece for removing them is a good grounding model.

## Novelty — the genuine delta  ★ the core of a good summary
- **Delta in one sentence:** A *web-only* synthetic grounding dataset built from the HTML↔pixel dual representation, plus a resolution-adapted LLaVA, produces a single grounding model accurate and general enough that a planner/grounder-split agent can run on pixels alone and still beat agents that additionally consume HTML/a11y trees.
- **Mechanistic reason the design must be this way:**
  - *Why pixel-only is the principled choice (not just cheaper):* The argument is that the rendered screen is the information-complete channel — it contains exactly what a human user needs and nothing irrelevant — whereas text representations are a lossy, noisy *proxy* for it that also costs more tokens/latency. So removing text input is not a sacrifice; it removes a source of error and overhead, *provided* grounding is solved. The whole paper is a constructive proof that grounding can be solved well enough to make pixel-only the better, not just the more elegant, interface.
  - *Why a separate grounding module (SeeAct-V), not a monolithic end-to-end agent:* The environment space (1B+ websites, dynamic states, idiosyncratic icons/jargon) is too large for any single model to internalize; grounding is precisely the capability that benefits from a dedicated, independently fine-tunable module that maps domain-specific semantics to coordinates and feeds them to a generic planner (Appendix B, p.19). Modularity also lets the grounder be reused across planners and avoids the cost of collecting joint plan+ground trajectory data needed to train monolithic agents.
  - *Why web data generalizes:* Webpages uniquely offer a *dual representation* — full HTML + visual rendering + exact element↔bounding-box correspondence + rich metadata (CSS, aria-*) — making them an automatic, scalable source of ⟨screenshot, RE, coordinates⟩ triplets (p.4, §2.2). GUI designs share structure across platforms, so web-trained grounding transfers to desktop/mobile (hypothesis stated p.4, confirmed on desktop with zero desktop training data, p.6).
  - *Why the RE taxonomy + hybrid synthesis:* Real planners emit visual, positional, and functional referring expressions (and composites); prior grounding data underrepresents this diversity (p.4). The hybrid pipeline (rules + LLaVA-NeXT-13B + Llama-3-8B) deliberately manufactures all three RE types so the grounder is robust to whatever a planner says.
  - *Why the architecture changes:* GUI screenshots need >1000px legibility; vanilla LLaVA/AnyRes tops out ~772px. They push AnyRes to 36 ViT slices (max 1344×1344 / 896×2016), use CLIP@224px for flexible splitting, a 16K-context Vicuna backbone, output raw (un-normalized) pixel coordinates as text, and drop the low-res global-context thumbnail (unhelpful >1000px) (p.5, §2.3; Appendix F).
- **Closest prior work and the precise difference:**
  - *SeeAct (Zheng et al., 2024):* same planner→grounder two-stage idea, but SeeAct's grounding selects from filtered HTML elements or SoM labels — both requiring HTML/a11y input. SeeAct-V swaps that for a pixel-only grounding model producing coordinates directly (p.3, §2.1).
  - *SeeClick (Cheng et al., 2024):* closest grounding model; finetunes Qwen-VL on simplistic web-synthetic + mobile data, limited by small input resolution. UGround uses a higher-resolution architecture and a much richer/larger RE-diverse dataset; with the *same* Qwen-VL backbone and only Web-Hybrid, UGround-Qwen still beats SeeClick by 10.1% absolute (Table C.1, p.20), isolating data quality from architecture.
  - *CogAgent (Hong et al., 2024):* 18B model with 140M grounding samples; underperforms SeeClick despite far larger size/data (noted p.20), so omitted from controlled comparison.
- **Motivation-vs-novelty check:** The contribution does NOT end at "text representations are noisy/slow" — that is the motivation. The genuine delta is the *constructive* result: a specific data-synthesis recipe + resolution recipe that makes a pluggable grounder good enough to remove text input without losing accuracy, validated across 6 benchmarks. The position ("act like humans, pixel-only") is backed by a working artifact, not just argued.
- **30-second test:** Webpages give you free, exact pixel↔element labels; mine them at scale into diverse referring expressions, fine-tune a high-resolution LLaVA on them, and you get one grounding model accurate and cross-platform enough that a vision-only planner+grounder agent beats agents that still read HTML.

## Core idea / method
1. **Data (Web-Hybrid, p.4-5 §2.2; Appendix E.1):** Render Common Crawl pages with Playwright at varied resolutions/aspect ratios (~1/3 mobile-friendly to trigger mobile layouts; up to 3 viewport blocks per long page; ~773K screenshots from ~700K URLs). For each interactive element synthesize REs via a hybrid pipeline: primary descriptors from HTML attributes (inner-text, alt, aria-label) or MLLM (LLaVA-NeXT-13B, condensed by Llama-3-8B); positional REs (absolute + relative + contextual) from rule-based neighbor/title/DOM analysis. Center-point coordinates are the target. OCR (EasyOCR) gates trivial text elements; frequent aria-labels are downsampled (e.g., "Next" 13K→1K). Supplemented by Web-Direct (GPT-4o, 408K) and existing Android sets (GUIAct, AndroidControl, Widget Caption, UIBert, AITZ). Total 10M elements / 1.3M screenshots; ~90% from Web-Hybrid (Table 1, p.5).
2. **Model (UGround, p.5 §2.3; Appendix F):** 7B LLaVA-NeXT backbone (Vicuna-1.5-7b-16k LM, frozen CLIP-ViT-L-14@224px), modified AnyRes up to 36 grids (1344×1344 / 896×2016), pad-by-width to preserve aspect ratio, output un-normalized pixel coordinates in natural-language form, no low-res global thumbnail. Trained with LoRA. Later UGround-V1 variants (2B/7B/72B) are built on Qwen2-VL with the same data mixture.
3. **Agent (SeeAct-V, p.3 §2.1; Fig.2):** Per step, an MLLM planner takes only the screenshot + task text and emits {action, element description, value}; UGround maps the element description to (x,y); a "Click" is auto-inserted before "Type". No HTML/a11y in observation, planning, grounding, or execution.

## Harness relevance
- **Environment / workspace:** Web, desktop (Windows/macOS/Linux), and mobile (Android) GUIs; offline cached states and live online environments (Mind2Web-Live websites, AndroidWorld emulator).
- **Observation interface:** Screenshots ONLY (task instruction is text). No HTML, no a11y tree. Long web pages split into 1280×1000 viewport blocks with simulated scroll (Appendix G.2).
- **Action interface:** Pixel-level operations — Click/Type/Select/Scroll, etc. — with click targets produced as (x,y) coordinates from the grounding model. On OmniACT, actions are PyAutoGUI scripts with coordinates substituted in; on Mind2Web-Live the action space is rewritten to remove all HTML dependence (Scroll Up/Down added; Fill Form/Search and API-based Select removed; Type + Press Enter used) (Appendix G.5).
- **Tool / API / shell / GUI layer:** Mouse+keyboard effectors; PyAutoGUI for desktop; AndroidWorld device control via the M3A agent skeleton (SoM images and a11y element lists stripped out, Appendix G.6).
- **Planner / executor / verifier / search structure:** Modular two-stage — MLLM planner (GPT-4 / GPT-4-turbo / GPT-4o as the foundation planner) + specialized UGround grounder + deterministic executor. No search/tree; no learned verifier (online benchmarks use their own functional/state-based evaluators). AndroidWorld baseline uses ReAct + self-reflection; SeeAct-V keeps the planner skeleton but removes text-element selection.
- **Evaluation harness:** Six benchmarks — ScreenSpot (grounding); Multimodal-Mind2Web, AndroidControl, OmniACT (offline agent); Mind2Web-Live, AndroidWorld (online agent). Metrics: ScreenSpot grounding accuracy, element accuracy, step accuracy (high/low), action score, completion rate, task success rate.
- **Training harness:** Two stages — LLaVA-1.5 pretrain/finetune (switch to absolute coords + modified AnyRes), then GUI grounding training on the 10M set. LoRA, device batch 4. Stage 1 ~50h on 4×A100; GUI stage ~6h on 112×H100 (global batch 448) (Appendix F.3).
- **Logging / trace / reproducibility:** Specific GPT endpoint names listed per benchmark (Appendix G.1, e.g., gpt-4o-2024-05-13). Dataset, model, and project page released (osu-nlp-group.github.io/UGround). Full planner prompts in Appendix H.
- **Safety / permission mechanism:** None for the agent. Ethics statement covers data: Common Crawl subset, content moderation before release, fair-use/non-commercial (p.11).

## Experimental setup
- **Benchmarks:** ScreenSpot (1,272 single-step grounding instructions across mobile/desktop/web; standard + agent settings); Multimodal-Mind2Web (1,013 test tasks, 100+ sites, element accuracy on cached pages); AndroidControl (500 random test steps, high/low settings, step accuracy); OmniACT (desktop PyAutoGUI, action score); Mind2Web-Live (live web, completion rate + success rate); AndroidWorld (116 tasks, 20 apps, success rate).
- **Baselines:** GPT-4/GPT-4o (general MLLM grounding), SeeClick, CogAgent (grounding); SeeAct Choice/SoM, M3A (text + image+SoM), DetACT, Pan et al. text-only agent (agent settings).
- **Models / planners:** UGround (7B LLaVA-NeXT) and UGround-V1 (Qwen2-VL 2B/7B/72B); planners GPT-4 / GPT-4-turbo-2024-04-09 / GPT-4o-2024-05-13.
- **Compute/cost:** Training compute reported (above). Online eval cost noted as high (only UGround grounder used online). Per-task dollar cost: Not reported.
- **Artifacts:** Dataset + model + framework released.

## Key results — read the figures, not just the prose
- **ScreenSpot Standard (Table 2, p.6):** UGround (7B LLaVA) avg 73.3 vs SeeClick 53.4 (+19.9 abs) and CogAgent 47.4; GPT-4o 18.3. UGround-V1-7B 86.3, UGround-V1-72B 89.4. The abstract's "up to 20% absolute" matches the standard-setting average gap over SeeClick.
- **ScreenSpot Agent (Table 3, p.6):** with GPT-4o planner, UGround 81.4 vs SeeClick 52.3 (+29.1 abs) — matches the prose "29% under the agent setting" (p.6). UGround-V1 variants 81.5–84.5.
- **Multimodal-Mind2Web element accuracy (Table 4, p.7):** SeeAct-V+UGround (GPT-4o) avg 46.8 vs SeeClick 32.9; beats text-input SeeAct Choice (42.3, GPT-4) and SoM (25.6). UGround-V1-7B 49.1. Notable: vision-only beats the HTML-Choice baseline.
- **AndroidControl step accuracy (Table 5, p.8):** UGround (GPT-4o) High 48.4 / Low 62.4 vs text-only M3A Choice 42.1 / 55.0 and SeeClick 41.8 / 52.8. UGround-V1-7B 49.8 / 66.2.
- **OmniACT action score (Table 6, p.8):** UGround (GPT-4o) 32.8 vs DetACT image+text 17.0 and text 11.6; SeeClick 29.6. UGround-V1-7B 34.0. Desktop performance despite zero desktop training data.
- **Mind2Web-Live (Table 7, p.9):** SeeAct-V+UGround GPT-4 CR 50.7 / SR 23.1 vs text Choice GPT-4 44.3 / 21.1, GPT-4o 47.6 / 22.1. Vision-only edges text on CR; SR roughly comparable (GPT-4o SeeAct-V SR 19.2 actually *below* text-GPT-4o 22.1 — a cell where vision-only does not win).
- **AndroidWorld (Table 8, p.9):** GPT-4o + UGround 32.8 SR vs text M3A Choice 30.6 and image+text SoM 25.4; GPT-4o + UGround-V1-7B 44.0. Beats both text and SoM variants.
- **Error analysis (Fig.4, p.9):** Planning errors dominate across benchmarks (e.g., Multimodal-Mind2Web 18.2% planner vs 8.7% grounding; AndroidControl-Low 5.3% vs ~1%; ScreenSpot-Desktop 46.5% planner vs 9.3% grounding) — i.e., the remaining bottleneck is the planner, not UGround. Long-tail idiosyncratic icons are the main grounding-error source on desktop/mobile.
- **Scaling (Fig.5, p.9):** Average ScreenSpot accuracy rises with Web-Hybrid size, diminishing after ~100K screenshots; at just 50K screenshots (~600K elements) UGround already beats SeeClick by >10% despite SeeClick's ~3M elements.
- **Ablations:** Web-Hybrid alone (76.9 avg) > "Others" supplementary alone (73.4); combined 81.4 (Table 9, p.10). Dynamic resolution > fixed (Table C.2). Positional REs help (+0.9 agent, +3.9 standard avg; Tables C.3/C.4). Same-backbone data ablation: UGround-Qwen (Web-Hybrid only) +10.1 over SeeClick; model design adds +14.5 (Table C.1, p.20).

Figures/tables are single-run point estimates — no error bars or variance reported anywhere. Headline abstract numbers (≈20% grounding gain; vision-only ≥ text-input agents) are consistent with the tables, with the caveat that "≥" is not literally true in every online cell (Mind2Web-Live GPT-4o SR).

---

# PASS 3 — Critique (challenge every assumption)

## Does the evidence actually support the claims?
- **Claim: UGround beats prior grounding models by up to ~20% absolute.** Strongly supported — ScreenSpot standard avg +19.9 over SeeClick, agent setting +29.1 (Tables 2-3). Verifies the novelty (the data/model recipe), not just the motivation.
- **Claim: vision-only SeeAct-V matches/beats text-input SOTA agents.** Supported in aggregate across all four agent benchmarks, but qualified: it is "at least comparable and often much better" rather than uniformly better — e.g., Mind2Web-Live GPT-4o SR (19.2) trails text GPT-4o (22.1). This compares grounding under a controlled fixed-planner setup; operation scores are deliberately omitted on Mind2Web as "orthogonal" (p.7), which is reasonable but narrows the claim to element/step-level grounding rather than full end-to-end superiority everywhere.
- **Claim: web-only data generalizes cross-platform.** Well isolated — UGround is never trained on desktop screenshots yet leads on ScreenSpot-Desktop and OmniACT (p.6, p.8). The scaling and same-backbone ablations (Tables C.1, 9) cleanly separate data-quality from architecture contributions. This verifies the central novelty.
- **Separating novelty-verifying vs motivation-confirming experiments:** The WebAIM statistic and token-cost figure merely confirm the *motivation* (text is noisy/costly). The grounding tables, controlled backbone ablation, scaling curve, and cross-platform transfer are what *verify the novelty*. The paper does the latter well.
- **Gaps:** No variance/significance anywhere (all single runs). AndroidControl uses only 500 random steps. SoM Multimodal-Mind2Web baseline is on 30-task subsets (Table 4 note), a weaker comparison point. No latency/cost numbers are actually measured to back the efficiency motivation — the 10× token and a11y-latency claims are cited from prior work, not re-measured here.

## Hidden assumptions & failure modes
- Assumes the planner can emit a referring expression that *uniquely* identifies the target; error analysis shows planner-side description errors are now the dominant failure (Fig.4). The framework is only as good as its planner.
- Assumes center-point coordinate = correct action; struggles with elements where the actionable region differs from the visual center, and on AndroidControl coordinates are post-hoc snapped to the smallest containing element (Appendix G.3) — a benchmark-specific crutch.
- Long-tail idiosyncratic icons (e.g., app-specific glyphs) remain a real grounding-failure source (p.9, §3.4); web training cannot cover them.
- Vision-only forces compromises: on Mind2Web-Live, API-based Select is disabled and some select widgets "cannot be easily operated with only Click" (Appendix G.5) — an admitted capability loss.
- No desktop training data at all; desktop performance, while strong, is acknowledged as limited by this (p.10).
- If I were reviewing: I'd press for measured end-to-end latency/cost (the efficiency premise is asserted, not demonstrated), variance over seeds, and full end-to-end success (not grounding-isolated) comparisons on the offline benchmarks.

## Could I reconstruct it? (reproducibility)
- **Code:** Released (project page osu-nlp-group.github.io/UGround). Not inspected here.
- **Data:** Web-Hybrid synthesis fully described (Playwright + Common Crawl CC-MAIN-2023-50, EasyOCR gating, LLaVA-NeXT-13B + Llama-3-8B prompts given in Appendix E/H). Dataset released. Reproducible in principle; exact Common Crawl sampling and filtering thresholds partially specified.
- **Models:** Backbone (LLaVA-NeXT 7B / Vicuna-1.5-7b-16k / CLIP-ViT-L-14@224px) and Qwen2-VL variants named; UGround released.
- **Environment:** Training compute given (4×A100 stage 1 ~50h; 112×H100 ~6h stage 2; LoRA, batch sizes). GPT endpoints pinned per benchmark (Appendix G.1).
- **License:** Data for research/non-commercial use; model license Not reported in extraction.
- **Exact commands/setup:** Not in paper; presumably in repo.
- **Missing details (blockers):** Exact AnyRes/LoRA hyperparameters beyond batch size, full Common Crawl filtering pipeline, and any data-dedup specifics. Core results are reconstructable from the released dataset+model; from-scratch data regeneration would require nontrivial effort.

## Strengths
- A clean, well-isolated result: same-backbone ablation proves the *data* is the main driver, separately from architecture (Table C.1).
- Genuinely broad evaluation — 6 benchmarks, 3 platforms, 3 settings — rare for this subfield.
- Strong, scalable, fully-automated data-synthesis recipe exploiting the web's HTML↔pixel duality; the RE taxonomy (visual/positional/functional) is a useful conceptual contribution.
- Modular, pluggable grounder usable with any MLLM planner — practical and reusable for harness design.
- Honest error analysis localizing the remaining bottleneck to planning, not grounding.

## Weaknesses and limitations
- No variance/significance; single-run numbers throughout.
- Efficiency motivation (latency/cost) is argued via cited figures, never measured for SeeAct-V itself.
- No desktop training data; long-tail icon grounding unsolved (both stated by authors, p.10).
- Data efficiency: 10M elements with heavy web redundancy; authors note room for better dedup (p.10).
- Vision-only forces action-space compromises (disabled Select, click-only) on at least one online benchmark.
- "Beats text-input agents" is not literally universal (one online SR cell trails).
- UGround is not a standalone agent — depends entirely on an external planner.

## Relationship to prior work
Extends SeeAct's planner/grounder decomposition into a fully vision-only one (SeeAct-V) by replacing HTML/SoM candidate selection with a coordinate-producing grounder. Supersedes SeeClick and CogAgent as the grounding model via a higher-resolution architecture and a far richer/larger, RE-diverse web-synthetic dataset (controlled comparison isolates both data and design gains). Distinct from Set-of-Mark prompting (no labels/segmentation needed) and from OmniParser-style element-detection pipelines (single generative grounder, not a detector). Genuinely new: the dual-representation data recipe + RE taxonomy + the empirical demonstration that pixel-only can match text-augmented agents; incremental parts: the LLaVA/AnyRes adaptations are engineering tweaks on existing techniques.

---

# Decision

## What I should read
- Must read: §1 (motivation/desiderata), §2.1-2.3 (SeeAct-V + data + model), Tables 2-8, §3.4 error analysis, Appendix B (philosophy), Appendix C.1 controlled ablation.
- Skim: Appendix E (data construction details) if reproducing data; Appendix F (training).
- Can skip: Appendix H full prompts unless re-implementing; reference list.
- Follow-up papers / references to chase: SeeAct (Zheng et al., 2024), SeeClick (Cheng et al., 2024), CogAgent (Hong et al., 2024), OmniParser (Lu et al., 2024), AndroidWorld (Rawles et al., 2024), Mind2Web/Multimodal-Mind2Web (Deng/Zheng), OmniACT (Kapoor et al., 2024); UGround-V1 (Qwen2-VL) follow-ups.

## Triage decision
Label: READ_SOON
Rationale (grounded in Five Cs + novelty + evidence): A foundational, well-evidenced new-method+dataset paper (ICLR 2025 Oral) that makes and empirically backs the pixel-only GUI-agent case — directly central to computer-use/GUI-agent harness interests. The genuine delta (web dual-representation data recipe + RE taxonomy + pluggable high-res grounder enabling vision-only agents to match text-augmented ones) is clearly isolated from the motivation via controlled ablations and cross-platform transfer. Evidence quality is high but not perfect (no variance, efficiency premise unmeasured, one online cell trails). Strong enough to read soon for the method and harness design lessons; not elevated to MUST_READ only because results are single-run and the core ideas are graspable from Pass 1-2 without a deep read.
Confidence: high
Reading time estimate: ~60-90 min for a deep read (skipping prompts/appendix H).

## Personal notes
The task prompt mentioned OSWorld, but this paper does NOT evaluate on OSWorld; desktop is covered by OmniACT (offline) and there is no OSWorld experiment. Verify before citing.

## Follow-up actions
- Add related paper: SeeClick, CogAgent, OmniParser, SeeAct.
- Compare with: monolithic end-to-end GUI MLLMs (Aguvis, ShowUI, Qwen2.5-VL grounding) on the same ScreenSpot.
- Re-run after new version: UGround-V1 (Qwen2-VL 2B/7B/72B) numbers already partly folded in.
- Check code: project page repo for training/data scripts + model license.
- Read benchmark details: ScreenSpot agent-setting RE generation; Mind2Web-Live modified action space (Appendix G.5).
