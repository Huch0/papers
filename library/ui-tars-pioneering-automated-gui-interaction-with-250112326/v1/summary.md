# UI-TARS: Pioneering Automated GUI Interaction with Native Agents

## Metadata
- Canonical key: arxiv-2501.12326
- Version: v1
- Fetch date: 2026-06-06T07:14:14Z
- Source: arxiv
- PDF: library/ui-tars-pioneering-automated-gui-interaction-with-250112326/v1/paper.pdf
- Venue: arXiv
- Year: 2025
- Authors: Yujia Qin, Yining Ye, Junjie Fang, Haoming Wang, Shihao Liang, Shizuo Tian, Junda Zhang, Jiahao Li, Yunxin Li, Shijue Huang, Wanjun Zhong, Kuanye Li, Jiale Yang, Yu Miao, Woyu Lin, Longxiang Liu, Xu Jiang, Qianli Ma, Jingyu Li, Xiaojun Xiao, Kai Cai, Chuang Li, Yaowei Zheng, Chaolin Jin, Chen Li, Xiao Zhou, Minchao Wang, Haoli Chen, Zhaojian Li, Haihua Yang, Haifeng Liu, Feng Lin, Tao Peng, Xin Liu, Guang Shi
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
UI-TARS is a single end-to-end vision-language model (built on Qwen-2-VL 2B/7B/72B, continually trained on ~50B tokens) that takes only screenshots as input and emits low-level GUI actions in a unified cross-platform action space, reportedly beating modular agent frameworks wrapped around GPT-4o and Claude on a range of perception, grounding, and online task-execution benchmarks.

## Why this paper matters
This is a flagship instance of the "native GUI agent model" thesis: that an end-to-end, data-driven model trained on perception + grounding + reasoning + action traces can outperform the prevailing paradigm of prompt-engineered, modular agent frameworks built on top of frozen commercial VLMs (p.3-5, p.7-9). For anyone working on computer-use/GUI agents, it consolidates (a) a unified pure-vision observation/action interface, (b) a concrete recipe for the data bottleneck (synthetic perception data, 6M filtered GUI tutorials, thought augmentation, online trace bootstrapping with reflection tuning and DPO), and (c) head-to-head numbers against Claude Computer Use and GPT-4o on OSWorld/AndroidWorld/Mind2Web/ScreenSpot. It is open-sourced (github.com/bytedance/UI-TARS, p.1), which makes it a reusable baseline and harness rather than just a closed result.

## Problem and gap
CLAIMED problem (p.3): GUI agents historically depend on textual representations (HTML, accessibility trees), which are platform-inconsistent, verbose, require system-level permissions, and scale poorly. Separately, most GUI systems are "agent frameworks" that modularize perception/grounding/memory/reasoning across components glued by hand-crafted prompts and workflows around a frozen VLM (e.g. GPT-4o). The paper argues frameworks are "design-driven" — fragile, high-maintenance, unable to update model parameters from new experience, and brittle on unfamiliar tasks (p.7-8 "Key Limitations of Agent Frameworks").

The GAP the paper targets: native (end-to-end, pure-vision) agent models are conceptually superior but underperform in practice because of (1) GUI-specific difficulties in perception, reasoning/planning, memory, and precise low-level action grounding, and (2) a fundamental data bottleneck — unified perception->reasoning->memory->action traces capturing expert workflow knowledge are historically scarce (p.3, p.20 §4.5). The paper's contribution is largely about manufacturing that missing data and a training pipeline to exploit it.

## Core idea
Train one model end-to-end so that, at each step, it consumes (task instruction, the last N=5 screenshot+thought+action tuples as short-term memory, current screenshot) and autoregressively emits an explicit "thought" t_n followed by an action a_n in a unified action space (p.14 Eq. 2-3). The "thought" is a ReAct-inspired but more structured System-2 deliberation step injected before every action. Four pillars (p.5-6):
1. Enhanced perception via a large synthetic GUI screenshot dataset with five task types: element description, dense captioning, state-transition captioning, QA, and set-of-mark prompting (§4.2, p.15-16).
2. Unified action modeling: one cross-platform action space (Table 1, p.17) trained on grounding data + multi-step traces (Table 2, p.17).
3. System-2 reasoning: enrich with ~6M filtered GUI tutorials, then "thought augmentation" of action traces via ActRe (reverse annotation conditioned on the action) and Thought Bootstrapping (forward sampling, keep the thought that yields the correct action) to avoid spurious thought-action alignment (§4.4, p.17-19).
4. Iterative learning from online traces: deploy the current model on hundreds of virtual machines, collect raw traces, filter (rule-based reward -> VLM scoring -> human review), fine-tune to produce M_{n+1}, plus reflection tuning (error-correction and post-reflection annotation) and Agent DPO over corrected-vs-erroneous action pairs (§4.5, p.20-22).
Training is three-phase: continual pre-training -> annealing (yields UI-TARS-SFT) -> DPO (yields UI-TARS-DPO), ~50B tokens total on Qwen-2-VL backbones (§4.6, p.22).

