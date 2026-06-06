# Agent S: An Open Agentic Framework that Uses Computers Like a Human

## Metadata
- Canonical key: arxiv-2410.08164
- Version: v1
- Fetch date: 2026-06-06T07:57:35Z
- Source: arxiv
- PDF: library/agent-s-an-open-agentic-framework-that-241008164/v1/paper.pdf
- Venue: International Conference on Learning Representations (ICLR 2025)
- Year: 2024 (arXiv v1, 10 Oct 2024)
- Authors: Saaket Agashe, Jiuzhou Han, Shuyu Gan, Jiachen Yang, Ang Li, Xin Eric Wang (Simular Research)
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

---

# PASS 1 — Triage (bird's-eye, ~5 min)

## One-sentence takeaway
Agent S is an MLLM-based desktop GUI agent that couples a hierarchical Manager/Worker planner with retrieval over self-built narrative (full-task) and episodic (subtask) memory plus live web search, and a language-level Agent-Computer Interface (ACI), nearly doubling OSWorld success over the OSWorld agent baseline (11.21% -> 20.58% with GPT-4o) and generalizing to Windows (13.3% -> 18.2%).

## The Five Cs
- **Category:** New method/system — an agentic framework (cognitive architecture) for full-desktop GUI control, plus an empirical study with ablations and error analysis. Not a benchmark or training paper.
- **Context:** Builds on MLLM agents (memory, structured planning, tool use, reflection — Reflexion, ReAct, Voyager, Generative Agents), GUI/OS agents (OSWorld, WindowsAgentArena, Synapse, OS-Copilot, Cradle), RAG-for-agents (RAP, AutoGuide, RADA), and explicitly extends the SWE-agent "Agent-Computer Interface" concept (Yang et al., 2024) from code to GUIs (p.2-3, sec.2). Uses GPT-4o and Claude-3.5-Sonnet as frozen backbones; no fine-tuning.
- **Correctness:** Core assumptions look sound on a first read: that grounding (not just reasoning) is the GUI bottleneck, that the accessibility tree gives reliable element coordinates, and that single-action-per-step interaction yields better feedback. Two caveats: (a) the abstract/intro miscite OSWorld and the OSWorld benchmark as "(OpenAI, 2023)" — OSWorld is Xie et al., 2024 (p.2, sec.1; p.7, sec.4.1); (b) all headline and ablation numbers appear to be single-run with no variance/seeds reported, a real concern given the small absolute success rates (~20%).
- **Contributions (claimed, p.3):** (1) the Agent S framework integrating experience-augmented hierarchical planning, self-supervised continual memory update, and an ACI; (2) the experience-augmented hierarchical planning method drawing on web knowledge + internal memory to decompose tasks; (3) extension of the ACI concept to GUI agents (bounded action space + image-augmented accessibility tree); (4) extensive OSWorld experiments with per-component ablations and Windows generalization.
- **Clarity:** Well written and structured; method (sec.3) is precise with formal notation (App. C), and ablations isolate each component. Weakly evidenced on statistical rigor (no variance, single runs) and on cost/step-count (explicitly deferred to future work, p.10).

## Why this matters to me now
Directly central to computer-use / GUI-agent harness design: one of the foundational OSWorld-era agents and the first to port the "ACI" abstraction from SWE-agent into the desktop GUI setting. The Manager/Worker/Self-Evaluator decomposition and the narrative-vs-episodic memory split are reusable harness patterns, and the error taxonomy (planning/grounding/execution) is a useful lens for any computer-use evaluation.

---

# PASS 2 — Content (what it actually does; section-grounded)

## Motivation — the problem (NOT the novelty)
Automating real desktop tasks via direct mouse/keyboard GUI control poses three concrete failure pressures (p.2, sec.1): (1) **domain knowledge** — applications and websites constantly change, so an agent needs specialized, up-to-date knowledge it cannot hold statically in weights; (2) **long task horizons** — desktop tasks are multi-step with interdependent, order-sensitive actions, requiring explicit subgoals and progress tracking; (3) **dynamic, non-uniform interfaces** — agents must parse large visual+textual state, pick relevant elements out of a vast action space, and respond to visual feedback. Underlying these, GUIs are built for humans (real-time perception) or scripts (APIs), but MLLM agents are a third user type: they act in slow discrete steps, lack an internal coordinate system, and cannot process per-pixel feedback (p.6, sec.3.3). Prior GUI agents are reported to be bottlenecked by **grounding** specifically (p.6, sec.3.3, citing Xie et al. 2024; Zheng et al. 2024a). This section is the problem statement only.

