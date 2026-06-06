# Android in the Zoo: Chain-of-Action-Thought for GUI Agents

## Metadata
- Canonical key: arxiv-2403.02713
- Version: v1
- Fetch date: 2026-06-06T07:57:29Z
- Source: arxiv
- PDF: library/android-in-the-zoo-chain-of-action-240302713/v1/paper.pdf
- Venue: EMNLP 2024 Findings (extraction header lists "Conference on Empirical Methods in Natural Language Processing"; arXiv id 2403.02713v2, 13 Jul 2024)
- Year: 2024
- Authors: Jiwen Zhang, Jihao Wu, Yihua Teng, Minghui Liao, Nuo Xu, Xiao Xiao, Zhongyu Wei, Duyu Tang (Fudan University; Huawei Inc.)
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
The paper introduces Chain-of-Action-Thought (CoAT) -- a prompting/annotation scheme that interleaves screen description, action thinking, next-action description, and action result -- and the Android-In-The-Zoo (AitZ) dataset (18,643 screen-action pairs over 2,504 instructions, derived from AitW) that operationalizes it, showing CoAT improves zero-shot action prediction and lets a ~1B fine-tuned model rival an 18B GUI agent.

## Why this paper matters
For a GUI-agent harness, the central artifact here is not a model but an *interface design*: it argues that an Android navigation agent should not emit raw `click (x,y)` coordinates conditioned only on a screenshot, but should pass through an explicit intermediate semantic chain (what is on the screen -> why this action -> which UI element -> what the action will produce). This is a concrete, reusable observation/reasoning schema for AitW-style mobile agents, and the AitZ dataset is the labeled supervision that makes the schema trainable for small models. The data-curation critique of AitW (template redundancy, train/test leakage, and many episodes that do not actually complete their instruction) is independently useful for anyone using AitW as a benchmark. CLAIMED relevance is high; the evidence is mid-scale (single dataset, two agents fine-tuned/evaluated, three proprietary LMMs zero-shot), so READ_SOON rather than MUST_READ.

## Problem and gap
CLAIMED problem (p1, Intro): existing LLM/LMM GUI agents predict an action sequence while ignoring the semantics of intermediate screenshots and operations -- prior methods (e.g. AUTO-UI / Chain-of-Action, SeeClick) concentrate on action *coordinates* like "click on (0.17, 0.89)" and ignore the logic behind the action (p1). The authors decompose the missing semantics into four questions: Screen Context, Action Think, Action Target, Action Result (p1).
Second gap (p2): complex context modeling "emerges at a large model scale," so small models cannot acquire this ability by fine-tuning without high-quality CoAT-style data -- and such data did not exist. UNCLEAR: the "emerges at scale" claim is asserted with a citation (Zhang et al., 2023), not demonstrated within this paper.
Third gap (p4, Fig 4): AitW itself has substantial label noise -- for the instruction "check the settings for the spotify app," 13 of 15 episodes never open Spotify -- motivating data validation. This is EVIDENCE for the data-cleaning contribution, shown via a concrete count.

## Core idea
CoAT reframes the policy. A standard agent learns pi(a_t | o_t, h_{t-1}, u) directly (p3, Sec 2.1). The paper argues this is hard because the relation between history, observation, and action is implicit, and inserts an intermediate textual chain so the decision factors through interpretable states. The four components (p3):
- Screen Description (SD): textual description of screen type and primary apps/widgets -- query-independent context.
- Action Think (AT): reasons over query + current screen + history to infer candidate actions; framed as p(AT | o_t, u, h_{t-1}), with the decision then approximable as p(a_t | AT).
- Next Action Description (AD): natural-language description of the operated UI element ("click on the shopping cart icon"), used to build a readable action history.
- Action Result (AR): synthesizes the outcome by comparing screenshots before/after the action, linking o_t and a_t to o_{t+1}; AR_{t-1} is folded into the next step's history.
Components are composable ("free to combine them according to language models used," p3), which the ablation (Table 6) exploits by routing SD and previous-AR to model *input* and AT/AD to model *output*.

