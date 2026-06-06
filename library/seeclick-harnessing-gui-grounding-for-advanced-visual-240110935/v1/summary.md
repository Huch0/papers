# SeeClick: Harnessing GUI Grounding for Advanced Visual GUI Agents

## Metadata
- Canonical key: arxiv-2401.10935
- Version: v1
- Fetch date: 2026-06-06T07:57:28Z
- Source: arxiv
- PDF: library/seeclick-harnessing-gui-grounding-for-advanced-visual-240110935/v1/paper.pdf
- Venue: Annual Meeting of the Association for Computational Linguistics (ACL 2024)
- Year: 2024
- Authors: Kanzhi Cheng, Qiushi Sun, Yougang Chu, Fangzhi Xu, Yantao Li, Jianbing Zhang, Zhiyong Wu
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
SeeClick is a screenshot-only ("pixels-in, click-coordinate-out") GUI agent built by continually pre-training Qwen-VL on ~1M GUI-grounding samples, and the paper argues — and benchmarks (including the new ScreenSpot grounding benchmark) — that GUI grounding is the bottleneck capability whose improvement directly raises downstream agent performance.

## Why this paper matters
This is one of the early, widely-cited papers establishing the "vision-only GUI agent" paradigm: an agent that observes a raw screenshot and emits a normalized click coordinate, with no HTML/accessibility-tree dependency. It introduces two artifacts that became reference points in the computer-use literature: (1) the idea of explicit GUI-grounding pre-training as the foundation for visual agents, and (2) ScreenSpot, the first cross-platform (mobile/desktop/web) grounding benchmark. For a harness-focused interest profile it is a clean, minimal instance of the screenshot-observation / coordinate-action loop, and its central empirical claim (grounding accuracy correlates with agent task success) is a load-bearing assumption behind much later work (CogAgent, UGround, OS-Atlas, etc.).

## Problem and gap
Prior GUI agents interact through structured text (HTML, DOM, Android view hierarchy). The paper identifies three concrete limitations of that approach (Intro, p1): (1) structured text is not always accessible (iOS, desktop apps); (2) it is verbose/inefficient as LLM context and omits layout, images, and icons; (3) its variety (HTML/DOM/VH) forces task-specific observation and action spaces. The proposed alternative is a purely visual agent. The preliminary finding (Sec 3, p2-3) is that the blocker for visual agents is *GUI grounding* — locating a screen element from an instruction — a capability that existing LVLMs, even those with natural-image grounding (Qwen-VL, GPT-4V), perform poorly on because GUI screenshots differ from natural images (dense text, many icons/widgets). The benchmark gap: prior UI-grounding research was largely confined to one 2017 Android dataset (RICO/Deka et al.), with no realistic cross-platform evaluation.

## Core idea
Reformulate grounding as language generation: given screenshot `s` and instruction text `x`, the LVLM directly generates the location `y` as natural-language numbers, e.g. `click (0.49, 0.40)`, optimized by ordinary cross-entropy — no special coordinate-token vocabulary (contrast with the 1000-bin approaches of Pix2Act/VisionLLM) (Sec 3.1, p3-4). Coordinates are two-decimal ratios in [0,1]. SeeClick is produced by *continual pre-training* of Qwen-VL on ~1M GUI samples (web grounding/OCR auto-curated from Common Crawl, mobile grounding reorganized from public datasets, plus LLaVA general VL data), then fine-tuned per downstream task. The thesis: a model that grounds well becomes a good agent, so invest pre-training in grounding rather than agent-specific tricks.

