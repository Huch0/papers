# ASSISTGUI: Task-Oriented Desktop Graphical User Interface Automation

## Metadata
- Canonical key: arxiv-2312.13108
- Version: v1
- Fetch date: 2026-06-06T07:57:28Z
- Source: arxiv
- PDF: library/assistgui-task-oriented-desktop-graphical-user-interface-231213108/v1/paper.pdf
- Venue: arXiv.org (the task framing notes CVPR 2024; the extracted PDF is arXiv:2312.13108v2, dated 1 Jan 2024, p.1)
- Year: 2023
- Authors: Difei Gao, Lei Ji, Zechen Bai, Mingyu Ouyang, Peiran Li, Dongxing Mao, Qinchen Wu, Weichen Zhang, Peiyi Wang, Xiangwu Guo, Hengxu Wang, Luowei Zhou, Mike Zheng Shou
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
ASSISTGUI introduces a 100-task Windows desktop GUI-automation benchmark over 9 productivity applications with reproducible project files and outcome-based evaluation, plus an Actor-Critic LLM agent (ACE) that reaches 46% overall success versus 85% for non-expert humans (p.1 abstract; Table 1, p.7).

## Why this paper matters
This is positioned as, to the authors' knowledge, "the first task specifically designed for desktop software automation" (p.2, §1). Unlike Web/Android benchmarks centered on games and basic device usage, it targets professional productivity software (After Effects, Premiere Pro, Word, PowerPoint, etc.), which stresses dense visual understanding, complex non-tap actions (drag, draw masks), and long multi-step procedures (p.2, §1). For a computer-use harness focus, it is an early data point on (a) how to evaluate desktop agents with outcome-oriented, file/state-based checks rather than action-matching, and (b) how badly raw vision-language grounding (GPT-4V-SoM, Semantic-SAM) fails on dense desktop GUIs (p.8, §5.2). The large human-vs-model gap (85% vs 46%) makes it a stress-test benchmark rather than a near-saturated one.

## Problem and gap
CLAIMED problem: Existing GUI-automation work (Android/Web) targets "simple device usage and entertainment operations," so agent proficiency there does not translate to productivity gains (p.1 abstract; p.2, §1). Three challenges are claimed to distinguish desktop productivity automation (p.2, §1): dense GUI understanding (icons, footage, not just salient text), complex operations (drag files, draw masks on footage), and long procedures (a single effect requires layer creation, import, effect add, animation, etc.).
Gap in prior methods (p.3, §2): single OCR / vision-language models capture only simple GUIs and fail on full desktop complexity, and single-step generation struggles with long procedures. Desktop metadata is also far less informative than web HTML — "specific texts and buttons are almost impossible to extract from the meta-data," forcing reliance on visual perception (p.3, §3.1).

## Core idea
Two contributions: (1) a benchmark with paired (textual query, instructional video, project file) per task, evaluated by checking the produced artifact/state against ground truth; (2) ACE, an Actor-Critic Embodied Agent that decomposes a task into a hierarchical milestone/subtask tree from the video subtitles, parses each screenshot into a DOM-like structured text via a tool-invoking GUI Parser, and iterates Critic (assess last action from before/after screenshots) -> Actor (update subtask, emit PyAutoGUI code) until done (p.5-6, §4).

