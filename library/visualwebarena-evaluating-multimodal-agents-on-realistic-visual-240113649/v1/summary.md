# VisualWebArena: Evaluating Multimodal Agents on Realistic Visually Grounded Web Tasks

## Metadata
- Canonical key: arxiv-2401.13649
- Version: v1
- Fetch date: 2026-06-06T07:57:32Z
- Source: arxiv
- PDF: library/visualwebarena-evaluating-multimodal-agents-on-realistic-visual-240113649/v1/paper.pdf
- Venue: ACL 2024 (arXiv preprint arXiv:2401.13649v2, dated 6 Jun 2024)
- Year: 2024
- Authors: Jing Yu Koh, Robert Lo, Lawrence Jang, Vikram Duvvur, Ming Chong Lim, Po-Yu Huang, Graham Neubig, Shuyan Zhou, Ruslan Salakhutdinov, Daniel Fried
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

---

# PASS 1 — Triage (bird's-eye, ~5 min)

## One-sentence takeaway
VisualWebArena is a benchmark of 910 self-hosted, execution-evaluated web tasks where every task requires visual understanding of the page (25.2% also take input images), exposing that the best VLM agent at submission reached only 16.4% success vs 88.7% for humans (p.1, Abstract; p.8 Tab.3).

## The Five Cs
- **Category:** Benchmark / dataset contribution plus an empirical evaluation of existing LLM/VLM agents, with one modest method proposal (a Set-of-Marks observation/action representation).
- **Context:** Built directly on WebArena (Zhou et al., 2024), reusing its self-hosted environments, POMDP formalism, and functional (execution-based) evaluation (p.1, §1; p.3, §3). Competes with text-web-agent benchmarks (Mind2Web, WebShop, MiniWoB++) and relates to VLM-agent work (CogAgent, GPT-4V GUI navigation, Set-of-Marks prompting of Yang et al. 2023a) (p.2, §2).
- **Correctness:** Core assumptions hold on first read — execution-based rewards over self-hosted sites are reproducible and the visual-grounding-by-construction claim is plausible. Two soft spots: the VQA/fuzzy evaluators are themselves model-based (BLIP-2-T5XL, GPT-4-Turbo), so reward fidelity depends on those models (p.4, §3.3); and all agent numbers appear to be single-run with no variance reported (p.8, Tab.3).
- **Contributions:** (1) 910 visually grounded tasks over three sites including a brand-new Classifieds environment with 65,955 real listings (p.1, §1; p.5, §4.1); (2) extensive benchmarking of SOTA LLM/VLM agents showing VLMs beat text LLMs but trail humans badly (p.1, §1; p.8); (3) a Set-of-Marks (SoM) representation that labels interactable elements with boxes+IDs, simplifying the action space and helping GPT-4V on visually dense sites (p.3, §2; p.7, §5.3).
- **Clarity:** Well written, well organized, generous appendix with per-difficulty and per-subset breakdowns, failure-mode case studies, and full prompts. Evidence is broad across many models but thin on statistical rigor (no error bars / seeds).

## Why this matters to me now
Directly relevant to multimodal/computer-use agent harnesses: it defines an observation interface (accessibility tree, screenshot, SoM-annotated screenshot), a discrete action interface keyed to element IDs, and a functional-correctness evaluator — exactly the harness primitives worth comparing against for any web/GUI agent project.

---

# PASS 2 — Content (what it actually does; section-grounded)

## Motivation — the problem (NOT the novelty)
Most agent benchmarks evaluate text-only agents over HTML or accessibility-tree representations, neglecting tasks that genuinely require seeing the page (p.1, Abstract; §1). Real human web tasks are visually grounded — "order a green polo shirt", "find this post (image)", recognizing colors/icons/layout — and these cannot be solved from text alone (p.1, §1). Because digital interfaces are built for human eyes, visual understanding is necessary for many routine computer tasks, yet the field lacks a realistic, reproducible benchmark that forces agents to integrate interleaved image-and-text inputs with web actions. The importance: without such a benchmark, multimodal web agents cannot be measured or driven forward.