## Novelty — the genuine delta  (the core)
- **Delta in one sentence:** A GUI agent improves most not from a smarter single policy but from *layering retrieval of self-evaluated, abstraction-stratified experience* (high-level full-task "narrative" memory for planning, low-level grounded "episodic" memory for execution) onto a *bounded language-level action interface that grounds via an image-augmented accessibility tree rather than via raw coordinates*. Strip "we propose" and the insight survives: experience should be stratified by abstraction level and matched to the planning vs. execution stage, and grounding should be delegated to the accessibility tree (tagged IDs) instead of asked of the MLLM as pixel coordinates.
- **Mechanistic reason the design must take this form:**
  - *Why two memories, not one:* the Manager plans and needs transferable strategy with concrete actions stripped out (narrative memory stores abstracted full-task experience, keyed by an observation-aware query Q); the Worker executes and needs concrete grounded action sequences (episodic memory stores plans-with-grounding for subtasks marked DONE, keyed by <Q, s_i, C_si>) (p.4-5, sec.3.1.1-3.1.2; App. C). A single memory would either pollute planning with brittle low-level coordinates or starve execution of step-level detail.
  - *Why web search in addition to memory:* memory is internal/stale; the live "How to do X" Perplexica query supplies up-to-date app-specific knowledge to handle changing software — addressing motivation challenge (1) directly (p.4, sec.3.1.1). The ablation that web knowledge is the single most impactful component (below) is the mechanistic evidence.
  - *Why summarize via a Self-Evaluator rather than store raw trajectories:* storing full trajectories as exemplars bloats context and includes failure noise; the Self-Evaluator turns episodes into a textual "reward" summary with no ground truth/human feedback, which the ablation shows outperforms full-trajectory storage (p.5, sec.3.1.3; Fig.7).
  - *Why an image-augmented accessibility tree instead of Set-of-Marks on the image:* MLLMs lack an internal coordinate system, so the agent refers to elements by integer ID and the ACI translates <primitive, ID> into Python; rather than augmenting the image with tree marks (prior work), Agent S augments the *tree* with OCR text blocks (IOU-matched) so missing interactable elements become referenceable (p.6-7, sec.3.3). This targets the stated grounding bottleneck.
  - *Why one bounded action per step:* unbounded code/script actions chain multiple steps, removing per-step feedback and risking safety; one discrete primitive at "the right temporal resolution" lets the slow, stateless MLLM observe immediate feedback (p.7, sec.3.3).
- **Closest prior work and precise difference:**
  - *SWE-agent / ACI (Yang et al., 2024):* introduced ACI for code agents; Agent S extends the abstraction to GUIs with a GUI-specific dual-input (image + tagged accessibility tree) and a GUI primitive set (p.3, sec.2; p.6, sec.3.3).
  - *RAG-for-agents (RAP, AutoGuide, RADA; Kagaya 2024, Fu 2024a, Kim 2024):* those retrieve task exemplars / state-aware guidelines / single-level experience. Agent S's stated difference (p.3, sec.2): hierarchical use of *both* full-task and subtask experience; the full-task experience is summarized into an abstractive textual reward; experience is self-evaluated/annotated before storage.
  - *Synapse (Zheng 2024b), OS-Copilot (Wu 2024), Cradle (Tan 2024):* contemporaneous GUI/OS cognitive architectures; Agent S's claimed unique modules are experience-augmented hierarchical planning + GUI-ACI + continual self-supervised memory update.
- **Motivation-vs-novelty check:** Mostly passes. The contribution does not end at "prior agents fail on long-horizon GUI tasks"; it states *how* experience must be stratified and *why* grounding is delegated to the tree. Weakest spot: framing (4) "extensive experiments... SOTA" as a contribution — that is evidence, not novelty. And contribution (1) ("a framework that integrates X, Y, Z") risks reading as "we add modules"; the genuine insight is the abstraction-stratified, stage-matched retrieval, not the integration per se.
- **30-second test:** Stratify agent memory by abstraction level and bind each level to the planning vs. execution stage, self-evaluate experience into summaries before storing it, and ground GUI actions through tagged accessibility-tree IDs (image-augmented) instead of MLLM-emitted coordinates.