## Harness relevance
- Environment / workspace: Real Windows desktop running productivity applications (After Effects, Premiere Pro, PowerPoint, MS Word, plus system settings, widgets, file manager). 5 categories: design, Office, system settings (Sys. Set.), widget usage, file management (File Mani.) (p.4, §3.2). A Python library exposes the local Windows client to a remote (Linux) server: PyWinAuto collects metadata + screenshots, the server returns actions executed locally (p.4, "Environment Implementation").
- Observation interface: Two streams (p.3, §3.1) — (1) OS textual metadata via PyWinAuto, limited mostly to panel/window layout rectangles (example metadata in Fig. 2, p.4); (2) raw screenshots for holistic visual context. Authors stress metadata is sparse for apps like Premiere Pro, so vision is required.
- Action interface: Raw mouse+keyboard actions in PyAutoGUI syntax `action_type(arguments)` with pixel-space targets — moveTo, click/right/double-click, write, hotkey, scroll, dragTo, mouseDown/Up, press, keyDown/Up (p.3-4, §3.1). Actor output is executable Python code; a step may be a single action or a sequence (p.6, §4.4).
- Tool/API/GUI layer (GUI Parser): An LLM invokes multiple vision tools to convert a screenshot into structured per-panel text (name + element labels + coordinates) (p.6, §4.2; example output Fig. 10, p.10). Tools: metadata for panel layout; Google OCR for text; a pattern-matching method for icons; YOLO-v8 for coarse object localization; LangSAM/Grounding-DINO+SAM for precise contours; plus simple algorithms for scrolls/reference lines (p.7, "Implementation Details").
- Planner/executor/verifier structure: Planner (LLM) builds a hierarchical task tree p=[p1..pN] of milestones, each with subtasks, by (1) translating video subtitles into a raw plan and (2) refining it against the user query; a traversal visits leaf subtasks in order (p.5, §4.1; Fig. 5, p.6). Critic (LLM) outputs Success flag + Finish flag + reason from the diff d(o_t, o_{t-1}) of before/after screenshots (p.6, §4.3; Fig. 7, p.7). Actor (LLM) advances the subtask (next() if Finish) and emits action code conditioned on (a_{t-1}, o_t, s_t, p_t, c_t) (Eq. 1, p.6).
- Evaluation harness: Outcome-oriented per-category metrics (p.5, §3.3): Design/Office compared to ground truth at pixel granularity with a per-task threshold (CLIP-Sim explicitly rejected because edits are animation not semantic changes); Widget compares final screenshot in the metadata-defined display region; Sys. Set. and File Mani. use scripts checking system settings / folder structure. Binary 1/0 per task -> success rate. Versions and languages standardized for fairness.
- Training harness: None — ACE is zero-shot prompting of off-the-shelf LLMs (default gpt-4-0613); no fine-tuning is performed (p.7). Authors note lightweight models "may require fine-tuning" but did not do it (p.8, §5.1).
- Logging/trace/reproducibility: Project files fix the initial state so all models start identically (p.5, §3.2); diff module is DeepDiff (p.7). No per-step trace logging format, seed handling, or run-count protocol is described. Not reported.
- Safety/permissions: Not reported. The agent directly controls the real mouse/keyboard with no sandboxing or permission-gating discussed.

## Method
Benchmark construction (p.4-5, §3.2): instructional videos (<= 5 min) selected from official sites and video-sharing platforms; one hand-crafted query per video, deliberately not always matching the video so the model must adapt steps. Project files come from official tutorials or annotator preparation, with versions documented. Quality check: annotators execute each task to verify both video correctness and project-file functionality. Final dataset = 100 tasks, 9 applications (VERIFIED, p.5 and Table 5, p.12).
ACE method (p.5-6, §4): Planner -> {GUI Parser, Critic, Actor} loop. Planner produces milestone/subtask hierarchy (Fig. 5). GUI Parser produces per-panel structured text (Fig. 6, Fig. 10). Critic judges the prior action via screenshot diff. Actor selects current/next subtask and generates PyAutoGUI code (Fig. 7). Loop runs until the task finishes.

## Experimental setup
- Benchmark: ASSISTGUI, 100 tasks / 9 apps / 5 categories (VERIFIED p.5, Table 5).
- Default LLM: gpt-4-0613 (p.7). Ablations also use gpt-3.5-turbo and Llama2-7B (Table 4, p.8).
- Vision tools: Google OCR, YOLO-v8, LangSAM (Grounding-DINO + SAM); DeepDiff for the diff (p.7).
- Baselines: No external SOTA exists for this task, so the authors build variants of their own pipeline (p.7, §5.1): planning-method comparison removes Planning + Actor-Critic and feeds subtitles to CoT vs ReAct vs Ours (Table 1); a Qwen-VL-Chat variant replaces the GUI Parser for grounding (Table 3); GPT-4V and GPT-4V-SoM are discussed qualitatively for grounding (p.8, §5.2). Human* = average of three non-experts who watched the video once (Table 1, reference only).
- Metrics: per-category success rate (%), aggregated to overall (p.5, §3.3).
- Compute/cost: Not reported. Number of runs / variance: Not reported.

