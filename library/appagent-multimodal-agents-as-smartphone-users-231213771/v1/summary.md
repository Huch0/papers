# AppAgent: Multimodal Agents as Smartphone Users

## Metadata
- Canonical key: arxiv-2312.13771
- Version: v1
- Fetch date: 2026-06-06T07:57:30Z
- Source: arxiv
- PDF: library/appagent-multimodal-agents-as-smartphone-users-231213771/v1/paper.pdf
- Venue: International Conference on Human Factors in Computing Systems (CHI 2025; arXiv preprint 2312.13771v2, Dec 2023)
- Year: 2023
- Authors: C. Zhang, Zhao Yang, Jiaxuan Liu, Yanda Li, Yucheng Han, Xin Chen, Zebiao Huang, Bin Fu, Gang Yu
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
AppAgent is a training-free GPT-4V smartphone GUI agent that operates real Android apps through a simplified tap/swipe/text action space over numbered UI elements, and bootstraps per-app knowledge via an exploration phase (autonomous trial-and-error or watching human demos) that produces a reusable per-element "document" later consulted at deployment time.

## Why this paper matters
This is an early (Dec 2023) and influential reference design for the now-standard "VLM + Set-of-Mark element labeling + simplified action space" recipe for mobile/computer-use agents (p.4, §3.1). For harness work it is relevant as a concrete instance of two ideas the user cares about: (1) an observation/action interface that sidesteps coordinate prediction by labeling interactive elements with integer IDs, and (2) a memory-construction mechanism (the per-app document) that is learned once during exploration and reused at inference without any model fine-tuning. It predates and motivates later mobile-agent benchmarks/harnesses (AndroidWorld, Mobile-Agent, etc.), so it is useful as a baseline/ancestor rather than a state-of-the-art system.

## Problem and gap
- Problem: build an agent that can operate *any* smartphone app like a human, using only on-screen GUI interaction (tap/swipe), without back-end API/function-call access in the style of Siri (p.2, §1).
- Gap in prior work: (a) text-only LLM agents cannot perceive GUIs; (b) adapting/fine-tuning embodied models needs large app-demonstration datasets that are costly to collect, and generalization to unseen apps is uncertain (p.2, §1); (c) GPT-4V can read typical UIs but struggles on new/atypical UIs (p.3, §2.1). The paper's answer is to avoid training entirely and instead learn a lightweight textual document per app.

## Core idea
A two-phase, training-free framework (p.4, Fig.2):
1. **Exploration phase** — the agent interacts with an app (autonomously, or by watching a human demo) and, by comparing before/after screenshots of each action, writes a natural-language "document" describing what each UI element does. Goal-oriented (task-driven) rather than blind DFS/BFS; it backs out of irrelevant pages (e.g. ads) via `Back()` (p.5, §3.2).
2. **Deployment phase** — for a new task, at each step the agent sees the current screenshot + the dynamically retrieved document for the visible elements, then emits Observation -> Thought -> Action, and summarizes the step into memory carried forward in the next prompt (ReAct-style + running summary) (p.5, §3.3).
The key enabler is the interface: GPT-4V never predicts xy coordinates; it references integer element IDs overlaid on the screenshot.

## Harness relevance
- **Environment / workspace**: real Android apps driven through a command-line interface (CLI); experiments on 10 real consumer apps (p.5, §3.1, §4.1). CLAIMED to generalize across apps; this is a deployment-on-live-apps setup, not a sandboxed/reset-able benchmark environment.
- **Observation interface**: per-step (a) a real-time screenshot and (b) an XML file of interactive elements. Each interactive element gets a unique integer ID (from the XML resource-id, or synthesized from class name + size + content) overlaid as semi-transparent numbers on the screenshot (p.4, §3.1). This is a Set-of-Mark-style labeling scheme — EVIDENCE supports the SoM-like (element bbox -> numbered label) description in the task brief.
- **Action interface**: simplified action space mirroring human gestures over *numbered* elements — `Tap(element:int)`, `Long_press(element:int)`, `Swipe(element:int, direction, dist)`, `Text(text:str)`, plus system-level `Back()` and `Exit()` (p.4–5, §3.1). Text input bypasses the virtual keyboard by writing directly into the focused field. UNCLEAR: exact CLI/automation backend (adb? UIAutomator?) is not named in the text; "Not reported" beyond "command-line interface."
- **Tool/API/GUI layer**: pure GUI layer; explicitly *no* back-end/API access (p.2, §1). This is the paper's central design claim.
- **Planner/executor/verifier**: single LLM (GPT-4V) plays observer+planner+executor in one ReAct-style loop; the "document" acts as learned per-app memory. No separate verifier module; task completion is self-declared via `Exit()` (p.5, §3.3). The exploration-then-deployment "learn a doc per app" mechanism is the load-bearing contribution.
- **Evaluation harness**: a hand-built benchmark of 10 apps / 50 tasks; quantitative table evaluated on 45 tasks / 9 apps (Lightroom excluded as ambiguous). Metrics: Success Rate (SR), a custom Reward model scoring proximity-to-goal of UI pages, and Average Steps (p.6–7, §4.2). SR failure = not finished within 10 steps. Reward model details are thin ("Unclear" how it was validated).
- **Training harness**: none — fully training-free / no parameter updates (p.2, §1; p.7).
- **Logging/trace/reproducibility**: per-step Observation/Thought/Action traces are shown qualitatively (Fig.3); the running per-step summary forms agent memory. No structured logging format or task-replay harness described — "Not reported."
- **Safety/permissions**: argues GUI-only operation improves security/privacy by avoiding deep system integration (p.2, §1); no explicit permission gating, confirmation, or guardrail mechanism — "Not reported."

