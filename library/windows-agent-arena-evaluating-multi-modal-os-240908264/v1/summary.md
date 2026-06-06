# Windows Agent Arena: Evaluating Multi-Modal OS Agents at Scale

## Metadata
- Canonical key: arxiv-2409.08264
- Version: v1
- Fetch date: 2026-06-06T07:57:29Z
- Source: arxiv
- PDF: library/windows-agent-arena-evaluating-multi-modal-os-240908264/v1/paper.pdf
- Venue: International Conference on Machine Learning
- Year: 2024
- Authors: Rogerio Bonatti, Dan Zhao, Francesco Bonacci, Dillon Dupont, Sara Abdali, Yinheng Li, Yadong Lu, Justin Wagle, K. Koishida, A. Bucker, Lawrence Jang, Zack Hui
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
A Windows-OS port of the OSWorld execution-based agent benchmark (154 real-app tasks) whose chief novelty is Azure cloud parallelization that collapses a multi-day serial eval into roughly 20 minutes, shipped with a reference multimodal agent (Navi) that tops out at 19.5% success vs 74.5% for a human.

## Why this paper matters
For anyone building or evaluating computer-use agents, this is a concrete reference design for the two hardest non-model parts of an OS-agent harness: (1) running a *real* OS (Windows 11 in a VM, not a simulator or DOM proxy) with execution-based per-task rewards, and (2) making full-benchmark evaluation cheap enough to iterate on by parallelizing across cloud workers rather than speeding up a single clock. The parallelization contribution is the genuinely transferable engineering idea; the benchmark itself is largely an adaptation of OSWorld. Navi is a useful baseline reference for how far off-the-shelf VLMs (GPT-4V/4o, Phi-3-V) are from human OS competence (large gap), and the Set-of-Marks/UIA/OmniParser ablations are directly relevant to observation-interface design choices.

## Problem and gap
CLAIMED problem (p1 abstract, p3 section 2): existing agent benchmarks are (i) narrow in modality/domain (text-only, web nav, Q&A, coding) and (ii) slow to evaluate (order of days) because tasks are multi-step and sequential, and OS clocks cannot be fast-forwarded like a physics sim. Prior real-OS benchmarks OSWorld (Linux) and AndroidWorld (mobile) addressed realism but not scalable evaluation: OSWorld parallelizes only within a single host (low-single-digit VMs, EVIDENCE p3 Table 1 footnote, p7). The gap WAA targets: a real-OS benchmark for **Windows** (CLAIMED 73% desktop market share, p2) with native cloud parallelization. This is incremental over OSWorld in benchmark design but new in the parallelization axis and OS target.

## Core idea
Adapt OSWorld's POMDP task formalism and JSON-configured, execution-based evaluation onto Windows 11 running inside a Docker-hosted QEMU/KVM VM, then make the whole benchmark a stateless unit of work that Azure ML can fan out: each task (or small batch) runs in its own isolated container/VM worker, so wall-clock time approaches the cost of the single slowest task rather than the sum of all tasks. A reference agent (Navi) is provided so the harness is usable out of the box, and the observation interface is deliberately modular (screenshot + UIA accessibility tree + multiple Set-of-Marks element detectors including OmniParser) so the harness doubles as an ablation testbed for screen-grounding methods.