## Harness relevance
- Environment or workspace: GUI screens across iOS, Android, macOS, Windows, and web; downstream RL/agent environments are MiniWob (Chrome-based simplified web), AITW (Android), Mind2Web (real websites, replayed from raw dump).
- Observation interface: screenshot ONLY. Qwen-VL backbone, resolution 448x448 (Sec 3.3, p4). No HTML / accessibility tree at inference. For Mind2Web the long page captures are cropped to a fixed 1920x1080 around target elements for training/eval (App C.4, p14-15).
- Action interface: model emits an action with `action_type` id and a normalized coordinate. Action space (App C.1, p13-14): `click(x,y)` [id 4], `type("text")` [3], `select("value")` [2], `swipe(direction)` [1/0/8/9], PRESS BACK [5], PRESS HOME [6], PRESS ENTER [7], plus TASK COMPLETE / TASK IMPOSSIBLE states. Click is realized purely as predicted coordinates falling inside the target element's box — this is the central evaluation criterion for "correct click."
- Tool/API/shell/GUI layer: none beyond the screenshot+coordinate interface; deliberately no GUI metadata. This is the paper's main selling point vs prior GPT-4V agents (AppAgent, MM-Navigator) that still consumed metadata.
- Planner/executor/verifier/search structure: none. Single LVLM does end-to-end next-action prediction conditioned on instruction + screenshot + last k=4 actions (App C.1, p14). No explicit planner, verifier, or search.
- Evaluation harness: ScreenSpot for grounding (click-in-box accuracy). Downstream: MiniWob success rate over 50 seeds/task; AITW screen-wise action-matching score + ClickAcc; Mind2Web Ele.Acc / Op.F1 / Step SR. Metrics largely follow the original benchmark authors.
- Training harness: continual pre-training of Qwen-VL-Chat, visual encoder gradients unlocked + LoRA, AdamW, cosine schedule, init LR 3e-5, global batch 64, ~10k steps (~1 epoch), ~24h on 8x A100 (Sec 3.3 + App A.2, p4/p12).
- Logging/trace/reproducibility: code/data/models open-sourced (github.com/njucckevin/SeeClick); the re-split AITW train/val/test promised to be released. No trajectory-logging or determinism mechanism described.
- Safety or permission mechanism: none implemented. Ethics section (p9) only discusses privacy, real-world action safety, and bias qualitatively.

## Method
- Grounding-as-generation: predict `p(y|s,x)` for grounding and `p(x|s,y)` for OCR/captioning; coordinates emitted as plain-text numbers (Sec 3.1).
- Data construction (Sec 3.2, App A.1, p4/p12): Web — ~300k Common Crawl pages; elements taken from (a) visible-text elements and (b) elements with a `title` attribute, yielding interactable element + instruction pairs; tasks text_2_point (271K), text_2_bbox (54K), point_2_text (54K), bbox_2_text (54K). Mobile — widget captioning data from Li et al. 2020b (~20k screenshots / 40k widgets / 100k descriptions) reversed into grounding; plus RICO-derived elements; tasks text_2_point (274K), text_2_bbox (56K), UI summarization (48K, Screen2Words), widget captioning (42K). General — LLaVA instruction data (145K). Total ~1M. Point prediction was found slightly better than bbox, so its proportion was increased.
- Backbone & training: Qwen-VL chosen for existing grounding ability + 448x448 resolution; LoRA fine-tune of both vision encoder and LLM (Sec 3.3 / App A.2).
- ScreenSpot benchmark (Sec 4, App B, p5/p12-13): >600 screenshots, 1200+ instructions across iOS, Android, macOS, Windows, web; explicitly includes both Text and Icon/Widget element types (Icon/Widget harder). Web pages drawn from WebArena categories (development, shopping, forum, tools). Four PhD/master annotators captured screens during routine use, drew bounding boxes, wrote English commands; curated to be novel / not in existing training resources; personal info removed. Metric: click point inside ground-truth bounding box.

## Experimental setup
- Datasets/benchmarks: ScreenSpot (grounding); MiniWob, AITW, Mind2Web (downstream agent tasks).
- Baselines: ScreenSpot — MiniGPT-v2, Qwen-VL, GPT-4V (generalist), Fuyu, CogAgent (GUI-specific). MiniWob — CC-Net, WebN-T5, MM-WebN-T5, WebGUM (text/HTML+image), Pix2Act (only prior pure-vision method), Qwen-VL. AITW — ChatGPT-CoT, PaLM2-CoT, GPT-4V, Qwen-VL. Mind2Web — MindAct (+gen), GPT-3.5-Turbo, GPT-4, Qwen-VL.
- Models: SeeClick is 9.6B (Qwen-VL size); CogAgent 18B for contrast.
- Metrics: as above (click-in-box accuracy; success rate; screen-wise match + ClickAcc; Ele.Acc/Op.F1/Step SR).
- Compute: ~24h on 8x A100 for pre-training (App A.2). Downstream fine-tune compute Not reported.
- Artifacts: model, data, code released; AITW instruction-wise split to be open-sourced.

## Key results
All numbers verified against the extraction tables.