## Harness relevance
- Environment / workspace: Android GUI navigation, **static/offline** -- episodes are pre-collected screenshot sequences sampled from AitW (Rawles et al., 2023), not a live device. Evaluation is screen-wise action matching against gold trajectories, not live execution.
- Observation interface: a single screenshot per step o_t. UI elements are additionally exposed either as set-of-mark tags drawn on the image or as a textual list of element type + bounding box (Fig 10, p15). In the zero-shot prompting study, CoAT adds a generated screen description to the observation.
- Action interface: a simplified 5-action space (Appendix A.2/A.3, p13): CLICK(coord_y, coord_x) in relative [0,1] coordinates, SCROLL(direction in {up,down,left,right}, purely textual), TYPE(text), PRESS(button in back/home/enter), STOP(task_state). AitW's `DUAL_POINT` is manually split into CLICK and SCROLL. AUTO-UI and CogAgent outputs are mapped into this space for comparison.
- Tool/API/GUI layer: pure GUI (pixel + coordinate). No shell/API tools. Set-of-mark tagging (Yan et al., 2023) and an icon-detection model (Liu et al., 2018) annotate clickable UI elements.
- Planner/executor/verifier structure: the CoAT chain itself is the planner/reasoner (Action Think = plan, Action Result = self-reflection). There is no search and no separate runtime verifier; "verification" is offline human checking of GPT-4V-generated annotations.
- Evaluation harness: atomic action-matching score ("match": correct iff action type AND details match gold) and episodic **goal progress** (GP = relative position of first error in the episode). For CLICK/TYPE, action-type accuracy is reported separately (Table 5).
- Training harness: AUTO-UI fine-tuned from the original weight-init strategy for up to 10 epochs, lr 1e-4, on the AitZ train split; CogAgent used zero-shot only (its training data is not public). Ablation places SD/previous-AR in input, AT/AD in output.
- Logging/trace/reproducibility: the AitZ annotations themselves are the trace (each step carries SD/AT/AD/AR). Generation prompts for all four annotation types are given in Appendix Fig 8 (p12). Code/data repo: github.com/IMNearth/CoAT.
- Safety/permission: none as an agent mechanism. Ethics section notes AitW is academic-use-licensed and sampled data contains no real personal info.

## Method
Two contributions: the CoAT schema (above) and the AitZ dataset built to supply it.
Data collection (Sec 3.1, p4-5):
1. Instruction sampling from AitW (715k episodes, 30k unique instructions) using per-subset strategies -- uniform sampling per instruction for GENERAL/GOOGLEAPPS/INSTALL (x = 3/5/3), balanced sampling over shopping site x object for WEBSHOPPING, and verb-grouping + tf-idf clustering + balanced sampling for SINGLE. This yields 3,461 unique instructions / 7,180 episodes; 10 annotators verify task completion; 5,147 successful episodes remain, and one episode is kept per unique instruction. (Note: the relationship between 3,461 sampled instructions and the final 2,504 is not explicitly reconciled in the text -- UNCLEAR.)
2. Semantic annotation: GPT-4V (via Azure API) generates SD, AT, AD, AR; an icon-detection model marks clicked elements; SCROLL/PRESS/etc. descriptions use templates. Three UI-expert annotators check AD against gold actions and, on mismatch, revise AD and force GPT-4V to regenerate AT/AR. Information given to GPT-4V varies by task (SD is query-independent; AD gets query + gold coordinate) -- see prompts in Fig 8.
Dataset analysis (Sec 3.2): SD typically 80-120 words, AT 30-70, AR 20-80 (Fig 5). Table 1 positions AitZ as the only Android dataset with all four annotation types (screen desc, action coord, action desc, action thinking) plus episode-feasibility verification.

