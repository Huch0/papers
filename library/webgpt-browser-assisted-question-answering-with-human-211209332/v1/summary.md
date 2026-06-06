# WebGPT: Browser-assisted question-answering with human feedback

## Metadata
- Canonical key: arxiv-2112.09332
- Version: v1
- Fetch date: 2026-06-06T07:57:31Z
- Source: arxiv
- PDF: library/webgpt-browser-assisted-question-answering-with-human-211209332/v1/paper.pdf
- Venue: arXiv.org (preprint; v3 dated 1 Jun 2022, p.1)
- Year: 2021
- Authors: Reiichiro Nakano, Jacob Hilton, Suchir Balaji, Jeff Wu, Long Ouyang, Christina Kim, Christopher Hesse, Shantanu Jain, Vineet Kosaraju, William Saunders, Xu Jiang, Karl Cobbe, Tyna Eloundou, Gretchen Krueger, Kevin Button, Matthew Knight, Benjamin Chess, John Schulman (OpenAI)
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
WebGPT fine-tunes GPT-3 to operate a bespoke text-based web browser for long-form question answering, training it via behavior cloning on human browsing demonstrations and then optimizing answer quality against a learned reward model (via rejection sampling and RL), with the model required to collect inline references so humans can judge factual accuracy.

## Why this paper matters
This is one of the foundational "LLM as a tool-using agent" papers and a direct precursor to the retrieval-augmented, citation-producing assistants (ChatGPT browsing, Bing/Copilot, Perplexity) that became mainstream. For a harness-focused reader it is a clean early template for three patterns now ubiquitous: (1) defining an agent's environment as a textual observation plus a small discrete command vocabulary so a plain language model can act in it; (2) the RLHF pipeline (demonstrations -> reward model -> RL / rejection sampling) applied to a multi-step interactive task rather than single-shot generation; and (3) requiring the agent to surface evidence (quotes/citations) specifically to make human evaluation tractable. It also pre-dates and complements InstructGPT (same RLHF lineage, Stiennon et al. 2020 summarization work is the explicit ancestor, p.1, p.4).

## Problem and gap
- Problem: long-form question answering (LFQA) — generating a paragraph-length answer to an open-ended question — where systems lagged human performance (Intro, p.1, citing Krishna et al. 2021).
- Gap in prior work: existing retrieval-augmented QA (REALM, RAG, DPR) frames retrieval as a *differentiable* inner-product search over a fixed corpus and targets short answers (Related work, p.11-12). That is fast to optimize but (a) cannot use a real search engine / non-differentiable browsing actions and (b) is less interpretable. Automated LFQA metrics like ROUGE-L are shown to be meaningless on ELI5 (Krishna et al. 2021), motivating a switch to human comparison as the primary metric (p.12).
- The authors' framing: rather than improving retrieval or synthesis components, "combine them using more faithful training objectives" (Intro, p.1) — i.e., let a human-imitating, human-feedback-optimized model drive a real search engine.

## Core idea
Set up question answering as a task a *human* can perform inside a constrained text browser, collect human browsing trajectories, and imitate then improve on them. The model never sees raw HTML or a GUI; at each step it receives a text summary of browser state (question, current page text at the cursor, past-action summary) and emits exactly one command from a fixed set (Table 1, p.3). Document retrieval is outsourced to the Bing Web Search API; synthesis comes from GPT-3's pretrained capabilities. Crucially, while browsing the model must issue Quote commands that capture page extracts; these become the references attached to the final answer, which is what lets human labelers judge factual accuracy without doing independent research (key contribution #2, p.2).

