# CoCo-Agent: A Comprehensive Cognitive MLLM Agent for Smartphone GUI Automation

## Metadata
- Canonical key: arxiv-2402.11941
- Version: v1
- Fetch date: 2026-06-06T07:57:29Z
- Source: arxiv
- PDF: library/coco-agent-a-comprehensive-cognitive-mllm-agent-240211941/v1/paper.pdf
- Venue: Annual Meeting of the Association for Computational Linguistics (ACL 2024 Findings)
- Year: 2024
- Authors: Xinbei Ma, Zhuosheng Zhang, Hai Zhao
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
A fine-tuned LLaVA-based (LLaMA-2-chat-7B + CLIP) smartphone GUI agent that pairs a multi-source environment representation (screenshot + OCR layouts + action history) with a top-down decomposed action format, reaching reported SOTA action accuracy of 79.05% on AITW and 88.27% on META-GUI (p6, Tables 3-4).

## Why this paper matters
This is a representative point in the "trainable open-source MLLM GUI agent" line (as opposed to GPT-4V-prompting agents), directly relevant to a harness perspective on Android device-control agents. Its central thesis - that cheap textual OCR layouts are a more effective "high-resolution module" than fancier vision encoders for GUI grounding (p7, Table 7) - is a load-bearing design claim worth understanding before building or evaluating any single-screen GUI agent. It also surfaces a measurement problem (label-match metrics underestimate agents because multiple valid action paths exist), which is a recurring concern for the whole AitW-style benchmark family.

## Problem and gap
CLAIMED problem: GUI agents need "comprehensive cognition" = exhaustive perception + reliable action response (abstract, p1). The authors frame two gaps:
1. Reliance on strong proprietary (M)LLMs (GPT-4V, ChatGPT) is brittle: domain mismatch between GUI commands and natural language, black-box API privacy/safety risk, and heavy dependence on prompt engineering (p1, sec 1).
2. Insufficient GUI environment modeling: vision encoders are low-resolution (e.g. 224x224) and pretrained for high-level captioning, so small but semantically loaded icons (a magnifier = "search") are missed; and the finite input window forces a visual/textual length trade-off (p1-2, sec 1).

EVIDENCE for the gaps: the gaps are argued conceptually plus supported downstream by the ablation (layouts and history each add ~5-6% action accuracy, Table 5) and the vision-encoder comparison (Table 7). UNCLEAR: the "API safety/privacy" argument is asserted, not measured - no experiment quantifies it. This is positioning rhetoric, not evidence.

## Core idea
Two design choices layered on a standard LLaVA backbone:

- Comprehensive Environment Perception (CEP): the textual prompt fuses goal g, OCR layouts L (item name + coordinate, e.g. "ICON_SETTINGS: [0.1783, 0.8701]"), and the last h historical actions, while the screenshot goes through CLIP. So the screen is perceived twice - holistically via the image and fine-grained via OCR text (p4, sec 3.3; Eq. 3). h = 8 in the main runs (Appendix A, p11).
- Conditional Action Prediction (CAP): instead of emitting the raw AITW JSON command with all redundant fields (action type, touch point, lift point, typed text), the action is refactored into a natural-language, top-down sequence: first the action TYPE, then the TARGET conditioned on type. The ambiguous AITW dual_point is split into three concrete types - scroll (endpoints far apart), click (tap inside a bounding box, with item name), tap (no matching box) (p4, sec 3.4; Table 1).

A normalization step snaps click targets to the centroid of the OCR bounding box and scrolls to four cardinal swipes (p4). The training objective is plain cross-entropy on the output sequence (Eq. 2, p3).

WHY-read: the genuinely novel/transferable part is the claim that OCR layout text substitutes for a high-resolution vision module, plus the conditional action factorization. The backbone itself is off-the-shelf.

