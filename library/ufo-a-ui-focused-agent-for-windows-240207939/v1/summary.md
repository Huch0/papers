# UFO: A UI-Focused Agent for Windows OS Interaction

## Metadata
- Canonical key: arxiv-2402.07939
- Version: v1
- Fetch date: 2026-06-06T07:57:28Z
- Source: arxiv
- PDF: library/ufo-a-ui-focused-agent-for-windows-240207939/v1/paper.pdf
- Venue: North American Chapter of the Association for Computational Linguistics
- Year: 2024
- Authors: Chaoyun Zhang, Liqun Li, Shilin He, Xu Zhang, Bo Qiao, Si Qin, Ming-Jie Ma, Yu Kang, Qingwei Lin, S. Rajmohan, Dongmei Zhang, Qi Zhang
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
UFO is a GPT-Vision-driven dual-agent (HostAgent for application selection, AppAgent for in-app control operations) framework that automates natural-language user requests on Windows by reading desktop/app screenshots plus the Windows UI Automation control tree and grounding actions through a pywinauto-based control interaction module, reaching an 86% success rate on a 50-request, 9-application benchmark.

## Why this paper matters
CLAIMED: the authors position UFO as "the first UI agent specifically tailored for task completion within the Windows OS environment" (Abstract, p.1; Conclusion, p.14). This is the load-bearing novelty claim - most prior GUI agents at the time targeted smartphones or web (Intro, p.2). WHY-read for me: it is an early, concrete blueprint for a desktop-OS computer-use agent harness. The interesting harness-design choices are (a) a two-tier agent split (cross-app orchestration vs. in-app execution), (b) observation built from screenshots *plus* the accessibility/UI-Automation control tree rather than pure pixels, and (c) action grounding via a real Windows automation library (pywinauto), all of which recur in later computer-use systems. It is foundational reading for understanding how the Windows-native branch of GUI agents was framed.

## Problem and gap
CLAIMED (Intro, p.2): VLMs can interact with software UIs to fulfill natural-language requests, evolving LLMs into "Large Action Models" (LAMs) whose decisions cause real actions. The gap: existing agents predominantly target smartphones (Yan et al.; AppAgent; MobileAgent) or web (Zheng et al.), leaving Windows OS - described as high-market-share, with versatile applications and tasks that require long-horizon, cross-application planning - "largely unexplored." So the problem is building a general agent that (1) interprets NL requests, (2) perceives Windows GUIs, (3) grounds actions without human intervention, and (4) spans multiple applications.

## Core idea
ANALYSIS: The central design is a separation of concerns across two GPT-Vision agents plus a deterministic grounding layer.
- HostAgent (Sec 3.2, p.5-6): sees the full desktop screenshot + a list of active applications and chooses which app to use; produces a coarse global plan; emits a CONTINUE/FINISH status; re-invoked to switch apps when a request spans multiple apps.
- AppAgent (Sec 3.3, p.6-7): operates inside the chosen app. At each step it receives three screenshots (previous-with-highlighted-control, clean, and Set-of-Mark-annotated) plus a filtered control list, then selects one control and one function to execute; produces a fine-grained local plan and a richer status set (CONTINUE / FINISH / PENDING / SCREENSHOT / APP_SELECTION).
- Control Interaction module (Sec 3.4, p.7-8): uses pywinauto over the Windows UI Automation backend to enumerate actionable controls, annotate them with Set-of-Mark, and execute the chosen function (Click, SetText, GetText, Scroll, plus custom Annotate and Summary).
Cross-application memory is the mechanism that makes multi-app tasks work: extracted text/image descriptions are written to memory and later read by AppAgent (e.g., compose an email from a Word doc + a Photos image), per Sec 3.3 (p.7). ANALYSIS: the design is essentially prompt/orchestration engineering on top of GPT-Vision - there is no model training; novelty is in the harness, the Windows-specific grounding, and the cross-app switching loop.

