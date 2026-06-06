# A data-driven approach for learning to control computers

## Metadata
- Canonical key: arxiv-2202.08137
- Version: v1
- Fetch date: 2026-06-06T07:57:31Z
- Source: arxiv
- PDF: library/a-data-driven-approach-for-learning-to-220208137/v1/paper.pdf
- Venue: International Conference on Machine Learning (ICML 2022)
- Year: 2022
- Authors: P. Humphreys, David Raposo, Tobias Pohlen, Gregory Thornton, Rachita Chhaparia, Alistair Muldal, Josh Abramson, Petko Georgiev, Alex Goldin, Adam Santoro, T. Lillicrap
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
CC-Net shows that a plain combination of behavioural cloning (on a very large human demonstration set) and RL, using only a human-aligned mouse/keyboard interface over pixels+DOM, reaches state-of-the-art and human-level *mean* performance on MiniWob++ — arguing that the missing ingredient in prior work was data scale, not specialized DOM actions or curricula.

## Why this paper matters
This is an early, influential data point for the modern "computer-use agent" line of work: it demonstrates that a generic perception-to-(mouse/keyboard)-action policy can solve a broad web-task suite at human level without DOM-specific action primitives or hand-built curricula. The central thesis — scale human demonstration data and the simple BC+RL recipe suffices — directly informs how later GUI/web agents think about demonstrations vs. specialized affordances. Relevant to the harness interest profile because the action/observation interface is deliberately human-aligned (keyboard+mouse, pixels+DOM), which is the design choice most downstream computer-use systems converge on.

## Problem and gap
Problem: build agents that operate a computer the way a human does — keyboard and mouse, natural-language goals — generalizable in principle to any digital-device task (p1-2).
Gap in prior work: At MiniWob's conception (Shi et al. 2017) the BC+RL combination over keyboard/mouse did *not* produce high-scoring agents; with only ~17 hours of human data, pure BC solved only ~5% more tasks than a random policy (p4). Subsequent work therefore added DOM-specific actions (Liu 2018; Gur 2018; Jia 2019), curricula (Gur 2018), and constrained-exploration / workflow guidance (Liu 2018) to get performance. CC-Net's claim is that this added machinery was unnecessary; the actual missing factor was the *size* of the human trajectory dataset (p2).

## Core idea
Keep the interface human-aligned (mouse/keyboard actions, pixel+DOM observations, NL goals) so that human demonstrations are directly usable, then scale the demonstration set by orders of magnitude and co-train a single multimodal agent on all tasks with an equally-weighted mixture of BC and RL (VMPO). The contribution is empirical/methodological rather than algorithmic novelty — the authors explicitly frame it as resolving a hypothesis from the original MiniWob work that "conventional" deep RL + demonstrations is adequate (p8-9).

## Harness relevance
- Environment or workspace: MiniWob++ suite of 104 web-browser instruction-following tasks (clicking, typing, dragging, form-filling) with programmatic per-task rewards (p2-3). A custom C++ environment stack runs Google Chrome, replacing the original Selenium interface.
- Observation interface: 165x220 RGB pixels (frame buffer via X11) plus a processed DOM tree (list of DOM elements with text, value, class, position, focus, interaction state — example in Fig. 9, p11), plus the NL task instruction and a dictionary of environment-provided "task-field" text strings (p3-4).
- Action interface: human-equivalent keyboard+mouse. 10 action types — no-op; 7 mouse (move, click, double-click, press, release, wheel up, wheel down); 2 keyboard (key press incl. macros like CTRL+C, emit text from a task-field string). Cursor coordinates discretized into 51 bins per axis, height autoregressive on width (p3-4, Table 2 p12). Deliberately *no* DOM-element actions in the baseline (those exist only as an ablation).
- Tool/API/shell/GUI layer: pure GUI control. Environment connects directly to an X11 server for input and frame buffer; uses Chrome DevTools Protocol (CDP) via passed file descriptors to read DOM and run JS (p3).
- Planner/executor/verifier/search structure: none — a single reactive policy (no explicit planner/verifier/search). Memory is provided by a dual-layer LSTM over the multimodal transformer output (p3-4).
- Evaluation harness: mean score across the 104 MiniWob++ tasks; compared against (a) aggregated best-published external SotA per task (with and without augmentations; 16/104 tasks have no external score and are filtered for that comparison) and (b) human participant scores. Scores are not time-discounted (p2-3, p5). Single seed per condition (p5).
- Training harness: co-train all 104 tasks from scratch with equal-weighted BC + RL (VMPO, Song et al. 2019); uniform sampling across demonstrations; built on DeepMind Interactive Agents Team infrastructure (p5, Acks p9). Hyperparameters in Table 1 (Adam, lr 1e-4, batch 256, unroll 64, discount 0.9, max 300 steps/episode) (p11).
- Logging/trace/reproducibility mechanism: Not reported (no code/data/model release stated; demonstration data and infra are internal).
- Safety or permission mechanism: browser runs in a Sandbox2 chroot jail restricting host syscalls; all network traffic rerouted to a local host-side socket via TCP proxy; CDP accessed via file descriptors to minimize attack surface — motivated partly by safe agent-environment interaction and safe crowdsourced (Mechanical Turk) data collection (p3).