## Harness relevance
- **Environment / workspace**: a real Windows 11 VM (not a simulator), deployed via QEMU+KVM inside a Docker container adapted from `dockur/windows` (p6 section 3.3). Licensing prevents shipping a prebuilt snapshot; users download a Microsoft trial image and scripts prepare it (~30GB snapshot). Runs locally on Ubuntu/WSL or on Azure ML.
- **Observation interface** (p4 section 3.1.1, A.1 p15): task instruction; clipboard content (text via pyperclip, or VLM-generated description for images); foreground/background window titles (pygetwindow); and a screen representation. Screen can be raw screenshot (RGB 1440x900x3, current + previous frame), DOM tree (browser only), Windows UI Automation (UIA) tree (via pywinauto), or pixel-model-generated Set-of-Marks. SoM generators: UIA parsing, DOM parsing, OCR (proprietary OneOCR / open Tesseract), icon+image detection (proprietary / open Grounding DINO), and OmniParser (proprietary multi-element detector with icon captioning). The UIA tree is NOT fed raw to the agent; it is parsed into SoM marks.
- **Action interface** (p4 section 3.1.2, Table 2 / A.2 Table 6 p18): two action spaces - free-form pyautogui/Python code execution, and a higher-level `Computer` class wrapper (mouse move_id(id)/move_abs(x,y)/single|double|right_click/scroll; keyboard write/press; clipboard copy_text/copy_image/paste; os.open_program; window_manager.switch_to_application). `move_id` lets the agent address screen elements by SoM ID rather than raw coordinates.
- **Tool/API/shell/GUI layer**: GUI-driven real applications (LibreOffice Writer/Calc, Edge, Chrome, File Explorer, Settings, VS Code, VLC, Notepad, Clock, Paint). Task setup can invoke PowerShell commands; a reverse proxy bridges Edge/Chrome to host ports for browser-state inspection (p6).
- **Planner/executor/verifier structure**: Navi is a single-loop chain-of-thought agent (no explicit search/tree). Each step it answers screen-understanding + planning questions, then emits exactly one action as Python code, plus a free-text "memory" block it can carry forward; decisions are DONE/FAIL/WAIT/COMMAND (prompt in D.1, p29-31). Episode ends on DONE/FAIL or t > t_max.
- **Evaluation harness** (p4 section 3.1.3, A.3 p23): execution-based, OSWorld-style. After the agent terminates, a per-task evaluator script inspects VM device state (config files, app settings, file contents, or web-based dynamic checks) vs initial/golden state. Reward R in [0,1]: binary {0,1} for rule-based tasks, continuous (0,1] for similarity-based tasks (e.g., golden-image comparison). Reward is terminal only; the authors note intermediate/partial-credit rewards are left as future work.
- **Training harness**: none. The paper only evaluates zero-shot generalist VLMs; it *discusses* using WAA to generate data at scale for RL/imitation as future work (p9 section 5), but trains nothing.
- **Logging/trace/reproducibility**: deterministic initial-state setup scripts per task (st=0); JSON task configs (id/instruction/config/evaluator/result, example A.6 Fig 12 p24); logs written to mounted volumes (local) or Azure Blob (cloud); per-step action history retained in agent context. Open-source code + an open-model agent variant `Navi_open` for reproducibility without proprietary models.
- **Safety/permission**: isolated compute instances + Docker containers; agent and VM control ports are not exposed to the internet, communication stays local (p7 "Security"). The Navi prompt itself grants the model "full and complete permission" to execute any code (D.1 p29) - i.e., no in-loop action gating; safety is at the container-isolation layer, not the agent layer. Discussion section flags human-in-the-loop/override as desirable future work.

## Method
Benchmark construction (p4-6 section 3.2): 154 tasks across 6 domains / 11 applications - Office (LibreOffice Writer+Calc) 43 tasks (28%), Web Browsing (Edge/Chrome) 30 (19%), Windows System (File Explorer/Settings) 24 (16%), Coding (VS Code) 24 (16%), Media & Video (VLC) 21 (14%), Windows Utilities (Notepad/Clock/Paint/Calculator) 12 (8%). CLAIMED ~2/3 of tasks adapted from OSWorld Linux configs (file paths, PowerShell conversions, reverse-proxy browser comms, evaluator/instruction fixes) and ~1/3 created from scratch for Windows-specific activities (p6). Tasks vary in difficulty (easy/medium/hard) and step count (Fig 2). Infeasible tasks are included to test refusal/feasibility recognition.

Infrastructure (p6-7 section 3.3): Docker container holds the Windows 11 VM; a Python Flask server inside the VM is the bridge receiving commands and returning observations/files to client processes (scheduler, agent, evaluator). Local mode mounts OS image + code as external volumes to avoid image rebuilds. Cloud mode uses Azure ML jobs; VMs spun up/torn down per submission, snapshot + logs in Azure Blob, tasks distributed evenly across workers, results aggregated. Contrasted with OSWorld's multi-VMware-VMs-per-host approach, which the authors argue caps at low-single-digit parallelism (p7).

Agent (p7 section 4.1, D.1): Navi, multimodal, CoT-prompted. Input = window titles + screen representation (one of the SoM configs) + previous-screen image + action history + clipboard + memory. Output = screen annotations, multi-step plan, one action code block, updated memory.

## Experimental setup
- **Benchmark**: WindowsAgentArena (154 tasks) plus a processed Mind2Web split (broken/missing-GT entries removed) for cross-benchmark validation (C.1 p27).
- **Models** (Table 4 p8): Phi-3-V, GPT-4o-mini, GPT-4o, GPT-4V-1106 as the reasoning backbone, each run across SoM input configs (Pytesseract+DOM+Grounding DINO [open]; OneOCR+proprietary detectors; OmniParser), each with UIA tree on/off.
- **Baselines**: human performance (single participant, ~1.5h over 5 sittings, A.5 p22) as the human reference; for Mind2Web, the original SeeAct agent (GPT-4V).
- **Metrics**: per-domain and total success rate (WAA); Element Accuracy / Operation F1 / Step Success Rate (Mind2Web, Table 5 p10).
- **Compute / cost** (A.7 p24-25): Azure CPU VMs supporting nested virtualization w/ KVM; primarily Standard D8 v3 (8 cores, 32GB, $0.384/hr). Median full-run times in Table 11 over ~50 parallel runs. OmniParser inference runs on CPU (no GPU), which is why it is slow.
- **Artifacts**: open-source code + benchmark + open-model agent variant `Navi_open`; webpage and GitHub repo (p2).