- ScreenSpot grounding (Table 1, p5-6), average click accuracy: SeeClick **53.4%**, CogAgent (18B) 47.4%, Fuyu 19.5%, GPT-4V 16.2%, MiniGPT-v2 5.7%, Qwen-VL 5.2%. SeeClick best overall despite fewer params than CogAgent. Per-cell highlights: Mobile-Text 78.0%, Mobile-Icon/Widget 52.0% (both best); SeeClick trails CogAgent on Desktop-Text (72.2 vs 74.2) and Web-Text (55.7 vs 70.4). All models weak on Icon/Widget — the benchmark's hard axis.
- MiniWob (Table 2, p6): On the 45-task text-vs-vision overlap, SeeClick (Image, 2.8K) **73.6%** > WebGUM (HTML+Image, 2.8K) 65.5%; WebGUM at 347K reaches 86.1%. On the 35-task vision overlap, SeeClick **67.0%** > Pix2Act 64.6% using **<0.3%** of Pix2Act's 1.3M training data; CC-Net(Image) 23.4%, Qwen-VL 48.4%. SeeClick beats the Qwen-VL baseline by ~19 pts ("nearly 20 percentage points"), the paper's evidence that grounding pre-training, not the backbone, drives the gain. (Table 8 full 55-task means: SeeClick 0.712 vs Qwen-VL 0.564.)
- AITW (Table 3, p6-7), instruction-wise split: SeeClick Overall **59.3** vs Qwen-VL 54.3 and GPT-4V 50.5; ClickAcc **66.4 vs 57.4** for Qwen-VL — the stated "9% increase in click accuracy." On the original episode-wise split (Table 7, p14) SeeClick 76.2 is roughly comparable to CogAgent 76.9 / Auto-UI 74.3, which the authors attribute to overfitting on that split.
- Mind2Web (Table 4, p7-8), vision-only (w/o HTML): SeeClick vs Qwen-VL — Cross-Task Step SR **25.5 vs 13.3**, Ele.Acc 28.3 vs 15.9; Cross-Website Step SR 16.4 vs 9.2; Cross-Domain Step SR 20.8 vs 12.0. SeeClick "nearly doubles" Ele.Acc and Step SR over the Qwen-VL baseline (CLAIMED + EVIDENCE: holds for Cross-Task/Cross-Domain; ~1.8x not exactly 2x for Cross-Website). SeeClick still trails HTML-based MindAct (Cross-Task Step SR 52.0), which the authors concede.
- Grounding–agent correlation (Sec 5.2.4, Fig 6, p8): plotting several SeeClick checkpoints, improved ScreenSpot grounding consistently tracks higher MiniWob/AITW/Mind2Web scores. This is the paper's headline correlation claim. CLAIMED + EVIDENCE, but UNCLEAR in strength: Figure 6's underlying numbers/correlation coefficient are not in the extracted text, so the support is a qualitative trend across checkpoints rather than a quantified correlation. The cross-baseline story (Qwen-VL -> SeeClick gains everywhere) reinforces it.
- Unified vs separate training (Table 5, p8): joint training across the three tasks slightly degrades vs per-task (e.g. MiniWob 64.1 vs 67.0), so a single unified agent is feasible but not free.

## Evidence quality
The core claims are reasonably supported but with caveats:
- Grounding-correlates-with-agent-performance is shown two ways (checkpoint trend in Fig 6; SeeClick-vs-Qwen-VL deltas across all three tasks). This is suggestive, not a controlled causal test — grounding pre-training also changes general UI comprehension, so the isolated effect of "grounding" vs "more UI exposure" is not separated. No correlation statistic is reported in-text.
- ScreenSpot is curated to avoid training overlap and is human-annotated, which strengthens it, but it is small (>600 screens / 1200+ instructions) and single-coordinate accuracy is a coarse metric; baselines are evaluated with their own recommended prompts (App B.3), introducing prompt-sensitivity confounds, especially for GPT-4V.
- Fair-comparison handling is a genuine strength: MiniWob is split into matched task subsets, and AITW is re-split instruction-wise to expose the overfitting risk of the standard episode-wise split — an honest move that lowers the headline AITW number.
- No statistical significance / variance reporting beyond MiniWob's 50-seed averaging. Mind2Web shows the approach still clearly trails HTML-based agents, which the paper states plainly rather than hiding.
- Ablations on data composition (web vs mobile vs general, point vs bbox) are mostly qualitative remarks (App A.1) rather than tables.

## Reproducibility and artifacts
- Code: github.com/njucckevin/SeeClick (stated available).
- Data: ~1M pre-training mix described with per-task counts (Table 6); web crawl from Common Crawl; mobile from public datasets (widget captioning, RICO, Screen2Words); general from LLaVA. ScreenSpot released; AITW instruction-wise split to be released.
- Models: SeeClick (Qwen-VL-Chat + LoRA), 9.6B.
- Environment: 8x A100, ~24h pre-train; AdamW, cosine, LR 3e-5, batch 64, ~10k steps.
- License: Not reported in extraction.
- Exact commands or setup: Not reported (prompt templates given for grounding and agent steps, App A/C).
- Missing details: downstream fine-tune hyperparameters/compute; exact Common Crawl snapshot; Figure 6 raw correlation values; per-task fine-tuning data sizes for AITW/Mind2Web.