## Method
Training-free in-context framework (p.4, §3). Environment = Android via CLI; per step the agent ingests screenshot + XML element list with overlaid integer IDs (p.4, §3.1). Action space = 4 core functions (tap / long_press / swipe / text) + back/exit (p.4–5). Exploration produces a per-app document by acting on elements and diffing before/after screenshots, updating an element's entry on repeated visits; demo-watching variant records only the elements/actions a human used, shrinking the search space (p.5, §3.2). Deployment consults the document + screenshot each step in an Observe->Think->Act->Summarize loop with carried-forward memory, terminating on self-judged completion (p.5, §3.3).

## Experimental setup
- **Benchmark**: 10 apps — Google Maps, Twitter, Telegram, YouTube, Spotify, Yelp, Gmail, TEMU, Clock, Lightroom — chosen for diversity (p.5, §4.1). 50 tasks total (p.2; Fig.1). Main quantitative table (Table 1) reports the **average over 45 tasks on 9 apps**, excluding Lightroom due to ambiguous task-completion assessment (p.6, §4.2 Results). VERIFIED: # apps = 10, # tasks = 50, main table = 45 tasks / 9 apps.
- **Step caps**: exploration capped at 40 steps; testing/deployment capped at 10 steps (p.6, §4.1). VERIFIED.
- **Model**: GPT-4 / GPT-4V (interleaved image+text) (p.6, §4.1). No open-source MLLM tested.
- **Baselines / configurations** (Table 1, p.7): GPT-4 with None document + Raw action API; GPT-4 with None document + Ours action space; AppAgent with Auto. Exploration doc; with Watching-Demos doc; with Manually-Crafted doc (oracle). So the ablation isolates (a) raw vs. simplified action space and (b) document source (exploration vs. docs).
- **Metrics**: SR-up, Reward-up (custom reward model scoring UI-page proximity to goal), Avg. Steps; plus a Lightroom user study (Avg. Rank-down, Num. Tools used) over 5 prepared images (p.7–8, §4.3).
- **Compute/cost**: "Not reported" (no token/$ cost, no latency).
- **Artifacts**: open-sourced framework; project page https://appagent-official.github.io/ (p.1, p.3 contributions). License "Not reported" in the text.

## Key results
Table 1 (p.7), SR / Reward / Avg.Steps — VERIFIED against extraction:
- GPT-4, None doc, **Raw** action space: SR **2.2%**, Reward 0.6, Avg. Steps 4.0.
- GPT-4, None doc, **Ours** action space: SR **48.9%**, Reward 3.5, Avg. Steps 6.9.
- AppAgent, **Auto. Exploration** doc: SR **73.3%**, Reward 5.1, Avg. Steps 4.4.
- AppAgent, **Watching Demos** doc: SR **84.4%**, Reward 4.7, Avg. Steps 5.1.
- AppAgent, **Manually Crafted** doc (oracle): SR **95.6%**, Reward 5.5, Avg. Steps 5.5.

Takeaways the numbers support:
- The simplified action space alone lifts SR from 2.2% -> 48.9% — i.e., coordinate-free element-ID actions are the single biggest driver (GPT-4 "struggles with producing accurate xy coordinates," p.6).
- Adding a learned document lifts SR further (48.9% -> 73.3% auto, -> 84.4% demos), approaching the 95.6% manual-doc oracle. So **exploration-derived docs > no docs, and watching-demos > autonomous exploration**, both below the manual oracle. EVIDENCE supports the "auto docs comparable to manual" claim only loosely — demos (84.4%) and especially auto (73.3%) are still well short of 95.6%.
- Lightroom user study (Table 2, p.7): Avg. Rank Manually-Crafted 1.75 < Watching-Demos 1.95 < GPT-4 baseline 2.30 (lower better); doc-equipped agents used more editing tools (5.8 demos / 4.0 manual vs 2.4 baseline) (p.8, §4.3).

