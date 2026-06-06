# Android in the Wild: A Large-Scale Dataset for Android Device Control

## Metadata
- Canonical key: arxiv-2307.10088
- Version: v1
- Fetch date: 2026-06-06T07:57:30Z
- Source: arxiv
- PDF: library/android-in-the-wild-a-large-scale-230710088/v1/paper.pdf
- Venue: Neural Information Processing Systems (NeurIPS 2023, Datasets & Benchmarks Track)
- Year: 2023
- Authors: Christopher Rawles, Alice Li, Daniel Rodríguez, Oriana Riva, T. Lillicrap
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
AITW is a 715k-episode, ~30k-instruction Android device-control dataset whose defining design choice is to drop UI-tree metadata in favor of pixel-only observations and a precise dual-point gesture action space, paired with OOD splits and an offline action-matching metric for evaluating GUI agents.

## Why this paper matters
This is a foundational data artifact for pixel-based mobile GUI agents. Almost every later Android-agent benchmark and model (the action-matching metric, the four-subset structure, the OOD generalization splits) is downstream of or reacting to AITW. For anyone building or evaluating device-control agents, AITW is the reference dataset that established (a) the assumption that agents must infer affordances from pixels rather than View Hierarchy metadata, and (b) the now-widely-copied offline action-matching evaluation. Understanding both its construction and its metric's limits is necessary to read the literature it spawned.

## Problem and gap
CLAIMED problem (p1-2): build device-control systems that map high-level natural-language goals to UI actions executed directly on-screen, "exactly as a human does," without app-specific APIs. EVIDENCE of the gap (p2, Table 1, p3): prior datasets are (i) orders of magnitude smaller — MoTIF, the largest predecessor, has ~4.7k feasible demos vs AITW's 715k; (ii) reliant on platform UI-tree metadata (View Hierarchy / DOM), which the authors argue is "poor quality or missing altogether" for real apps (WebViews, Canvas, Electron, Accessibility-gated VH); (iii) often phrased as low-level step commands ("Click the button labeled Cancel") rather than high-level goals. WHY-read: the gap framing is the paper's main intellectual move — it deliberately makes the problem *harder* (pixels only, arbitrary gestures) to be more realistic, which is the lens through which all results should be read.

## Core idea
Two coupled design decisions distinguish AITW from prior work:
1. Pixel-only observation. Episodes store screenshots plus *pixel-derived* features (OCR text + IconNet icon-class labels, one of 96 icon types, p5), explicitly NOT the View Hierarchy. The authors expect users to swap these noisy features for stronger screen-understanding models.
2. Dual-point gesture action space (p4-5). Each gesture is a (touch_point, lift_point) pair at arbitrary normalized <x,y>; a tap is the degenerate case where the two points are within 0.04 Euclidean distance, a scroll is a longer drag. This lets the data represent precise drags (carousels, sliders, month-switching) that element-based action spaces cannot. Action types: dual-point gesture, type, go_back, go_home, enter, task_complete, task_impossible.
The dataset is organized into OOD splits (unseen Android version, unseen subject, unseen verb, unseen domain) to turn it into a generalization benchmark, not just a training corpus.

## Harness relevance
This is a DATASET paper, so harness elements are adapted to how episodes/screens/actions are represented and evaluated.