## Method
Agent (CC-Net, Fig. 2, p3-4):
- Perception: 165x220 RGB pixels through 4 ResNet blocks (3x3 kernels, strides 2,2,2,2; channels 32,128,256,512) → 14x11 feature map flattened to 154 tokens. Language inputs (instruction, DOM, and — for the policy only — task fields) tokenized against a 370-word vocab plus 1000 hashed OOV slots, embedded to size-64, then aggregated per-string by a 1-layer 4-head "language transformer" via cross-attention with a learnable CLS-like query → 512-dim embedding each.
- Integration/memory: pixel tokens + DOM/instruction language embeddings + 2 extra learned embeddings fed to an 8-layer, 8-head, 512-dim multimodal transformer. Outputs of the extra embeddings concatenated with mean-pooled remaining outputs and a previous-action embedding → 1536-dim vector → dual-layer LSTM (512 units/layer, residual around each layer). Authors note LSTM ablations were not run in the final config; earlier tuning favored dual-layer but did not control for parameter count (p4).
- Policy: 4 outputs (action type, cursor coords, keyboard-key index, task-field index). Most logits are linear; task-field index logits come from dot-product attention over task-field embeddings (and, in the DOM-action ablation, over DOM-element embeddings).

Data and training:
- 2.4M+ demonstrations across the 104 tasks from 77 participants (~6300 hours), crowdsourced at a fixed hourly rate, ethically reviewed (p4-5).
- Split into 2.2M train / 310K test episodes; filter out episodes with final reward < 0.5 (~5%); cleave runs of "no-op" steps up to 10 consecutive (p5). Removing no-action steps gave best results despite exaggerating human/agent timing differences (p2-3).
- Co-train all tasks, equal-weight BC and RL losses (from scratch), VMPO for RL. For smaller-data scaling runs the BC loss weight is scaled by sqrt(relative dataset size) to slow overfitting (p6-7).

## Experimental setup
- Benchmark: MiniWob++ (104 tasks). Per-task human, CC-Net, BC-only, and external scores tabulated in Appendix Table 3 (p14-15).
- Baselines: aggregated external SotA per task from World of Bits (Shi 2017), Workflow-Guided Exploration (Liu 2018), Learning to Navigate the Web (Gur 2018), DOM-Q-Net (Jia 2019), reported both BC&RL-only and with augmentations; plus internal ablations (RL-only, BC-only, no-DOM-obs, no-pixel-obs, no-task-field-action, DOM-action). Human performance as a ceiling.
- Models: single CC-Net architecture; total parameter count Not reported (only per-module dims and hyperparameters in Table 1 are given).
- Metrics: mean task score (not time-discounted); human-action log-probability on train/validation for the data-scaling study (Fig. 7).
- Compute/cost: agents evaluated at 2 billion frames in the scaling study (Fig. 7); tuning by hand "based on a limited number of experiments"; only one seed per reported condition (p5-7). Total compute/training cost Not reported.
- Implementation/artifacts: custom C++ environment stack (Chrome + X11 + CDP + Sandbox2). No code, data, or model release stated.

