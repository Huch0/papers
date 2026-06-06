# You Only Look at Screens: Multimodal Chain-of-Action Agents

## Metadata
- Canonical key: arxiv-2309.11436
- Version: v1
- Fetch date: 2026-06-06T07:57:30Z
- Source: arxiv
- PDF: library/you-only-look-at-screens-multimodal-chain-230911436/v1/paper.pdf
- Venue: COLM 2024 (arXiv v4 dated 7 Jun 2024; extraction header lists ACL-affiliated venue, but the task and arXiv record this as COLM 2024)
- Year: 2023 (arXiv first posting; published 2024)
- Authors: Zhuosheng Zhang (SJTU), Aston Zhang (Meta GenAI; work done at AWS)
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
Auto-GUI is a sub-1B multimodal encoder-decoder that maps a raw Android screenshot plus a natural-language goal directly to a low-level touch/type action, using a "chain-of-action" of past action histories and predicted future action-type plans, reaching 74% overall action accuracy and ~90% action-type accuracy on AITW without any OCR/HTML/view-hierarchy parsing or app APIs.

## Why this paper matters
This is an early (2023) and clean instance of the "screenshot-in, action-out" paradigm that has since become dominant in computer-use / GUI agents. It is directly relevant to harness design: it argues against the then-standard "parse the screen into HTML text, feed to an LLM" pipeline, on grounds of inference latency and error propagation (p1, Sec 1). The contribution worth tracking is not the absolute scores (the backbone is a small T5/FLAN-Alpaca, not a modern VLM) but the design stance: a unified, API-free, pixel-only agent can match or beat a specialized behavioral-cloning baseline. For anyone studying observation interfaces (pixels vs. accessibility tree vs. HTML) and action spaces (normalized coordinate gestures vs. element-index clicks), this is a foundational reference point.

## Problem and gap
CLAIMED problem (p1, Sec 1): prior GUI agents operate in a "sandbox" setting that (1) parses the visual environment into textual elements (OCR + icon detection -> HTML) and (2) relies on application-specific APIs (e.g., JavaScript element selection, Python interpreters) to execute predicted actions. Two stated failure modes: lengthy parsed inputs cause inference inefficiency and can exceed context limits; parsing introduces error propagation / information loss; and internal APIs are often unavailable in third-party apps.
EVIDENCE in paper: the latency claim is supported by Table 5 (p9) - Auto-GUI infers in <1s vs. Llama-2 at 8.5 s/inference, ~10-45x faster. The "information loss from HTML" claim is supported indirectly by Table 6 (p9): ChatGPT (HTML input) reaches only 8.5% click accuracy and 4.0% scroll accuracy despite 41.7% action-type accuracy, vs. Auto-GUI 58.3 / 82.7 / 87.0. WHY this is the right framing: it cleanly separates "knowing what action type" from "knowing where," and shows the textual pipeline mainly fails on the spatial sub-problem.
UNCLEAR: the paper does not directly measure error introduced by the OCR/icon parser itself (e.g., parser recall/precision), so "error propagation" is asserted rather than quantified.

## Core idea
Two ideas. (1) First-principles / pixel-only interaction (p3-4, Sec 3.2): a single multimodal model reads the screenshot through a frozen vision encoder (BLIP-2) and the goal+history through a language encoder, fuses them, and decodes the action string directly - no environment parsing, no app API. (2) Chain-of-action (p4, Sec 3.2, Fig 2): the language input is augmented with a "chain of previous action histories" Xhistory (up to 8 prior action tuples) and the decoder is trained to first emit a "chain of future action plans" Yplan (a short list of upcoming action *types*, up to 4) before emitting the concrete current action Yaction. So past actions are an input conditioning signal and future plans are an auxiliary output prefix - a lightweight planning scaffold rather than search or a separate planner module.