## Harness relevance
- Environment / workspace: a bespoke text-based web-browsing environment, mostly Python with some JavaScript (Appendix A, p.15). State is reset to a fresh context each step, so the only "memory" is what is serialized into the observation (Section 2, p.3) — the agent is effectively stateless/Markov over the text summary.
- Observation interface: a written text summary of browser state shown to the model (Figure 1b, p.2): question, current page title, scrollbar position, current page text at the cursor, a summary of past actions, quotes collected so far, and actions-left counter. Pages are produced by sending Bing results or fetched HTML (simplified via Mozilla Readability.js, then html2text) into a simplified text page; links are rendered in a special bracketed format with numeric link IDs (Appendix A, p.15).
- Action interface: a fixed command vocabulary (Table 1, p.3) — Search <query>, Clicked on link <ID>, Find in page: <text>, Quote: <text>, Scrolled down/up <1,2,3>, Top, Back, End: Answer, End: <Nonsense, Controversial>. Any other generated text counts as an invalid action (still consumes the action budget). After ending browsing, the model is reprompted with the question plus collected quotes and must compose the final answer.
- Tool/API layer: Microsoft Bing Web Search API for retrieval (Intro, p.1); Node.js fetch + Readability.js for page simplification; pdfminer.six for PDFs (Appendix A, p.15). reddit.com and quora.com results/links are stripped to stop answer-copying; pages with a 10-gram overlap with the question/reference are censored to prevent cheating (Appendix A, p.15).
- Planner/executor/verifier structure: no explicit separate planner — the single fine-tuned policy interleaves browsing (executor) and a final answering phase. The reward model acts as a verifier/ranker over completed answers (used both for RL reward and for best-of-n selection).
- Reference/citation mechanism (the load-bearing design choice): Quote actions record (page title, domain, extract) as references; the final answer cites them. This is the mechanism that makes factual-accuracy labeling tractable and is presented as central to the approach (Section 6.4, p.11).
- Evaluation harness: primarily human pairwise comparisons (same protocol as RM training data) — WebGPT vs. human demonstrators on ELI5; WebGPT (references stripped, new contractors, minimal instructions) vs. ELI5 highest-voted Reddit answers; plus TruthfulQA (human eval for WebGPT, automated metric for GPT-3 baselines) and TriviaQA exact-match (Appendix G). Ties counted as 50% preference.
- Training harness: four methods (Section 3.2, p.4) — (1) Behavior cloning / supervised fine-tuning on demonstrations; (2) Reward modeling from comparisons (Elo-style scalar, cross-entropy loss, ties as soft 50% labels); (3) RL via PPO against the RM with a per-token KL penalty from the BC model to limit overoptimization; (4) Rejection sampling (best-of-n, n in {4,16,64}) selecting the RM-highest answer. Best model = BC + rejection sampling.
- Logging/trace/reproducibility: the entire browsing process is inspectable, which the authors cite as a transparency benefit (Section 6.4, p.11). A comparison dataset is released (see below). Full training code is NOT released.
- Safety/permission mechanism: the action space is the permission boundary — the only outside-world interactions allowed are Bing queries and following existing links; no forms, so actions like editing Wikipedia are not available (Section 6.5, p.11). Authors note RL could reinforce such exploits if available, and propose escalating "burden of proof of safety" and tripwire tests as models get more capable.

## Method
- Data collection (Section 3.1, p.3; Appendix B, p.16): ~6,000 demonstrations (92% ELI5) and ~21,500 comparisons (98% ELI5), the rest from TriviaQA, ARC, ELI5-fact-check, and hand-written questions. Exact Table 4 totals: 6,209 demonstrations and 21,548 comparisons (ELI5: 5,711 demos / 21,068 comparisons). Demonstrations averaged ~15 min, comparisons ~10 min; collected via Upwork (~25%, 10 contractors) and Surge AI (~75%, 46 contractors); top 5 contractors gave ~50% of data (Appendix C, p.17). Researcher-labeler agreement 74%, labeler-labeler 73%.
- Comparisons used only the final overall-usefulness rating in training (5-point Likert collapsed to better/worse/equal); a richer per-claim annotation procedure was collected but auxiliary-loss experiments did not improve RM validation accuracy (Appendix C.2, p.18).
- Models: GPT-3 family at 760M, 13B, and 175B parameters (Section 3.2, p.4).
- Training pipeline: BC -> RM (BC model with unembedding removed -> scalar) -> RL (PPO) and/or rejection sampling. Disjoint question sets for BC/RM/RL; ~4% of demos held out for BC validation; final RMs trained on ~16,000 comparisons (remaining ~5,500 for eval). RL trained on 90% ELI5 / 10% TriviaQA with 15 extra answering-only episodes per browsing episode for ~2x sample efficiency, and randomized 20-100 max browsing actions (Section 3.2/p.5).
- Three headline "WebGPT" models, each BC + best-of-n at matched size, chosen from the Pareto/compute-efficient frontier (Figure 8, p.9): 760M best-of-4, 13B best-of-16, 175B best-of-64. Eval temperature 0.8, max 100 browsing actions (Section 4, p.5). RL excluded from the headline models because it gave no significant benefit on top of rejection sampling (Figure 4).