## Harness relevance
- Environment / workspace: GUI environments across web, desktop (Ubuntu/Windows/macOS), and mobile (Android). Online evaluation uses OSWorld (369 real web+desktop tasks across 3 OSes, screenshot-only mode, scores averaged over 3 runs) and AndroidWorld (116 tasks across 20 apps on a live Android emulator) (p.25-26).
- Observation interface: pure vision — raw device screenshots only, no HTML/DOM/a11y tree. History limited to last N=5 observations to fit a ~32k token budget; full prior thoughts+actions retained as short-term memory (p.14-15 §4.1).
- Action interface: unified action space (Table 1, p.17). Shared: Click(x,y), Drag(x1,y1,x2,y2), Scroll(x,y,direction), Type(content), Wait(), plus terminal Finished() and CallUser(). Desktop-specific: Hotkey(key), LeftDouble, RightSingle. Mobile-specific: LongPress, PressBack, PressHome, PressEnter. Coordinates are predicted as normalized relative coordinates (center of bounding box) for resolution invariance (§4.3, p.17).
- Native model vs agent-framework distinction: the central thesis. UI-TARS internalizes perception/grounding/reasoning/memory into one set of parameters (Stage 3 "Native Agent Model", p.8), contrasted explicitly with Stage 2 modular frameworks. Tables 4-9 separate baselines into "Agent Framework" vs "Agent Model" rows to make this comparison.
- Planner/executor/verifier structure: no external planner/verifier — planning ("thoughts": task decomposition, long-term consistency, milestone recognition, trial&error, reflection) is emitted in-model before each action (p.18-19, Fig. 6). Verification during training is external (rule-based reward, VLM scoring, human review in the online loop).
- Evaluation harnesses: perception (VisualWebBench, WebSRC, ScreenQA-short); grounding (ScreenSpot, ScreenSpot v2, ScreenSpot Pro); offline agent (Multimodal Mind2Web, AndroidControl Low/High, GUI Odyssey); online agent (OSWorld, AndroidWorld) (§5).
- Training harness: synthetic perception/grounding data from a screenshot+metadata parsing pipeline; 6M-tutorial reasoning corpus filtered from MINT/OmniCorpus via fastText + LLM filtering + dedup; thought augmentation (ActRe + bootstrapping); online bootstrapping on hundreds of VMs with multi-stage filtering; reflection tuning (SFT on corrected steps only) and Agent DPO (Bradley-Terry preference over corrected vs erroneous actions) (§4.2-4.6).
- Logging/trace/reproducibility: traces logged in structured (screenshot, element box, metadata) and (o,t,a) tuple formats; code/models open-sourced. However exact training data, VM infrastructure, and hyperparameters are largely "Not reported" in numeric detail.
- Safety/permission mechanism: CallUser() terminal action for cases requiring human intervention (e.g. login/authentication) is the only explicit safety/permission affordance (Table 1, p.16-17). No broader safety/guardrail discussion.

## Method
See Core idea. Key method specifics verified against the text:
- Perception data built bottom-up (element -> dense caption -> state transition -> QA -> SoM) from auto-crawled + human-assisted screenshots with extracted metadata (element type, depth, bounding box, text) (§4.2).
- Action/grounding data: Table 2 (p.17) reports open-source grounding counts of 14.8M (web), 2.5M (mobile), 1.1M (desktop) elements and trace counts of 6.4k (web), 145k (mobile) traces; the authors' own annotated data rows are marked "*" (counts not disclosed). Average trace steps: web 6.7, mobile 9.6, ours 14.9.
- Reasoning enrichment: ~6M GUI tutorials, averaging 510 text tokens and 3.3 images each (p.18).
- Thought augmentation handles a real failure mode (reverse-annotated thoughts can match actions only superficially) via bootstrapping with an early checkpoint UI-TARS_early; thoughts annotated in both Chinese and English; vanilla no-thought traces also retained (p.18-19).
- Online loop: M_n executes instruction set I_n on VMs -> raw traces -> 3-stage filter -> fine-tune to M_{n+1}; instructions iteratively refined by humans (HumanRefine) (p.20).
- Reflection tuning: error-correction pairs (T-/T+ at error step tau) and post-reflection pairs (correcting the step after the error, acknowledging the prior mistake); SFT loss computed only on corrected steps (p.21).
- Agent DPO: Bradley-Terry preference of corrected action over erroneous action, standard DPO objective with KL constraint to the SFT policy (p.21-22).