## Harness relevance
- Environment / workspace: Android device-control episodes from the AITW benchmark (Rawles et al. 2023); 715K episodes, 30K unique instructions, 350+ apps/websites, 5 subsets (General, Install, GoogleApps, Single, WebShopping) (p5, Table 1). This is offline/static evaluation on logged episodes, not a live interactive emulator loop.
- Observation interface: a single screenshot per step (Xscreen, h x w x 3), encoded by a frozen BLIP-2 image encoder (p4, Sec 3.2). Crucially, at inference NO HTML, NO OCR, NO icon-detection, NO view-hierarchy / accessibility tree is used - pixels only. (An optional variant adding HTML "screen descriptions" exists only as an ablation, Table 10, p15.)
- Action interface: a 4-tuple {action_type, touch_point, lift_point, typed_text} emitted as a string (p4-5, Sec 3.3). Six action types: dual-point gesture (covers click and scroll), type, go_back, go_home, enter, status_complete. Clicks/scrolls use normalized [y,x] coordinates (clicks kept to 4 decimals; scrolls snapped to 4 canonical directional coordinate pairs). System actions fill coordinates with -1. This is a continuous-coordinate action space, unlike the LLM baselines which can only click a detected element index.
- Planner/executor/verifier/search: no explicit planner/verifier/search. "Planning" is the auxiliary Yplan future-action-type prefix decoded before the action; execution is single-step greedy decoding. No tree search, no self-reflection, no verifier.
- Tool/API/shell/GUI layer: none - the explicit design goal is to avoid app-dependent APIs. The model output coordinates are assumed directly executable on a device (p4, footnote on halting via simple rules).
- Evaluation harness: screen-wise action matching score = correct actions / episode length (p6, Sec 4.3). Correct = action type matches AND gesture matches; click correct if within 14% screen distance or same bounding box as gold; scroll correct if same axis. Authors note this metric is shown (in Rawles et al.) to correlate with human task-completion judgments.
- Training harness: encoder-decoder (T5-style) initialized from FLAN-Alpaca, frozen BLIP-2 vision features, single-head self-attention + gated fusion, up to 10 epochs, lr 1e-4, max seq len 512, batch 4, 8x V100 32G; large/base take 75/25 h (p6, Sec 4.4). Two regimes: Auto-GUIseparate (per-subset) and Auto-GUIunified (one model over all subsets, using only 10% of GoogleApps to mitigate imbalance and cut ~80% compute).
- Logging/trace/reproducibility: code released (github.com/cooelf/Auto-GUI); dataset is public AITW. No per-episode trace logging mechanism described beyond standard eval.
- Safety/permission: none described.

## Method
The model (Fig 2, p3; Sec 3.2-3.3) runs in three stages. Encode: frozen BLIP-2 gives Hscreen (1 x ds), projected by trainable W to language dimensionality; language encoder encodes Xlanguage = {Xgoal, Xhistory}. Interact: single-head self-attention with Q=Hlanguage, K=V=projected screen features, then a sigmoid gated fusion Hfuse = (1-lambda)*Hlanguage + lambda*Hattn. Decode: Transformer decoder emits the string "{Action Plan: Yplan, Action Decision: Yaction}", i.e., future action types first, then the concrete 4-tuple. Coordinate normalization (Sec 3.3) reduces coordinate ambiguity and is reported to speed convergence. The authors deliberately keep the interaction module a single layer to stay <1B parameters and modality-extensible (p4, footnote 2).

## Experimental setup
- Benchmark: AITW, 5 subsets, 80/10/10 episode-wise split (p5, Tables 1/7).
- Baselines (p5-6, Appx B.2): ICL LLMs - few-shot PaLM 2-CoT, ChatGPT(turbo-3.5)-CoT, and multimodal GPT-4V (results imported from Yan et al. 2023); fine-tuned Llama-2-7B via LoRA on 1% of training data with HTML screen descriptions; specialized agent - Behavioural Cloning BC-single and BC-history (prior SOTA from Rawles et al. 2023, uses screen+action history, OCR/BERT/icon embeddings).
- Models: Auto-GUI at small (60M), base (200M/"220M"), large (700M/"770M"); BLIP-2 vision; FLAN-Alpaca init.
- Metric: screen-wise action matching (overall = average over subsets); plus category accuracies (click region, scroll direction, action type, typed text).
- Compute/cost: Table 5 (p9) - Auto-GUI <1s/action, <10GB GPU; Llama-2 8.5 s/inference, 49.7GB.
- Artifacts: code public; AITW public.