## Novelty — the genuine delta  ★ the core of a good summary
- **Delta in one sentence:** A reproducible, execution-evaluated web benchmark in which visual understanding is *required to compute the reward* (visually grounded tasks plus new visual reward primitives), not merely incidental — turning "can the agent see?" into a measurable, functionally-checked outcome.
- **Mechanistic reason the design takes its form:** WebArena's tasks and reward functions operate over textual/HTML state, so an agent can often succeed without any vision. To force and *verify* visual competence, the benchmark needs (a) tasks whose specification or target is only resolvable visually (e.g., "the red one in the second row", an input image), and (b) reward functions that can check open-ended visual outcomes. Hence the new primitives eval_vqa (queries BLIP-2-T5XL with a yes/no question about the resulting page state) and eval_fuzzy_image_match (SSIM threshold between produced and ground-truth images), plus must_exclude (p.4-5, §3.3). These exist because exact-ID enumeration of acceptable answers is infeasible for open-ended visual goals like "buy a green hoodie under $10" (p.4, §3.3). Separately, the SoM representation is motivated mechanistically: on visually dense pages (Classifieds, Reddit) many small images sit spatially close and the accessibility tree cannot disambiguate them, so labeling each interactable element with a box+ID lets a strong VLM act in a visual-centric space and avoid implicit acc-tree-to-pixel co-referencing (p.8, §6; p.18, §C.5).
- **Closest prior work and the precise difference:**
  - *WebArena (Zhou et al., 2024):* same self-hosted framework, POMDP formalism, and functional evaluation; VWA adds visual grounding to every task, a new Classifieds site, image inputs in 25.2% of tasks, and visual reward primitives (p.1, §1; p.3, §3).
  - *Set-of-Marks prompting (Yang et al., 2023a):* VWA applies the marks idea to live, interactive web pages via JavaScript-generated boxes/IDs as the observation+action space, and is "the first to systematically benchmark this on a realistic and interactive web environment" (p.7, §5.3) rather than as a static proof-of-concept.
  - *Zheng et al. (2024), GPT-4V as generalist web agent:* contemporaneous; it does action grounding to pick HTML elements, whereas VWA's SoM gives the VLM marks to reference directly (p.3, top).
- **Motivation-vs-novelty check:** The framing "text agents fail on visual tasks" is motivation, and the abstract/intro lean on it. The genuine novelty that survives "delete 'we propose'" is the *benchmark whose rewards require and verify visual understanding* plus the *Classifieds environment* and the *visual reward primitives*. The SoM "agent" is a representation/prompting choice, not a new architecture; its delta is empirical (it helps GPT-4V specifically) rather than conceptually deep.
- **30-second test:** A reproducible web benchmark where you cannot get reward without seeing the page, achieved by visually-grounded tasks plus model-based visual reward functions, on which today's best VLM scores ~16% against ~89% human.