## Experimental setup
- Models: UI-TARS-2B, -7B, -72B, all continual-trained from Qwen-2-VL (2B/7B/72B) on ~50B tokens. SFT (post-annealing) and DPO variants both reported; DPO reported only where it helps most (OSWorld) (§4.6, §5.4).
- Baselines (p.22): commercial — GPT-4o, GPT-4/GPT-4V, Claude-3.5-Sonnet / Claude Computer-Use, Gemini-1.5-Pro, Gemini-2.0 (Project Mariner); academic/open — CogAgent, OmniParser, InternVL, Aria-UI, Aguvis (7B/72B), OS-Atlas (4B/7B), UGround, ShowUI, SeeClick, Qwen-VL/Qwen2-VL, UIX-Qwen2-7B, Qwen-VL-Max.
- Metrics: perception (accuracy / task scores); grounding (point-in-bounding-box accuracy); offline agent (Element Accuracy, Operation F1, Step Success Rate for Mind2Web; Type/Grounding/SR for AndroidControl & GUI Odyssey); online agent (task success rate). System-1 vs System-2 ablation uses Best-of-N (N=1,16,64) step success rate (§5.5).
- Compute/cost: "hundreds of virtual machines" for online bootstrapping; ~50B training tokens. Exact GPU count, training time, and dollar cost are Not reported.
- Implementation/artifacts: open-sourced at github.com/bytedance/UI-TARS (p.1). Exact training data and configs not fully released in the paper text.

## Key results
Verified numbers from the extraction (page anchors in parentheses):
- OSWorld (online, screenshot-only) — THE headline result (Table 9, p.26): UI-TARS-72B-DPO scores 24.6 at 50 steps and 22.7 at 15 steps, vs Claude Computer-Use 22.0 (50 steps) and 14.9 (15 steps). UI-TARS-72B-SFT = 18.8 (15 steps); UI-TARS-7B-DPO = 18.7, -7B-SFT = 17.7 (15 steps). GPT-4o (agent model) = 5.0. Note the 24.6@50 and 22.7@15 results use the DPO model; SFT-only numbers are lower.
- AndroidWorld (online, Table 9, p.26): UI-TARS-72B-SFT = 46.6, beating GPT-4o (SoM) 34.5 and the best framework GPT-4o+Aria-UI 44.8, and far above agent-model Aguvis-72B 26.1.
- Perception (Table 3, p.23): UI-TARS-72B = 82.8 on VisualWebBench (> GPT-4o 78.5, Claude-3.5 78.2); UI-TARS-7B leads WebSRC at 93.6; UI-TARS-72B leads ScreenQA-short at 88.6.
- Grounding ScreenSpot Pro (Table 4, p.23): UI-TARS-72B = 38.1 avg (SOTA), vs UGround-V1-7B 31.1, OS-Atlas-7B 18.9, Claude Computer Use 17.1, GPT-4o 0.8. Clear scaling: 2B 27.7 -> 7B 35.7 -> 72B 38.1.
- Grounding ScreenSpot (Table 5, p.24): UI-TARS-7B = 89.5 avg (best UI-TARS), 72B 88.4, 2B 82.3; competitive with Aguvis-72B 89.2.
- Grounding ScreenSpot v2 (Table 6, p.24): UI-TARS-7B = 91.6, 72B 90.3, both > OS-Atlas-7B 87.1.
- Offline Multimodal Mind2Web (Table 7, p.25): UI-TARS-72B SOTA on Step SR — Cross-Task 68.6, Cross-Website 63.5, Cross-Domain 62.1; UI-TARS-7B (e.g. 67.1 Cross-Task SR) surpasses Aguvis-72B and Claude.
- Offline AndroidControl / GUI Odyssey (Table 8, p.25): UI-TARS-72B AndroidControl-Low SR 91.3, High SR 74.7, GUI Odyssey SR 88.6; ~25-point absolute SR gain over prior SOTA OS-Atlas-7B on GUI Odyssey (62.0 -> 88.6) per the authors (p.24).
- System-1 vs System-2 (Fig. 8, §5.5, p.26-27): at N=1, System-2 is slightly worse than System-1 on the three in-domain benchmarks; at N=16/64, System-2 overtakes System-1; on OOD AndroidWorld at Bo1, System-2 clearly beats System-1. Scaling 7B->72B helps online far more than offline.