## Strengths
- Clean, influential framing: grounding as the foundational capability; coordinate-as-text generation is simple and avoids special tokenization.
- Strong data-efficiency result on MiniWob (beats Pix2Act with <0.3% data; beats WebGUM at equal 2.8K).
- ScreenSpot is a genuinely new, realistic, cross-platform grounding benchmark with explicit Icon/Widget hardness.
- Honest evaluation choices (matched MiniWob subsets; instruction-wise AITW re-split exposing overfitting; admitting it trails HTML agents on Mind2Web).
- Fully metadata-free inference (screenshot only), making it platform-universal.

## Weaknesses and limitations
- Author-stated (Limitations, p9): action space simplified to mainly click/type, excluding drag and double-click; agent-specific fine-tuning is still required for multi-step tasks (not zero-shot).
- The central grounding->agent correlation is demonstrated qualitatively; no quantified correlation, and the confound between "grounding" and "general UI pre-training exposure" is not isolated.
- Low backbone resolution (448x448) limits fine-grained/desktop-web text grounding (it loses to CogAgent there) and forces cropping hacks on Mind2Web's long pages.
- ScreenSpot is small; baseline-specific prompting may bias cross-model comparison.
- No verifier/planner/recovery; single-shot coordinate prediction with k=4 action memory only. No safety/permission layer.
- Mind2Web absolute performance remains far below HTML-based agents — vision-only real-web navigation is still hard.

## Relationship to prior work
- Closest vision-based predecessor: **Pix2Act** (Shaw et al. 2023) — the only prior pure-vision GUI approach; SeeClick beats it with far less data and uses text-number coordinates instead of binned tokens. **CogAgent** (Hong et al. 2023) — concurrent GUI-specific LVLM, larger (18B), higher resolution, used as the main ScreenSpot competitor (SeeClick wins on average, loses on some desktop/web text). **Fuyu** — GUI-capable LVLM baseline.
- Backbone: **Qwen-VL** (Bai et al. 2023), which SeeClick continually pre-trains; Qwen-VL is also the controlled baseline isolating the grounding-pre-training effect.
- HTML/text agents it contrasts against: MindAct/Mind2Web (Deng et al.), WebGUM (Furuta et al.), Synapse (Zheng et al., source of MiniWob trajectories), GPT-4V metadata-based agents (AppAgent, MM-Navigator).
- Genuinely new: GUI-grounding pre-training as an explicit recipe + the ScreenSpot benchmark + the grounding/agent-performance correlation thesis. Incremental: the agent loop itself (screenshot -> next action) and coordinate-as-text generation both build directly on Qwen-VL / prior LVLM grounding.

## What I should read
- Must read: Sec 3 (grounding-as-generation + data construction), Sec 4 (ScreenSpot design), Table 1 and Sec 5.2.4/Fig 6 (the correlation claim).
- Skim: Tables 2-4 (downstream numbers), App C.1 (action space + agent prompt formulation — useful for harness comparison).
- Can skip: full MiniWob per-task table (Table 8) and the qualitative case-study figures unless debugging specific behaviors.
- Follow-up papers: CogAgent, UGround / SeeClick-successor grounding models, OS-Atlas, Mind2Web and WebArena originals, AITW (Rawles et al.).

## Triage decision
Label: READ_SOON
Rationale: Foundational, frequently-cited reference for the screenshot-only GUI agent paradigm and for the ScreenSpot grounding benchmark; directly relevant to harness/computer-use interests (clean observation=screenshot, action=coordinate loop). Evidence is solid though the headline correlation is qualitative. Not MUST_READ only because the method is now superseded by higher-resolution successors, but the conceptual framing and benchmark remain worth a careful pass.
Confidence: high
Reading time estimate: ~45-60 min for main body + ScreenSpot/agent-formulation appendices.

## Personal notes
The cleanest takeaway for harness design: the entire agent contract is "screenshot in, normalized click/type out, k=4 action history" with zero metadata — a useful minimal baseline to compare richer accessibility-tree harnesses against. ScreenSpot's Icon/Widget vs Text split is the most reusable diagnostic here. Watch the resolution bottleneck: many later gains come simply from feeding higher-res / tiled screenshots.

## Follow-up actions
- Add related paper: CogAgent (arXiv 2312.08914); Pix2Act (Shaw et al. 2023).
- Compare with: later grounding models (UGround, OS-Atlas) on ScreenSpot.
- Re-run after new version: check if v2/successor adds drag/double-click or higher resolution.
- Check code: github.com/njucckevin/SeeClick (data curation scripts + ScreenSpot eval).
- Read benchmark details: App B (ScreenSpot annotation/evaluation) before using ScreenSpot numbers elsewhere.
