# ScreenAgent: A Vision Language Model-driven Computer Control Agent

## Metadata
- Canonical key: arxiv-2402.07945
- Version: v1
- Fetch date: 2026-06-06T07:57:28Z
- Source: arxiv
- PDF: library/screenagent-a-vision-language-model-driven-computer-240207945/v1/paper.pdf
- Venue: International Joint Conference on Artificial Intelligence (IJCAI 2024)
- Year: 2024
- Authors: Runliang Niu, Jindong Li, Shiqi Wang, Yali Fu, Xiyu Hu, Xueyuan Leng, He Kong, Yi Chang, Qi Wang
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
ScreenAgent connects a VLM to a *real* desktop OS over the VNC protocol, drives it through a planning-acting-reflecting control loop using only screenshots and mouse/keyboard actions, and ships a 273-session human-annotated dataset plus a fine-grained CC-Score metric; a CogAgent-Chat model fine-tuned on this data matches GPT-4V overall while substantially beating it on click-coordinate precision.

## Why this paper matters
This is an early (Feb 2024) entry in the pixel-level computer-use agent line that directly targets the OS desktop rather than a browser DOM or labeled mobile UI. Its design choices anticipate the now-dominant "screenshot in, mouse/keyboard out, no accessibility tree" paradigm later popularized by Claude/OpenAI computer-use. For a harness-focused reader it is relevant as (a) a concrete real-screen environment over VNC, (b) an explicit planning/acting/reflecting decomposition with a typed JSON action space, and (c) a dataset + evaluation metric that scores coordinate accuracy via feasible bounding boxes rather than exact pixels. It is foundational/historical rather than SOTA: the trained model is small (18B, inherited from CogAgent) and the task set is tiny by current standards.

## Problem and gap
Problem: build a VLM agent that can control an arbitrary real computer through the GUI, end to end, across multi-step tasks (p.1, Abstract; p.1-2, §1).
Gap in prior work the authors target (p.2, §1):
- CogAgent does GUI understanding/planning but "lacks the capability of a complete thinking chain" / full tool-invocation loop.
- AppAgent (phones) "lacks a planning process," and constrains clicking by pre-labeling each UI element, so it cannot click arbitrary pixels.
- Most prior environments/datasets (WebNav, Mind2Web, SWDE, Seq2act, Screen2Words) assume access to HTML/UI metadata or are browser/Android-only (p.4, §4), whereas mouse+keyboard on a raw screen is the universal interface they want to fill.
So the claimed gap is: no existing VLM agent interacts with a *real* computer via continuous, freely-positioned mouse/keyboard commands with a full plan->act->reflect loop.