Qualitative claims: DPO meaningfully improves OSWorld over SFT (negative samples help distinguish optimal/suboptimal actions); Claude transfers well to web but poorly to mobile, whereas UI-TARS does both (p.24).

## Evidence quality
- WELL SUPPORTED: The core CLAIM (a native end-to-end model can match/beat framework + commercial-VLM setups) is backed by consistent wins across 10+ benchmarks, with baselines cleanly split into framework vs model rows. The OSWorld 15-step vs 50-step comparison against Claude is a fair-ish efficiency argument and is the strongest single piece of evidence. ScreenSpot Pro 38.1 SOTA and the clear grounding scaling curve are convincing.
- PARTIALLY SUPPORTED / caveats: The abstract attributes "24.6 / 22.7 outperforming Claude 22.0 / 14.9" to "UI-TARS" without flagging that these are the DPO model and that DPO is applied selectively (only OSWorld benefits per §5.4); SFT-only OSWorld is 18.8@15. AndroidWorld 46.6 is the SFT model, while Claude Computer-Use there is only 27.9 and GPT-4o 34.5 — but the strongest framework (GPT-4o+Aria-UI 44.8) is close, so the "surpassing GPT-4o" framing understates the nearest competitor. Numbers checked: all headline figures match the tables.
- UNCLEAR / weak: (a) No statistical variance reported except OSWorld being averaged over 3 runs; no error bars on tables. (b) Potential train/eval overlap — Mind2Web, AndroidControl, GUI Odyssey are explicitly in-domain (have corresponding training data, p.26), so their offline wins partly reflect supervised fitting rather than generalization; the authors themselves note offline benchmarks may not capture real capability. (c) The authors' own annotated grounding/trace data volumes are masked ("*", Table 2), so the data-scale claim is not fully auditable. (d) Continual pre-training started from Qwen-2-VL, so some gains may inherit from a strong backbone; no ablation isolates backbone vs UI-TARS data. (e) No ablation isolating the contribution of each of the four pillars (perception data vs tutorials vs thought augmentation vs online/DPO), beyond the System-1/2 and SFT-vs-DPO comparisons. (f) "Hundreds of VMs" and "~50B tokens" are the only compute disclosures; reproducing the online loop is effectively infeasible from the paper alone.

## Reproducibility and artifacts
- Code: Open-sourced at https://github.com/bytedance/UI-TARS (p.1).
- Data: Training datasets (synthetic perception, 6M tutorials, annotated traces, online bootstrapped traces) described qualitatively; exact released subsets and authors' annotation volumes Not reported / masked.
- Models: UI-TARS-2B/7B/72B (SFT and DPO) referenced as open-sourced; specific checkpoint availability/weights not enumerated in the paper text.
- Environment: Evaluation environments are public (OSWorld, AndroidWorld, ScreenSpot*, Mind2Web, AndroidControl, GUI Odyssey, VisualWebBench, WebSRC, ScreenQA). Training VM infrastructure not specified.
- License: Not reported in the extraction.
- Exact commands or setup: Not reported (N=5 history window, 3-phase training, OSWorld screenshot-only and 15/50-step budgets, 3-run averaging are the main reproducible knobs).
- Missing details: hyperparameters (LR schedule values, beta for DPO, filtering thresholds), GPU/time/cost, authors' data volumes, per-component ablations.

## Strengths
- A clean, well-motivated articulation of the framework->native-model evolution (§2), useful as a survey in its own right.
- Genuinely unified pure-vision observation + cross-platform action space (Table 1) that is directly reusable as a harness interface.
- Concrete, reproducible-in-spirit recipe for the data bottleneck: thought augmentation with the ActRe-vs-bootstrapping distinction is a thoughtful fix for spurious thought-action alignment.
- Online bootstrapping + reflection tuning + Agent DPO is a coherent self-improvement loop with a real safety affordance (CallUser).
- Broad, consistent benchmark coverage (perception, grounding, offline, online) with apples-to-apples framework-vs-model tables; open-sourced.
- Honest reporting of a counterintuitive finding: System-2 reasoning can hurt at N=1 in-domain but helps OOD and at higher N.