## Core idea / method
The environment is a deterministic POMDP E=(S,A,Ω,T) inherited from WebArena, with reward R:S×A→{0,1} returned at the final step (p.3, §3). Observation options: raw HTML DOM, accessibility tree (WebArena's default), raw screenshot, or the new SoM screenshot where every interactable element gets a colored bounding box + unique ID, accompanied by a text list "[id] [tagType] [text]" (p.3, §3.1; p.24, Fig.16). The action space is 12 discrete actions (click, hover, type, press, new_tab, tab_focus, tab_close, goto, go_back, go_forward, scroll, stop), with element-ID arguments rather than (x,y) coordinates, deliberately to keep agents at high-level reasoning since SOTA models are not trained for fine-grained pixel referencing (p.3, Tab.1, §3.2).

Benchmark construction: 6 CS-grad-student co-authors wrote 314 intent templates expanded to 910 tasks (avg 2.9/template), spanning Classifieds (new), Shopping and Reddit (from WebArena), with 4.9% multi-site tasks and some Wikipedia knowledge-base use (p.5, §4.2; p.12, Fig.4). 5.1% (46 tasks) are deliberately unachievable to test early termination, scored via fuzzy_match on the agent's stated reason (p.5, §4.2). Each task is annotated with action difficulty (≤3 / 4-9 / ≥10 human actions) and visual difficulty (basic ID / patterns+OCR-short / multi-image+fine-detail), averaged into an overall level (p.6, §4.2). Reward primitives: text (exact_match, must_include, fuzzy_match via GPT-4-Turbo, new must_exclude) and visual (new eval_vqa via BLIP-2-T5XL, new eval_fuzzy_image_match via SSIM); navigation tasks use a (locator, URL) pair to fetch final-state content and reuse the text/visual checks (p.4-5, §3.3).

## Harness relevance
- **environment / workspace:** Three self-hosted web apps — Classifieds (OSClass CMS, 65,955 Craigslist-scraped listings, PII scrubbed via scrubadub), Shopping (WebArena/WebShop Amazon data), Reddit (WebArena forum, 31,464 image posts); some tasks span multiple sites and a self-hosted Wikipedia (p.5, §4.1; p.19, §D).
- **observation interface:** URLs, open tabs, and focused-tab content as one of {HTML DOM, accessibility tree, RGB screenshot, SoM-annotated screenshot}; 25.2% of tasks add one or more input images to the intent (p.3, §3.1).
- **action interface:** 12 discrete browser actions with element-ID arguments (Tab.1); "stop [answer]" emits a string for information-seeking tasks (p.3, §3.2).
- **tool / API / shell / GUI layer:** Browser GUI driven through element IDs; SoM marks injected via JavaScript preprocessing; a homepage at homepage.com plus password page for site logins (p.24, Fig.16).
- **planner / executor / verifier / search structure:** Agents are single prompt-based policies with Chain-of-Thought and 3 in-context examples; no explicit planner, search, or memory module — failure analysis explicitly attributes loops/early-give-up to the lack of state/history tracking (p.7, §5; p.16, §C.4).
- **evaluation harness:** Functional-correctness reward functions (execution-based) returning binary reward; open-ended outcomes checked by model-based evaluators (GPT-4-Turbo fuzzy_match, BLIP-2-T5XL eval_vqa, SSIM image match) (p.4-5, §3.3).
- **training harness:** None — all agents are prompt-based / zero-fine-tuning; the paper speculates fine-tuning on trajectories would help (p.7, §5; p.13, §C.1).
- **logging / trace / reproducibility:** Deterministic self-hosted sites ensure reproducibility; full execution trajectories shown in case studies; viewport 1280×2048 (1280×720 for short-context models), text truncated to 3840 tokens (640 for short-context); temperatures/top-p specified per model family (p.19-20, §F).
- **safety / permission mechanism:** None enforced in-environment; the Ethical Impacts section flags safety/bias concerns and positions VWA as a sandbox, not a deployment target (p.9, §8).

## Experimental setup
- **Benchmarks/subsets:** 910 tasks; analysis subsets for OCR (17.1%), exact image match (8.7%), image-input (25.2%); human study on 230 tasks (one per template) (p.6, §4.3; p.9, §6.1).
- **Baselines/models:** Text-only LLMs (LLaMA-2-70B, Mixtral-8x7B, Gemini-Pro, GPT-3.5, GPT-4 Turbo) over accessibility tree; caption-augmented LLMs (acc-tree + BLIP-2-T5XL or LLaVA-v1.5-7B captions); multimodal VLMs (IDEFICS-80B-Instruct, CogVLM, Gemini-Pro, GPT-4V) in two settings — "Image+Caps+Acc.Tree" and "Image+Caps+SoM" (p.7, §5).
- **Metrics:** Binary success rate per site and overall (p.8, Tab.3).
- **Compute/cost:** Not reported numerically; GPT-4V noted as "prohibitively expensive," so ablations use Gemini-Pro (p.13, §C.1).
- **Artifacts:** Code, baselines, data public at https://jykoh.com/vwa (p.1, Abstract). All baselines use 3 in-context examples (one per environment) with no benchmark overlap (p.7, §5).

## Key results — read the figures, not just the prose
- Human success 88.7% overall (91.07% Classifieds / 87.10% Reddit / 88.39% Shopping) on the 230-task sample (p.8, Tab.3).
- Best text-only LLM: GPT-4 7.25% overall; caption augmentation raises GPT-4 to 12.75% (p.7, §6; p.8, Tab.3).
- Multimodal GPT-4V (Image+Caps+Acc.Tree) 15.05%; GPT-4V+SoM 16.37% overall, the best at submission (p.8, Tab.3). SoM helps GPT-4V most on visually dense sites: Reddit 12.38%→17.14%, Classifieds 8.12%→9.83% (p.8, §6).
- SoM does not help weaker VLMs (IDEFICS-80B 0.99%, CogVLM 0.33%, Gemini-Pro 5.71% with SoM vs 6.04% without) — attributed to only GPT-4V having SoM grounding ability (p.8, §6, Tab.3).
- Subset analysis of GPT-4V+SoM: OCR tasks 13.4% vs non-OCR 16.9% (OCR is a bottleneck); image-input tasks 19.0% vs 14.9% (more tractable once seen); exact-image-match 18.9% vs 16.2% (not a primary bottleneck) (p.9, Tab.4).
- **Abstract-vs-table consistency:** Abstract's "16.4%" matches Tab.3's 16.37% and the appendix Fig.6 overall 16.4% for GPT-4V+SoM — consistent.
- **Post-deadline addendum (Tab.5):** GPT-4o (Image+Caps+SoM) reaches 19.78% overall, surpassing GPT-4V's 16.37%; Gemini-Pro-1.5 11.98%; Llama-3-70B (caption-augmented) 9.78% — a big jump over Llama-2-70B's 0.66% (p.13, §B). These are not in the abstract headline.
- **Critical read of figures:** All Tab.3/Tab.5 numbers appear single-run with no variance or significance. Difficulty heatmaps (Fig.6) confirm success falls with action/visual difficulty and that multimodality helps most on hard-visual tasks (GPT-4V+SoM 12.4% vs caption 8.0% vs text 4.8%) (p.14, §C.2). Trajectory-length analysis (Fig.10) shows most tasks terminate <10 steps but error rate stays roughly uniform across lengths — i.e., longer trajectories are not where it specifically fails.

---

# PASS 3 — Critique (challenge every assumption)

## Does the evidence actually support the claims?
- *Claim: VLMs outperform text LLMs.* Supported by Tab.3 (GPT-4V 15.05% vs GPT-4 text 7.25%, and Gemini-Pro 6.04% multimodal vs 3.85% caption-aug). This experiment **verifies the motivation** (vision matters) more than a novel mechanism.
- *Claim: SoM helps.* Supported but narrowly — only for GPT-4V (+1.3 pts overall, larger on Reddit/Classifieds); it actually slightly hurts Gemini-Pro and does nothing for IDEFICS/CogVLM (Tab.3). This is the experiment that **verifies the SoM novelty**, and it shows the benefit is model-dependent, not a general property.
- *Claim: tasks are genuinely visually grounded.* Indirectly supported: text-only GPT-4 scores far below caption/multimodal variants, and the human study controls leakage by not assigning creators their own tasks (p.6, §4.3). But "every task requires vision" is asserted by construction/annotation, not independently audited; a text-only baseline scoring nonzero (GPT-4 7.25%) shows some tasks are partly solvable from text.
- *Weak spots:* No variance/seeds; model-based evaluators (BLIP-2-T5XL VQA, GPT-4-Turbo fuzzy, SSIM) can mis-score, and their accuracy is not validated against human labels in the main text; ablations (in-context count) run only on Gemini-Pro for cost reasons, so they may not transfer to GPT-4V.

## Hidden assumptions & failure modes
- The reward functions assume the chosen locator/VQA/SSIM checks are faithful proxies for task success; an agent could pass eval_vqa by reaching a superficially matching state, or fail despite a correct-but-phrased-differently answer.
- SoM assumes the VLM can ground numbered marks; the paper concedes only GPT-4V reliably can (p.8, §6).
- Documented agent failure modes: undoing correct actions (shopping #54, #397), giving up too early before scrolling (shopping #248), append-instead-of-replace in text fields (shopping #345), oscillating between tabs/pages (classifieds #205), and failing surprisingly easy tasks (shopping #46 red item, second row) (p.15-17, §C.4).
- Human baseline itself is imperfect (88.7%), failing exhaustive-search tasks — so the headroom to "human" may understate the true ceiling for some tasks.

## Could I reconstruct it? (reproducibility)
- Code: Released at https://jykoh.com/vwa (p.1).
- Data: 910 tasks + three site datasets (Classifieds 65,955 listings, Reddit 31,464 posts) released; input images from royalty-free sources and MS-COCO (p.5, §4.2; p.19, §D).
- Models: API models (GPT-4 Turbo, GPT-4V, GPT-3.5, Gemini-Pro/1.5, GPT-4o) plus open models (LLaMA-2/3-70B, Mixtral-8x7B, IDEFICS-80B, CogVLM); evaluators BLIP-2-T5XL and GPT-4-Turbo.
- Environment: Self-hosted Docker-style web apps (OSClass for Classifieds), WebArena infrastructure.
- License: Not reported in the extracted text.
- Exact commands/setup: Viewport, truncation, temperature/top-p, 3 in-context examples, and full prompts given (p.19-20, §F; Figs.16-17) — enough to reproduce baselines.
- Missing details: SSIM threshold value t left abstract; exact prompt for eval_vqa/fuzzy_match evaluators and their validation; per-task seeds and number of runs.

## Strengths
- Reproducible, execution-based evaluation over realistic self-hosted sites with a genuinely new Classifieds environment built from real scraped data (p.5, §4.1).
- Visual grounding is enforced by construction and partly verified by the text-vs-multimodal gap; visual reward primitives extend functional evaluation to open-ended visual goals (p.4-5, §3.3).
- Broad model coverage (text, caption-augmented, multimodal, SoM) plus rich failure-mode and per-subset/difficulty analysis and full prompts.
- Strong, well-documented human baseline with leakage controls (p.6, §4.3).

## Weaknesses and limitations
- Headline agent scores are very low (16.4%), so the benchmark is far from saturated but also gives noisy signal for weak models (most open models ≈0 on medium/hard) (p.6, §4.2).
- No reported variance, seeds, or significance; single-run tables.
- Reward fidelity depends on model-based evaluators that are not independently validated in-paper.
- SoM benefit is GPT-4V-specific; the "agent" contribution is a prompting/representation tweak, not a deep method.
- Binary rewards only; authors note continuous scoring as future work (p.4, footnote 2).
- Cost prevents running the strongest model on ablations.

## Relationship to prior work
Genuinely new vs WebArena: the visual-grounding requirement on every task, the Classifieds environment, image inputs (25.2%), and visual reward primitives (eval_vqa, eval_fuzzy_image_match, must_exclude). Genuinely new vs Set-of-Marks prompting: first systematic use of marks as a live observation+action space on interactive web pages. Incremental: the agent itself is a prompted VLM with CoT and in-context examples (no planning/memory/search), and the text/caption baselines follow WebArena closely. Distinct from Zheng et al. (2024), which grounds actions onto HTML elements rather than using injected visual marks.

---

# Decision

## What I should read
- Must read: §3 (environment, observation/action spaces, evaluation primitives) and §5-6 + Tab.3 (baselines and results); §C.4 failure modes for harness design lessons.
- Skim: §2 related work; appendix §B (post-deadline GPT-4o/Gemini-1.5 numbers); §F settings.
- Can skip: §8 ethics; reference list.
- Follow-up papers / references to chase: WebArena (Zhou et al., 2024); Set-of-Marks (Yang et al., 2023a); Zheng et al. (2024) generalist web agent; CogAgent (Hong et al., 2023); Mind2Web (Deng et al., 2023).

## Triage decision
Label: READ_SOON
Rationale (Five Cs + novelty + evidence): A foundational, widely-cited multimodal web-agent benchmark with a clear reproducible harness, well-defined observation/action interfaces, and functional-correctness evaluation — directly useful as a reference design and comparison point. Novelty is real but moderate (benchmark + visual reward primitives + Classifieds site; SoM is a model-specific tweak). Evidence is broad but single-run with model-based evaluators, so confidence in exact numbers is bounded. Strong relevance keeps it above SKIM; moderate methodological novelty keeps it below MUST_READ.
Confidence: high
Reading time estimate: ~60-75 min for a thorough pass including the appendix.

## Personal notes
The most transferable harness ideas: element-ID action space (avoid pixel coords for non-grounding models), SoM-as-observation injected via JS, and visual reward primitives (VQA/SSIM) for open-ended functional evaluation. Watch the evaluator-fidelity risk if reusing eval_vqa/fuzzy_match.

## Follow-up actions
- Add related paper: WebArena; Set-of-Marks; Zheng et al. 2024.
- Compare with: WebArena (text-only baseline), Mind2Web, OSWorld-style GUI benchmarks.
- Re-run after new version: track later VWA leaderboard / stronger native multimodal models (GPT-4o already at 19.78%).
- Check code: https://jykoh.com/vwa (SSIM threshold, evaluator prompts).
- Read benchmark details: §3.3 reward primitives and §D Classifieds environment.