- Environment / workspace: Android Emulator driven via AndroidEnv [40] (p2, p4). Raters used mouse+keyboard on a desktop; clicks logged as touch events. Four Android versions (v10-13), eight device types (Pixel 2 XL -> Pixel 6), varying resolutions.
- Observation interface: RGB screenshot + post-processed UI elements, each a bounding box with either OCR text or one of 96 IconNet icon classes (p5). Stored per-step as TFRecord fields (Appendix C, p20): image/encoded, image/ui_annotations_positions (y,x,h,w), ui_annotations_text, ui_annotations_ui_types, current_activity, android_api_level. Crucially NO View Hierarchy is provided.
- Action interface: dual-point gesture (touch_point, lift_point as (y,x)), plus type (typed_text), go_back, go_home, enter, task_complete, task_impossible (p5). Captured at 10 Hz; LIFT actions dropped after gesture extraction. This is the "precise gesture" action space that is the paper's signature.
- Tool/API/GUI layer: pure GUI / pixel layer; the explicit thesis is to avoid API and accessibility-tree dependence.
- Planner/executor/verifier structure: not part of the dataset; two baseline agents are provided (BC Transformer; PaLM-2 LLM over an HTML-ified screen). No search.
- Evaluation harness: offline **action matching** (p8) — two actions match if action types are equal AND, for taps, fall within 14% screen distance OR within the same detected bounding box (inflated to 240% size); two scrolls match if they share the primary axis (vertical/horizontal). Yields partial match (correct actions / episode length) and complete match (partial = 1.0), following Li et al. [28]. Code released.
- Training harness: BC agent trained with cross-entropy on a 2x2 V2 TPU slice, Acme/Haiku/JAX, 4-layer Transformer, lr 1e-4, batch 128, dropout 0.1; grid-search HP on val (Appendix B.1, p14, p18-19).
- Logging/trace/reproducibility: per-step TFRecords (GZIP) with episode_id, step_id, episode_length, goal_info, current_activity, action fields. Dataset + action-matching code public on GitHub.
- Safety / permission: ethical section (p10) — raters told to enter no PII; no real-user data; authors flag malicious-use risks (CAPTCHA bypass, prompt/screen manipulation). No in-dataset permission mechanism.

Limits of the proposed metric (load-bearing for harness users): action matching is a distance heuristic that penalizes functionally-equivalent alternatives (e.g., nav-bar back vs in-app back), so complete-match is a **lower bound** on true success (p8). The authors validate it with human evaluation only on a small GOOGLEAPPS subset (~86.5 episodes/split, Figure 3, p8-9) and find partial match correlates with true completion "especially if the number of steps is small." This is a weak validation base and a known source of metric noise in downstream work.

## Method (dataset construction)
Two-stage pipeline (Figure 1, p2; section 3, p4-5):
1. Multi-step collection. Instructions sourced from (a) the authors, (b) achievable subset of PixelHelp [28], (c) LLM-generated prompts. Raters execute end-to-end on a randomized starting screen ("Imagine a friend is asking you to perform the task on their phone"), ending with task_complete or task_impossible. Verification-style tasks already in target state are marked complete.
2. Hindsight language relabeling [31,32] (section 3.2). Raters review collected multi-step trajectories and annotate short 2-5 frame subsequences (>=3 per video) with result-describing phrases, explicitly avoiding "click/tap/scroll" wording. This produces the SINGLE single-step set without re-collection.
Composition (Table 2, p4): 715,142 episodes / 5,689,993 screens / 30,378 unique prompts, split as GOOGLEAPPS (625,542 ep; 306 prompts), INSTALL (25,760 ep; 688 prompts; 88 apps), WEBSHOPPING (28,061 ep; 13,473 prompts), GENERAL (9,476 ep; 545 prompts), SINGLE (26,303 ep; 15,366 prompts). Figure 1 annotates the pipeline as ~15K multi-step prompts -> 689K multi-step demos + 26K hindsight-relabeled episodes. Coverage: 357+ apps/websites headline (Table 1); finer breakdown 159 Android apps + 198+ websites (p6, "conservative estimate"). Episode lengths 2-16 (5th-95th pct); WEBSHOPPING longest; Chrome/Google apps most frequent.