## Experimental setup
- Datasets/benchmarks: ELI5 (primary, Fan et al. 2019); TruthfulQA (Lin et al. 2021, adversarial short-form); TriviaQA (short-form, Appendix G).
- Baselines: human demonstrators (browser-based answers); ELI5 highest-voted Reddit answers; Krishna et al. 2021 (prior LFQA system); base GPT-3 with "QA prompt" and "helpful prompt"; UnitedQA on TriviaQA.
- Metrics: human pairwise preference (% preferred, ties=50%); TruthfulQA % truthful and % truthful-and-informative; TriviaQA exact-match.
- Compute/cost: no FLOP/dollar totals reported. Relative scaling laws are given (see Key results); RM is an Elo where a 1-point gap ~= sigmoid(1) ~= 73% preference (p.8). Hyperparameters fully tabulated (Appendix E, Tables 5-8): e.g. BC minibatch 512, Adam step multiplier 0.1, up to 12 epochs (early-stopped at 2/5/3 for 760M/13B/175B); PPO with KL reward coefficient 0.02, 256 parallel envs.
- Artifacts: a comparison dataset of 19,578 comparisons released (Appendix K, p.32); an answer-viewer web page released. Bing API, GPT-3, training code: not released.

## Key results
All numbers below verified against the extraction.
- ELI5 vs. human demonstrators: 175B best-of-64 preferred 56% of the time (Abstract; Section 4.1, p.5). Interpreted by authors as human-level browser usage and evidence that human feedback (not imitation alone) is what pushes past 50%.
- ELI5 vs. highest-voted Reddit reference answer: 175B best-of-64 preferred 69% of the time, vs. 23% for Krishna et al. 2021's best model against the same references (Section 4.1, p.5). (References stripped, new contractors, minimal instructions for fairness.)
- TruthfulQA (175B): answers true 75% of the time and both true-and-informative 54% of the time (Intro, p.2; Figure 3). All WebGPT sizes beat all GPT-3 prompts on both metrics, and truthful-and-informative rises with model size for WebGPT (unlike GPT-3). Still below human performance.
- Method comparison (175B, Section 5.1, p.7): best-of-64 BC preferred 68% over plain BC; RL preferred 58% over BC; RL helps only when *not* also using rejection sampling (Figure 4), and combining RL + rejection sampling gives little gain over rejection sampling alone.
- Scaling (Section 5.2, p.8): doubling demonstrations raised policy RM score by ~0.13; doubling comparisons raised RM accuracy by ~1.8%; doubling policy params raised RM score by ~0.09; doubling RM params raised RM accuracy by ~0.4% (parameter trends noisier).
- TriviaQA (Appendix G, Table 9): GPT-3 175B + WebGPT 175B BC reaches 69.5% total exact match vs. 58.7% for GPT-3 175B alone and 68.9% for UnitedQA-E; slightly better than UnitedQA-E on no-overlap questions, slightly worse on overlap questions.
- Bias/truthfulness qualitative (Section 6, Appendix H): WebGPT sometimes quotes unreliable sources on out-of-distribution TruthfulQA questions; affirming-stance questions tend to elicit more inaccurate answers; "What does a wedding look like?" defaulted to Western/American framing (20 of 64 answers mentioned America/American).

## Evidence quality
- Strong where it counts: the central claims (beats demonstrators 56%, beats Reddit 69%, beats GPT-3 on TruthfulQA) are supported by human evaluations with reported standard errors (±1 SE error bars in Figures 2-5), and the authors take real care with the ELI5-reference comparison (stripping citations, fresh contractors, minimal instructions) to address blinding/ecological-validity concerns (Section 4.1, p.6). This is unusually careful for the era.
- Caveats the authors themselves flag: the 56%/69% headline preferences are *relative* to specific baselines, not absolute correctness; references can be cherry-picked to look convincing without being a fair assessment (Section 6.4, p.11); factual accuracy was hard for labelers to assess for subtle hallucinations, so reduced non-imitative falsehoods are argued indirectly rather than measured (Section 6.1, p.9).
- Limits a reader should note: the stance and reference-point-bias experiments are explicitly small-sample (60 questions; 64 answers to one question) and described as suggestive only (Appendix H). No automated/absolute factuality benchmark beyond TruthfulQA. RM Elo scaling numbers are internal-metric (validation RM score), which is a proxy that can be overoptimized — though the authors validate it against human preference for n<=64 (Figure 5, Appendix I). No compute/cost accounting, limiting reproducibility and cost-tradeoff judgment.

## Reproducibility and artifacts
- Code: Not released (environment described in Appendix A; no public training/browser code).
- Data: Comparison dataset released — 19,578 comparisons, GPT-2-tokenized prefix+completion with question, quotes, answer, and signed preference score (Appendix K, p.32). Demonstrations not released.
- Models: Not released (built on proprietary GPT-3 and Bing API).
- Environment: Depends on the paid Bing Web Search API and proprietary GPT-3; not reconstructable as-is from the paper alone, though the simplification pipeline (Readability.js, html2text, pdfminer.six) is described.
- License: Not reported.
- Exact commands/setup: Hyperparameters fully tabulated (Appendix E, Tables 5-8); no runnable commands.
- Missing details: total compute/cost, full demonstration data, model weights, exact Bing query handling beyond high-level description.