## Core idea / method
A closed-loop hierarchical architecture (Fig.3, p.4):
1. **Manager (G)** receives task T_u and initial observation O_0 (annotated accessibility tree + screenshot), forms an observation-aware "How to do X" query Q = LLM(T_u, O_0), runs (a) online web search via Perplexica and (b) similarity retrieval from **Narrative Memory M_n** (abstractive full-task experiences, success and failure, actions stripped). Experience Context Fusion combines them into K_fused = LLM(M_n(Q), K_web), which the Subtask Planner turns into a topologically sorted subtask queue <s_0...s_n> with per-subtask context C_si (p.4-5, sec.3.1.1; App. C.1).
2. **Workers (w_0...w_n)** execute subtasks sequentially. Each retrieves subtask experience E_si = Retrieve(M_e, <T_u, s_i, C_si>) from **Episodic Memory M_e** (complete plans with grounded actions, only from DONE subtasks), and a per-worker **Trajectory Reflector** gives in-episode reflective advice to avoid repetition. The Action Generator emits a structured CoT (prior-action status, observation analysis, semantic next action, grounded next action) yielding one grounded action a_j; DONE ends a subtask, FAIL triggers Manager replanning from the current state (p.5, sec.3.1.2; App. C.2).
3. **Self-Evaluator (S)** turns completed subtask episodes into episodic summaries (textual rewards) and completed full tasks into narrative summaries, all without human feedback or ground truth — described as a hierarchical-RL-like loop where retrieval is the learning mechanism (p.5, sec.3.1.3; App. C.3).
4. **Memory construction (p.5-6, sec.3.2):** bootstrapped by self-supervised exploration on synthetic tasks (50 most-common app tasks = environment-independent; tasks generated from OSWorld/WindowsAgentArena initial environments = environment-aware), run with only web knowledge to collect initial narrative/episodic experience; then **continual memory update** keeps writing experience during inference.
5. **ACI (p.6-7, sec.3.3; App. A.1):** dual input (screenshot for salient-change perception; integer-tagged, OCR-augmented accessibility tree for grounding); bounded action space of ~11 primitives (click, type, scroll, hotkey, hold_and_press, drag_and_drop, save_to_buffer, switch_applications, wait, done, fail — Table 5, p.15), one action per step, translated to Python.