## Key results
All success rates (%), VERIFIED against Tables 1-4.
- Planning methods, Overall (Table 1, p.7): CoT 12.0; ReAct 32.0; Ours 46.0; Human* 85.0. Per-category Ours: Design 32.4, Office 40.5, Widget 60.0, Sys. Set. 75.0, File Mani. 72.7. Human* per-category: 73.5 / 83.7 / 100.0 / 100.0 / 100.0.
- Reasoning ablation (Table 2, p.7): Full 46.0; w/o Planning 35.0; w/o Critic 41.0; w/o Ins. Video 37.0. Effects concentrate in complex Design/Office; Critic helps less than expected because its judgments are unreliable on complex tasks (p.7).
- GUI Parser ablation (Table 3, p.8): Full 46.0; w/o Panel Layout 44.0; w/o Icon 13.0; w/o OCR 4.0; w/o Others 43.0; Qwen-VL-Chat as parser 5.0. So OCR and Icon parsing are by far the most load-bearing; panel layout and "others" matter little.
- LLM ablation (Table 4, p.8): GPT-4 (Planner) + GPT-4 (Actor&Critic) 46.0; GPT-3.5 planner 12.0; GPT-4 planner + Llama2 actor/critic 1.0; GPT-3.5 actor/critic 19.0; Llama2 planner + GPT-4 5.0. Heavy dependence on GPT-4, attributed to output-format adherence and hallucination (p.8).
- Qualitative (p.8, §5.2): GPT-4V cannot output button positions; GPT-4V-SoM is "almost nullified" on desktop because Semantic-SAM segmentation fails on productivity software. Common failures: complex footage ops (roto brush), blurred/blank regions (document margins), and sub-word selection in dense text (uncontrollable OCR box granularity).
- Benchmark comparison (Table 5, p.12): AssistGUI = 9 apps / 100 tasks / Windows / productivity / project files (yes), vs AndroidEnv (~30 apps, >100 tasks, no files), WebShop (1 app, 1 task / 12K instructions, no files), AutoDroid (13 apps, 158 tasks, no files). VERIFIED.

## Evidence quality
- The 46% headline is internally consistent across all four tables (Full model overall = 46.0 everywhere), which is a good sign of bookkeeping consistency.
- Baselines are entirely self-constructed ablations of the authors' own system; there is no independent external desktop baseline (justified by novelty, but it means "outperforms existing methods" is really "outperforms CoT/ReAct re-implemented inside our pipeline," p.7, §5.1).
- No variance, confidence intervals, or run counts are reported for any number, and the per-category denominators are small (e.g., Widget has 5 tasks implied by 20.0/60.0/100.0 increments, Sys. Set. by 62.5/75.0 increments). With small per-category task counts, single-percentage-point differences (e.g., 44.0 vs 46.0, 41.0 vs 46.0) are likely within noise — UNCLEAR whether some ablation gaps are significant.
- Human* is only three non-experts watching once and is explicitly "a reference," not a rigorous ceiling (Table 1 caption, p.7).
- Evaluation thresholds for Design/Office pixel similarity are per-task and "varies slightly," with no table of thresholds — reproducibility of the grader is UNCLEAR (p.5, §3.3).

## Reproducibility and artifacts
- Code: Project page https://showlab.github.io/assistgui/ (p.1). Whether code/data are released is not stated in the extracted text. Not reported in-text.
- Data: 100 tasks, each with query + instructional video + project file; versions documented (p.5). Distribution mechanism not stated in extraction.
- Models: gpt-4-0613 default; gpt-3.5-turbo, Llama2-7B; Qwen-VL-Chat; Google OCR; YOLO-v8; LangSAM; DeepDiff (p.7-8). All off-the-shelf, no released checkpoint of their own.
- Environment: Windows client + remote server via PyWinAuto + PyAutoGUI; communication library described but not named/linked in extraction (p.4).
- License: Not reported.
- Exact commands/setup: Not reported.
- Missing details: per-task pixel thresholds, number of tasks per category, run counts/seeds, prompt texts (only diagram excerpts), exact Critic diff representation.