## Key results (numbers VERIFIED against extraction)
- Overall action accuracy (Table 2, p7): Auto-GUIunified 74.27, Auto-GUIseparate 74.07. Baselines: BC-history 73.1 (prior best, underlined), BC-single 68.7, GPT-4V 52.96, PaLM 2-CoT 39.6, Fine-tuned Llama-2 28.40, ChatGPT-CoT 7.72. So the headline "74%" = 74.27 (unified). It beats BC-history overall but is LOWER on Install (76.89 vs 77.5) and GoogleApps (71.37 vs 75.7) - authors attribute the GoogleApps gap to using only 10% of its training data (Appx C.1, p15).
- Action-type prediction accuracy "~90%" (Fig 4, p7-8): 90.1% average across subsets. Per-category averages: Click 67.4%, Scroll 82.0%, Action Type 90.1%, Typed Text 93.1%. CLAIMED bottleneck = click region and scroll direction (spatial grounding), consistent with EVIDENCE.
- Chain-of-action gain: +5.74% VERIFIED. Table 3 (p7) / Table 9 (p15): full 74.27 vs. "w/o chain of actions" 68.53 -> +5.74. Decomposed: removing future action plan drops to 68.81 (the future plan carries almost all the benefit, ~5.46), removing previous action history alone drops only to 73.78 (~0.49). Coordinate normalization gain +4.04 (74.27 vs 70.23). [Note: the per-row arithmetic 74.27-68.53 = 5.74 and 74.27-70.23 = 4.04 both check out.]
- Efficiency (Table 5, p9): >10x faster inference than Llama-2, <1s per action.
- Feature/scale analysis (Table 4, p9): BLIP-2 > CLIP (74.27 vs 71.84 overall); FLAN-Alpaca > FLAN-T5 > vanilla-T5; small/base/large = 71.38 / 72.84 / 74.27 - scaling helps only marginally (~3 pts across a >10x param range), supporting the CLAIMED "scale matters less here" conclusion.
- Generalization (Fig 5, p8): cross-subset transfer is "decent" but degrades off-domain (e.g., a Single-trained model gets 81 on Single but 17-35 elsewhere); the unified model is the practical choice.
- With HTML screen descriptions added (Table 10, p15): base model rises 72.84 -> 75.54, showing the pixel-only setup leaves headroom that parsing could recover - a useful honesty point, since it slightly undercuts the strong "parsing is harmful" framing (parsing helps accuracy here; it is dropped for practicality, not because it hurts performance).

## Evidence quality
Reasonably strong for its scope. Strengths: a credible prior-SOTA baseline (BC-history) on the same metric; ablations isolate chain-of-action (+5.74) and coordinate normalization (+4.04); feature and scale studies; a latency comparison. EVIDENCE supports the two headline claims (74% overall, ~90% action type) and the efficiency claim. Caveats that weaken the broader narrative: (1) the metric is offline screen-wise action matching, NOT live task completion - a proxy the authors acknowledge correlates with human judgments but is not end-to-end success on a real device. (2) No statistical significance / variance reporting; differences vs. BC-history are small (74.27 vs 73.1 overall, and Auto-GUI loses on 2/5 subsets). (3) "Error propagation from parsing" is asserted, and Table 10 shows HTML descriptions actually *raise* accuracy, so the parsing critique is really about practicality/latency, not pure accuracy. (4) Single benchmark only (AITW) - authors state this as a limitation. (5) GPT-4V / PaLM numbers are imported from other papers, not re-run uniformly.

## Reproducibility and artifacts
- Code: public, github.com/cooelf/Auto-GUI (p1).
- Data: AITW (Rawles et al. 2023), public.
- Models: FLAN-Alpaca init + frozen BLIP-2 (blip2_t5_instruct); small/base/large sizes specified.
- Environment: 8x NVIDIA Tesla V100 32G; train large 75h / base 25h.
- License: Not reported.
- Exact commands/setup: hyperparameters given (10 epochs, lr 1e-4, max len 512, batch 4); exact run commands Not reported (deferred to repo).
- Missing details: parser-error quantification; significance/variance; live-execution success; reason 10% GoogleApps subsampling does not even improve with full data ("possibly data imbalance", Appx C.1) is not deeply diagnosed.