## Evidence quality
- **Strong signal, weak rigor.** The action-space ablation is the most convincing result and is internally consistent. But the benchmark is small (45 tasks / 9 apps for the headline number), single-seed, with **no variance/CI/significance reporting** and a single model (GPT-4V) — so absolute SR figures should be read as indicative, not robust.
- The **Reward metric relies on a custom reward model** whose construction and validation are essentially "Unclear" (p.6) — it scores per-UI-page proximity to goal, but no inter-rater or correctness check is given. SR (binary, 10-step cutoff) is the more trustworthy number.
- **Lightroom is excluded** from Table 1 for ambiguity yet is the showcase for vision capability via a separate small user study (5 images), so the visual-editing claims rest on a tiny, subjective sample.
- **Self-declared completion** (`Exit()`) plus author-defined success raises mild evaluator-reliability concerns; no independent/automated verifier.
- **Contamination/aging**: tasks run on live consumer apps (Maps, Gmail, YouTube...) whose UIs change over time, so results are not reproducible against a frozen environment — a structural limitation of the harness rather than a flaw in the claims.

## Reproducibility and artifacts
- Code: open-sourced framework, project page https://appagent-official.github.io/ (p.1, p.3). Repo contents not described in text.
- Data: 50-task / 10-app benchmark described in prose; no released task suite/specification detailed in the paper — "Not reported" as a downloadable artifact.
- Models: GPT-4 / GPT-4V (closed, API).
- Environment: Android via CLI; exact automation backend (adb/UIAutomator) "Not reported."
- License: "Not reported" in text.
- Exact commands or setup: "Not reported."
- Missing details: prompt templates, reward-model spec, per-app/per-task breakdowns, seeds, cost/latency.

## Strengths
- Clean, influential interface design: integer-ID element labeling removes coordinate prediction, demonstrably the dominant performance lever (2.2% -> 48.9%).
- Training-free: per-app knowledge captured as an editable natural-language document; no fine-tuning, easy to update when UIs change.
- Two complementary knowledge-acquisition modes (autonomous exploration vs. watching demos) with an oracle (manual doc) upper bound — a clean ablation axis.
- Real apps, broad app diversity (social, email, maps, shopping, image editing).

## Weaknesses and limitations
- Author-stated: simplified action space excludes multi-touch and irregular gestures (p.8, Limitation).
- Small, single-seed benchmark; no statistical reporting; single proprietary model.
- Custom, under-specified Reward model; subjective Lightroom user study on 5 images.
- Live-app environment is non-reproducible and ages quickly.
- Self-judged task completion; no independent verifier or safety/permission layer.
- Document quality depends on exploration coverage; failure modes of stale/incorrect docs not analyzed.

## Relationship to prior work
- Closest contemporaries: GPT-4V-based zero-shot smartphone GUI navigation (Yan et al., 2023, "GPT-4V in Wonderland", p.3/refs) and web-navigation agents (WebAgent/Gur et al.; Furuta et al.). AppAgent's novelty vs. these is the **persistent per-app document learned by exploration/demos** and the explicit integer-ID action space, rather than purely zero-shot per-episode prompting.
- Builds directly on ReAct (Yao et al., 2023) for the Observe/Think/Act loop and on Set-of-Mark-style visual prompting.
- Versus fine-tuned embodied/GUI models (RT-1/RT-2, Gato), the contribution is *training-free* generalization. Genuinely new: the doc-as-memory mechanism; incremental: the ReAct loop and SoM-style labeling are adopted from prior work.

## What I should read
- Must read: §3.1 Environment & Action Space (p.4) and §3.2–3.3 exploration/deployment (p.5) — the interface and the doc mechanism. Table 1 (p.7) for the action-space vs. document ablation.
- Skim: §4.3 Lightroom case study (p.7–8); Fig.3 qualitative traces (p.6).
- Can skip: §2 Related Work (standard 2023 LLM-agent survey), reference list.
- Follow-up papers: Mobile-Agent, AndroidWorld/AndroidControl, CogAgent, SeeAct, and any benchmark that turns this into a reproducible harness.

## Triage decision
Label: READ_SOON
Rationale: Foundational, frequently-cited reference design for the VLM + element-labeling + simplified-action-space mobile-agent recipe, directly relevant to harness/observation-action-interface interests; method section is short and high-value. Evidence is indicative rather than rigorous, but the interface ideas are the takeaway, not the leaderboard. Keeping READ_SOON — nothing in the extraction contradicts the existing label.
Confidence: high
Reading time estimate: 25–35 min (focus on §3 and Table 1; rest skimmable).

## Personal notes
Free-form notes for later.

## Follow-up actions
- Add related paper: Mobile-Agent; AndroidWorld; CogAgent; Set-of-Mark prompting.
- Compare with: later reproducible mobile-agent harnesses (frozen-env benchmarks) to contrast non-reproducible live-app eval.
- Re-run after new version: CHI 2025 camera-ready may differ from arXiv v2 — check for expanded eval.
- Check code: project page repo for action backend (adb/UIAutomator) and prompt/doc format.
- Read benchmark details: per-app/per-task breakdown and reward-model spec (not in paper text).
