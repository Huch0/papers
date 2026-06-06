# Ferret-UI: Grounded Mobile UI Understanding with Multimodal LLMs

## Metadata
- Canonical key: arxiv-2404.05719
- Version: v1
- Fetch date: 2026-06-06T07:57:28Z
- Source: arxiv
- PDF: library/ferret-ui-grounded-mobile-ui-understanding-with-240405719/v1/paper.pdf
- Venue: European Conference on Computer Vision
- Year: 2024
- Authors: Keen You, Haotian Zhang, E. Schoop, Floris Weers, Amanda Swearngin, Jeffrey Nichols, Yinfei Yang, Zhe Gan
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
Ferret-UI adapts the Ferret referring-and-grounding MLLM to mobile UI screens by adding an "any-resolution" sub-image split and curating template-/GPT-generated training data over 11 elementary and advanced UI tasks, yielding a self-contained (raw-pixel input) model that surpasses GPT-4V on elementary referring/grounding tasks.

## Why this paper matters
This is one of the early, influential demonstrations that a single MLLM can do fine-grained UI perception (referring + grounding) directly from screen pixels, without external accessibility trees, view hierarchies, or detection modules at inference time. For anyone studying mobile/GUI agents, it is a foundational "perception backbone" paper: the elementary tasks (OCR, icon recognition, widget classification, find-X, widget listing) define the low-level capabilities a downstream agent needs before it can plan or act. The any-resolution trick (p.5-6) is a concrete answer to the recurring problem that UI screens are elongated and dominated by tiny elements, and the data-generation recipe (template + GPT-4/GPT-3.5) is widely reused. It is Apple-authored and built on Apple's own AMP/Screen-Recognition detection stack (p.6-7), which is both a strength (high-quality annotations) and a coupling concern.

## Problem and gap
CLAIMED problem (p.2-3): general-domain MLLMs cannot reliably comprehend or act on UI screens; a UI system must both comprehend the whole screen and focus on specific elements, mapping language to actions and locations. The paper frames this as needing both *referring* (region in the input) and *grounding* (region in the output).

EVIDENCE for the gap (p.3): (i) natural-image grounding MLLMs (Ferret, Shikra, Kosmos2) are restricted to natural images and lose detail when UI screens are resized to a low-resolution global image; (ii) UI-targeted works either process whole screens as single inputs (Pix2Struct, ILuvUI, CogAgent), support only one input bounding box (Spotlight), or lean on GPT-4V navigation (MM-Navigator, AppAgent, MobileAgent), and none covers all dimensions of UI understanding. Two concrete motivating measurements are given (p.6): UI screens have more elongated aspect ratios (Tab. 1a) and many target elements (icons) occupy <0.1% of the screen.

## Core idea
Two extensions to Ferret (p.5-6):
1. Architecture — "any-resolution" (anyres). Beyond Ferret's global image features, each screen is resized to one of two pre-defined grids, 1x2 or 2x1, chosen by aspect ratio, then split into 2 sub-images (portrait split horizontally, landscape split vertically). Each sub-image is encoded separately by the same CLIP-ViT-L/14 encoder; the LLM (Vicuna decoder) consumes global features + sub-image features + region features (from Ferret's spatial-aware visual sampler) + text (Fig. 2, p.5). The sub-images "magnify details" of small elements.
2. Data — define UI referring/grounding tasks and generate instruction-following data with region annotations, then add GPT-4-generated advanced reasoning tasks.

Note: the split is into exactly 2 sub-images (VERIFIED against abstract and p.6), not a larger NxM grid; only 1x2 and 2x1 configurations are used.

