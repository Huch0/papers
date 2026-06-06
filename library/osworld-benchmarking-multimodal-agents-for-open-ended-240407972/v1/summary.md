# OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments

## Metadata
- Canonical key: arxiv-2404.07972
- Version: v1
- Fetch date: 2026-06-06T07:14:04Z
- Source: arxiv
- PDF: library/osworld-benchmarking-multimodal-agents-for-open-ended-240407972/v1/paper.pdf
- Venue: arXiv (preprint, "Under review", v2 dated 30 May 2024)
- Year: 2024
- Authors: Tianbao Xie, Danyang Zhang, Jixuan Chen, Xiaochuan Li, Siheng Zhao, Ruisheng Cao, Toh Jing Hua, Zhoujun Cheng, Dongchan Shin, Fangyu Lei, Yitao Liu, Yiheng Xu, Shuyan Zhou, Silvio Savarese, Caiming Xiong, Victor Zhong, Tao Yu
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
OSWorld is a real-OS (Ubuntu/Windows/macOS) virtual-machine environment plus a 369-task benchmark with per-task initial-state setup and execution-based checker scripts, which exposes that state-of-the-art LLM/VLM agents top out near 12% success where humans reach ~72%.

## Why this paper matters
This is an expansion-era milestone for computer-use agents: it moves evaluation from app- or domain-specific simulators (web-only, coding-only, mobile-only) to a full real desktop OS with raw mouse/keyboard control and multi-application workflows (p.2-3). For harness research it is a reference design for execution-based, per-example evaluation in an open-ended GUI setting, and its large human-vs-model gap (§4.2) sets a concrete capability target. Many later computer-use agent papers and product evaluations adopt OSWorld as a standard benchmark, so understanding its construction and its measurement caveats is directly relevant to anyone building or evaluating desktop agents.

## Problem and gap
CLAIMED problem (p.1-2, §1): prior agent benchmarks either (a) provide static demonstration datasets without an executable environment (Mind2Web, AITW, OmniAct) — forcing non-execution evaluation that assumes a single gold solution and penalizes valid alternatives — or (b) provide executable environments restricted to a single application/domain (web: MiniWoB++, WebShop, WebArena, VisualWebArena; coding: InterCode), so they cannot evaluate open-ended tasks that span multiple apps and interfaces (GUI + CLI) on a real OS.