## Harness relevance
- **Environment/workspace:** Real executable desktop environments — OSWorld (Ubuntu, 369 tasks; OS, LibreOffice Calc/Impress/Writer, Chrome, VLC, Thunderbird, VS Code, GIMP, multi-app Workflow) and WindowsAgentArena (Windows, 154 tasks) (p.7, sec.4.1).
- **Observation interface:** Dual — RGB screenshot + accessibility tree tagged with integer IDs and augmented with OCR text blocks (PaddleOCR, IOU-matched) (p.6-7, sec.3.3).
- **Action interface:** Bounded discrete language primitives referencing elements by ID; exactly one primitive per timestep; ACI compiles <primitive, ID> to executable Python (Table 5, p.15; p.7, sec.3.3).
- **Tool/API/GUI layer:** ACI is the GUI abstraction layer; external tool = Perplexica web search; embeddings = text-embedding-3-small for retrieval; OCR = PaddleOCR (p.7, sec.4.1).
- **Planner/executor/verifier/search:** Manager = planner; Workers = executors with Trajectory Reflector; Self-Evaluator = verifier-as-summarizer (no ground-truth verification — it self-labels success/failure). FAIL -> Manager replans (bounded re-planning loop, not tree search) (p.4-5, sec.3.1).
- **Evaluation harness:** Reuses OSWorld and WindowsAgentArena execution-based success-rate evaluators (the benchmarks' own checkers), not the agent's Self-Evaluator (p.7-9, sec.4).
- **Training harness:** None in the gradient sense — backbones are frozen GPT-4o / Claude-3.5-Sonnet. "Learning" is purely retrieval over a continually-updated memory built by self-supervised exploration (p.5-6, sec.3.2).
- **Logging/trace/reproducibility:** Trajectories/episodes are summarized and stored in memory; qualitative trajectories shown (Figs.5,8-16). No released trajectory logs or seeds described in the paper; code is released (github.com/simular-ai/Agent-S).
- **Safety/permissions:** Implicit only — the bounded one-action-per-step space is argued to improve safety/precision vs. arbitrary executable code (p.7, sec.3.3). No sandboxing/permission model beyond the benchmark VMs.

## Experimental setup
- **Benchmarks:** OSWorld (369 tasks, full set; an ablation subset testsub of 65 stratified instances) and WindowsAgentArena (154 tasks) (p.7-9, sec.4).
- **Backbones:** GPT-4o and Claude-3.5-Sonnet for OSWorld; GPT-4o for WindowsAgentArena and for all ablations.
- **Baselines:** OSWorld agent with accessibility tree + screenshot (coordinate-based action) reported by Xie et al. 2024 (GPT-4o, GPT-4V, Claude-3, Gemini-Pro-1.5); WindowsAgentArena NAVI (GPT-4o, a11y tree + OCR + Set-of-Marks, chainable actions) (p.7, sec.4.1).
- **Metric:** Task success rate (%); plus error-type rates and subtask failure rate (sec.4.4).
- **Compute/cost:** Not reported (number of steps and wall-clock explicitly flagged as unaddressed, p.10). GPT-4o chosen for ablations "considering the inference cost" (p.8).
- **Artifacts:** Code released; Perplexica, PaddleOCR, text-embedding-3-small are the external dependencies.

## Key results — read the figures, not just the prose
- **OSWorld overall (Table 1, p.8):** Agent S w/ GPT-4o = **20.58%** vs GPT-4o baseline **11.21%** -> **+9.37 pts, 83.6% relative** (matches the abstract). Agent S w/ Claude-3.5 = 20.48%. Per category (Agent S GPT-4o vs best baseline): OS 45.83 vs 41.67; Office 13.00 vs 6.99 (GPT-4V); Daily 27.06 vs 24.50 (GPT-4V); Professional 36.73 vs 18.37 (GPT-4V); Workflow 10.53 vs 7.46. The gains over the *GPT-4o* baseline are large in Office/Daily/Professional/Workflow, but GPT-4V is a surprisingly strong baseline on Daily (24.50) and is sometimes the per-category "best baseline" — so "nearly doubling" holds only against the GPT-4o row.
- **Per-app detail (Table 8, p.16):** big jumps in VS Code (30.43->52.17), Thunderbird (6.67->40.00), GIMP (0.00->23.08), OS (1.67->45.84); but LibreOffice Calc *regresses* (4.26->2.13). The OS-category headline (45.84) is dominated by this one app's leap; Calc and Workflow remain very weak.
- **WindowsAgentArena (Table 4, p.10):** Agent S **18.2%** vs NAVI **13.3%**, no adaptation. Driven by Windows System (29.2->45.8) and Coding (9.1->29.2); Agent S is *worse* than NAVI on Web Browser (20.0->13.3) and Media&Video (25.3->19.1), and 0.0% on Office/Notepad/Lib Calc/Win Calc/Paint/Writer (Table 9, p.16). "Generalization" is real but uneven.
- **Experience ablation (Table 2, p.9; testsub n=65):** Agent S 26.15% -> w/o Web Knowledge 16.80% (largest drop, web is most impactful) -> w/o Episodic 18.46% -> w/o Narrative 21.41% -> w/o All 13.85% vs baseline 10.77%. On OS, "w/o Web Knowledge" drops *below* baseline (16.60 vs 33.33), suggesting web knowledge can mislead in some categories.
- **ACI ablation (Fig.6 / Table 6, p.8-9,15):** Baseline 10.77 -> +Retrieval 12.31 -> ACI-only 12.31 -> ACI+Retrieval 20.00 -> full Agent S (adds hierarchical planning) 26.15. Supported: retrieval helps far more once ACI is present (synergy), and hierarchical planning adds 20.00->26.15.
- **Memory mechanism ablation (Fig.7 / Table 7, p.9,15):** full 26.15 -> w/o Continual Update 23.08 -> w/o Self-Evaluator 18.46 -> w/o Self-supervised Exploration 15.38. Self-supervised exploration is the most load-bearing memory component; summaries beat full trajectories.
- **Error analysis (Table 3, p.10; Fig.13, p.21):** Execution errors 79.59%, grounding 53.06%, planning 34.69% (overlapping). Of 39 execution errors, 54% self-induced, 31% grounding-induced, 15% planning-induced; 46% trace to planning/grounding. Grounding remains the practical bottleneck the ACI only partially fixes.
- **Critical flags:** No variance, seeds, or significance reported anywhere — all numbers appear single-run; absolute success ~20% means a few tasks swing categories. testsub (n=65) is the authors' own resampling (the official "small" set of 39 is called too imbalanced, footnote p.8). Headline relative-improvement framing is computed against the GPT-4o baseline only. Abstract/intro miscite OSWorld as "(OpenAI, 2023)".

---

# PASS 3 — Critique (challenge every assumption)

## Does the evidence actually support the claims?
- *Claim: experience-augmented hierarchical planning helps.* **Supported** by Table 2 and the ACI/hierarchy decomposition (Fig.6), which separate web/narrative/episodic contributions and show hierarchy adds 20.00->26.15 — these verify the novelty, not merely the motivation.
- *Claim: ACI elicits better reasoning / enables learning.* **Supported in direction** by Fig.6 (retrieval helps much more with ACI present), though "elicits reasoning" is inferred from end-task success, not a reasoning-quality measurement.
- *Claim: summaries beat raw trajectories; self-supervised exploration matters.* **Supported** by Fig.7/Table 7. Genuine novelty-verifying ablations.
- *Claim: new SOTA / nearly doubling.* **Supported against the stated baselines** (Table 1, Table 4) but with the caveats above (single run, GPT-4o-baseline framing, GPT-4V sometimes stronger per category).
- *Claim: broad generalization across OS.* **Partially supported** — overall Windows gain is real (13.3->18.2) but several app categories regress or are 0% (Table 9), so "broad" is generous.
- *What merely confirms the motivation:* the error analysis (Table 3, Fig.13) re-shows that grounding/planning are hard — it characterizes the problem more than it validates the solution.
- *Gaps:* no variance/significance; no cost/step-count (admitted, p.10); no comparison to contemporaneous GUI agents (Synapse, OS-Copilot, Cradle) on the same tasks despite naming them as closest work; ablations only on GPT-4o and only on the 65-task subset.

## Hidden assumptions & failure modes
- Assumes a **reliable, well-populated accessibility tree** with coordinates for "almost every element" (p.6). Breaks on canvas-heavy / custom-rendered apps — consistent with GIMP and Calc weaknesses and the GIMP grounding-loop failure (Fig.16). Web/Chrome a11y trees are noisier, matching the Windows web-browser regression.
- Assumes **self-evaluation labels are trustworthy** with no ground truth; mislabeled successes would poison memory. Not measured.
- Assumes **web search returns relevant, correct guidance**; the OS-category drop when web is the *only* signal (16.60 vs 33.33 baseline, Table 2) hints web knowledge can mislead.
- **Single-action-per-step** + slow MLLM means long latency; the unmeasured step/time cost could make many "successes" impractical.
- Cascading failure mode documented: grounding error -> repeated actions -> execution error (Figs.14,16). Trajectory Reflector does not reliably break these loops.
- If reviewing it, I would press on: variance/seeds, contemporaneous-agent baselines, leakage between self-supervised exploration tasks (generated from benchmark initial environments) and the test tasks, and the cost dimension.

## Could I reconstruct it? (reproducibility)
- **Code:** Released (github.com/simular-ai/Agent-S) — strongest reproducibility lever.
- **Data:** Benchmarks public (OSWorld, WindowsAgentArena). Exploration/synthetic tasks generated by an unspecified task generator; exact prompts/task lists Not reported in the paper body.
- **Models:** GPT-4o, Claude-3.5-Sonnet (frozen, proprietary; exact versions/dates Not reported), text-embedding-3-small, PaddleOCR, Perplexica.
- **Environment:** OSWorld/WindowsAgentArena VMs.
- **License:** Not reported in extraction.
- **Exact commands/setup:** Not in the paper; presumably in the repo.
- **Missing details blocking paper-only reconstruction:** prompt templates, task-generator details, retrieval thresholds/top-k, max-step limits, seeds. With the repo, reconstruction is plausible; from the paper alone, not fully.

## Strengths
- Clean, well-motivated decomposition (Manager/Worker/Self-Evaluator) with a principled memory split (narrative vs episodic) tied to planning vs execution stages.
- Thorough, component-isolating ablations (experience, ACI, memory mechanism) that actually probe the novelty.
- Strong, established results vs reported baselines on two real-environment benchmarks; code released; zero-fine-tuning recipe.
- Honest, detailed error taxonomy and failure-case figures (rare and useful).

## Weaknesses and limitations
- No variance/seeds/significance; single-run numbers at low absolute success rates.
- Cost/latency/step-count unmeasured (authors flag this, p.10) — a major omission for practical computer-use.
- No head-to-head with the contemporaneous GUI agents it names as closest.
- Generalization claim is uneven (multiple Windows categories at 0% or regressed; Calc regresses on Linux).
- Heavy dependence on accessibility-tree quality limits applicability to non-a11y or canvas apps.
- Abstract/intro miscitation of OSWorld undermines polish (minor but notable).

## Relationship to prior work
Genuinely new relative to prior RAG-for-agents (RAP/AutoGuide/RADA): two-level experience (full-task + subtask), abstractive textual-reward summarization, and self-evaluated annotation before storage. Genuinely new relative to SWE-agent's ACI: the GUI-specific dual-input (image + OCR-augmented tagged a11y tree) and GUI primitive action set. Incremental relative to the broader "cognitive architecture" line (Reflexion/ReAct/Voyager/Generative Agents and contemporaneous OS agents): it recombines memory + reflection + hierarchical planning + bounded interface rather than introducing a fundamentally new learning mechanism — "learning" here is retrieval, not gradient updates.

---

# Decision

## What I should read
- Must read: sec.3 (Agent S architecture, esp. sec.3.1 hierarchical planning and sec.3.3 ACI), Table 1, Tables 2/6/7 + Figs.6/7 (ablations), sec.4.4 + Table 3 + Fig.13 (error analysis).
- Skim: sec.2 related work; App. C (formalization); App. D qualitative/failure figures.
- Can skip: reference list; repetitive qualitative success figures (8-12) once the pattern is clear.
- Follow-up papers / references to chase: SWE-agent ACI (Yang et al., 2024); OSWorld (Xie et al., 2024) and WindowsAgentArena (Bonatti et al., 2024) for harness/eval details; Synapse, OS-Copilot, Cradle for the contemporaneous comparison the paper omits; Agent S2 / later versions for the cost and grounding follow-ups.

## Triage decision
Label: READ_SOON
Rationale (Five Cs + novelty + evidence): A foundational OSWorld-era computer-use agent with a genuinely reusable insight (abstraction-stratified, stage-matched experience retrieval + a GUI ACI grounded on tagged accessibility trees), strong relative results on two real-environment benchmarks, and unusually good ablations and error analysis. Evidence quality is the main reservation (single-run, no variance, no cost), and generalization is uneven — enough to keep it from MUST_READ but clearly worth a deep read for harness design. Evidence does not strongly differ from the prior READ_SOON judgment.
Confidence: high
Reading time estimate: 60-90 min for a deep pass (method + ablations + error analysis).

## Personal notes
The narrative/episodic split and "self-evaluator turns episodes into textual rewards, retrieval is the learning step" are the transferable ideas. Watch the unmeasured step/latency cost and the accessibility-tree dependence when reusing this pattern.

## Follow-up actions
- Add related paper: Agent S2 (successor) if not in library; Cradle, OS-Copilot, Synapse.
- Compare with: OSWorld and WindowsAgentArena harness papers; SWE-agent (ACI origin).
- Re-run after new version: check ICLR 2025 camera-ready for added variance/cost numbers.
- Check code: github.com/simular-ai/Agent-S (prompts, top-k, max-step limits, task generator).
- Read benchmark details: OSWorld task construction and evaluator reliability; WindowsAgentArena setup.