## Harness relevance
- Environment / workspace: Android smartphone GUI automation. Two offline, static benchmarks - AITW (AndroidInTheWild) and META-GUI. These are recorded episode datasets, not live emulators; the agent does single-step next-action prediction against logged screens, NOT closed-loop control of a device.
- Observation interface: per step the agent receives (i) the current screenshot (CLIP, encoded to a 256-length / 4096-hidden vector, p7), (ii) OCR layouts as (item name, coordinate) text lines, (iii) up to 8 previous full actions, (iv) the goal. Prompt template in Appendix A (p11). No future screens are seen.
- Action interface: a finite command set - PRESS_HOME / PRESS_BACK / PRESS_ENTER / STATUS_TASK_COMPLETE / TYPE / DUAL_POINT (refactored into SCROLL / CLICK / TAP). Coordinates are normalized floats in [0,1]. Output is the CAP natural-language action line, parsed back to JSON for scoring (Table 1, p4; sec 4.2, p5).
- Tool/API/shell/GUI layer: the only external tool is OCR (used to build layouts and to normalize click targets). No app APIs, shell, or accessibility-tree beyond OCR-derived text.
- Planner/executor/verifier/search structure: none. Single forward pass produces one action; CAP's "decomposition" is sequential token generation within one output, not a multi-module planner. No verifier, no search. A "future actions" probe (predict n-next without intermediate states) shows planning is weak: 70.96% (1-next) collapses to 37.74% (3-next) (Table 8, p7).
- Evaluation harness: step-level action accuracy following Rawles et al. 2023. A coordinate is correct if it lands in the same bounding box or within 14% screen distance; scroll correct if main direction matches; typed text correct if the label is contained in the prediction; META-GUI also uses F1 (input text) and BLEU (utterances). An action is correct only if all JSON fields match (sec 4.2, p5).
- Training harness: full supervised fine-tuning of LLaVA (LLaMA-2-chat-7B + CLIP ViT-L/14). Max input length 2048; 8/10/12 epochs; lr 2e-5; batch 12/16 per device; 4x Nvidia A800 GPUs. AITW trained both per-subset ("separate") and jointly ("unified") (sec 4.2 p5; Appendix A p11).
- Logging/trace/reproducibility: code released at github.com/xbmxb/CoCo-Agent. Hyperparameters and prompt template given. No per-run seeds, variance, or trace logs reported.
- Safety/permission mechanism: none implemented. The Ethics Statement (p9) argues qualitatively that GUI (vs CLI) is more interpretable and that not using LLM APIs preserves privacy, but no permission/guard mechanism exists in the system.

## Method
1. Backbone: LLaVA = LLaMA-2-chat-7B decoder + CLIP image encoder + one-layer linear projector mapping image features into the text embedding space; concatenate image and text embeddings, decode, cross-entropy loss (Eq. 2, p3).
2. CEP builds the textual input from goal + OCR layout lines + last 8 actions, alongside the raw screenshot (sec 3.3).
3. CAP rewrites each ground-truth action into a decomposed natural-language line, splitting dual_point into scroll/click/tap (sec 3.4, Table 1).
4. Normalization aligns click coordinates to OCR box centroids and scrolls to 4 directions (sec 3.4).
5. Train per-subset and unified; evaluate step-level action accuracy.

## Experimental setup
- Datasets: AITW (715K episodes, 30K intentions, 5 subsets: General/Install/GoogleApps/Single/WebShopping) and META-GUI (1K episodes, ~18K steps, 11 apps / 6 domains, with agent<->user dialogue turns) (sec 4.1, Table 2, p5). Splits 8:1:1; first 1000 test samples used as validation (Appendix A).
- Baselines (AITW): PaLM-2 and ChatGPT (5-shot, pseudo-HTML); MM-Navigator (GPT-4V, few-shot SOTA); Behavioural Cloning (BERT-based); LLaMA-2 (text-only, pseudo-HTML); Auto-UI (T5+BLIP); CogAgent (9B visual LLM, prior trained SOTA); and an LLaVA-unified ablation baseline (sec 4.3, p5).
- Baselines (META-GUI): LayoutLM, LayoutLMv2, BERT, m-BASH (prior SOTA, Faster R-CNN + ROI pooling), plus LLaVA and LLaVA w/ history (sec 4.3).
- Models: CoCo-Agent at 7B (LLaVA backbone).
- Metrics: step-level action accuracy (all-fields match), plus parameter-level breakdowns (action type, item, direction, input F1, utterance BLEU).
- Compute: 4x A800; lr 2e-5; 8-12 epochs.
- Artifacts: code released; CLIP = openai/clip-vit-large-patch14.