The gap they target: no benchmark offers a real, controllable, multi-app desktop environment with reliable per-task execution-based evaluation and support for intermediate initial states. Table 4 (p.9) operationalizes this with columns (Control. Exec. Env., Environment Scalability, Multimodal, Cross-App, Intermediate Init. State, # Exec.-based Eval. Func.); OSWorld is the only row marked positive on all of them, with 134 eval functions vs <=125 for others.

## Core idea
Run agents inside real OS virtual machines and evaluate by executing checker scripts against the final machine state rather than matching action sequences. Each task is a tuple of (natural-language instruction, a setup config that downloads files / opens apps / arranges windows to create a realistic *intermediate* starting state, and a custom execution-based evaluation script that retrieves final artifacts from the VM/cloud and computes a reward in [0,1]). The agent observes screenshots and/or an accessibility (a11y) tree and emits `pyautogui` Python code for raw mouse/keyboard control, plus special actions WAIT/FAIL/DONE. Formalized as a POMDP (S,O,A,T,R) with an execution-based reward (§2.1, p.3).

## Harness relevance
- Environment / workspace: real OS desktops in virtual machines — Ubuntu 22.04 is the main public set; Windows is a 43-task analytic set requiring user activation due to copyright; macOS is supported by the environment but excluded from the benchmark for legal reasons (§3.1 p.6; App. B.1 p.26). VMs give isolation against irreversible host damage and snapshot-based reset (§2.2 p.3). Multiple VMs can run in parallel on one host; headless operation supported (Fig. 2 p.4; App. A.1 p.23). VMs run their own kernel (broader OS/CPU compatibility than Docker, App. A.1).
- Observation interface: full-desktop screenshot (default 1920x1080, includes cursor), XML-format accessibility tree (via pyatspi/ATSPI on Ubuntu, pywinauto on Windows), terminal output, and an unused video recorder (§2.3 p.5; App. A.2 p.23). For model input the a11y tree is filtered to a compact tab-separated table keeping tag/name/text/position/size (§4.1 p.10). Set-of-Marks: numbered bounding boxes derived from the filtered a11y tree overlaid on the screenshot (§4.1 p.11).
- Action interface: raw mouse + keyboard via `pyautogui` Python code (moveTo, click, write, hotkey, scroll, dragTo, keyDown/Up, etc.; Table 2 p.6; App. A.3 p.23-25), plus WAIT/FAIL/DONE. Actions can use Python control flow (for-loops). A finite `computer_13` variant (13 action types) is provided for RL research (App. A.3.2, Table 8 p.26). Authors argue raw control is a superset of web-only action spaces (e.g., right-click, ctrl-click) (§2.4 p.6).
- Tool/API/shell/GUI layer: agents drive real GUI apps and the terminal (CLI). Eight focal apps: Chrome, VLC, Thunderbird, VS Code, LibreOffice Calc/Writer/Impress, GIMP, plus basic OS apps (§3.1 p.6).
- Planner/executor/verifier/search structure: baselines are simple prompted single-agent loops (most recent 3 observation/action turns in chat format, temperature 1.0, top-p 0.9, max 15 steps; §4.1 p.10). No built-in planner/search/reflection module — the paper explicitly flags exploration/memory/reflection as future work (§7 p.17-18).
- Evaluation harness: example-specific execution-based checkers. Pipeline = pre-setup config -> agent interaction -> post-processing (activate window, save files) -> getter functions retrieve artifacts (files, cookies, a11y subtree, cloud reference) -> evaluator function returns reward (Fig. 2 p.4; §2.2.3, Table 1 p.5; §3.2 p.7). 134 unique evaluation functions; dynamic getters (e.g., crawlers) handle real-time-valued tasks. Per-app evaluation uses openpyxl/python-docx/python-pptx, Playwright (Chrome, via socat/Ncat port forwarding), VLC HTTP interface, a custom VS Code extension, GIMP config files, and Firefox Decrypt for Thunderbird (App. B.6 p.29-30).
- Training harness: none used for the reported results (all baselines are zero/few-shot prompted). The environment is *designed* to support interactive learning and the `computer_13` discrete action space for RL, but no training experiments are reported.
- Logging / trace / reproducibility: VM snapshots store full machine state and allow reset; tasks ship as config files specifying the snapshot plus setup/eval. A hybrid setup (snapshot + scripted file prep) is used instead of per-example snapshots to avoid multi-GB storage per example (§2.2.2 p.4). 302 distinct initial states recorded (Table 3 p.8). Resolution is configurable to avoid pixel memorization (App. A.2.1).
- Safety / permission: VM isolation is the primary safety mechanism (§2.2, §7 p.17). Authors note no harmful behavior was observed (attributed to weak agent capability), explicitly flag misuse risks (CAPTCHA bypass, account abuse, vulnerability exploitation), and state there is NO reliable safety metric — checkers assess only task correctness, not side effects (§7 p.17). This is an acknowledged open limitation, not a solved feature.

## Method
Benchmark construction (§3, p.6-8): 9 CS-student authors over ~3 months / ~1800 man-hours collected tasks from forums, tutorials, how-to sites, video courses, and brainstormed multi-app workflows; cross-checked by two other authors for feasibility/ambiguity/source-alignment. Each task gets (1) a setup config (3 stages: start VM/restore snapshot, prepare files, run reprocessing commands; ~1 man-hour each, App. B.5 p.29) and (2) an execution-based evaluator (~2 man-hours each), with getters extracting key components and evaluators scoring them. 84 tasks are integrated from NL2Bash, Mind2Web, SheetCopilot, PPTC, and GAIA to demonstrate unification; 30 infeasible tasks (deprecated/hallucinated features) test refusal. Quality control: each example is attempted by two non-annotating authors acting as agents; >400 man-hours over four rounds of fixes during human/baseline runs.

Distribution (Table 3 / Fig. 3, p.8; Table 10 p.28): 369 Ubuntu tasks = 268 single-app (72.6%) + 101 multi-app workflow (27.4%); 84 integrated (22.8%); 30 infeasible (8.1%); 302 initial states; 134 eval scripts; plus 43 Windows analytic tasks. Per-app counts (Table 10): OS 24, Calc 47, Impress 47, Writer 23, VLC 23, Thunderbird 17, Chrome 15, VS Code 46, GIMP 23, Workflow 101.

## Experimental setup
- Benchmark: OSWorld 369-task Ubuntu set (the main reported numbers); 43-task Windows set used only for the cross-OS correlation analysis (§5.3).
- Baselines / models: closed-source GPT-4 / GPT-4V / GPT-4o, GPT-3.5, Gemini-Pro / Gemini-Pro-Vision / Gemini-Pro-1.5, Claude-3-Opus, Qwen-Max; open-source Mixtral-8x7B, Llama-3-70B, CogAgent (§4.1 p.9, Table 5 p.10).
- Input settings (4): a11y tree (text-only), screenshot (vision-only), screenshot + a11y tree, Set-of-Marks (§4.1 p.10-11).
- Agent config: chat-mode history of last 3 (obs, action) turns, temp 1.0 / top-p 0.9, max 15 steps. Default screen 1920x1080.
- Metric: execution-based success rate (reward 1 / partial decimal / 0), grouped by OS / Office / Daily / Professional / Workflow.
- Human study: CS-major students unfamiliar with the samples/software; 100 WebArena examples sampled under the same protocol for comparison (§3.4 p.8-9).
- Compute / cost: Not reported (no GPU hours, no API cost, no per-run wall-clock for models).

## Key results
- CLAIMED headline gap, EVIDENCE supports (Table 5 p.10, §4.2): best model overall success = 12.24% (GPT-4 with a11y tree); human overall = 72.36%. (Abstract states ">72.36%" and "best model 12.24%".) Screenshot-only best VLMs ~5.26%-5.80%. Baselines span ~0.99% (CogAgent SoM) to 12.24%.
- Workflow (multi-app) tasks are much harder: best ~6.57% (GPT-4V SoM), generally <5%, while humans stay ~73% (Table 5; §4.2; §5.1 Table 6 lists multi-app 6.57% vs single-app 13.74%).
- Human consistency vs model variance (EVIDENCE, Table 5): human success is flat ~70-75% across categories (variance <5%); model success swings >20% across categories and settings, doing relatively better on CLI/OS-type tasks and worst on GUI-heavy Office (LibreOffice Calc subsets often 0%, §5.1 p.13).
- Auxiliary-input effects are model-dependent (EVIDENCE, partly mixed, §4.2): a11y tree helps GPT-4V and Claude-3 but the conclusion reverses for Gemini-Pro; Set-of-Marks *reduces* GPT-4V performance vs screenshot+a11y (attributed to high resolution / many elements / coordinate-level tasks), contradicting SoM's usual benefit.
- Human study (EVIDENCE, §3.4 Fig. 4 p.8-9): OSWorld median human time 111.94s vs WebArena 35.38s; human accuracy 72.36% vs 88% on WebArena — i.e., OSWorld tasks are slower and harder for humans too.
- Difficulty/feasibility (GPT-4V SoM, Table 6 p.12): Easy 16.78%, Medium 13.12%, Hard 4.59% (humans 84.91/81.08/49.57%); Infeasible 16.67% vs Feasible 13.34% (note: high "infeasible" score is partly false positives from agents prematurely emitting FAIL, §5.1).
- Observation ablations (§5.2, 10% subset): higher screenshot resolution generally helps screenshot-only; for SoM, downsampling to 0.4 (768x432) *improved* then 0.2 hurt. Longer *text* (a11y) history improves SoM; longer *image* history does not help screenshot-only — VLMs are weak at image-based history. a11y tree is long (90th percentile ~6344 tokens, Fig. 6).
- Cross-OS (§5.3, Table 7 p.14): GPT-4V screenshot-only success Ubuntu 4.88% vs Windows 2.55%, correlation 0.7 across the migrated subset.
- Error analysis (§5.4 p.15): among ~550 failed examples sampled across settings, >75% involve mouse-click inaccuracy ("strong planning, weak execution"), plus repetitive clicks, environmental-noise dilemmas, and missing software domain knowledge. Claude-3-Opus trails GPT-4V by 2.84%-7.76% despite stronger common-benchmark scores, due to grounding hallucinations.

## Evidence quality
- Strong support for the core claim (large human-model gap, multi-app hardness, model variance): execution-based per-example checkers, a same-protocol human study, and category breakdowns make the headline numbers credible.
- UNCLEAR / weak points:
  - No statistical reporting: success rates are single-run point estimates; with 369 tasks, differences of a few percent (e.g., 11.21% vs 12.17% vs 12.24%) are within plausible noise but no variance/CI/seeds are reported. Temperature 1.0 implies run-to-run variance that is not quantified.
  - False positives/negatives explicitly acknowledged (§3.3 p.7-8): authors say further red-teaming "could further reduce false positives and negatives," and the infeasible-task score is inflated by spurious FAIL outputs — so absolute numbers have an unmeasured error bar.
  - Several ablations (resolution, history, window perturbation) run on only ~10% / 28-task subsets (§5.2), limiting generality.
  - Benchmark leakage: 84 tasks are integrated from existing public datasets; checkers are custom, but instructions overlap prior corpora. Low headline scores make leakage a minor concern here.
  - Human baseline uses different annotators ("CS students unfamiliar with software") than the 9 author-annotators; reasonable but not a controlled expert-vs-novice comparison.
  - Compute/cost untracked, so efficiency claims (a11y token burden, longer context) are qualitative.
- Minor caveats to verify against the PDF: Table 10 per-app counts and the §5.4 "~550 failed examples / >75% mouse error" sample are aggregated across settings, not a single run.

## Reproducibility and artifacts
- Code: CLAIMED public at https://os-world.github.io (abstract, §1; environment, baselines, eval scripts, docs released).
- Data: 369 Ubuntu tasks with configs + 134 eval scripts + 302 initial states released; 43 Windows tasks require user activation (copyright).
- Models: baselines are external API/open-weight models; the paper provides baseline agent *implementations*, not new model weights.
- Environment: VM-image based (Ubuntu 22.04 with pinned app versions, e.g., LibreOffice 7.3.7.2, Thunderbird 115.6.0); requires a VM platform (vmrun) + Flask control receiver. macOS excluded (legal); Windows partial.
- License: Not reported in the extraction (software-selection criteria mention open-source licensing of included apps; benchmark license not stated in text).
- Exact commands / setup: described conceptually (config-file schema in Fig. 2; setup three-stage pipeline App. B.5); no literal run commands in the paper.
- Missing details: per-model API versions/dates, seeds, compute/cost, exact prompt token budgets beyond App. C.1 reference, and VM image distribution/licensing.

## Strengths
- First real-OS, multi-app, execution-based agent benchmark with intermediate initial states (Table 4 differentiator).
- Reliable evaluation design: 134 example-specific checkers using real app internals (file parsing, Playwright, HTTP interfaces, custom extensions) instead of fragile trajectory matching.
- Universal raw mouse/keyboard action space (superset of web-only spaces); supports both GUI and CLI and multi-app workflows.
- Rigorous, costly annotation and multi-round quality control; honest human study and detailed error/qualitative analysis.
- Practical reproducibility scaffolding (VM snapshots, parallel/headless execution, configurable resolution) and an RL-friendly `computer_13` action space.

## Weaknesses and limitations
- Author-stated: residual false positives/negatives in checkers; no safety/side-effect metric; a11y-tree quality varies by app and is token-heavy; macOS not benchmarked; Windows set gated by copyright.
- Inferred: single-run results without statistical reporting; many analyses on small subsets; baselines are simple prompting loops (no planner/memory/reflection), so the benchmark measures current models more than ceiling agent architectures; absolute success numbers (especially infeasible-task scores) have an unquantified error bar; compute/cost untracked.
- Snapshot of a fast-moving model landscape (GPT-4V/Gemini-Pro/Claude-3 era) — the specific leaderboard is already dated even if the environment endures.

## Relationship to prior work
- Closest executable benchmarks: WebArena / VisualWebArena (web-only, few eval scripts), MiniWoB++ / WebShop (web), InterCode (code), AgentBench (multi-isolated), WorkArena (web knowledge work), AssistGUI (desktop, non-interactive). OSWorld generalizes these to a real full-desktop, cross-app, interactive setting (Table 4 p.9).
- Closest static datasets: Mind2Web, AITW, OmniAct, WebLINX, PixelHelp, MetaGUI, GAIA — no executable environment / no execution-based eval.
- Genuinely new: real-OS VM environment + universal pyautogui action space + per-example execution-based checkers + intermediate initial states + cross-app workflows, unified in one harness. Incremental parts: reuse of Set-of-Marks (Yang et al.), VisualWebArena-style prompting, and 84 tasks adapted from existing benchmarks.

## What I should read
- Must read: §2 (environment: task def, infrastructure, observation/action spaces, p.3-6); §2.2.3 + Table 1 (execution-based evaluation, p.4-5); §4.2 + Table 5 (results, p.10-12); §3.4 (human study, p.8-9).
- Skim: §5 analysis (resolution/history/perturbation/cross-OS, p.12-14); §5.4 qualitative error taxonomy (p.15); App. A.3 / Table 8 (action spaces); App. B.6 (per-app evaluation mechanics, p.29-30) if building checkers.
- Can skip: References; App. B.3 task-source URL tables (p.27-28); t-SNE instruction-distribution figures.
- Follow-up papers: WebArena (2307.13854), VisualWebArena (2401.13649), Mind2Web (2306.06070), CogAgent (2312.08914), SeeClick (2401.10935), GAIA (2311.12983), and later OSWorld-based agent systems.

## Triage decision
Label: READ_SOON
Rationale: Foundational, widely-adopted benchmark that defines the real-desktop computer-use evaluation paradigm and the execution-based checker design pattern directly relevant to harness work; the human-vs-model gap is a key capability reference point. Not MUST_READ only because the methods are benchmark/infra-centric (no novel agent algorithm) and the leaderboard numbers are dated.
Confidence: high
Reading time estimate: ~60-75 min for the core sections; ~2 hr including appendices on evaluation mechanics.

## Personal notes
The single most load-bearing result: human ~72.36% vs best model 12.24% overall success (Table 5, §4.2). The "strong planning, weak execution" finding (>75% of failures are mouse-click/grounding errors, §5.4) is the most actionable insight for harness/agent design — it argues for better GUI grounding and/or index-based (SoM-like) action mapping, though SoM did not help GPT-4V here at desktop resolution/element density.

## Follow-up actions
- Add related paper: WebArena, VisualWebArena, GAIA, CogAgent, SeeClick.
- Compare with: WebArena (web-only execution-based) and AssistGUI (desktop, non-interactive) on eval-harness design.
- Re-run after new version: check whether a later OSWorld version updates the leaderboard / fixes checker false positives.
- Check code: https://os-world.github.io — VM image setup, config schema, getter/evaluator function library.
- Read benchmark details: App. B.6 (per-app getters/evaluators) before reusing checkers.