## Key results
- **VERIFIED: Best Navi = 19.5% total success** (GPT-4V-1106 + UIA + OmniParser), vs **VERIFIED: human 74.5%** (Table 4 p8; abstract). Large gap confirms zero-shot generalist VLMs are far from human OS competence.
- **VERIFIED: 154 tasks** (p2 contributions, p4 section 3.2, p10 conclusion, Table 1). Abstract's "150+" is a rounded restatement of the same 154; both consistent.
- **VERIFIED: Azure full-eval "as little as 20 minutes"** (p2; A.7 Table 11). EVIDENCE nuance: most configs finish <20 min (e.g., GPT-4o + OneOCR + no-UIA = 6.5 min; GPT-4o + Pytesseract/DINO + UIA = 16.1 min), but OmniParser configs are 37.8-82.2 min because OmniParser runs on CPU. So "~20 min" is achievable, not universal across configs. Median times computed over ~50 parallel runs.
- Per-domain spread (Table 4): best agent strong on text-dominant interfaces (Web Browser, Windows System 33.3%) and weak on icon/shortcut-heavy ones (Office 0%, Windows Utils 8.3%). Human is inverse-ish: highest on Windows Utilities 91.7%, lowest on VLC 42.8% (also Table 8 p23).
- **UIA markers matter**: adding UIA on top of pixel detectors boosts GPT-4V-1106 by CLAIMED 57% (OmniParser), 52% (open models), 15% (proprietary pixel) (p8). But UIA querying can take seconds to minutes on complex screens (a real latency cost).
- **Model gap**: GPT-4V-1106 best; >2x GPT-4o's success in the UIA+OmniParser config; Phi-3-V hallucinates on long contexts / multi-step planning.
- **Failure modes** (p8, Fig 6): imprecise SoM bounding boxes -> wrong element selection; visual-language misalignment (correct textual intent, wrong visual ID). OmniParser's edge is attributed to its icon-captioning linking IDs to descriptions.
- **Mind2Web** (Table 5 p10): Navi multimodal Image+SoM(DOM+Pixel) with GPT-4o reaches Element Acc 47.3% / Op-F1 85.8% / Step-SR 45.2%, beating SeeAct GPT-4V (44.3% / 71.8% / 38.3%) - CLAIMED SOTA on this processed split.

## Evidence quality
Mixed. The benchmark and harness are solid and execution-based rewards are a real strength over static/text-match benchmarks. Weaknesses in the evidence: (1) **Human baseline = a single casual user, ~1.5h** (A.5 p22) - the 74.5% "human" reference therefore has no variance/CI and is statistically thin; it anchors the headline gap claim. (2) **No statistical reporting** (no seeds, no variance) on agent success rates despite LLM stochasticity. (3) The "20 minutes" headline is the best-case config; the strongest *accuracy* config (OmniParser) is the slowest (~39-82 min), so the speed and accuracy peaks do not coincide - a caveat the body discloses but the abstract elides. (4) **OSWorld overlap**: ~2/3 of tasks are adapted from OSWorld, so this is more a Windows re-port than a fresh task suite; novelty concentrates in infrastructure. (5) Mind2Web "SOTA" is on a *processed* (filtered) split, limiting comparability. (6) Per-domain n is small (e.g., Office 43, Utilities 12), so single-task swings move category percentages a lot. No reward-hacking / evaluator-robustness analysis is reported.

## Reproducibility and artifacts
- Code: Yes - open-source, https://github.com/microsoft/WindowsAgentArena (p2).
- Data: 154 task JSONs released; full task list enumerated in A.4 (p19-22).
- Models: Reference agent Navi released; `Navi_open` uses only open SoM models (Tesseract, Grounding DINO, open OmniParser). Reasoning backbones (GPT-4V/4o/4o-mini, Phi-3-V) are external API/model dependencies.
- Environment: Real Windows 11 VM via QEMU/KVM + Docker (`dockur/windows`-derived); local (Ubuntu/WSL) or Azure ML.
- License: Not reported in extraction (repo license not stated in paper text).
- Exact commands or setup: Not in paper body; deferred to open-source repo instructions. Azure VM guidance + cost table in A.7.
- Missing details: cannot ship Windows snapshot (licensing) - users self-provision a Microsoft trial image; exact Navi prompt is in D.1 but proprietary OCR/detector/OmniParser weights are not open.