## Key results
- Mean MiniWob++ performance: CC-Net reaches state-of-the-art and matches human-level *mean* performance across the task suite, exceeding aggregated external SotA "by a wide margin," and does so *without* environment augmentations (p2, p5, Fig. 3). VERIFIED: claim is "human-level mean performance," not per-task parity — Table 3 confirms some tasks where humans are clearly better and some where CC-Net is better.
- Per-task detail (VERIFIED against Table 3, p14-15): CC-Net effectively fails two tasks — simon-says (-0.00 vs human 0.62; agent observes at ~2Hz and misses parts of the sequence) and terminal (-0.01 vs human 0.88) (p5-6). CC-Net beats humans most strikingly on moving-items (0.88 vs 0.18 human, where humans suffered control latency). Other gaps where humans lead: click-scroll-list (0.60 vs 0.91), copy-paste-2 (0.63 vs 0.94), text-transform (0.60 vs 0.86), drag-cube (0.79 vs 0.99), simple-algebra (0.75 vs 0.86), social-media-all (0.75 vs 0.89).
- Data scale: ~400× more data than originally collected (Shi 2017, ~17 hours) is required to reach human-level (p2, p8). Using 1/1000 of the dataset (~6 hours) overfits rapidly and gives no significant gain over RL-only; performance improves continuously across ~3 orders of magnitude up to the full set (Fig. 7, p6-7). VERIFIED dataset size: 2.4M+ demonstrations, 77 participants, ~6300 hours; 2.2M/310K train/test split.
- Ablations (Fig. 8, p7-8): removing DOM observation → ~75% drop in mean performance (agent is strongly DOM-reliant); removing pixels is far less harmful (the MiniWob "canvas" is cleanly represented in the DOM — a benchmark artifact that would not hold for general computer control). Removing the privileged task-field action still solves form-filling (the agent learns to highlight+drag text). DOM-element actions underperform the mouse/keyboard baseline, and adding DOM actions to the baseline gave no boost (data not shown).
- Transfer: co-training all 104 tasks is significantly more data-efficient *per task* than single-task training (Fig. 5, p5-6), cited as evidence of cross-task transfer and against pure memorization.
- BC+RL necessity: BC-only and RL-only ablations are "much worse"; both signals are needed (Fig. 3, p5).

## Evidence quality
Mixed but mostly supportive of the headline claim. Strong points: the data-scaling curve spans three orders of magnitude with train/validation log-prob curves showing the overfitting story (Fig. 7); the input/output ablations are clean and the authors are candid that the DOM-reliance (75% drop) plus the DOM-encoded canvas means pixel-only / general-computer-control performance is unproven. Key caveats the reader must weigh: (1) "human-level" is a *mean* across tasks, not per-task, and is partly inflated by tasks where humans do poorly due to latency (e.g. moving-items 0.18) — the comparison is to these specific crowdworkers, not expert humans. (2) Only ONE seed per reported condition and hand-tuning (p5), so no statistical/variance reporting; the authors themselves flag high per-task variance (Fig. 13). (3) The external-SotA aggregate sets non-reported tasks to zero and filters 16 tasks, which can flatter the "wide margin." (4) Several LSTM/architecture choices were not ablated in the final config. None of these undermine the core "data scale is the missing factor" finding, but they temper the "human-level" framing.

## Reproducibility and artifacts
- Code: Not reported (no release stated).
- Data: 2.4M+ human demonstrations — internal, not released.
- Models: Not released; total parameter count Not reported.
- Environment: custom C++ stack (Chrome + X11 + CDP + Sandbox2) over MiniWob++; not released. Original MiniWob++ is public (Liu et al. 2018).
- License: Not reported.
- Exact commands or setup: Not reported; training hyperparameters in Table 1 (p11), but infra and demonstration data are unavailable.
- Missing details: total params, compute budget, number of seeds (stated as 1), exact data-collection task distribution.

## Strengths
- Clear, well-supported central thesis (data scale > specialized machinery) with a clean scaling study and ablations.
- Human-aligned mouse/keyboard interface that is directly reusable for demonstrations and forward-looking toward general computer use.
- Thoughtful environment engineering (X11/CDP/Sandbox2) with explicit security/sandboxing for safe crowdsourced data collection.
- Honest reporting of failures (simon-says, terminal), of the DOM-reliance / canvas-in-DOM artifact, and of single-seed/hand-tuning limitations.
- Evidence of cross-task transfer from joint training.