## Harness relevance
- Environment / workspace: Windows OS desktop with native applications (Outlook, Photos, PowerPoint, Word, Adobe Acrobat, File Explorer, Visual Studio Code, WeChat, Edge), live GUIs, not a simulator (Sec 4.1, p.11).
- Observation interface: screenshots - desktop screenshot for HostAgent; for AppAgent a triple of previous/clean/Set-of-Mark-annotated app screenshots - combined with the Windows UI Automation control tree surfaced via pywinauto (control name/type/title, location, bounding box) (Sec 3.2-3.4, p.5-8). Hybrid pixel + accessibility-tree observation.
- Action interface: control-level operations grounded by pywinauto/UI Automation - Click (left/right, single/double), SetText (keyboard text entry), GetText, Scroll, plus custom Annotate and Summary; effectively keyboard/mouse emulation on a selected control (Sec 3.4, p.7-8). EVIDENCE: function signatures appear in case studies, e.g. set_edit_text(...), click_input(button='left', double=False), wheel_mouse_input(wheel_dist=-20) (Figs 6-7, p.15-16).
- Tool/API/GUI layer: pywinauto (Bim & Min-shuai, 2014) on the Windows UI Automation API backend; Set-of-Mark prompting (Yang et al., 2023a) for control annotation (Sec 3.4, p.7-8).
- Planner/executor/verifier/search structure: HostAgent = high-level app-selection planner; AppAgent = per-step executor with continuous plan reflection (Sec 3.5.4, p.10). No explicit external verifier or tree-search; "verification" is the agent's own observation that the prior action took effect (Sec 3.3, p.7). The two-phase loop (Phase 1 = first app, Phase 2 = after APP_SELECTION switch) is the only search-like structure.
- Control interactor: the Control Interaction module is the grounding component translating GPT-Vision decisions into executed Windows operations (Sec 3.1 and 3.4).
- Evaluation harness: WindowsBench - 50 NL requests over 9 apps, 5 per app + 5 cross-application; three runs per request with the highest-completion-rate run selected (Sec 4.1, p.11; Tables 5-7, p.20-22).
- Training harness: None - UFO uses GPT-Vision off the shelf with prompting/examples; no fine-tuning is reported.
- Logging / trace / reproducibility: Memory module stores prior thoughts, comments, actions, execution results (Sec 3.2-3.3). Open-source code at github.com/microsoft/UFO; case-study videos linked (p.13-14). UNCLEAR: no structured trace-logging format or deterministic-replay mechanism is described in the paper.
- Safety / permission: Safeguard mechanism requests user confirmation before sensitive actions (send email, delete/modify files, close app, webcam/mic access, install/uninstall, browser-history/password retrieval); list is non-exhaustive and the agent assesses sensitivity itself (Sec 3.5.5 + Table 2, p.11). Also an Interactive Mode for user-supplied steps like password entry (Sec 3.5.1, p.9).

## Method
ANALYSIS of the pipeline (Sec 3, p.4-11):
1. User submits an NL request. HostAgent observes desktop + app list, selects an app, and writes a global plan (CoT-style Observation/Thoughts/Selected Application/Status/Global Plan/Comment outputs).
2. Selected app is focused. AppAgent loops: capture clean + Set-of-Mark-annotated screenshots, enumerate filtered controls, choose one control + one function, execute via Control Interaction, update local plan, repeat until FINISH or APP_SELECTION.
3. On APP_SELECTION, control returns to HostAgent to switch apps (Phase 2, etc.), passing information through shared Memory. Loop continues until all sub-requests are done; Interactive Mode allows follow-ups.
Special designs (Sec 3.5): Interactive Mode; Action Customization (register custom operations into the prompt); Control Filtering (hard filter = 10 relevant control types {Button, Edit, TabItem, Document, ListItem, MenuItem, TreeItem, ComboBox, Hyperlink, ScrollBar}; soft filter = dynamic re-annotation of a smaller control set via SCREENSHOT status); Plan Reflection (re-plan every step); Safeguard.

## Experimental setup
- Benchmark: WindowsBench, 50 requests across 9 apps (Outlook, Photos, PowerPoint, Word, Adobe Acrobat, File Explorer, VS Code, WeChat, Edge), 5 single-app per app + 5 cross-application; each app has at least one follow-up request to exercise Interactive Mode (Sec 4.1, p.11; Tables 5-7).
- Baselines: GPT-3.5 and GPT-4, each run as "Human Surrogate" - the model emits step-by-step instructions and a human executes them, pausing when visual ability is needed (Sec 4.1, p.11). ANALYSIS: these are weak, indirect baselines; no other Windows agent existed to compare against (authors state this explicitly).
- Models: GPT-Vision (GPT-4V) powers UFO (Abstract; Intro). Exact API version / temperature: Not reported.
- Metrics (Sec 4.1, p.12): Success (binary task completion), Step (number of actions, efficiency), Completion Rate (ratio of correct steps to total steps), Safeguard Rate (how often UFO requests confirmation when the request is sensitive).
- Protocol: 3 tests per request, best-by-completion-rate selected - applied to baselines too. ANALYSIS: "best of 3" inflates reported numbers vs. single-shot and there is no variance/std reporting.
- Compute / cost: Not reported (no token counts, latency, or dollar cost).
- Artifacts: open-source code (github.com/microsoft/UFO); demo videos.