## Strengths
- Real Windows OS with real apps (high ecological validity) and execution-based, state-checking rewards rather than trajectory matching or text-match.
- Cloud-native parallelization is the standout engineering contribution: turns multi-day serial evals into ~20 min, lowering iteration cost.
- Modular observation stack (screenshot / UIA / DOM / multiple SoM detectors) makes it a clean ablation testbed for screen-grounding methods; UIA-vs-pixel and OmniParser ablations are genuinely informative.
- Open-source with an all-open-model agent variant; second-benchmark (Mind2Web) validation adds external robustness signal.
- Includes infeasible tasks to probe refusal/feasibility recognition.

## Weaknesses and limitations
- Single-user, ~1.5h human baseline; no statistical/variance reporting anywhere.
- ~2/3 task overlap with OSWorld - incremental as a benchmark; main novelty is infrastructure + OS target.
- Speed/accuracy tradeoff: best-accuracy (OmniParser) config is far from the "20 min" headline; OmniParser bottlenecked on CPU.
- Terminal-only binary/continuous reward; no partial credit (authors note as future work), so multi-step tasks score all-or-nothing.
- No in-loop safety/permission gating - agent prompt grants full code-execution permission; isolation is purely at the container boundary.
- Cannot distribute the OS image (licensing friction for reproducibility).
- Absolute agent performance is low (19.5%), limiting headroom analysis; many domains at 0% for some configs.

## Relationship to prior work
- Closest: **OSWorld** (Xie et al. 2024) - WAA directly adapts its POMDP formalism, JSON task structure, and execution-based evaluation; key differences are Windows (vs Linux) and Azure cross-machine parallelization (vs single-host VMware). **AndroidWorld** (Rawles et al. 2024a) - Table 1 is adapted from it; mobile analogue.
- Static/data-collected benchmarks it contrasts against: Mind2Web, WebLinx, PixelHelp, MoTIF, AiTW, OmniAct (no live reward).
- Interactive web/desktop benchmarks: MiniWoB++, WebArena, VisualWebArena, WorkArena, MMInA, GAIA.
- Agent/grounding lineage: Set-of-Marks prompting (Yang et al. 2023), OmniParser (Lu et al. 2024), SeeAct (Mind2Web baseline), UFO (Windows GUI agent), CogAgent, MM-Navigator, OS-Copilot.
- Genuinely new: cloud-scalable real-OS eval infra for Windows + the SoM/UIA/OmniParser observation ablations. Incremental: the task suite (OSWorld-derived) and the agent architecture (standard CoT single-action VLM loop).

## What I should read
- Must read: section 3.1 (POMDP, observation/action spaces, execution reward), section 3.3 (deployment/parallelization infra), Table 4 + section 4.2 analysis (results + failure modes), A.7 (Azure parallelization timing/cost).
- Skim: section 4.1 Navi design, Table 5 Mind2Web, A.1/A.2 observation-action details, D.1 agent prompt (useful as a reference computer-use prompt).
- Can skip: A.4 full 154-task enumeration (reference only), reference list, qualitative figure walkthroughs (B).
- Follow-up papers: OSWorld, AndroidWorld, OmniParser, Set-of-Marks, UFO, SeeAct.

## Triage decision
Label: READ_SOON
Rationale: Directly relevant to computer-use agent harness design - real-OS environment, execution-based rewards, cloud-parallel evaluation, and a clean observation-interface ablation. The parallelization pattern and the UIA/SoM/OmniParser comparisons are reusable; the OSWorld overlap and thin human baseline keep it below MUST_READ. Evidence does not strongly differ from the scaffold's prior label.
Confidence: high
Reading time estimate: 45-60 min for the must-read sections.

## Personal notes
The transferable lesson is harness-shaped, not model-shaped: stateless per-task workers + cloud fan-out is the right way to make a real-OS agent benchmark iterable, and the slowest-task wall-clock framing is the key intuition. Note the speed/accuracy mismatch (OmniParser best but CPU-bound) as an argument for GPU-backed perception workers. The Navi prompt (D.1) is a compact, citable example of a single-action CoT computer-use prompt with DONE/FAIL/WAIT/COMMAND control tokens and a free-text memory channel.

## Follow-up actions
- Add related paper: OSWorld (arXiv 2404.06411), AndroidWorld (arXiv 2405.14573), OmniParser (arXiv 2408.00203).
- Compare with: OSWorld (parallelization + reward design), UFO (Windows GUI agent architecture).
- Re-run after new version: check for v2/leaderboard updates and any expanded task count beyond 154.
- Check code: github.com/microsoft/WindowsAgentArena - license, Navi_open setup, Azure ML job scripts.
- Read benchmark details: A.6 task JSON schema (id/config/evaluator/result) before reusing evaluators.