## Strengths
- Clear, practical design stance: pixel-only, API-free, <1B params, <1s inference - deployable.
- Chain-of-action is a simple, well-ablated trick with a real gain (+5.74), most of it from predicting future action *types*.
- Continuous normalized-coordinate action space lets it click anywhere, unlike element-index LLM baselines - and the category analysis cleanly shows where it wins (spatial execution).
- Honest reporting: shows where it loses to BC-history and where HTML would help.

## Weaknesses and limitations
- Author-stated (Limitations, p9): not scaled to very large models; experiments confined to AITW.
- Inferred: offline action-matching metric, not live task completion; small absolute margin over prior SOTA with no significance testing; loses on Install and GoogleApps; the anti-parsing argument is undercut by Table 10; weak spatial grounding (click 67.4%, scroll 82.0%) is the real ceiling and points to vision-feature quality, not the chain-of-action idea; no safety/permission consideration for an agent that emits raw device gestures.

## Relationship to prior work
- Closest baseline / dataset: AITW / Behavioural Cloning (Rawles et al. 2023) - Auto-GUI replaces BC's OCR+icon+BERT pipeline with pixel-only multimodal modeling on the same benchmark and metric.
- Multimodal-CoT lineage: builds on the authors' own Multimodal-CoT (Zhang et al. 2023b) and CoT prompting (Wei et al. 2022); chain-of-action is the action-space analogue of chain-of-thought.
- Contrasts with sandbox/API agents: WebArena (Zhou et al. 2023), WebAgent (Gur et al. 2023), and HTML-parsing mobile agents (Wen et al. 2023).
- Concurrent pixel-grounding agents it positions against: SeeClick (Cheng et al. 2024) and CogAgent (Hong et al. 2023b), which add GUI grounding pretraining - Auto-GUI deliberately does not, staying lightweight.
- Genuinely new: the unified, API-free, screenshot-only formulation on AITW plus the chain-of-action output prefix. Incremental aspects: the backbone (T5/BLIP-2/gated fusion) and CoT-style conditioning are reused from prior multimodal work.

## What I should read
- Must read: Sec 3.2-3.3 (architecture, action space, coordinate normalization); Table 2 (main results); Table 3/9 (ablation, the +5.74 chain-of-action gain); Fig 4 (category accuracies).
- Skim: Sec 5.4 feature/scale analysis (Table 4); Table 5 efficiency; Fig 5 transfer.
- Can skip: Appendix data examples (Figs 6-9) and full LLM prompts (Figs 10-11) unless reproducing baselines.
- Follow-up papers: AITW (Rawles et al. 2023), SeeClick (Cheng et al. 2024), CogAgent (Hong et al. 2023b), GPT-4V-in-Wonderland (Yan et al. 2023).

## Triage decision
Label: READ_SOON
Rationale: Foundational, well-scoped reference for the screenshot-only / API-free GUI-agent paradigm and for a simple chain-of-action planning scaffold; directly informative for observation- and action-interface design in computer-use harnesses. Not MUST_READ because the backbone is dated (small T5, frozen BLIP-2), evaluation is single-benchmark offline action-matching, and the headline margin over prior SOTA is small. Evidence does not strongly diverge from the prepared label, so READ_SOON is retained.
Confidence: high
Reading time estimate: ~45-60 min for the core (Secs 3-5 + key tables).

## Personal notes
The most reusable insight is empirical: predicting the *future action-type plan* carries nearly all of the chain-of-action benefit (74.27 -> 68.81 when removed), while feeding *past action history* alone contributes little (74.27 -> 73.78). And the failure is spatial, not semantic: action-type 90%+ but click region only ~67%. For modern harnesses this argues that a strong VLM (better grounding) plus a cheap future-action-type prefix should dominate this design.

## Follow-up actions
- Add related paper: AITW (Rawles et al. 2023), SeeClick, CogAgent.
- Compare with: HTML/accessibility-tree agents vs. pixel-only agents on the observation-interface axis.
- Re-run after new version: arXiv v4 is current; this is the COLM 2024 version.
- Check code: github.com/cooelf/Auto-GUI (action-string format, coordinate normalization).
- Read benchmark details: AITW subset definitions and the 14%-screen-distance click matching rule.