## Core idea
Three coupled contributions (p.2, §1):
1. A real-screen "RL environment" exposing the desktop via VNC: state = screenshots (before `s` and after `s'`), action = typed JSON function calls converted to VNC mouse/keyboard events, reward = an open/pluggable interface (no concrete reward model is shipped) (p.3, §3.1).
2. An automated control pipeline with Planning, Acting, Reflecting phases (p.3, §3.2; Fig. 2). The reflecting phase (motivated by Kolb's experiential learning cycle, p.2) lets the agent decide per subtask: continue / retry / reformulate the plan.
3. The ScreenAgent Dataset + CC-Score metric (p.4, §4), and a fine-tuned model (ScreenAgent, from CogAgent-Chat) that adds precise positioning (p.6, §5.2).

## Harness relevance
- Environment / workspace: a real desktop OS (Linux and Windows), not a simulator. Connected via remote desktop **VNC protocol** (p.3, §3.1). Described as an "RL environment" but the RL framing is nominal — no learned policy via RL, no concrete reward model (reward is an "open interface," p.3).
- Observation interface: raw **screenshots** only (single frame). State space is the screenshot image; `s` before and `s'` after each action (p.3, §3.1). Explicit limitation: single-frame images only, no video/multi-frame (p.7, §6).
- Action interface: typed **JSON function calls** parsed by the environment and translated to VNC device events (p.3-4). Action types (Table 1, p.4): Mouse Move / Click / Double Click / Scroll Up / Scroll Down / Drag, with button (left/middle/right) and integer width/height position; Keyboard Press (key or combo, per `keysymdef`) and Text; Wait; plus meta-actions PlanAction (element string) and EvaluateAction (situation = success/retry/reformulate + advice). Coordinates are absolute pixels from top-left.
- Tool/API/GUI layer: pure GUI control; no accessibility tree, no DOM, no set-of-marks labeling (deliberately contrasted with AppAgent's labeled-element clicking, p.2). This is genuine pixel-to-action.
- Planner / executor / verifier structure: Planner = Planning phase (decompose task into subtask list from screenshot + task prompt). Executor = Acting phase (emit low-level mouse/keyboard JSON for current subtask). Verifier = Reflecting phase (VLM acts as a reward/judge model deciding continue/retry/reformulate). Full prompt templates for all three phases are in Appendix A (p.10-12) — useful if reusing the harness.
- Evaluation harness: CC-Score (Vision Language Computer Control Score), Appendix D (p.5, §4; p.14). Sequence-level: a max-weight monotonic alignment between predicted and labeled action sequences, normalized by label length. Per-action similarity: action-type match, mouse-action-type, mouse-button, and whether the click falls within an annotated *feasible bounding box* (so positioning is scored by region membership, not exact pixel); text/keys scored by BLEU. Reported as a CC-Score plus per-attribute F1/accuracy/BLEU breakdowns (Tables 2-3).
- Training harness: supervised vision fine-tuning of CogAgent-Chat, with 4-phase curriculum data mixing (Table 4, p.6). Hyper-parameters in Appendix F (Table 6, p.14): 6258 total steps, LR 1e-5 cosine, batch size 8, weight decay 0.05, warmup ratio 0.02.
- Logging/trace/reproducibility: the data-annotation process (Fig. 3, p.4) logs (task, before-screen, GPT-4V original response, human-corrected golden response, after-screen), forming chosen/reject pairs intended for future RLHF. No agent-run trace/replay system is described beyond before/after screenshots.
- Safety / permission mechanism: none implemented. Only an Ethical Statement (p.7-8) flagging misoperation risk, CAPTCHA bypass, fraud, privacy. No sandboxing, action gating, or human-confirmation layer is built in; in fact "human intervention is still necessary" because reflection is unreliable (p.6).

## Method
Pipeline (p.3, §3.2; Fig. 2): given a task prompt, (1) Planning emits a JSON list of PlanActions (subtasks) from the current screenshot; (2) Acting, per current subtask, emits one or more low-level mouse/keyboard JSON actions, which the environment parses and dispatches over VNC, then captures the after-screen; (3) Reflecting consumes the after-screen and outputs an EvaluateSubTaskAction = sub_task_success / need_retry / need_reformulate (with free-text advice fed back into the next prompt). This yields a continuous loop able to retry subtasks or replan.

Dataset construction (p.4, §4; Appendix C): interactive annotation where GPT-4V generates a first-draft response and human annotators correct it to a "golden" label; actions are parsed and actually executed on the real machine (Fig. 3). Coverage: Linux + Windows; daily office, booking, info retrieval, card games, entertainment, programming, system operations, etc.

CC-Score (above, and Appendix D, p.14): alignment-based sequence scoring + per-attribute metrics with bounding-box-tolerant positioning.

Training (p.6, §5.2; Table 4): fine-tune CogAgent-Chat. To boost localization, COCO and Widget Captions detection datasets are reformulated into click/drag tasks (click object center, or drag a bounding box); Mind2Web sessions are converted into the ScreenAgent action schema (CLICK/SELECT->click center; TYPE->click+text(+Enter)). Data are mixed across 4 phases with increasing ScreenAgent-data share (20%->...->70% for ScreenAgent data; Table 4). Templates for these conversions are in Appendix B (p.12-13).

## Experimental setup
- Dataset / benchmark: ScreenAgent Dataset — **273 complete task sessions total; 203 training sessions (3005 screenshots) and 70 test sessions (898 screenshots); 39 sub-task categories across 6 themes** (p.4, §4, verified). Training-set stats (Table 5, p.14): avg task-prompt tokens 13.2 En / 23.8 Zh; avg chosen-response tokens 97.1 En / 129.9 Zh; avg 1.5 actions per sub-task interaction; ~60% of tasks need 3-5 plan steps, avg 4, max 13. Action-type mix (Fig. 4/5a): Evaluate 29.24%, Plan 28.68%, Mouse 24.67%, Keyboard 15.29%, Wait 2.12%.
- Baselines/models evaluated on test set: GPT-4V(ision), LLaVA-1.5 (13B, max input 336x336), CogAgent (18B; CogAgent-VQA and CogAgent-Chat, the latter also via a GPT-3.5 JSON-extraction helper), and the fine-tuned ScreenAgent (p.5, §5.1).
- Metrics: (Table 2) proportion of *successful function calls* — i.e., output contains the required attribute keys, regardless of value correctness; (Table 3) fine-grained CC-Score with per-attribute Plan(BLEU), Action Type(F1), Mouse Action Type(F1), Mouse Button(F1), Mouse Position(Accuracy), Keyboard Keys/Text(BLEU), Reflecting Situation Assessment(F1).
- Compute/cost: training hyper-parameters reported (Table 6); no GPU-hours, dollar cost, or inference cost reported. Not reported.
- Artifacts: code at https://github.com/niuzaisheng/ScreenAgent (p.1). License: Not reported in the paper text.

## Key results
Verified against extraction (Table 3, p.5, fine-grained CC-Score on successfully-matched actions):
- Overall **CC-Score: GPT-4V 0.63, ScreenAgent 0.61, LLaVA-1.5 0.51, CogAgent-Chat(+GPT-3.5) 0.33.** So ScreenAgent is "comparable to GPT-4V" overall (slightly below), supporting the abstract's comparability claim.
- **Mouse Position (Accuracy): ScreenAgent 0.51 vs GPT-4V 0.12 vs LLaVA-1.5 0.03 vs CogAgent 0.02.** This is the headline win — fine-tuning gives far more precise clicking. The paper notes GPT-4V often "refuses to give precise coordinate results" (p.6).
- Action Type F1: GPT-4V 0.98, ScreenAgent 0.98 (tie). Mouse Action Type F1: GPT-4V 0.96 vs ScreenAgent 0.94. Mouse Button F1: GPT-4V 0.99 vs ScreenAgent 0.97. Keyboard Keys/Text BLEU: GPT-4V 0.92 vs ScreenAgent 0.87. Plan BLEU: GPT-4V 0.47 vs ScreenAgent 0.31 (ScreenAgent clearly weaker at planning — authors attribute this to GPT-4V's superior common-sense/planning, p.6). Reflecting Situation Assessment F1: GPT-4V 0.60, ScreenAgent 0.52, LLaVA-1.5 0.52 — all poor.
- Function-call success (Table 2, p.5): GPT-4V and LLaVA-1.5 high; raw CogAgent-VQA/Chat near-zero (they ignore the JSON format), only partially recovered with a GPT-3.5 helper. After fine-tuning, ScreenAgent reaches GPT-4V-level format compliance (e.g., Mouse Position key-presence 0.91 vs GPT-4V 0.85).
- Qualitative (p.6, §5.3; Figs 7-8): ScreenAgent produces concise effective plans and can recover after a failed action via reflection; LLaVA tends to click bottom-left repeatedly; CogAgent often fails to emit click coordinates.

Caveat: Table 3 scores are computed *only over successfully matched/parsed actions*, so they partly condition out the format-failure problem; absolute end-to-end task success rate is **Not reported** as a single number.

## Evidence quality
- The central comparability claim (ScreenAgent ~ GPT-4V, better positioning) is supported by Table 3: overall CC-Score 0.61 vs 0.63 and Mouse Position 0.51 vs 0.12. The positioning advantage is large and credible given the explicit localization fine-tuning.
- Weak spots in the evidence:
  - Tiny test set: 70 sessions / 898 screenshots. No confidence intervals, no significance testing, single run. Statistical reporting absent.
  - Metric tolerance: positioning scored by membership in an annotated *feasible bounding box*, not exact pixels — generous, and box quality depends on annotators. CC-Score is a similarity-to-human-trace metric, not task completion; a high CC-Score does not guarantee the task succeeded on the real machine.
  - No reported end-to-end success rate / autonomous full-task completion numbers; reflection F1 <=0.60 for all models means the loop's self-verification is unreliable and "human intervention is still necessary" (p.6) — undercutting the "entirely automated" framing.
  - "RL environment" is a misnomer here: no RL training, no concrete reward model; the chosen/reject pairs are only proposed for *future* RLHF.
  - Baselines are somewhat constrained: LLaVA-1.5 limited to 336px, CogAgent needs a GPT-3.5 crutch to parse — so format-compliance comparisons are not apples-to-apples.
- No ablation isolating the contribution of each curriculum phase or of the reflecting phase on full-task outcomes.

## Reproducibility and artifacts
- Code: https://github.com/niuzaisheng/ScreenAgent (stated, p.1). Not inspected here.
- Data: ScreenAgent Dataset described with full statistics (p.4, Appendices C); availability/license in repo, Not reported in text.
- Models: ScreenAgent = fine-tuned CogAgent-Chat (18B). Training hyper-parameters fully listed (Table 6).
- Environment: real OS via VNC; full plan/act/reflect prompt templates in Appendix A; dataset-conversion templates in Appendix B — enough to reconstruct the harness.
- License: Not reported.
- Exact commands/setup: Not reported in the paper (likely in repo).
- Missing details: reward-model interface concretely; end-to-end success protocol; annotator count/agreement; bounding-box construction details beyond "feasible."

## Strengths
- Genuine pixel-level control of a *real* OS over VNC, Linux + Windows, no accessibility tree — ahead of its time (Feb 2024).
- Clean, reusable typed action schema and full prompt templates (Appendices A/B).
- Explicit plan/act/reflect decomposition with an in-loop verifier and replanning.
- A purpose-built dataset (human-corrected golden traces) and a thoughtful alignment-based CC-Score that scores coordinates by feasible region.
- Demonstrates that lightweight localization fine-tuning closes the click-precision gap to GPT-4V (0.12 -> 0.51 accuracy).

## Weaknesses and limitations
- Author-stated (p.7, §6): single-frame input only (no video); language capability bounded by the base LM; even GPT-4V has poor support for non-English on-screen text.
- Inferred: very small eval (70 sessions); CC-Score measures trace similarity not task success; reflection/self-verification is unreliable (F1 <=0.60), so it is not truly autonomous; "RL environment" with no actual RL/reward; no safety/sandboxing layer; small base model (18B) likely uncompetitive with later computer-use systems; planning is markedly weaker than GPT-4V (Plan BLEU 0.31 vs 0.47).

## Relationship to prior work
- Closest: CogAgent (Hong et al., 2023) — the base model ScreenAgent fine-tunes; ScreenAgent adds the full plan/act/reflect loop and precise positioning CogAgent lacked. AppAgent (Yang et al., 2023) — mobile, labeled-element clicking; ScreenAgent removes element labeling for free pixel clicking and adds planning. Mind2Web (Deng et al., 2023) — web/DOM dataset, reused here as converted training data.
- Lineage of environments: MiniWoB++, WebShop, WebNav (web/RL sims); Seq2act, Screen2Words, META-GUI (Android). ScreenAgent's novelty is the *real desktop OS via VNC with raw screenshots and universal mouse/keyboard*, plus the CC-Score region-tolerant evaluation.
- Genuinely new: the real-screen VNC harness + plan/act/reflect + CC-Score + dataset combination. Incremental: the model itself is a CogAgent fine-tune; planning/reflection prompting is standard agent decomposition.

## What I should read
- Must read: §3 Framework (env + pipeline, p.3-4), Table 1 action space (p.4), §4 dataset + CC-Score (p.4-5), Tables 2-3 results (p.5), §5.2 fine-tuning (p.6).
- Skim: Appendix A prompt templates (p.10-12) if reusing the harness; Appendix B data conversion (p.12-13); §5.3 case studies.
- Can skip: Related Work (§2) unless mapping the 2023-era landscape; Appendix E generated samples; Appendix D math if you only need the CC-Score intuition.
- Follow-up papers: CogAgent, AppAgent, Mind2Web; and later real-OS computer-use agents to compare interface/metric choices.

## Triage decision
Label: READ_SOON
Rationale: Directly on-target for a computer-use harness interest — a real-OS, pixel-level, plan/act/reflect agent with a reusable action schema, prompt templates, dataset, and a region-tolerant evaluation metric. Evidence is modest (tiny test set, trace-similarity metric, unreliable reflection, "RL"/reward overclaimed) so it is foundational/reference reading rather than a SOTA result to chase. Worth a focused read for the harness and metric design; verified core numbers (CC-Score 0.61 vs GPT-4V 0.63; Mouse Position 0.51 vs 0.12) match the comparability claim. Keeping the scaffold's READ_SOON label.
Confidence: high
Reading time estimate: 45-60 min for the core (§3-5 + Tables 1-3); +20 min for Appendix A/B if reusing the harness.

## Personal notes
Free-form notes for later.

## Follow-up actions
- Add related paper: CogAgent (arXiv 2312.08914), AppAgent (2023), Mind2Web (2023).
- Compare with: later real-OS computer-use agents (interface = screenshot + mouse/keyboard, no a11y tree) and their success-rate-based evals vs CC-Score.
- Re-run after new version: check repo for newer ScreenAgent releases / larger base model.
- Check code: https://github.com/niuzaisheng/ScreenAgent — VNC env wrapper, action parser, CC-Score implementation, dataset license.
- Read benchmark details: Appendix C (dataset stats) and Appendix D (CC-Score alignment algorithm).
