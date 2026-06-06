# Set-of-Mark Prompting Unleashes Extraordinary Visual Grounding in GPT-4V

## Metadata
- Canonical key: arxiv-2310.11441
- Version: v1
- Fetch date: 2026-06-06T07:57:31Z
- Source: arxiv
- PDF: library/set-of-mark-prompting-unleashes-extraordinary-visual-231011441/v1/paper.pdf
- Venue: arXiv.org
- Year: 2023
- Authors: Jianwei Yang, Hao Zhang, Feng Li, Xueyan Zou, Chunyuan Li, Jianfeng Gao
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
Set-of-Mark (SoM) is an image-side prompting trick that segments an image into regions and overlays each with a "speakable" symbolic mark (numbers/letters/boxes/masks), so GPT-4V can ground answers by naming a mark instead of emitting coordinates -- turning visual grounding into a discrete pick-a-label problem.

## Why this paper matters
CLAIMED: this is "the first study to demonstrate that the emergent visual grounding ability of GPT-4V can be unleashed by visual prompting" (page 2). WHY-read for the harness: although the paper frames itself as a vision-grounding study, its real downstream impact is as the standard click-target mechanism for GUI agents. By converting "where do I act?" into "which numbered mark do I pick?", SoM sidesteps the fact that LMMs cannot reliably emit pixel coordinates (the paper measures GPT-4V's raw coordinate REC accuracy at 25.7 vs 86.4 with SoM -- page 9). That single reframing is the conceptual seed behind set-of-mark style accessibility-tree / segment overlays in later GUI/computer-use agents. The paper itself never builds a GUI agent, but page 21-23 already shows SoM applied to a game controller, a 2D platformer, and an apartment floor-plan navigation -- i.e. it gestures directly at the agentic use case.

## Problem and gap
CLAIMED (page 2): GPT-4V has strong vision-language understanding but weak fine-grained grounding -- "GPT-4V can hardly produce a sequence of accurate coordinates for a dog ... or a few traffic lights." The authors argue (citing Pix2Seq [7]) that forcing an LMM to emit textual descriptions interleaved with numeric coordinates both hurts LLM fluency and discards the spatial structure of the underlying vision encoder.
Gap in prior visual prompting (page 2): existing overlays (red circle [41], highlighted region [48], circles+arrows [49]) refer to only one or a few objects and use marks that are not "speakable" by an LLM, so they cannot scale to dense, multi-object grounding.

## Core idea
EVIDENCE (pages 3-5): Two properties are required: (1) partition the image into semantically meaningful regions (grounding); (2) overlay marks that are both interpretable and "speakable" so the LMM can refer to them in text. SoM augments the image I into a marked image I_m and feeds (I_m, T_i) to the LMM, leaving the text query unchanged (Eq. 2, page 3). Because each mark m_k is bijectively tied to a region mask r_k, any mark named in the text output can be traced back to a mask, yielding triplets <r_k, m_k, text_k> (page 6) -- this is what lets a pure-text LMM produce mask/box outputs.
UNCLEAR / notable: the mechanism is empirical -- the authors explicitly state in the Discussion (page 11) that it is "still mysterious why" SoM works on GPT-4V, and that LLaVA-1.5 and MiniGPT-v2 "can hardly interpret the marks," so SoM is not a general LMM technique in this paper, only a GPT-4V one.

## Harness relevance
This is a PROMPTING METHOD, not an agent system, but it is the key enabler that later GUI agents adopt. Adapting the harness lens:
- Environment / workspace: a single static image (or two images for video / cross-frame). No interactive environment, no episodic loop. The "GUI-agent" framing is the reader's extrapolation; the paper's own agentic gestures are one-shot Q&A over screenshots/floor-plans (pages 21-23).
- Observation interface: the marked image I_m. The segmentation+numbering overlay IS the observation transform -- it converts raw pixels into a finite menu of labeled regions. This is the load-bearing idea for GUI agents: a screenshot becomes an enumerated set of clickable candidates.
- Action interface: "pick a mark." The model outputs a mark id (e.g. "the laptop turned on: 2", page 7), which dereferences to a region/mask. For a GUI agent this becomes "click element N" -- grounding collapses to discrete selection over a candidate set rather than coordinate regression.
- Tool / API / GUI layer: an off-the-shelf segmentation toolbox (SEEM [65], SAM [19], Semantic-SAM [21], MaskDINO [24]) proposes regions at selectable granularity, automatic or interactive (page 4). A mark-allocation algorithm (page 5) places each id via distance transform on the area-sorted, overlap-excluded mask, so marks do not collide -- the practical detail that makes dense overlays usable as click targets.
- Planner / executor / verifier / search: none. Single forward call per question; "for each question, we use a new chat window to avoid context leakage" (page 5, page 8) -- no memory, no multi-step planning.
- Evaluation harness: manual. No API; authors "exhaustively send the SoM augmented images to the ChatGPT interface" with a "divide-and-conquer strategy" (page 8). Subsampled benchmarks (Table 1, page 8).
- Training harness: none. "We do not need to train any models" (page 8); all results zero-shot.
- Logging / trace / reproducibility: the region<->mark<->text triplet is itself the trace linking a textual decision back to a pixel region. No automated logging framework.
- Safety / permission: none. (Notably page 18 shows SoM helping GPT-4V solve a CAPTCHA, which is a latent safety concern the paper does not discuss.)

## Method
1. Image partition (page 3-4): segment I (H x W) into K binary masks R = [r_1..r_K] using a suite of segmentation models chosen for strong performance (MaskDINO), open vocabulary (SEEM), and granularity incl. parts (SAM, Semantic-SAM). Granularity and automatic/interactive mode are user-selectable.
2. Mark generation (page 4-5): pick a mark TYPE (alphanumeric primarily, read via GPT-4V OCR; optionally box and mask-boundary), chosen image-dependently to avoid conflicts (e.g. avoid numeric marks on arithmetic images). Pick mark LOCATION via the Mark_Allocation algorithm (Fig. 5): sort regions ascending by area, exclude area covered by earlier masks, then distance-transform to place the mark at the point maximally far from boundaries; nudge off tiny regions.
3. Interleaved prompt (page 5): either a plain text prompt (GPT-4V auto-grounds on marks with no mark mentioned in text) or an interleaved prompt that injects mark ids directly as symbolic references.
4. SoM for vision (page 6-7): trace marks back to masks to support open-vocab segmentation, referring expression segmentation/comprehension, phrase grounding, and video object segmentation.

## Experimental setup
- Datasets (Table 1, page 8), all SUBSAMPLED due to GPT-4V quota: COCO (100 img / 567 inst, generic seg, Precision), ADE20K (100 / 488, OV seg, Precision), Flickr30K (100 / 274, phrase grounding, Recall@1), RefCOCO (100 / 177, RES mIoU and REC ACC@0.5), DAVIS (71 / 157, VOS, J&F). Note Table 1 says RefCOCO while the results table and text say RefCOCOg -- minor inconsistency (page 8 vs page 9).
- Baselines (page 8): GPT-4V predicting raw coordinates; specialist SOTA (MaskDINO, OpenSeeD, Grounding DINO, GLIPv2, PolyFormer, SEEM, SegGPT); open/closed LMMs (LLaVA-1.5, MiniGPT-v2, Shikra, Ferret, RedCircle, FGVP). Specialist numbers marked with * are from original papers on FULL val sets; SoM numbers are on the subsampled sets -- so the comparisons are NOT strictly apples-to-apples except where the authors re-ran the baseline on their subset.
- Model: GPT-4V via the ChatGPT web interface, numeric marks for main results, zero-shot.
- Metrics: per task above. No variance / repeated-trial reporting.

## Key results
VERIFIED against Table 2 (page 9), GPT-4V + SoM:
- OV/Generic Segmentation: COCO Precision 75.7 (vs fine-tuned MaskDINO 80.7 -- close, page 9); ADE20K 63.4 (vs zero-shot OpenSeeD 23.4 -- much higher).
- RefCOCOg REC (ACC@0.5): GPT-4V raw coordinates 25.7 -> SoM 86.4. This is the headline gain (+60.7 absolute) and beats specialists GDINO 86.1 and PolyFormer 85.8 and LMMs Shikra 82.6, MiniGPT-v2 84.4, Ferret 85.8, LLaVA-1.5 63.3.
- RefCOCOg RES (mIoU): SoM 75.6, vs PolyFormer 67.2 and SEEM 65.7 (re-run on the authors' subset). CLAIMED "outperforms PolyFormer by a large margin" (page 9) -- supports the abstract's claim of beating a fully-finetuned referring-segmentation model in zero-shot.
- Phrase Grounding Flickr30K (R@1): SoM 89.2, "comparable" to GLIPv2 87.7* and below GDINO 90.5 (page 9).
- VOS DAVIS2017 (J&F): SoM 78.8, best among generalist vision models, vs SegGPT 75.6 (page 10).
Ablations:
- Mark type (Table 3, page 9): Number+Mask 84.4 -> Number+Mask+Box 89.2 on Flickr30K (R@1) -- adding boxes "improves significantly."
- Golden mark location (Table 4, page 9-10): replacing predicted masks with GT masks raises RefCOCOg RES from 75.6 (MaskDINO masks) to 90.1 (GT masks), i.e. +14.5 mIoU -- shows much of the residual error is segmentation-proposal quality, not GPT-4V grounding.
Qualitative (page 10): GPT-4V+SoM corrects some erroneous "golden" dataset annotations (Fig. 8), and the center-of-region mark placement is "not always best."

## Evidence quality
- Strong directional signal: the 25.7 -> 86.4 REC jump is large and internally consistent (same model, same subset), and the GT-mask ablation cleanly attributes residual error to proposals. These two are the most trustworthy results.
- Weak statistical rigor: all benchmarks are tiny subsamples (71-100 images) run manually through a web UI, no API, no seeds, no repeated trials, no confidence intervals. CLAIMED SOTA-beating comparisons mix subset numbers (SoM) with full-val numbers (* baselines from papers), so several head-to-head wins are not strictly comparable; the authors flag this with * but the abstract states the win unqualified.
- Selection / construction risk: the authors choose segmentation tools and mark types per task and per image ("dynamically determining which type of mark to use is important," page 10), which is human-in-the-loop tuning that inflates zero-shot framing.
- No ablation on number of regions K, on plain vs interleaved prompt quantitatively, or on why GPT-4V works but open LMMs do not (left as hypotheses: scale + data curation, page 11-12).

## Reproducibility and artifacts
- Code: CLAIMED public at https://github.com/microsoft/SoM (page 1). Playground: https://som-gpt4v.github.io/.
- Data: subsampled COCO/ADE20K/Flickr30K/RefCOCOg/DAVIS; exact image ids Not reported in extraction.
- Models: GPT-4V (ChatGPT web UI, no API at the time); segmentation tools SEEM, SAM, Semantic-SAM, MaskDINO, Grounding DINO publicly available.
- Environment: manual ChatGPT interface, "divide-and-conquer" across authors (page 8).
- License: Not reported.
- Exact commands or setup: thresholds given for phrase grounding (GDINO box threshold 0.27, then SAM mask per box; alpha=0.4/0.2 for COCO/ADE20K overlays, page 9). Prompt templates shown by example (Fig. 7) but no full prompt logs in extraction.
- Missing details: per-image prompts, exact subset composition, run-to-run variance.

## Strengths
- A genuinely simple, training-free idea with a large measured effect on the hardest capability gap of GPT-4V.
- The pick-a-mark formulation is the right abstraction: it decouples grounding into (segmentation proposals) + (discrete selection), each independently improvable -- evidenced by the GT-mask ablation.
- Broad task coverage (segmentation, REC/RES, phrase grounding, VOS) plus a rich appendix of agentic/embodied use cases (controller, platformer, floor-plan navigation, CAPTCHA).
- Mark-allocation algorithm is a small but real engineering contribution enabling dense overlays.

## Weaknesses and limitations
- Tiny, manually-run, subsampled benchmarks; comparisons partly non-apples-to-apples (authors' own caveat, Table 2 footnote).
- GPT-4V-specific and unexplained; does not transfer to the open LMMs tested (page 11).
- Human-in-the-loop mark/tool selection undercuts the "zero-shot" framing.
- Depends entirely on external segmentation quality; degrades when proposals miss regions (Table 4).
- No safety analysis despite demonstrating CAPTCHA solving (page 18).
- Not an agent: no closed-loop action, no environment, no planning/verification -- the GUI-agent value is potential, realized by later work, not by this paper.

## Relationship to prior work
- Closest visual-prompting predecessors: RedCircle [41] and FGVP [48] (single-object overlays for CLIP) and the GPT-4V "dawn of LMMs" report [49] (hand-drawn circles/arrows). SoM's genuine novelty is many speakable, automatically-placed marks enabling dense multi-object grounding, vs the one/few-object, non-speakable marks of prior work (page 2, page 11). Table 2 shows SoM REC 86.4 vs RedCircle 59.4 and FGVP 63.3.
- Builds directly on the authors' own segmentation lineage (SEEM, Semantic-SAM, MaskDINO, X-Decoder, OpenSeeD) -- SoM is a way to wire those into GPT-4V without training.
- Conceptually links text prompting (CoT/ToT [46,52]) to visual prompting: "prompting the model to look location-by-location" but with no in-context examples (page 11).

## What I should read
- Must read: Section 2 (pages 3-5, the method + mark-allocation algorithm) and Table 2 (page 9, the numbers).
- Skim: Section 4.3 ablations (Tables 3-4) and the Discussion (pages 11-12) on why it works.
- Skim for harness relevance: Appendix use cases pages 21-23 (controller, platformer, navigation) -- these prefigure the GUI-agent application.
- Can skip: the reference list and the many full-page qualitative dialogues (pages 17-20) once the pattern is clear.
- Follow-up papers: SEEM [65], Semantic-SAM [21], SAM [19] for the segmentation side; and later GUI/computer-use agents that adopt set-of-mark click targets (not in this paper's refs).

## Triage decision
Label: READ_SOON
Rationale: Foundational, widely-adopted prompting primitive whose pick-a-mark grounding became the standard click-target mechanism for GUI/computer-use agents. Method is short and high-leverage to understand. Evidence is directionally strong (25.7 -> 86.4 REC) but methodologically light (tiny manual benchmarks, mixed comparisons), so it warrants reading but not MUST_READ-level deep scrutiny. Evidence does not strongly differ from the prior label.
Confidence: high
Reading time estimate: 35-45 min (method + Table 2 + appendix use cases).

## Personal notes
The single most reusable abstraction here for the harness: segmentation+numbering turns grounding into discrete selection over an enumerated candidate set, removing the LMM's coordinate-regression weakness. For GUI agents the analogue is overlaying ids on accessibility-tree elements / detected UI components and having the model output "click N." Watch the GT-mask ablation (75.6 -> 90.1): in a GUI setting the equivalent ceiling lift comes from a clean element detector, so candidate-set quality, not the LLM, is often the bottleneck.

## Follow-up actions
- Add related paper: SEEM (2304.06718), Semantic-SAM (2307.04767), SAM (Kirillov 2023).
- Compare with: later GUI-agent papers using set-of-mark click targets.
- Re-run after new version: v2 already the fetched version (6 Nov 2023); watch for journal/CVPR extension.
- Check code: https://github.com/microsoft/SoM.
- Read benchmark details: exact subset composition for RefCOCOg REC/RES and Flickr30K.