## Experimental setup
- Splits (section 4, p6-7): Standard (per-subset 80/10/10 episode-wise, averaged across subsets); Unseen Android version (train/val on v10-12 at 90/10, test entirely on v13); Unseen subject and Unseen verb (instructions templated by masking subject/verb phrases via a few-shot LLM — 6,111 subject templates, 22,122 verb templates — then templates split 80/10/10 so paraphrases don't leak); Unseen domain (split by web domain / app name; excludes SINGLE and GOOGLEAPPS).
- Baselines / models (section 5.1, p7-8): BC-single and BC-history (2 prior steps) Transformer behavioral-cloning agents that output the full dual-point action space; LLM-0 (PaLM-2 zero-shot, HTML-ified screen, click-on-element only) and LLM-hist-5-CoT (5-shot chain-of-thought with action history), adapted from Wang et al. [43].
- Metric: partial / complete action-matching score (above). BC evaluated on full test sets; LLM evaluated on 288 sampled episodes per split (compute cost), with binomial 95% CIs.
- Compute: 2x2 V2 TPU slice for BC training; LLM inference cost cited as the reason for the 288-episode sampling.
- Artifacts: dataset + action-matching code at the google-research GitHub.

## Key results (VERIFIED against extraction, Table 4 p9; Table 5 p17)
Standard-split partial match: BC-history **73.1**, BC-single 68.7, LLM-hist-5-CoT 39.6, LLM-0 30.9.
OOD partial match (BC-history / LLM-hist-5-CoT): Version 63.2 / 29.5; Subject 68.5 / 44.4; Verb 70.4 / 41.7; Domain 59.7 / 35.8.
- BC-history is best across every split; history helps (+~4 pts over BC-single on Standard).
- The LLM's element-only action space is a structural handicap: 33% of standard-set episodes contain non-element taps that are simply infeasible for it; on the feasible subset LLM-hist-5-CoT reaches 58% partial match (p8).
- BC-history per-subset (Table 5, p17): Standard ranges 63.7 (GENERAL) to 80.3 (SINGLE); Domain only available for WEBSHOPPING (49.6) and INSTALL (66.9). GOOGLEAPPS is easy on Standard (75.7) but hard on Subject/Verb (48.4/57.4) because it has few unique prompts but many demos each.
- Human-eval validation (Figure 3, p8): partial match correlates with true complete-match; automated complete-match is a lower bound. Validated only on a small GOOGLEAPPS subset.

## Evidence quality
The dataset-scale and diversity claims are well supported (Tables 1-2, statistics in Figure 2). The baselines are explicitly framed as reference points, not strong agents, so absolute numbers are less important than the relative story (custom pixel BC >> adapted element-based LLM). UNCLEAR / weak spots: (1) the central metric's fidelity is validated on a single subset (~86.5 episodes/split) and only argued to hold for short episodes — a thin basis for a metric the whole field adopted; (2) the LLM baseline is handicapped by an action-space mismatch the authors themselves introduced (element-only vs the dataset's gesture space), so the BC-vs-LLM gap partly measures interface fit, not model capability; (3) no fine-tuned-LLM baseline (acknowledged as future work); (4) prompt-template OOD splits rely on an LLM extractor whose error rate is not reported. Statistical reporting is reasonable (binomial CIs for LLM; BC CIs stated <0.1% and omitted).

## Reproducibility and artifacts
- Code: action-matching evaluation + agent code referenced on google-research GitHub (p1).
- Data: 715k episodes as GZIP TFRecords, per-step schema in Appendix C (p20). Public.
- Models: BC architecture/hyperparameters fully specified (Appendix B.1); LLM prompts given verbatim (Appendix B.2, p17-20). Model weights: Not reported as released.
- Environment: AndroidEnv + Android Emulator; AITW agents "can be evaluated using AndroidEnv" (p2).
- License: Not reported in extraction.
- Exact commands/setup: training recipe given; no command lines.
- Missing details: rater count, hourly wage, total annotation cost ("cannot include ... due to global privacy concerns", Appendix A.1); IconNet/OCR error rates; template-extraction accuracy.

## Strengths
- Two orders of magnitude larger than prior device-control datasets, with real (non-synthetic) screens and genuine high-level goal instructions.
- Pixel-only + dual-point gesture design is realistic and harder than VH/element-based setups; representative of deployment conditions.
- Purpose-built OOD splits (version / subject / verb / domain) make it a generalization benchmark, not just a corpus.
- Reusable offline metric (action matching) with released code — a major reason for its adoption.
- Clean, well-documented per-step record format enabling reuse.