## Experimental setup
- Datasets/benchmarks: (a) preliminary zero-shot study on 50 episodes randomly sampled from AitW (p3); (b) main study on AitZ train/test split -- 1,998 train / 506 test episodes (~70/30), 13,919 train / 4,724 test screens (Table 4, p5; SINGLE's 844 episodes / 2,594 screens are all placed in train because they are single-step). Authors stress no instruction overlap -> no leakage.
- Baselines / agents: zero-shot -- Qwen-VL-Max, Gemini-1.0-Pro-Vision, GPT-4V (prompting-method comparison); CogAgent-Chat-18B (zero-shot, +/-CoAT). Fine-tuned -- AUTO-UI-base (~1.2B; BLIP2-opt-2.7b encoder, FLAN-Alpaca-base decoder, 224x224), +/-CoAT, trained from scratch on AitZ. Architecture/data comparison of the two agents in Table 7 (p14).
- Metrics: format hit rate, atomic action-matching accuracy (overall + per action type), goal progress.
- Compute/cost: Not reported (no GPU-hours, no API cost).
- Artifacts: code/data at github.com/IMNearth/CoAT. License of AitZ not explicitly stated beyond inheriting AitW academic-use permission.

## Key results
VERIFIED against extraction.
Zero-shot prompting comparison, action accuracy (Table 2, p3), CoA -> CoT -> CoAT:
- Qwen-VL-Max: 44.4 -> 49.4 -> **52.4**
- Gemini-1.0-PV: 47.7 -> 52.0 -> **54.5**
- GPT-4V: 62.8 -> 64.1 -> **73.5**
So CoAT beats the better of CoA/CoT by +3.0 (Qwen), +2.5 (Gemini), and **+9.4** (GPT-4V over CoT; +10.7 over CoA). Format hit rates stay high (94.5-99.8). The largest gain is on the strongest model, consistent with the "emerges at scale" framing; on Gemini the CoAT hit rate (96.4) is slightly below CoT (97.5).
Main results (Table 5, p6), Total action-match / Goal Progress:
- CogAgent (ZS): 44.52 / 13.82 -> +CoAT **53.28 / 17.13** (GP +3.31). Mixed per-type: CLICK match 67.40 -> 45.80 *drops*, but STOP 4.76 -> 24.60 and SCROLL type 56.41 -> 70.22 rise.
- AUTO-UI (FT): 34.46 / 6.59 -> +CoAT **47.69 / 14.51** (GP +7.92, more than doubled). STOP match 60.12 -> 74.40, CLICK match 67.80 -> 81.40.
Headline cross-model claim (Abstract; Sec 5.1; Appendix B.2): AUTO-UI(~1.2B)+CoAT achieves on-par performance with CogAgent-Chat-18B -- supported on goal progress (AUTO-UI+CoAT 14.51 vs CogAgent+CoAT 17.13, and 14.51 > CogAgent-no-CoAT 13.82). EVIDENCE is on the AitZ test set only; "on-par" is most defensible on GP and overall match, less so per-action-type.
Ablation (Table 6, p6-7): previous-AR, especially with AT+AD, drives the biggest gains; STOP match rises 60.12 -> 79.17 when AR-style coherence is added (row 3). Learning AT as output *without* input SD/AR is hard (rows 5-7). Adding SD to input slightly *hurts* AUTO-UI (rows 9 vs 10), attributed to its low 224x224 resolution -- an honest negative result. Best overall AUTO-UI config (row 9: PAR+AT+AD) = 82.98 total / 14.51 GP. Fig 6 shows CoAT also improves training efficiency over epochs.
Complete prompting table (Table 8, p15): set-of-mark tagging generally beats textual UI representation; GPT-4V+CoAT+tag leads.

## Evidence quality
The two headline claims (CoAT > CoA/CoT zero-shot; small-model-rivals-large) are each supported by direct numbers that reconcile with the tables. Strengths of the evidence: per-action-type breakdowns, an ablation that isolates input-vs-output placement and reports a negative (SD hurts AUTO-UI), and explicit motivation of the data-cleaning step with a concrete leakage/noise example. Weaknesses: (1) the zero-shot prompting study uses only **50 AitW episodes** -- small, and no variance/seeds reported; no statistical significance anywhere. (2) Evaluation is offline action-matching, not live device execution, so real task success is not measured. (3) On the +CoAT rows CogAgent actually leads on total atomic match (53.28 vs 47.69) while AUTO-UI leads on goal progress is the reverse (AUTO-UI 14.51 vs CogAgent 17.13 -- CogAgent higher); so "on-par with 18B" is framing that mixes metrics and slightly favors the authors' model. (4) CogAgent is evaluated zero-shot while AUTO-UI is fine-tuned on AitZ -- an asymmetric comparison the authors acknowledge (Limitations: differing architecture/training data make comparison "less intuitive"). (5) Annotation quality depends on GPT-4V + a small human-expert pass (three annotators); inter-annotator agreement is Not reported. (6) Resolution/pretraining confounds are explicitly left unmeasured (Limitations).

## Reproducibility and artifacts
- Code: github.com/IMNearth/CoAT (linked p1). Not inspected here.
- Data: AitZ -- 2,504 instructions / 18,643 screen-action pairs; train/test split in Table 4. Built on AitW.
- Models: AUTO-UI-base (~1.2B) reused; CogAgent-Chat-18B reused zero-shot; GPT-4V / Gemini-1.0-Pro-Vision / Qwen-VL-Max via APIs.
- Environment: offline screenshot trajectories (AitW-derived); no live emulator harness described.
- License: AitW academic-use is inherited; explicit AitZ license Not reported in the paper body.
- Exact commands/setup: AUTO-UI fine-tuning hyperparameters given (<=10 epochs, lr 1e-4, original weight init); annotation prompts in Fig 8. No run scripts in the paper.
- Missing details: API costs, GPT-4V version/date, annotator agreement, seed/variance, reconciliation of 3,461->2,504 instruction counts.

## Strengths
- Clear, reusable interface abstraction (SD/AT/AD/AR) that is composable and maps cleanly onto an offline GUI agent's input/output.
- A genuinely new dataset filling a real gap (Table 1): first Android nav dataset combining screen description + action coordinate + action description + action thinking + episode feasibility.
- Useful, evidence-backed critique of AitW data quality (template redundancy, train/test leakage, non-completing episodes) with a concrete 13/15 example.
- Honest ablation including a negative result (SD hurts low-res AUTO-UI) and an explicit limitations section on resolution/pretraining confounds.

## Weaknesses and limitations
- Offline action-matching only; no live execution / true task-success metric.
- Asymmetric main comparison (fine-tuned 1.2B vs zero-shot 18B); "on-par" framing depends on which metric is chosen.
- Tiny (50-episode) zero-shot prompting study; no variance, no significance testing anywhere.
- Annotation pipeline relies on GPT-4V with limited human verification (3 experts); no agreement metric.
- Some count reconciliation gaps (3,461 sampled vs 2,504 final instructions) left implicit.
- Author-stated: architecture/data differences make agent comparison less intuitive; impact of image resolution, text-recognition, and GUI-grounding pretraining on navigation left unmeasured.

## Relationship to prior work
- AitW (Rawles et al., 2023): the source of AitZ's episodes and the "Standard" prompting baseline; AitZ is a cleaned, re-sampled, semantically-annotated subset.
- AUTO-UI / Chain-of-Action (Zhan and Zhang, 2023): the coordinate-only baseline CoAT is positioned against, and the fine-tuned backbone.
- Chain-of-Thought (Wei et al., 2022): CoAT generalizes CoT by adding screen/action-specific structure (history, screen desc, action result) rather than free-form reasoning.
- CogAgent (Hong et al., 2023): the high-resolution 18B GUI agent used as the strong reference.
- SeeClick (Cheng et al., 2024), AppAgent (Yang et al., 2023a), GPT-4V smartphone navigation (Yan et al., 2023): related LMM-as-GUI-agent lines. Genuinely new: the four-part action-thought annotation schema and the dataset that makes it trainable for small models; the agents and base CoT idea are reused.

## What I should read
- Must read: Sec 2 (CoAT definition, p3) and Table 2; Sec 3.1 data collection + Fig 4 leakage example (p4-5); Table 5 main results.
- Skim: Ablation Table 6 and Fig 6; Appendix A.3 action space (p13); Table 7 agent comparison.
- Can skip: Related Work (Sec 6), reference list, Fig 8 prompt verbatim (read once if reproducing annotations).
- Follow-up papers: AitW (Rawles 2023), AUTO-UI (Zhan & Zhang 2023), CogAgent (Hong 2023), SeeClick (Cheng 2024).

## Triage decision
Label: READ_SOON
Rationale: High harness relevance -- a concrete, reusable observation/reasoning interface for Android GUI agents plus a labeled dataset, with an actionable AitW data-quality critique. Held below MUST_READ because evaluation is offline action-matching only, the cross-model "on-par" claim mixes metrics, and the zero-shot study is small. Evidence does not strongly contradict the claims, so the prior READ_SOON label stands.
Confidence: high
Reading time estimate: 35-45 min for the core (Sec 2-3, Tables 2/5/6), +20 min for appendices if reproducing.

## Personal notes
The most portable idea for harness design: factor a GUI policy through SD -> AT -> AD -> AR and route context-providing pieces (SD, previous AR) to *input* and reasoning pieces (AT, AD) to *output*. The negative SD-on-low-res result is a useful caution: textual screen descriptions help only if the visual encoder can ground them; on a 224x224 encoder they add noise.

## Follow-up actions
- Add related paper: Android in the Wild (AitW), AUTO-UI, CogAgent, SeeClick
- Compare with: AitW (as benchmark, given the leakage critique)
- Re-run after new version: arXiv v2 already extracted; check if camera-ready EMNLP Findings adds live-execution results
- Check code: github.com/IMNearth/CoAT (dataset format, annotation prompts)
- Read benchmark details: AitZ train/test split (Table 4), action-space mapping (Appendix A.3)