## Key results
VERIFIED against extraction (all from Tables 3-5, p6-7):
- AITW Overall action accuracy: CoCo-Agent unified = 79.05, separate = 77.82. Beats CogAgent 76.88, Auto-UI unified 74.27, BC w/ history 73.1, LLaVA-unified 70.37, MM-Navigator (GPT-4V) ~52.96 (Table 3). Per-subset unified: General 70.96, Install 81.46, GoogleApps 76.45, Single 91.41, WebShopping 75.00. (Note: lower-half Table 3 lists GoogleApps 75.30 and WebShopping 76.10 for the parameter-breakdown rows - a minor internal inconsistency with the top table's 76.45 / 75.00.)
- Single is the one subset where CoCo-Agent does NOT top all baselines - CogAgent reaches 93.49 vs CoCo-Agent 91.41 (p5-6 text confirms "except for Single subset").
- META-GUI action accuracy: CoCo-Agent = 88.27, vs m-BASH 82.74 (prior SOTA), LLaVA w/ history 81.08 - roughly a 12-point gain in action accuracy and a large item-accuracy jump (91.72 vs 85.90). Utterance BLEU 65.90 is below LLaVA's 67.24, so dialogue generation did not improve (Table 4, p6).
- Ablation (Table 5, p7, on AITW General / META-GUI): adding CAP +0.66 (57.81->58.47 General); adding Layouts +5.82 (58.47->64.29); adding 8 full-action history +5.63 (64.29->69.92, via 8-act-types 67.80). Layouts and history are the dominant contributors. VERIFIED: layouts +5.82%, action history +5.63%.
- Vision-encoder comparison (Table 7, p7, General subset): CoCo-Agent (CLIP + Layout) = 71.0, beating CogAgent's high-res cross module 65.4, Auto-UI 65.9, LLaVA 58.9, mPLUG 53.0. Supports the "OCR layouts beat fancier vision modules" claim.
- Replacement probe (Table 6, p7): corrupting layouts or action history hurts action accuracy most (70.96 -> ~57.55 / 58.45); corrupting the image hurts least (-> 59.69), because layouts compensate.
- Realistic-potential human study (p8): of first 500 General actions, 118 (23.6%) differ from labels, but only 54 (10.8%) strictly contradict the episode; the rest stay goal-consistent, implying the metric underestimates the agent.

## Evidence quality
- The headline accuracy claims are well supported by side-by-side tables against strong, current baselines (CogAgent, Auto-UI, MM-Navigator), and the core design claims (layouts > extra vision; history matters) are backed by both an ablation and a replacement probe - good internal triangulation.
- Weaknesses: (i) no variance/seeds/significance, so the 79.05 vs CogAgent 76.88 margin has no error bars. (ii) Evaluation is single-step, offline, label-match against recorded episodes - it never executes a full episode on a device, and the authors themselves flag this underestimation (sec 5.4.2) and the weak future-action prediction (Table 8). (iii) The internal table mismatch on GoogleApps/WebShopping (top vs bottom of Table 3) is unexplained. (iv) META-GUI dialogue quality (BLEU) did not improve, undercutting the "comprehensive" framing for the conversational setting. (v) Parameter count comparability is loose - CoCo-Agent 7B vs CogAgent 9B is noted but other-baseline sizes are uneven.

## Reproducibility and artifacts
- Code: github.com/xbmxb/CoCo-Agent (CLAIMED released).
- Data: AITW and META-GUI are public; splits specified (8:1:1; Single split from Auto-UI).
- Models: LLaVA / LLaMA-2-chat-7B / openai/clip-vit-large-patch14 - all public.
- Environment: 4x Nvidia A800.
- License: Not reported.
- Exact commands or setup: prompt template + hyperparameters given (Appendix A); no run scripts in the paper text.
- Missing details: OCR engine/version not named; seeds/variance absent; exact epoch/batch chosen per subset ("{8,10,12}", "{12,16}") left as ranges.

## Strengths
- Strong, clearly tabulated results vs current trained and API baselines on two benchmarks.
- A genuinely useful, transferable finding: cheap OCR layout text functions as a high-resolution complement, outperforming heavier vision encoders (Table 7).
- Good ablation + replacement-probe design isolating the contribution of each input channel.
- Honest discussion of metric underestimation and weak multi-step planning.
- Open weights/backbone and released code; no proprietary API dependency.

## Weaknesses and limitations
- Authors' stated: large data / training cost vs zero-shot methods; future-action (multi-step) prediction remains poor (Limitations, p9).
- Inferred: purely offline single-step evaluation - no closed-loop device execution; no error bars; dialogue (BLEU) not improved on META-GUI; internal table inconsistency; OCR dependence is a hidden pipeline component whose errors are not analyzed; "safety/privacy" advantages are asserted, not measured.

## Relationship to prior work
- Closest: Auto-UI (Zhang & Zhang 2023) - same trainable-MLLM, screenshot-driven AITW line; CoCo-Agent adds OCR layouts + CAP and a 7B LLaVA backbone. CogAgent (Hong et al. 2023) - the prior trained SOTA using a dedicated high-resolution cross-attention vision module; CoCo-Agent argues OCR text replaces that module more cheaply. MM-Navigator (Yan et al. 2023) - GPT-4V prompting agent, the few-shot API baseline. m-BASH (Sun et al. 2022) - prior META-GUI SOTA.
- Genuinely new: the OCR-layout-as-high-res-module insight and the conditional/top-down action refactoring. Incremental: the backbone (LLaVA) and the benchmark/metric protocol (inherited from AITW).

## What I should read
- Must read: sec 3.3-3.4 (CEP/CAP, Table 1); Tables 3-5 (main results + ablation, p6-7); Table 7 (vision-encoder comparison, p7); sec 5.4.2 (metric underestimation, p8).
- Skim: sec 5.2-5.3 (visual capability, future actions); Appendix A prompt template/example (p11-12) if implementing.
- Can skip: Related Work (sec 2) unless surveying; Ethics/Future Work boilerplate.
- Follow-up papers: Auto-UI, CogAgent, AITW (Rawles 2023), META-GUI (Sun 2022), MM-Navigator.

## Triage decision
Label: READ_SOON
Rationale: Directly relevant to Android GUI-agent harness design; the OCR-layout-vs-vision-module result and the action-decomposition format are concrete, reusable ideas, and the metric-underestimation discussion matters for evaluating any AITW-family agent. Not MUST_READ because it is single-step/offline with no closed-loop or planning component and the backbone is standard. Evidence supports the headline claims, consistent with keeping the prepared label.
Confidence: high
Reading time estimate: 35-45 min for the must-read sections.

## Personal notes
The strongest takeaway for harness work: a good accessibility/OCR text layer can outweigh a bigger vision encoder for single-screen GUI grounding - relevant when deciding how to build the observation interface. Watch the offline-vs-online gap: 79.05% step accuracy is NOT episode success, and 3-next drops to 37.74%, so do not read these numbers as end-to-end task completion.

## Follow-up actions
- Add related paper: Auto-UI, CogAgent, AITW, META-GUI, MM-Navigator
- Compare with: CogAgent (high-res vision module vs OCR layouts), Auto-UI (same line, no layouts/CAP)
- Re-run after new version: arXiv v3 (2 Jun 2024) is the extracted text; check for newer revisions
- Check code: github.com/xbmxb/CoCo-Agent (OCR engine, training scripts, seeds)
- Read benchmark details: AITW metric definition (14% screen-distance correctness) and META-GUI dialogue eval