## Weaknesses and limitations
- Metric is a distance heuristic that under-credits valid alternative actions; complete-match is only a lower bound and validated narrowly (authors acknowledge, section 5.2, Future Work).
- English-only prompts; raters not globally representative; dynamic Internet content not representative (section 6.1).
- Raters used mouse/keyboard, not native touch — interaction patterns may differ (section 6.1).
- Phone form factor only; no tablets/other factors.
- UI drift over time only partially captured (via Android-version split); continuous per-app UI evolution and dataset *aging* are not modeled — a real contamination/staleness concern as apps/websites change after collection.
- Class imbalance: GOOGLEAPPS is 87% of episodes but only 306 prompts, skewing aggregate numbers and standard-split difficulty.
- LLM baseline underpowered by interface mismatch; no fine-tuned multimodal baseline.

## Relationship to prior work
Closest predecessors (Table 1, p3): MoTIF [9] (largest prior Android goal dataset, ~4.7k feasible demos), PixelHelp [28] (187 Pixel-Help tasks; source of the action-matching metric and a prompt subset), UGIF [42] (multilingual), Mind2Web [14] (web), RicoSCA/UIBert/MiniWoB++ (element-grounding or synthetic). Genuinely new: scale (715k), pixel-only observation by design, arbitrary dual-point gesture action space, and the OOD-split organization. Incremental/borrowed: the action-matching metric (from [28]) and the LLM-over-HTML-screen baseline (from Wang et al. [43]).

## What I should read
- Must read: section 3 (data pipeline, action space, screen features, p4-5); section 5.2 evaluation methodology / action matching (p8); Table 2 (p4); Appendix C dataset format (p20).
- Skim: section 4 OOD splits (p6-7); section 5.3 results + Tables 4-5; section 6 limitations.
- Can skip: full reference list; Appendix B.2 verbatim LLM prompt (read once for prompt format only).
- Follow-up papers: AndroidEnv [40]; Wang et al. CHI'23 LLM-UI [43]; MoTIF [9]; PixelHelp/Li et al. ACL'20 [28]; Mind2Web [14]; and later AITW-derived benchmarks (AndroidControl, AndroidWorld) for how the metric/splits evolved.

## Triage decision
Label: READ_SOON
Rationale: Foundational dataset for pixel-based mobile GUI agents; defines the action space, observation format, OOD splits, and the action-matching metric that downstream work builds on. Evidence broadly supports the dataset claims; the metric's narrow human validation is the main caveat but does not undercut the artifact's importance. Keeping READ_SOON per the scaffold; evidence does not strongly differ.
Confidence: high
Reading time estimate: ~45-60 min for the core sections above.

## Personal notes
Key verified numbers: 715,142 episodes; 5,689,993 screens; 30,378 unique prompts; subsets GOOGLEAPPS 625,542 / INSTALL 25,760 / WEBSHOPPING 28,061 / GENERAL 9,476 / SINGLE 26,303; coverage 357+ apps+websites (159 apps + 198+ websites); INSTALL spans 88 apps. Action match: tap within 14% screen distance or same bbox @240%; scroll by axis. Baselines (Standard partial match): BC-history 73.1, BC-single 68.7, LLM-hist-5-CoT 39.6, LLM-0 30.9. Watch the contamination/aging angle: real web/app screens captured 2023 on Android v10-13 — already drifting.

## Follow-up actions
- Add related paper: AndroidEnv [40]; later AITW-derived benchmarks (AndroidControl, AndroidWorld).
- Compare with: MoTIF, Mind2Web, PixelHelp for dataset/metric lineage.
- Re-run after new version: check if a v2/erratum adjusts the action-matching thresholds.
- Check code: action-matching implementation (14% / 240% constants) on google-research GitHub.
- Read benchmark details: how downstream papers report online vs offline AITW scores.