## Harness relevance
This is a *perception* MLLM, not a full agent loop, but it is the observation layer that mobile agents sit on.
- Environment / workspace: static single mobile UI screenshots (iPhone via AMP dataset; Android via RICO/Spotlight subset). No live device interaction or multi-step navigation in this paper.
- Observation interface: raw screen pixels only (CLAIMED "self-sufficient, taking raw screen pixels as model input," p.6). At inference no view hierarchy / accessibility file is needed. Input = global image + 2 anyres sub-images; regions can be referred to as point, box, or scribble (Fig. 1, p.2).
- Action interface: none executed. "Actions" appear only as text — interaction conversations propose goal-oriented actions and function inference deduces screen purpose; outputs include grounded bounding boxes (raw coordinates). UNCLEAR how these map to real device events; no actuator is implemented.
- Tool/API/GUI layer: training-time only — a pre-trained pixel UI detection model (Screen Recognition / AMP, ref [58]) plus Apple Vision Framework OCR produce element type + bbox + text; heuristics group detections (p.7). At inference the model does not call these.
- Planner/executor/verifier/search: none. Single-turn or multi-turn QA; no search or verifier.
- Evaluation harness: a benchmark of 14 mobile UI tasks (3 Spotlight tasks + dual iPhone/Android versions of the 11 elementary+advanced tasks; p.4, p.9). Grounding scored by IoU>0.5 accuracy; referring by (exact-match) accuracy; Spotlight by CIDEr (S2W, WiC) and F1 (TaP); advanced tasks scored by GPT-4 as prediction-score / label-score percentage (p.10-11).
- Training harness: instruction-following format, same objective as Ferret; vision encoder frozen, decoder + projection updated; total training mixture 250K samples; Ferret-UI-base ~1 day, Ferret-UI-anyres ~3 days on 8 A100 GPUs (p.10).
- Logging/trace/reproducibility: Not reported (no released code/weights mentioned; data built on internal AMP detector).
- Safety/permission mechanism: Not reported.
How it underpins downstream agents: the elementary tasks instill spatial+semantic grounding of icons/text/widgets; ablations (Tab. 4a) show this foundation measurably lifts advanced reasoning, supporting the paper's framing of elementary tasks as the substrate for higher-level UI interaction and, by extension, for agents that must select and act on specific elements.

## Method
- Base model: Ferret (CLIP-ViT-L/14 encoder + Vicuna decoder + spatial-aware visual sampler for region features) (p.5).
- Anyres: grids 1x2 / 2x1; per-aspect-ratio selection; 2 sub-images encoded separately; features fused with global + region + text in the LLM (p.6, Fig. 2).
- Data collection (p.6-9):
  - Android: subset of RICO via Spotlight tasks (screen2words, widget captions, taperception) — 26,527 train / 3,080 test images.
  - iPhone: AMP dataset subset — 84,685 train / 9,410 test images (resolution breakdown in Tab. 1a).
  - Element annotations from a pixel UI detector + Apple Vision OCR, with grouping heuristics.
- Task construction (3 routes):
  1. Reformatting Spotlight tasks into conversational QA (GPT-3.5 Turbo prompt variants).
  2. Elementary tasks (template-based, GPT-3.5 for prompt variants): 7 tasks per platform — referring: OCR, icon recognition, widget classification; grounding: widget listing, find text, find icon, find widget. ~40k samples each per task (Tab. 1b).
  3. Advanced tasks (GPT-4-generated, iPhone-only, images not sent to GPT-4): detailed description, conversation perception, conversation interaction, function inference; ~10k each (Tab. 1b); 40K valid conversations total.
- Benchmark: 14 tasks; advanced test sets tiny (e.g., 56 unique iPhone images, 13 Android; 20/40/38/20 iPhone and 5/10/10/10 Android questions for the four advanced tasks — p.9).

## Experimental setup
- Datasets/benchmarks: own splits over RICO/Spotlight (Android) and AMP (iPhone); 3 public Spotlight tasks; 11 self-defined tasks dual-platform; UIBert REC for a zero-shot check.
- Baselines: Spotlight (Spotlight tasks only), Ferret (base, natural-image), GPT-4V (with Set-of-Mark prompting), and on advanced tasks Fuyu-8B and CogAgent.
- Models compared: Ferret-UI-base, Ferret-UI-anyres.
- Metrics: CIDEr (S2W, WiC), F1 (TaP), accuracy / exact-match (referring), IoU>0.5 accuracy (grounding), GPT-4 relative score (advanced). Widget listing excluded from elementary average (auxiliary).
- Compute: 8 A100, 1 day (base) / 3 days (anyres); 250K-sample mixture.
- GPT-4V caveats (p.10 footnotes): only 100 random instances sampled for Spotlight+elementary; SoM overlays indexed boxes so GPT-4V *selects* candidate boxes for grounding rather than generating coordinates.
- Artifacts: Not reported (no code/data/model release stated).