## Weaknesses and limitations
- Selective application of DPO (only OSWorld) makes the headline abstract number not representative of the deployed/default model across benchmarks.
- Heavy in-domain overlap for offline benchmarks weakens generalization claims; authors acknowledge offline metrics may mislead.
- No per-pillar ablation; cannot attribute gains to specific innovations vs the Qwen-2-VL backbone.
- Masked data volumes and minimal compute disclosure limit reproducibility despite the open-source claim.
- No variance/significance reporting on most tables.
- Safety/guardrails beyond CallUser are essentially unaddressed for an agent that issues real mouse/keyboard actions on live systems.
- "Active and lifelong agent" (Stage 4) is positioned as future work / prospect, not demonstrated (§2.3).

## Relationship to prior work
- Closest peers (native/end-to-end GUI models, p.8, p.22): Aguvis (Xu et al. 2024), OS-Atlas (Wu et al. 2024b), ShowUI, UGround, Aria-UI, CogAgent, SeeClick, Claude Computer Use (Anthropic 2024b). UI-TARS positions itself one step beyond these by adding explicit System-2 thoughts, the online bootstrapping/reflection/DPO self-improvement loop, and larger unified data.
- Method lineage: ReAct (thoughts before actions, generalized here), ActRe (thought annotation), DPO (Rafailov et al. 2023), behavior cloning, Set-of-Mark prompting, Qwen-2-VL backbone.
- Genuinely new vs incremental: The unified pure-vision interface and end-to-end training are shared with contemporaries (incremental over Aguvis/OS-Atlas). The notable novelty is the integrated online reflective self-improvement pipeline (reflection tuning + post-reflection + Agent DPO over self-generated error traces) and the System-1/System-2 framing with the bootstrapped thought data. The survey/evolution-path framing (§2-3) is a useful synthesis but not a technical contribution.

## What I should read
- Must read: §4.4 (System-2 reasoning, ActRe vs Thought Bootstrapping, p.17-19); §4.5 (online bootstrapping, reflection tuning, Agent DPO, p.20-22); Table 1 action space (p.17); Table 9 online results (p.26); §5.5 System-1/2 ablation (p.26-27).
- Skim: §2 evolution path and §3 core capabilities (good framing, light on novelty); §4.2-4.3 perception/grounding data construction; Tables 3-8.
- Can skip: most of the related-work prose in §3.1; the reference list.
- Follow-up papers: Aguvis, OS-Atlas, UGround, Claude Computer Use, OSWorld and AndroidWorld benchmark papers, ScreenSpot Pro; later UI-TARS versions / UI-TARS-1.5 if present in library.

## Triage decision
Label: READ_SOON
Rationale: Milestone native GUI agent with a directly reusable observation/action interface, a concrete data+self-improvement recipe, open weights/code, and clean framework-vs-model benchmarks. Caveats (selective DPO reporting, in-domain offline overlap, no per-pillar ablation) matter for citation but do not reduce its value as a baseline/harness reference.
Confidence: high
Reading time estimate: ~90 minutes for a focused read of §4-5; ~3 hours for the full paper including the evolution-path survey.

## Personal notes
The most defensible single claim is OSWorld efficiency: UI-TARS-72B-DPO at 15 steps (22.7) roughly matches Claude at 50 steps (22.0), and reaches 24.6 at 50 steps. When citing the AndroidWorld 46.6 figure, note the nearest competitor is GPT-4o+Aria-UI at 44.8, not the 34.5 GPT-4o(SoM) the abstract emphasizes. Watch for in-domain leakage when quoting Mind2Web/AndroidControl/GUI Odyssey gains.

## Follow-up actions
- Add related paper: Aguvis (Xu et al. 2024), OS-Atlas (Wu et al. 2024b), UGround (Gou et al. 2024a)
- Compare with: Claude Computer Use; later UI-TARS / UI-TARS-1.5 if available
- Re-run after new version: check for v2 / UI-TARS-1.5 with RL-based single-pass System-2
- Check code: github.com/bytedance/UI-TARS (weights, action-space spec, eval harness)
- Read benchmark details: OSWorld (369 tasks, screenshot-only, 3-run avg) and AndroidWorld (116 tasks, 20 apps)