## Strengths
- Clean, influential formulation of an LLM agent: textual observation + small discrete command set + statelessness, which generalizes far beyond QA.
- End-to-end RLHF applied to a multi-step interactive task, with a careful BC-vs-RL-vs-rejection-sampling ablation that yields a non-obvious finding (rejection sampling beats RL here, with plausible mechanistic explanations).
- The reference/citation requirement is both a capability and an evaluation-tractability mechanism — a genuinely good idea that became standard.
- Honest, extensive discussion of failure modes (truthfulness, perceived authority/automation bias, bias reinforcement, live-web risks) and a released comparison dataset.

## Weaknesses and limitations
- Author-stated: still struggles on out-of-distribution questions; can quote unreliable sources; references can be cherry-picked; more authoritative-looking answers risk overreliance (automation bias); inherits and can reinforce GPT-3's biases and question framing.
- Inferred: heavy dependence on proprietary GPT-3 + paid Bing API plus unreleased code limits reproducibility; no compute/cost reporting; bias/stance experiments are small-sample and only suggestive; primary metric is relative human preference rather than absolute accuracy; reddit/quora and 10-gram censoring mitigate but do not eliminate train/eval contamination concerns; only English, ELI5-centric distribution.

## Relationship to prior work
- Directly builds on Stiennon et al. 2020 (learning to summarize from human feedback) — same RM/RL recipe extended from summarization to interactive browsing (p.1, p.4); and on GPT-3 (Brown et al. 2020) for synthesis.
- Contrasts with differentiable retrieval QA: REALM (Guu et al. 2020), RAG (Lewis et al. 2020a), DPR (Karpukhin et al. 2020) — those use end-to-end differentiable inner-product search over fixed corpora and short answers; WebGPT instead uses a non-differentiable real search engine and is more interpretable but cannot backprop through retrieval (Section 7, p.11-12).
- Closest in spirit: Krishna et al. 2021 (LFQA on ELI5, the main quantitative baseline) and RL-for-search/browsing work (Yuan et al. 2019; Adolphs et al. 2021; web-control via Shi et al. 2017, Gur et al. 2018).
- Genuinely new: combining a real search-engine browsing environment + imitation + human-feedback optimization + mandatory references in one end-to-end LFQA system that beats human demonstrators. Incremental parts: the underlying RLHF machinery and the use of Bing.

## What I should read
- Must read: Section 2 + Table 1 (environment and action set, p.3) and Appendix A (environment details, p.15) for the harness design; Section 3.2 (four training methods, p.4); Section 5.1 (RL vs rejection sampling finding, p.7).
- Skim: Section 4 (eval protocol and the 56%/69% results); Section 6.4 (why references aid evaluation); Appendix E (hyperparameters) if reproducing.
- Can skip: Appendix H stance/bias case studies and Appendix J full reference texts unless specifically interested; Appendix I estimator math unless implementing best-of-n prediction.
- Follow-up papers: Stiennon et al. 2020 (summarization RLHF); InstructGPT/Ouyang et al.; TruthfulQA (Lin et al. 2021); RAG/REALM for the retrieval contrast; later citation-grounded systems (GopherCite, Sparrow).

## Triage decision
Label: READ_SOON
Rationale: Foundational LLM-agent / RLHF-tool-use paper with a clean text-environment + command-set + reference-collection design that is directly relevant to harness work; evidence supports the headline claims without strongly contradicting the prior triage. Not elevated to MUST_READ only because the core ideas are now well-absorbed into the field, but it remains high-value primary source material.
Confidence: high
Reading time estimate: ~60-90 minutes for the main body (Sections 2-6); +30 minutes for Appendices A/E if reconstructing the harness.

## Personal notes
The most quotable harness insight: making the task human-performable (text browser + small command set) is what enables imitation learning to bootstrap the policy, and mandatory quoting is what makes human factuality labeling cheap enough to scale RLHF. The rejection-sampling-beats-RL result is a useful, transferable caution about reward-model overoptimization.

## Follow-up actions
- Add related paper: Stiennon et al. 2020 (summarization from human feedback); TruthfulQA.
- Compare with: RAG/REALM (differentiable retrieval) and later citation agents (GopherCite, Sparrow).
- Re-run after new version: current dir is v1 of the arxiv record (PDF is v3, Jun 2022); no further action needed unless a newer arxiv version appears.
- Check code: no official code; look for community reimplementations of the text-browser environment.
- Read benchmark details: ELI5 (Fan et al. 2019) and TruthfulQA construction for eval design.