## Strengths
- First-of-kind desktop productivity-software automation benchmark with a clear difficulty argument (dense GUI, complex actions, long procedures).
- Outcome/artifact-based evaluation (pixel similarity, system-setting scripts, folder-structure scripts) rather than fragile action-trajectory matching, plus fixed project files for reproducible initial states (p.5).
- Useful, decisive ablations: OCR (4.0 without) and icons (13.0 without) are shown to dominate; the GPT-4V-SoM failure on desktop is a concrete, actionable finding for harness designers (p.8).
- Realistic client/server architecture decoupling the (Linux) model from the (Windows) execution environment.

## Weaknesses and limitations
- Author-stated: model struggles with footage operations (roto brush), blurred/blank regions, and selecting specific words in dense text; Critic accuracy is poor on complex tasks; lightweight LLMs (GPT-3.5, Llama2) fail badly and likely need fine-tuning (p.8).
- Inferred: small per-category task counts and no variance reporting make fine-grained comparisons unreliable; no external baseline; heavy single-model (GPT-4) dependence limits generality; no safety/permission layer for real mouse/keyboard control; the benchmark deliberately targets "relatively basic tasks" at this "early stage" (p.4), so it under-covers truly long expert workflows.
- Aging/contamination risk: tasks are tied to specific app versions and languages; over time, app UI drift can break project files and graders. Instructional videos are public, and GPT-4's training data may already contain tutorials for these well-known apps — mild contamination risk for the Planner, though grading is outcome-based so this is partially mitigated.

## Relationship to prior work
Closest benchmarks: AndroidEnv, AutoDroid (Android), WebShop, Mind2Web, WebArena (Web) — ASSISTGUI differs by platform (Windows desktop) and task focus (productivity software with project files) (Table 5, p.12; p.10-11, §6). Method lineage: GUI Parser follows the tool-invoking pattern of MM-ReAct and VisualClues (p.6, §4.2); planning contrasts with CoT and ReAct (Table 1); grounding contrast is GPT-4V-SoM / Set-of-Mark + Semantic-SAM (p.8). Genuinely new: the desktop productivity benchmark + project-file evaluation and the milestone/subtask + Critic loop driven by instructional-video subtitles. Incremental: the agent components individually reuse established patterns (Actor-Critic, tool-calling parser, ReAct-style loop).

## What I should read
- Must read: §3 (benchmark: task formulation, data collection, evaluation, p.3-5) and Tables 1-5 (p.7-8, 12) — the core reusable contribution for a harness.
- Skim: §4 method (Planner/Parser/Critic/Actor, p.5-6) and the qualitative GUI-Parser-vs-Semantic-SAM comparison (p.8).
- Can skip: related-work prose (§2) and the reference list.
- Follow-up papers: AutoDroid (2308.15272), WebArena (2307.13854), Mind2Web (2306.06070), GPT-4V-SoM / Set-of-Mark (2310.11441), AssistGPT (2306.08640, same group).

## Triage decision
Label: READ_SOON
Rationale: Foundational, frequently-cited early desktop computer-use benchmark directly relevant to a computer-use/harness interest; the benchmark-construction and outcome-based evaluation design and the strong empirical evidence on what makes desktop GUI grounding fail (OCR/icons essential; GPT-4V-SoM nullified) are worth a careful read. Evidence is solid enough to keep the existing label rather than upgrade/downgrade — it does not strongly differ from the prior judgment.
Confidence: high
Reading time estimate: 35-45 min for a focused read of §3-5 and the tables.

## Personal notes
Free-form notes for later.

## Follow-up actions
- Add related paper: AutoDroid (2308.15272); WebArena (2307.13854)
- Compare with: OSWorld / later Windows-desktop agent benchmarks (check whether the library has them)
- Re-run after new version: v2 already extracted (1 Jan 2024); watch for a CVPR camera-ready
- Check code: project page https://showlab.github.io/assistgui/ for code/data release
- Read benchmark details: §3.3 evaluation metrics and per-category task counts/thresholds