## Weaknesses and limitations
- "Human-level" is a mean over tasks and depends on a specific crowdworker population; per-task humans still beat the agent on several tasks, and some "wins" stem from human latency disadvantages.
- Heavy DOM dependence (75% drop without it) plus the canvas-encoded-in-DOM artifact means true pixel-only / non-DOM computer control is not demonstrated — a real gap for "controlling computers in general."
- Single seed, hand-tuned, no variance/statistical reporting; large compute and proprietary infra/data limit reproducibility.
- No algorithmic novelty (authors acknowledge this); contribution is empirical.
- Total parameter count and compute cost not reported.
- MiniWob++ sidesteps the hard "understand human intent/language/preferences" problem (scripted goals, programmatic low-noise rewards), as the authors note (p8).

## Relationship to prior work
- Directly revisits and overturns the negative result from World of Bits / original MiniWob (Shi et al. 2017) that BC+RL over keyboard/mouse underperforms — attributing the earlier failure to insufficient demonstration data.
- Contrasts with DOM-action / curriculum / workflow-guided lines: Workflow-Guided Exploration (Liu 2018), Learning to Navigate the Web (Gur 2018), DOM-Q-Net (Jia 2019) — CC-Net matches/exceeds their aggregate SotA without DOM actions or augmentations.
- Methodologically downstream of large-scale-demonstration + RL work: DeepMind Interactive Agents Team (2021) (shared infra), AlphaStar (Vinyals 2019), AlphaGo (Silver 2016), and scaling-laws intuition (Kaplan 2020).
- Related computer/web/mobile-control agents: WebGPT (Nakano 2021, text browser interface), AndroidEnv (Toyama 2021), AppBuddy (Shvo 2021), Codex (Chen 2021).
What is genuinely new: the demonstration that scale of human keyboard/mouse demonstrations is the decisive factor, plus the human-aligned C++/X11/CDP environment and the multimodal-transformer agent operating without DOM-specific actions. Incremental: the BC+RL+VMPO algorithm and transformer/LSTM architecture per se.

## What I should read
- Must read: Sec. 2.3 Agent Architecture (p3-4) and Sec. 3.4 Input/Output Ablations + Fig. 8 (p7-8) — the core design and the DOM-reliance finding; Sec. 3.3 Scaling + Fig. 7 (p6-7).
- Skim: Sec. 2.1-2.2 (MiniWob++ and environment interface, p2-3) for the harness; Sec. 3.1-3.2 results and transfer (p5-6); Discussion (p8-9).
- Can skip on a first pass: full per-task Table 3 (p14-15) unless you need specific task numbers; appendix key-press/action-distribution figures.
- Follow-up papers: WebGPT (Nakano 2021); later GUI/computer-use agents that adopt pixel+DOM, mouse/keyboard interfaces; WebArena/Mind2Web-style benchmarks for how the field moved beyond MiniWob++.

## Triage decision
Label: READ_SOON
Rationale: Foundational early demonstration of the human-aligned (keyboard/mouse, pixel+DOM) computer-control interface and the "scale demonstrations + BC+RL" recipe that underpins the modern computer-use-agent line. Architecture and ablations are directly relevant to harness/interface design. Kept at READ_SOON: the headline numbers verify against the extraction and the contribution is solid, but evidence has notable caveats (single seed, mean-only human parity, DOM dependence) so it is important context rather than a must-implement.
Confidence: high
Reading time estimate: ~45-60 minutes for the core sections; +20 if reading Table 3 in detail.

## Personal notes
Watch the framing trap: "human-level" = mean across 104 tasks, and some agent wins are due to human latency disadvantage (moving-items). The DOM-reliance ablation (75% drop) is the most important caveat for anyone wanting *pixel-only* computer use — MiniWob++'s canvas being in the DOM makes the benchmark easier than general GUIs. Verified numbers: 2.4M+ demos / 77 participants / ~6300 hours; ~400x the original data; 2.2M/310K split; total params Not reported.

## Follow-up actions
- Add related paper: WebGPT (Nakano et al. 2021); a modern pixel-based computer-use agent for contrast.
- Compare with: DOM-action benchmarks (Liu 2018, Gur 2018, Jia 2019) and later WebArena-style suites.
- Re-run after new version: arXiv v2 (11 Nov 2022) is the extracted version; no further action unless a new revision appears.
- Check code: none released — track if DeepMind open-sources environment/data.
- Read benchmark details: Appendix Table 3 (per-task scores) and Fig. 9 (observation format).
