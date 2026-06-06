# Cradle: Empowering Foundation Agents towards General Computer Control

## Metadata
- Canonical key: arxiv-2403.03186
- Version: v1
- Fetch date: 2026-06-06T07:57:29Z
- Source: arxiv
- PDF: library/cradle-empowering-foundation-agents-towards-general-computer-240303186/v1/paper.pdf
- Venue: International Conference on Machine Learning
- Year: 2024
- Authors: Weihao Tan, Ziluo Ding, Wentao Zhang, Boyu Li, Bohan Zhou, Junpeng Yue, Haochong Xia, Jiechuan Jiang, Longtao Zheng, Xinrun Xu, Yifei Bi, Pengjie Gu, Xinrun Wang, Börje F. Karlsson, Bo An, Zongqing Lu
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

(Venue note: the scaffold metadata lists ICML 2024 and the task brief says NeurIPS 2024, but the extracted PDF header (p.1) reads "Preprint. Under review." with arXiv:2403.03186v3, 2 Jul 2024. The venue stamp is therefore Unclear from the extraction itself; metadata above is left as-supplied.)

## One-sentence takeaway
CRADLE proposes the General Computer Control (GCC) setting -- agents that act on any software using only screenshots in and keyboard/mouse out -- and a six-module GPT-4o framework that, as a preliminary demonstration, plays four commercial games (incl. 40-min RDR2 story missions) and five desktop apps plus OSWorld without any built-in APIs.

## Why this paper matters
CLAIMED: This is positioned as the first framework to let LMM agents follow a main storyline and complete 40-minute real missions in a complex AAA game (RDR2) under a pure screenshot/keyboard/mouse interface, and to span both games and office software with one framework (abstract; p.4, p.8).
WHY READ: The GCC framing (vision-only observation, OS-level keyboard+mouse action, no internal APIs/DOM/accessibility tree) is exactly the "hardest" harness setting for computer-use agents and is directly relevant to the harness-design interest profile. The six-module decomposition (information gathering, self-reflection, task inference, skill curation, action planning, memory) is a concrete, reusable agent architecture. EVIDENCE for the headline claims is largely qualitative/human-evaluated rather than benchmark-graded, so the value is more in the setting and architecture than in any leaderboard number.

## Problem and gap
Problem: existing foundation agents do not generalize across virtual environments because each environment ships its own hand-designed observation and action space (raw HTML/DOM, internal APIs, predefined semantic actions, accessibility element IDs), so an agent built for one cannot transfer (p.1, p.4-5).
Gap (CLAIMED, p.4-5): prior web/GUI/mobile agents that use screenshots still rely on built-in APIs or tools to get interactive element IDs (e.g., Set-of-Mark, DOM); game agents (JARVIS-1, MineDojo, StarCraft II, CivRealm) use internal textual observations and predefined semantic action spaces; VPT outputs raw keyboard/mouse but needs costly action-labeled video; SIMA needs expensive human gameplay data and targets 10-second tasks. None operate purely from screen pixels with raw keyboard/mouse across both games and software. CRADLE targets that uncovered combination.

## Core idea
CRADLE is a training-free, modular LMM-orchestration loop (GPT-4o backbone) that converts a short screen video into low-level keyboard/mouse code. The key mechanism is that the LMM writes Python "skill" functions wrapping an io_env class (e.g., key_hold('tab'), place_residential_zone(x1,y1,x2,y2)), so semantic intent is bridged to OS-level control without any environment API (p.5-6, Fig. 5). Six modules form a "reflect on the past, summarize the present, plan for the future" loop (p.7): perceive (information gathering) -> judge outcome (self-reflection) -> pick the next subtask (task inference) -> fetch/generate code skills (skill curation) -> instantiate parameters into an executable action (action planning), all backed by episodic + procedural memory. Skills are embedded with text-embedding-ada-002 and retrieved by similarity (p.8).