## Key results
VERIFIED against Tab. 2 (p.10):
- Elementary tasks (category averages), Ferret-UI-anyres vs GPT-4V:
  - Referring iPhone (Ref-i): 82.4 vs 61.3
  - Referring Android (Ref-A): 82.4 vs 37.7
  - Grounding iPhone (Grd-i): 81.4 vs 70.3
  - Grounding Android (Grd-A): 83.8 vs 4.7 (GPT-4V collapses on Android grounding — many small widgets, SoM degrades)
  - Ferret-UI-base counterparts: 80.5 / 82.4 / 79.4 / 83.5. Base Ferret: 13.3 / 13.9 / 8.6 / 12.9.
  - So Ferret-UI surpasses GPT-4V on all four elementary category averages (CLAIM "surpasses GPT-4V on all the elementary UI tasks" holds at the *average* level; the text notes one per-task exception — iPhone find text — p.11, EVIDENCE in per-task Fig. 5, not in extracted numbers).
- Spotlight (public) tasks, Ferret-UI-anyres / base vs Spotlight baseline:
  - S2W (CIDEr): 115.6 / 113.4 vs 106.7
  - WiC (CIDEr): 140.3 / 142.0 vs 141.8
  - TaP (F1): 72.9 / 78.4 vs 88.4 — Ferret-UI is *below* Spotlight on TaP; authors attribute this to noisy taperception labels (Appendix C: human labels agree 76% with GPT-4V but only 8% with the dataset label).
  - Notable since Spotlight pre-trains on 80M web + 2.69M mobile screenshots (p.10).