## Key results
VERIFIED against Table 3 (p.12):
- UFO: Success 86%, avg Step 5.48, Completion Rate 89.6%, Safeguard Rate 85.7%.
- GPT-4 (Human Surrogate): Success 42%, Step 8.44, Completion 47.8%, Safeguard 57.1%.
- GPT-3.5 (Human Surrogate): Success 24%, Step 7.86, Completion 31.6%, Safeguard 50%.
CLAIMED (p.12): UFO surpasses the best baseline (GPT-4) "by more than double" on success - VERIFIED (86% vs 42%).
Per-application breakdown, UFO (Table 4, p.12) - VERIFIED selected rows: Outlook 100% success; Word 100%; File Explorer 100%; WeChat 100%; Photos / PowerPoint / VS Code / Edge 80% each; Adobe Acrobat lowest at 60% success / 78.7% completion (attributed to control types unsupported by Windows UI Automation, p.13).
Cross-Application (Table 4, p.12-13) - VERIFIED: Success 80%, avg Step 9.8 (highest step count, as expected for multi-app), Completion 83%, Safeguard 100%. CLAIMED: UFO "maintains a high level of performance" across apps (p.13) - EVIDENCE supports this for the 80% cross-app success.
Qualitative: two main case studies (PowerPoint "Remove All Presentation Notes" shortcut, Sec 4.3.1; cross-app email composition from Word + Photos + Outlook, Sec 4.3.2) plus six appendix cases (D.1-D.6, p.24-29) including PDF reading, VS Code dark-mode, Twitter post, news-to-WeChat.

## Evidence quality
ANALYSIS:
- The headline 86% comes from a 50-task benchmark authored by the same team, with "best of 3 runs" selection and no statistical/variance reporting - so the absolute number should be read as an upper-ish estimate on a self-designed benchmark, not a robustly measured success rate.
- Baselines are not true competitors: GPT-3.5/GPT-4 "human surrogate" cannot see screenshots or act, so the comparison mostly demonstrates that perception+grounding matter, which is somewhat tautological. There is no comparison to contemporaneous GUI agents (e.g., a Windows port of AppAgent/CogAgent), partly justified by the "first Windows agent" claim but still a gap.
- No ablations: the contribution of each component (Set-of-Mark annotation, control filtering, plan reflection, three-screenshot input, memory) is asserted but not isolated experimentally. UNCLEAR which design elements actually drive the 86%.
- Completion Rate is a self-defined "correct steps / total steps" metric whose correctness judgment is presumably manual and not described as blind; potential for optimistic grading.
- Small N (5 requests/app) makes per-app percentages coarse (each task = 20 points). The Adobe Acrobat failure analysis is plausible and honest.
Overall: a strong systems/feasibility demonstration, but the quantitative evidence is suggestive rather than rigorous.

## Reproducibility and artifacts
- Code: Yes - github.com/microsoft/UFO (open-source) (Abstract, p.1).
- Data: WindowsBench requests are fully listed (Tables 5-7, p.20-22), but the underlying user files (documents, images, slides, mailboxes) are personal/environment-specific and not a packaged dataset. Reproduction requires recreating the app states.
- Models: GPT-Vision / GPT-4V; exact version and decoding params Not reported.
- Environment: Windows OS + the 9 named applications; pywinauto + Windows UI Automation backend.
- License: Not reported in the paper (check the repo).
- Exact commands or setup: Not reported in the paper.
- Missing details: GPT-V version/settings, prompt texts (referenced as "Examples" but not included), cost/latency, grading rubric for Completion Rate, environment setup for each task.

## Strengths
- First articulated, working Windows-native GUI agent with a clean dual-agent decomposition (HostAgent app-selection vs. AppAgent in-app action).
- Hybrid observation (screenshots + UI Automation control tree) gives precise, addressable controls instead of relying solely on pixel grounding - a pragmatic and influential choice.
- Real action grounding via pywinauto enables full automation without a human in the loop.
- Cross-application support via shared memory is genuinely demonstrated (email-from-multiple-apps case).
- Thoughtful auxiliary mechanisms: Set-of-Mark annotation, dual-level control filtering, plan reflection, and an explicit Safeguard for sensitive actions.
- Transparent failure analysis (Adobe Acrobat) and full benchmark request disclosure.