## Harness relevance
- Environment or workspace: arbitrary commercial software and games run on a normal Windows 10 machine; no source code or APIs required. Evaluated on 4 games (RDR2, Stardew Valley, Dealer's Life 2, Cities: Skylines), 5 apps (Chrome, Outlook, CapCut, Meitu, Feishu), and the OSWorld benchmark (p.3-4, p.8).
- Observation interface: screenshots only -- specifically a short screen video clip recording the last action's execution, sampled at 2 fps; complete-screen video of variable length (p.5, p.8). (Audio is explicitly part of the GCC definition but NOT used in this work -- p.11 limitation ii.)
- Action interface: keyboard + mouse only -- key_press, key_hold, key_release, mouse_move, wheel_scroll (plus mouse buttons), including press duration and mouse-move speed, combinable into combos/shortcuts; simulated via Python and encapsulated in io_env (p.5). Authors note prior work rarely models key_hold/key_release/mouse speed, which matter in games.
- Tool/API/shell/GUI layer: GUI-only; explicitly NO built-in APIs/DOM/accessibility IDs. Perception is augmented with external vision tools -- template matching, Grounding DINO, and SAM -- for grounding/localization (p.6).
- Planner/executor/verifier/search structure: the six modules. Information Gathering = perception (visual: UI elements, layout, imagery, animations; text via OCR: content, navigation, notifications, instructions). Self-Reflection = verifier (did last action/task succeed, why failed). Task Inference = high-level planner choosing the next subtask. Skill Curation = retrieve/update/generate code skills. Action Planning = instantiate skill parameters (duration, position, speed) into the concrete action. An Executor maps semantic actions to OS keyboard/mouse commands (p.6-8). No tree/beam search; self-consistency and ToT were excluded due to request-rate limits (p.11).
- Evaluation harness: primarily human evaluation for all games and apps (like SIMA), because no general automatic success signal exists across diverse software; OSWorld is the one place with provided automatic evaluation scripts used as a comparison baseline (p.8).
- Training harness: none -- no fine-tuning or RL in this work; training is explicitly left to future work (p.11 limitation iv).
- Logging/trace/reproducibility: episodic memory stores key screenshots, module outputs, actions, tasks, reasoning, with periodic summarization into long-term summaries; procedural memory stores code skills (p.7). Setup/load scripts and game saves/checkpoints are provided in the repo to reset state (p.8).
- Safety/permission: no runtime sandbox/permission gate described. Authors flag misuse risk (game cheats, harmful software operations) and call for external regulations/safeguards (p.11-12), but no mechanism is implemented.

## Method
Backbone: GPT-4o (gpt-4o-2024-05-13) for all LMM calls; text-embedding-ada-002 for skill embeddings (p.8). Pipeline per step (p.5-8):
1. Capture a screen video clip of the last action's execution (2 fps).
2. Information Gathering: LMM (+ optional Grounding DINO / SAM / template matching) extracts visual and textual state, OCRing on-screen guidance.
3. Self-Reflection: LMM judges whether the last action and current task succeeded and diagnoses failures from sequential key screenshots + prior context.
4. Task Inference: LMM selects the highest-priority next subtask and decides when to stop/switch tasks.
5. Skill Curation: retrieve relevant code skills from procedural memory; update or generate new ones (skills can come from in-game tutorials/manuals or self-exploration; Fig. 5 shows examples per game).
6. Action Planning: select skills and fill parameters (duration/position/speed) to form the executable action; Executor runs it as OS keyboard/mouse commands.
Memory: episodic (multimodal experience + periodic summaries) and procedural (code skills, similarity-retrieved). Note: RDR2 and Stardew Valley environments are paused while waiting for LMM responses (latency); other environments run continuously (p.8).

## Experimental setup
- Datasets/benchmarks: 4 games (RDR2 first two Chapter-I story missions = 13 checkpoint tasks + 1 open-ended "Buy Supply" in Chapter II; Stardew Valley 3 tasks; Dealer's Life 2 weekly shop management; Cities: Skylines city-building) and 5 apps (5 tasks each), plus OSWorld (369 tasks across Office 117, OS 24, Daily 78, Workflow 101, Professional 49) (p.8-9, Table 4).
- Baselines: ReAct-like (gather + skill curation + action planning only), Reflexion-like (adds self-reflection + episodic memory), Voyager-like (text-only, image described to text -- ablates vision), and backbone swap to Claude 3 Opus; on OSWorld, GPT-4o and GPT-4o+SoM (Set-of-Mark) (p.11, Tables 4 & 6). Authors state no existing method is directly applicable to GCC, so baselines are "-like" adaptations.
- Models: GPT-4o (main), Claude 3 Opus (ablation backbone).
- Metrics: human-judged success rates and task-specific metrics; results given as mean +/- std over 5 runs or (s/t) successful runs; OSWorld uses its automatic scripts.
- Compute/cost: most run on regular Windows 10; RDR2 on RTX-3060 and RTX-4090 (slight gain on 4090 due to stability). Step limits: RDR2 500/task, Stardew Valley 100/task, software apps 30/task, Cities: Skylines 1000 steps or budget exhausted (p.8-10). LMM API cost not quantified.
- Artifacts: open-source framework claimed (project site baai-agents.github.io/Cradle); repo includes setup/load scripts and saves.

## Key results
VERIFIED against extraction:
- RDR2 (p.8-9, Fig. 7): high success on simple navigation/follow tasks (e.g., Follow Dutch, Go to Barn); struggles with real-time combat and search/indoor tasks due to poor enemy/object localization. Even with Grounding DINO, Protect Dutch (nighttime combat) success drops to 20%. Each RDR2 task: max 500 steps, retries allowed. (CLAIMED first agent to complete 40-min main-storyline missions; EVIDENCE is human-evaluated trajectory success rates, not an external benchmark.)
- Stardew Valley (Table 1, p.9): Farm Clearup 14.8 +/- 5.0 grids cleared; Cultivation 4/5; Shopping 1/5. GPT-4o struggles to localize nearby objects in this 2D pixel-art (OOD) style.
- Dealer's Life 2 (Table 2, p.9): Avg. Haggling Count 1.95 +/- 0.43; Turnover Rate 93.6 +/- 6.9%; Item Profit Rate 37.8 +/- 19.1%; Total Profit Rate 39.6 +/- 27.3%, peaking at +87.4% in a single run. (Abstract's "maximal weekly total profit of 87%" = this single-run peak, NOT the mean -- the mean total profit rate is ~39.6%.)
- Cities: Skylines (Table 3, p.10): Roads in Closed Loop 4/5; Sufficient Water Supply 1/5 (most common failure: unconnected water pipes); Sufficient Electricity 5/5; Zones Area >=90% 4/5; Maximal Population 450 +/- 224, rising to 850 +/- 142 with human assistance (-w-HA, <=3 unit operations). The "city of a thousand people" headline is achieved only after human assistance (Fig. 10b shows 1100+ people post-fix). UNCLEAR/caveat: the marquee "thousand-person city" is not a fully autonomous result.
- Software apps (Fig. 11, p.10-11): mixed success rates, max 30 steps/task; GPT-4o fails to recognize specific UI items even in familiar Chrome/Outlook (e.g., forgetting Save, confusing enabled vs disabled buttons), worse on non-standard layouts (CapCut, Meitu, Feishu). Exact per-task numbers are in a figure, not transcribed in the extraction (Not reported here as text).
- OSWorld (Table 4, p.10): overall success -- GPT-4o 5.03%, GPT-4o+SoM 4.59%, CRADLE 7.81% (All=369). CRADLE is highest overall and especially strong on Professional (49 tasks): 20.41% vs GPT-4o 4.08% / +SoM 2.04%. On OS (24): CRADLE 16.67% < +SoM 20.83%. Office (117) tied at 3.58% across all three. Absolute numbers are low for every method.
- Ablation (Table 6, p.11-12): only CRADLE (GPT-4o) completes the harder tasks. CRADLE(GPT-4o): Follow Dutch 13+/-3 (5/5), Follow Micah 33+/-3 (5/5), Hitch Horse 26+/-5 (4/5), Protect Dutch 461+/-0 (1/5), Search for Supplies 134+/-0 (1/5), Cultivation 24+/-4 (4/5). ReAct-like, Reflexion-like, Voyager-like, and Claude-3-Opus all hit N/A (all-5-runs failure) on Hitch Horse, Protect Dutch, Search for Supplies, and Cultivation. Voyager-like (no vision) is worst; Claude 3 Opus fails from unreliable OCR of in-game guidance.

## Evidence quality
Mixed.
- Strong where it counts for the contribution's framing: the ablation (Table 6) cleanly isolates the value of task inference + procedural memory (ReAct-like/Reflexion-like fail the harder tasks) and of vision (Voyager-like collapses). 5-run mean+/-std / (s/t) reporting gives some variance signal.
- Weak: the flagship claims (40-min RDR2 missions, thousand-person city, image/video editing) rest on human evaluation with tiny task counts (5 runs, ~13 RDR2 tasks, 3-5 tasks per app) and no inter-rater reliability or external grader. The "thousand-person city" requires human assistance and the "87% profit" is a single-run peak -- both are presented prominently in the abstract in a way that overstates the typical autonomous result. OSWorld (the only auto-graded benchmark) shows CRADLE at 7.81% overall -- a real but very low absolute number, and it is even beaten by GPT-4o+SoM on the OS split. Baselines are author-adapted "-like" versions, not canonical implementations, so the comparison is suggestive rather than definitive. Per-app success rates live only in figures. Net: the paper convincingly demonstrates the GCC setting is operable end-to-end, but does not demonstrate strong absolute task competence.

## Reproducibility and artifacts
- Code: CLAIMED open-source ("open-source CRADLE framework", project site https://baai-agents.github.io/Cradle/). Not verified here.
- Data: setup/load scripts, game saves and checkpoints provided in repo for state reset (p.8). Games/apps are commercial and must be obtained separately.
- Models: GPT-4o gpt-4o-2024-05-13; text-embedding-ada-002; Claude 3 Opus (ablation). External tools: Grounding DINO, SAM, template matching.
- Environment: Windows 10; RDR2 on RTX-3060 / RTX-4090.
- License: Not reported (in extraction).
- Exact commands or setup: implementation details in Appendices A-H (only TOC of appendix is in the read extraction; specific commands Not reported in main body).
- Missing details: per-app success numbers (figures only), LMM API cost/token counts, full prompts (in appendix), automatic-evaluation criteria for the human-judged tasks.

## Strengths
- Defines a clean, ambitious, and standardizable setting (GCC: vision-only obs, raw keyboard/mouse, no APIs) that is highly transferable across software.
- Genuinely API-free, code-as-skill execution via io_env; models press duration and mouse speed, which most prior GUI agents ignore -- important for dynamic/game UIs.
- Breadth: same framework spans AAA 3D games, 2D games, simulation/management games, office apps, creative apps, and OSWorld.
- Modular architecture is a useful, reusable template; ablation supports the necessity of task inference, procedural memory, and vision.
- Honest qualitative failure analysis (localization, OOD icons, missing Save clicks).

## Weaknesses and limitations
- Author-stated (p.11): poor on OOD icons/styles (e.g., Stardew Valley) due to LMM limits; no audio modality despite GCC including it; heavy per-step LMM calls -> high cost/latency; no training (RL/imitation) yet; only a limited task set explored.
- Inferred: low absolute success (OSWorld 7.81%; many 1/5 results); flagship results lean on human assistance (thousand-person city) or single-run peaks (87% profit), risking over-claiming; human evaluation without reliability reporting; baselines are adapted approximations; per-app numbers buried in figures; environments must be paused for latency in two games (not real-time), which weakens the "react quickly / precise timing" motivation.

## Relationship to prior work
- Closest: SIMA (Raad et al. 2024) -- also screenshot-in/keyboard-mouse-out across many games, but trained via behavior cloning on human gameplay and short (~10s) tasks; CRADLE is training-free and tackles long-horizon (40-min) tasks. VPT -- raw keyboard/mouse from pixels but needs action-labeled video. JARVIS-1 / Voyager -- open-world Minecraft agents, but rely on internal APIs / predefined semantic actions (Voyager is the code-skill+memory ancestor here; CRADLE reuses its skill-embedding/retrieval recipe). OSWorld -- the contemporaneous benchmark CRADLE evaluates on. Web/GUI agents (Mind2Web, WebVoyager, UFO, CogAgent, SeeClick, AppAgent, OS-Copilot) -- screenshot-aware but API/DOM/SoM-dependent.
- Genuinely new: combining (a) no built-in APIs, (b) both complex commercial games and office software, (c) long-horizon real missions, under one training-free LMM framework. Incremental parts: the six modules individually echo ReAct/Reflexion/Voyager; the novelty is their composition for GCC plus the duration/speed-aware io_env action space.

## What I should read
- Must read: section 3 The CRADLE Framework (p.5-8) for the six modules and io_env/skill mechanism; Fig. 4-6; section 4.1 settings (p.8); Table 6 ablation (p.11-12); OSWorld Table 4 (p.10).
- Skim: per-game result sections (p.8-10) and the limitations section (p.11-12).
- Can skip: game/app descriptive prose (p.3-4) if already familiar; reference list.
- Follow-up papers: OSWorld (Xie et al. 2024), SIMA (Raad et al. 2024), Voyager (Wang et al. 2024), VPT (Baker et al. 2022); appendices A-H for prompts/implementation if reproducing.

## Triage decision
Label: READ_SOON
Rationale: Directly on-target for computer-use / harness design -- it stakes out the strictest observation/action interface (pixels + raw keyboard/mouse, no APIs) and gives a concrete six-module architecture and code-skill executor worth studying and comparing against. Evidence does not strongly differ from the assigned label: contributions are real for the setting/architecture, but absolute performance is weak and several headline numbers are caveated (human assistance, single-run peak), so it is not a MUST_READ for results -- it is a READ_SOON for ideas and framing.
Confidence: high
Reading time estimate: ~45-60 min for the main paper; +30 min if reading appendices for prompts/implementation.

## Personal notes
The abstract/intro headline numbers need care: "thousand-person city" = with human assistance (autonomous max pop 450+/-224); "87% profit" = single-run peak (mean total profit 39.6%); RDR2 "40-min missions" = human-evaluated trajectory success, with combat/search tasks frequently failing (Protect Dutch 20% even with Grounding DINO). The most defensible quantitative claim is the OSWorld comparison (CRADLE 7.81% vs GPT-4o 5.03% vs +SoM 4.59%, no internal APIs), driven largely by the Professional split (20.41%). Two game environments are paused during LMM inference, so "real-time" should be read loosely.

## Follow-up actions
- Add related paper: OSWorld (arXiv:2404.07972), SIMA (arXiv:2404.10179).
- Compare with: API/DOM-based GUI agents (UFO, OS-Copilot) vs pure-pixel here; Voyager skill-curation lineage.
- Re-run after new version: check whether later versions add audio, training/RL, or fully-autonomous Cities: Skylines results.
- Check code: confirm open-source repo + license at baai-agents.github.io/Cradle.
- Read benchmark details: Appendices A-H for prompts, per-environment implementation, and exact OSWorld setup.