- Anyres effect: with anyres added to base, iPhone referring and grounding improve by ~2 points (p.11, VERIFIED: 80.5->82.4 Ref-i, 79.4->81.4 Grd-i). Advanced iPhone tasks jump ~20 points (73.4->93.9, Tab. 3) but Android advanced *drops* (80.5->70.1) because no Android advanced data is in training.
- Advanced tasks (Tab. 3): GPT-4V still scores highest overall (iPhone avg 114.3, Android 128.2 — these exceed 100 because GPT-4V's verbose answers outscore the reference under GPT-4 judging). Ferret-UI-anyres iPhone avg 93.9 beats CogAgent (64.9) and Fuyu (21.0).
- Zero-shot UIBert REC framed as find-widget: 76% (p.11).
- Grounded conversation-interaction box accuracy (manual grading): Ferret-UI 91.7% vs GPT-4V 93.4%, despite Ferret-UI emitting raw coordinates vs GPT-4V choosing from predefined boxes (p.15).

## Evidence quality
- Elementary-task superiority over GPT-4V is the strongest, well-supported claim, but the GPT-4V comparison is not apples-to-apples: GPT-4V is evaluated on only 100 sampled instances and, for grounding, is forced into SoM candidate selection, which the authors themselves show fails on dense Android screens. So the dramatic Grd-A gap (83.8 vs 4.7) partly reflects a prompting limitation of the GPT-4V harness rather than pure model capability — worth flagging.
- Advanced-task evaluation uses GPT-4-as-judge on very small test sets (tens of questions; 13 unique Android images), and the judge favors verbosity (authors acknowledge, p.12, p.15), making scores >100 and cross-model comparisons noisy. UNCLEAR statistical significance; no variance/CIs reported anywhere.
- The "raw pixels only" self-sufficiency claim is true at inference, but the entire training signal is bootstrapped from a proprietary UI detector, which is explicitly called a bottleneck (p.16): the model cannot learn anything the detector misses (colors, design, status-bar icons).
- Ablations (Tab. 4a/4b) are solid and support the elementary->advanced transfer hypothesis (advanced-only 64% -> +both elem. 73.4 iPhone / 80.5 Android).

## Reproducibility and artifacts
- Code: Not reported.
- Data: Built on RICO/Spotlight (public) and AMP (Apple internal); generated splits and GPT-generated data not stated as released. Apple Vision Framework + Screen Recognition detector are dependencies.
- Models: No weight release mentioned.
- Environment: 8x A100; Ferret/Vicuna/CLIP stack.
- License: Not reported.
- Exact commands/setup: Not reported (training objective "same as Ferret"; 250K mixture; sampling ratios from the elementary pool "in experiments" but exact ratios Not reported).
- Missing details: sampling ratios, exact data sizes after filtering, GPT-4 judge prompt for scoring (advanced-task generation prompts are in Appendix D but scoring prompt is Unclear), per-task elementary numbers only in Fig. 5 (not in extracted text).

## Strengths
- Clean, transferable architectural idea (anyres 2-split) directly targeting the elongated-screen / tiny-element problem, with measured gains.
- Comprehensive task taxonomy (11 tasks, referring + grounding + reasoning) and a matching 14-task benchmark — useful as a capability checklist for UI agents.
- Inference-time self-sufficiency (raw pixels, no view hierarchy).
- Honest analysis sections (OCR/widget/find-text failure modes, detector bottleneck, SoM limitations, taperception label noise).
- Strong, well-isolated ablations showing elementary->advanced and advanced->Spotlight positive transfer.

## Weaknesses and limitations
- Author-stated: UI detection model is a hard ceiling on what the model can perceive (p.16); only tap actions covered in interaction data (other actions like scroll/long-press/text-entry are future work, Appendix B); Android advanced performance regresses with anyres due to missing Android advanced training data.
- Inferred: not an agent — no execution, no multi-step navigation, no real-device evaluation; advanced-task test sets are tiny and GPT-4-judged (favoring verbosity); GPT-4V baseline handicapped by SoM forcing, so headline "surpasses GPT-4V" should be read with that caveat; no released artifacts limit reproducibility; coupling to Apple-internal AMP/detector.

## Relationship to prior work
- Directly extends Ferret [53] (refer/ground on natural images) into the UI domain.
- Anyres borrowed from SPHINX [16,33], LLaVA-NeXT [36], Monkey [32].
- Advanced-task data recipe follows LLaVA [37] (GPT-generated instruction data).
- Contrasts with: Spotlight [30] (single input box, no grounding output), Pix2Struct/ILuvUI/CogAgent (whole-screen, limited referring/grounding), GPT-4V-as-agent works (MM-Navigator, AppAgent, MobileAgent). Genuinely new: first UI-centric MLLM combining referring + grounding + reasoning from raw pixels with the anyres split and the dual-platform 11-task data/benchmark. Incremental aspects: architecture is Ferret+anyres (both pre-existing); data recipe is LLaVA-style.

## What I should read
- Must read: Sec. 3 + Fig. 2 (anyres architecture); Sec. 4 (data/task formulation, Tab. 1); Tab. 2 + Sec. 5.1 (main results, esp. elementary vs GPT-4V).
- Skim: Sec. 5.2 ablations (Tab. 4); Sec. 5.3-5.4 qualitative failure analyses; Appendix A (elementary data rules) and Appendix E (GPT-4V eval setup, to judge the baseline fairness).
- Can skip: full reference list; Appendix F example outputs.
- Follow-up papers: Ferret [53], Spotlight [30], CogAgent [20], SeeClick [9], ScreenAI [4], Set-of-Mark [50].

## Triage decision
Label: READ_SOON
Rationale: Foundational mobile-UI perception MLLM that defines the referring/grounding capability set underpinning downstream GUI agents; the anyres split and data-generation recipe are directly reusable. Evidence is solid on elementary tasks (VERIFIED Ferret-UI-anyres >> GPT-4V on all four category averages, e.g. Grd-A 83.8 vs 4.7) though the GPT-4V baseline is handicapped and advanced-task eval is small/GPT-judged. Evidence does not strongly differ from the assigned label, so kept at READ_SOON.
Confidence: high
Reading time estimate: 45-60 min for the core (Sec. 3-5 + Tab. 1-4).

## Personal notes
Key mental model: Ferret-UI = Ferret + 2-way anyres split + UI instruction data. It is the *eyes* for a mobile agent, not the agent. The detector-bootstrapped training is the main caveat to remember when reasoning about its ceiling. The Grd-A 83.8 vs 4.7 number is striking but is as much about SoM-forced GPT-4V failing on dense screens as about Ferret-UI's strength.

## Follow-up actions
- Add related paper: SeeClick, ScreenAI, Ferret v2 (if in scope).
- Compare with: CogAgent, Spotlight, GPT-4V-as-agent navigation papers.
- Re-run after new version: check for Ferret-UI 2 / released weights.
- Check code: no release found in v1 — verify if later released.
- Read benchmark details: Sec. 4.2 + Appendix A/E for exact task construction and GPT-4V eval fairness.