## Weaknesses and limitations
- Author-stated (Sec 5, p.14): capabilities are bounded by what pywinauto / Windows UI Automation expose; non-standard apps/controls (e.g., much of Adobe Acrobat) are unsupported. Proposed fixes: Win32 API backend or dedicated GUI vision models (CogAgent-style).
- Author-stated: poor handling of unfamiliar/niche app UIs; proposes external knowledge from web search.
- Inferred: no training/learning - performance is entirely tied to GPT-Vision's zero/few-shot ability; no adaptation from failures beyond in-context memory.
- Inferred: weak evaluation rigor - small self-made benchmark, weak surrogate baselines, no ablations, no variance, "best of 3" selection, no cost reporting.
- Inferred: safety relies on a non-exhaustive list plus the model's own judgment; no guarantee against missed sensitive actions (the appendix tables show some safeguard failures on certain WeChat/PowerPoint requests).

## Relationship to prior work
Closest: AppAgent (Yang et al., 2023b) and MobileAgent (Wang et al., 2024) - smartphone VLM agents; Yan et al. (2023) GPT-4V mobile navigation; CogAgent (Hong et al., 2023b) - a trained GUI VLM; Zheng et al. (2024) - GPT-4V web agent. Multi-agent lineage: AutoGen, MetaGPT, AutoAgents; reflection from Reflexion (Shinn et al.) and TaskWeaver (Qiao et al.). Grounding technique borrowed: Set-of-Mark (Yang et al., 2023a). ANALYSIS: genuinely new = the Windows-OS target, the UI-Automation-based control grounding, and the HostAgent/AppAgent cross-app switching loop. Incremental = the underlying recipe (VLM + screenshot + Set-of-Mark + CoT + memory + reflection) is assembled from existing components rather than introducing a new model or learning algorithm.

## What I should read
- Must read: Sec 3.1-3.4 (p.4-8) - dual-agent architecture, agent I/O, and the Control Interaction grounding layer; this is the reusable harness design. Sec 4.1-4.2 + Tables 3-4 (p.11-13) - benchmark and headline numbers.
- Skim: Sec 3.5 (special designs - filtering, reflection, safeguard) for ideas worth borrowing; Sec 5 limitations.
- Can skip: Appendix D case-study narratives (D.1-D.6, p.24-29) unless you want qualitative behavior examples; the per-baseline app breakdowns (Tables 8-9).
- Follow-up papers: CogAgent; AppAgent (mobile); later Windows/desktop agent work and the UFO repo's evolution (UFO2 / multi-app benchmarks).

## Triage decision
Label: READ_SOON
Rationale: Foundational, well-cited blueprint for Windows-native computer-use agents directly relevant to harness design (hybrid screenshot + accessibility-tree observation, dual-agent orchestration, pywinauto grounding, safeguard). The evidence is feasibility-grade rather than rigorous, so it is a design reference more than a benchmark to chase. Worth a focused read of Sec 3.
Confidence: high
Reading time estimate: ~35-45 min for the core (Sec 3 + Sec 4 tables); ~75 min full.

## Personal notes
Numbers to remember: 50 tasks / 9 apps / 5 cross-app; UFO 86% success, 89.6% completion, 5.48 steps, 85.7% safeguard; GPT-4 surrogate 42%, GPT-3.5 24%; cross-app 80% success at 9.8 steps. Key reusable ideas: control tree from Windows UI Automation as structured observation; Set-of-Mark over enumerated controls; soft control filtering (SCREENSHOT status to re-annotate a smaller set); shared memory as the cross-app data bus. Main caveat: no ablations, weak baselines, best-of-3.

## Follow-up actions
- Add related paper: CogAgent (2312.08914), AppAgent (2312.13771).
- Compare with: later desktop/OS agents and any OSWorld-style benchmarks; mobile AppAgent.
- Re-run after new version: check for UFO2 / updated arXiv versions and expanded benchmarks.
- Check code: github.com/microsoft/UFO (license, prompt files, current architecture).
- Read benchmark details: WindowsBench request tables (Tables 5-7, p.20-22) and grading definition of Completion Rate.
