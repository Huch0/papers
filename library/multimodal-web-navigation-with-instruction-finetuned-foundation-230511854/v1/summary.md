# Multimodal Web Navigation with Instruction-Finetuned Foundation Models

## Metadata
- Canonical key: arxiv-2305.11854
- Version: v1
- Fetch date: 2026-06-06T07:57:30Z
- Source: arxiv
- PDF: library/multimodal-web-navigation-with-instruction-finetuned-foundation-230511854/v1/paper.pdf
- Venue: International Conference on Learning Representations
- Year: 2023
- Authors: Hiroki Furuta, Ofir Nachum, Kuang-Huei Lee, Yutaka Matsuo, S. Gu, Izzeddin Gur
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
WebGUM shows that a fully offline, imitation-trained multimodal agent (instruction-finetuned Flan-T5 encoder-decoder + ViT, consuming HTML + screenshots and emitting text actions) can beat prior offline SoTA, online RL SoTA, humans, and GPT-4 prompted agents on MiniWoB++, while transferring to WebShop and real-world Mind2Web.

## Why this paper matters
This is an early, foundational data-point for the now-dominant recipe of "web/computer-use agent = finetuned VLM over (HTML/DOM + screenshot), output = parsable text actions, trained by offline imitation." It directly argues against the prior orthodoxy that online RL with billions of frames (CC-Net) is required for proficient web navigation, and shows that pre-trained instruction-tuned foundation models supply enough inductive bias to make offline behavioral cloning competitive. Relevant to the harness because it cleanly separates the contributions of (1) multimodal perception, (2) instruction-finetuning, (3) data scaling, and (4) text-action formulation -- each is a design lever for a computer-use harness. It also released a 347K-episode multimodal MiniWoB++ demonstration dataset, a reusable training-harness artifact.

## Problem and gap
- ANALYSIS: Prior web-navigation agents fell into two unsatisfying camps. (a) Online RL (Liu 2018; Gur 2019; Humphreys 2022 / CC-Net) reaches high success but needs massive trial-and-error (CC-Net uses 2.4M demos + extra billions of online frames), which is unsafe and impractical on real sites (wrong password -> account freeze, wrong email -> business problem) (p.1-2). (b) Offline supervised learning is safe but had been sub-optimal (WebN-T5 = 48.4% on MiniWoB++) (p.2,4).
- A second gap: prior models used web-specific architectures (LSTM, self-attention, GNN over DOM) and fixed categorical action spaces (p.1, Appendix I per text), preventing reuse of out-of-domain pre-trained models and open-ended action output.
- The paper's bet: convert web navigation into a VQA-style (text+image -> text) problem so general foundation models can be used, and recover the lost offline performance via better perception + instruction-tuning + data scale.

## Core idea
Four coupled choices (p.2):
1. Multimodal observation: feed both raw HTML (text) and screenshot (image via a pre-trained ViT) so the agent gets grounded spatial understanding.
2. Instruction-finetuned LLM backbone: use Flan-T5 (instruction-tuned T5) instead of vanilla T5, because web navigation is inherently instruction-following; this is claimed to improve HTML comprehension and multi-step reasoning.
3. Large multimodal demonstration corpus: collect HTML+screenshot demonstrations and jointly finetune the LLM and ViT.
4. Free-form text actions: output actions like {'action': 'click', 'ref': '6'} as text, removing web-specific categorical heads.

## Harness relevance
- Environment / workspace: MiniWoB++ simulated websites (56 evaluation tasks, 100 episodes/task) (p.6); WebShop online-shopping simulator with real product data (p.8); Mind2Web real-world dataset (~2K instructions, 137 websites) for action-prediction transfer (p.9).
- Observation interface: per-step raw HTML as a text sequence + a screenshot image. Screenshots cropped to remove the yellow instruction bar (160x160), padded to 224x224 for ViT (p.5). History of H=2 steps of patched screenshots gives temporal tokens.
- Action interface: constrained action space function(selector, text) where function in {click, type}, selector is an integer element ref, text is the typed string (p.4). Emitted as free-form text decoded by the T5 decoder. Episode success = instruction satisfied (r=1); failure on invalid action or wrong terminal state.
- Tool/API/shell/GUI layer: GUI/web layer -- no shell or external tools; the "action API" is the click/type ref-based interface of MiniWoB++/WebShop.
- Planner/executor/verifier/search structure: none explicit. Single end-to-end policy (reactive, history-conditioned); no separate planner, no search, no learned verifier. Multi-step reasoning is implicit in the Flan-T5 weights (no explicit chain-of-thought decoding reported for the action policy).
- Evaluation harness: average success rate over MiniWoB++ tasks (time limit ignored during eval due to compute, p.22); WebShop score (% of required attributes covered) + success rate; Mind2Web element accuracy, operation F1, step success rate, and full success rate across cross-task/website/domain splits (top-50 candidate generation, direct-QA formulation following Deng 2023).
- Training harness: offline imitation / behavioral cloning. T5 (Flan-T5) + ViT-B16 jointly finetuned. SeqIO pipeline, SentencePiece 32K vocab (C4), batch size 128, input length 4096 tokens, single seed per model, cloud TPU-v4; Base = 256 cores, XL = 512 cores, 1-2 days (Appendix C, p.19-20).
- Logging/trace/reproducibility: public checkpoints reused (T5, Flan-T5, WebN-T5-3B); the 347K-episode multimodal dataset is released (HTML, screenshots, actions, instructions per step). Per-task dataset composition given in Table 7. NOTE: only one training seed per model -- no variance reporting.
- Safety/permission mechanism: none implemented. Safety is the motivation (offline avoids unsafe online exploration), and broader-impacts note removes the 54K LLM-generated demos from the public release (-> 347K) (Appendix A, p.19). No runtime guardrails.

## Method
- Architecture (Fig 2, p.3): encoder-decoder T5. ViT-B16 (86M params, ImageNet-21K pre-trained) maps screenshots to image tokens. Each image -> 14x14 patch tokens; with H=2 temporal window -> 14x14x2 = 392 visual tokens. T5 encoder consumes HTML tokens + temporal/local visual tokens jointly; decoder predicts the text action. "Local" tokens = one token per patch (not the CLS/global token) for fine spatial info; "temporal" tokens = stacked recent steps for action consistency (p.5).
- Backbone: Flan-T5 (instruction-finetuned) vs vanilla T5 ablation. Sizes Base(220M)->Large(770M)->XL(3B)->XXL(11B); multimodal variants add ViT (Base+ViT reported as 310M, Large+ViT 860M, XL+ViT 3B) (Table 5, p.20).
- Data collection (Sec 4.3, p.5; Appendix F, p.21): bootstrap from the public WebN-T5 finetuned-LLM policy (Gur 2022). Rollout 100 episodes/task -> 2.8K successful episodes; finetune Flan-T5-XL on these; run at 10,000 episodes/task keeping only successes; add 54K demos via Synapse (Zheng 2023, PaLM-2-based prompting) plus a scripted policy for book-flight, for hard tasks (click-scroll-list, enter-time). Total = 401K (347K released + 54K). Table 7 totals 346,827 episodes / 867,277 steps (the released 347K).
- Mind2Web transfer (Sec 5.5, p.9): take WebGUM finetuned on the 401K MiniWoB++ data, then further finetune on the Mind2Web training set; predict element id + operation + value.

## Experimental setup
- Benchmarks: MiniWoB++ (56 tasks, 100 eval episodes each); WebShop; Mind2Web (cross-task / cross-website / cross-domain).
- Baselines: CC-Net (SL and SL+RL), WebN-T5 (offline SoTA), WGE, Human; LLM in-context agents RCI (GPT-3.5-turbo / GPT-4), AdaPlanner (text-davinci-003), Synapse (GPT-3.5-turbo) on MiniWoB++; on WebShop: Rule, IL, IL+RL, Act and ReAct (PaLM-540B), WebN-T5; on Mind2Web: GPT-4 (ICL), MindAct-Large/XL.
- Models: Flan-T5 Base->XXL + ViT-B16; decoder-only Flan-PaLM-8B for an architecture comparison.
- Metrics: success rate (MiniWoB++, WebShop); WebShop attribute score; Mind2Web Ele.Acc / Op.F1 / Step SR / SR.
- Compute: TPU-v4, single seed (see Harness/training).
- Artifacts: released 347K dataset (gresearch/webllm bucket); reuses public T5 / Flan-T5 / WebN-T5-3B checkpoints; videos site linked.

## Key results
All verified against the extraction.
- MiniWoB++ headline: best WebGUM = 94.2% (Flan-T5-XL + ViT-B16, 401K data) (Table 1, p.4; Sec 5, p.7). CLAIMED to exceed previous best offline WebN-T5 (48.4%) by "more than 45.8%" -- EVIDENCE: 94.2 - 48.4 = 45.8 (exact), so the abstract's "more than 45.8%" is essentially the exact gap, not strictly "more than" (the conclusion phrases it as 48.4%->94.2%). Also exceeds online-RL SoTA CC-Net SL+RL (93.5%, +0.7%) and Human (93.5%), and GPT-4-based RCI (94.0%) (Table 1).
- Note on stronger MiniWoB++ baselines: Synapse (GPT-3.5-turbo, ICL) is listed at 98.5% in Table 1 -- i.e. one in-context LLM agent reports higher average success than WebGUM. UNCLEAR / important caveat: the paper's "outperforming ... GPT-4-based agent" refers to RCI(GPT-4)=94.0%, not to the higher Synapse number; the headline framing understates that Synapse scored higher on the same table.
- Data efficiency: Base+ViT with only 2.8K demos = 61.1%, already beating WebN-T5's 48.4% (Table 1, Table 4). HTML-only Base with 2.8K = 55.7% (Table 4, p.20). Scaling data Base+image: 2.8K->61.1%, 68K->62.3%, 347K->66.1% (Table 4).
- Model scaling (347K data): HTML-only 57.2/72.4/75.5/79.0% for Base/Large/XL/XXL; HTML+Image 66.1/77.4/80.3% for Base/Large/XL (Table 5, p.20). Decoder-only Flan-PaLM-8B = 72.8%, only ~Large-level, supporting encoder-decoder preference (p.7-8).
- Visual-token ablation: temporal+local = 66.1% > temporal-only 64.2% > local-only 64.0% (Fig 4 / p.6-7). White-image input collapses multimodal model back to HTML-only level (~88.7%) confirming the image is actually used (Fig 3). Different pre-trained ViTs (JFT, CLIP, MAE, DINO) gave marginal differences (~64-66.3%) -- the token design matters more than the ViT pretraining.
- Per-task image gains: book-flight +50%, identify/click-shape +22%, social-media +21% (abstract/p.2, Fig 3 right).
- Robustness (HTML comprehension): compositional tasks (6 stitched click-* tasks) -- WebGUM HTML+Image 78.5% vs WebN-T5 51.0% vs Synapse 73.8% (Fig 5, p.7). Perturbation robustness (Fig 6): with added coordinate attributes WebGUM HTML+Image 62.6% vs WebN-T5 6.4%; top-perturbation 71.8% vs 24.7%; bottom 64.7% vs 42.8%. WebSRC HTML-QA: Flan-T5-XL EM/F1 68.91/78.48 vs T5-XL 63.85/71.44 (Table 6, p.21).
- WebShop (Table 2, p.8): WebGUM (Flan-T5-XL, SL) score 67.5 / success 45.0%, beating ReAct PaLM-540B (66.6 / 40.0%), Act PaLM-540B (62.3 / 30.1%), IL+RL (62.4 / 28.7%), WebN-T5 (61.0 / 29.8%). VERIFIED. WebGUM has 3B params vs PaLM-540B.
- Mind2Web (Table 3, p.9): WebGUM-XL > MindAct-XL and GPT-4 across all three splits. Cross-task SR 8.5 (MindAct-XL 5.2, GPT-4 2.0); cross-website SR 5.2 (5.1, 2.0); cross-domain SR 3.2 (2.9, 2.0). Ele.Acc / Op.F1 / Step SR also higher for WebGUM-XL (e.g. cross-task 57.2 / 80.3 / 53.7). EVIDENCE: positive transfer is real but absolute full-task SR remains low (3-9%), i.e. real-world web navigation is far from solved.
- Dataset: 347K released multimodal demos = "38x" the prior 12K human-demo dataset (Liu 2018). VERIFIED 12K * ~29 ~= 347K; the "38x" figure is the paper's claim (12K * 38 = 456K, which does not match 347K). UNCLEAR: the "38 times larger" multiplier does not arithmetically match 347K/12K ~= 29x; treat "38x" as the authors' stated number but note the discrepancy.

## Evidence quality
- Strong, well-decomposed ablations: input replacement (white/random images), visual-token type, ViT pretraining, data size, model size, backbone (Flan-T5 vs T5, encoder-decoder vs decoder-only), compositional and perturbation robustness, plus a clean WebShop test that deliberately decouples reasoning from MiniWoB-specific perception. This is unusually thorough for the era.
- Key weakness: single training seed per model (stated, Appendix C) -- no variance/CI, so small margins (e.g. +0.7% over CC-Net, or 80.3 vs 79.0) are not statistically backed.
- Benchmark-framing caveat: the headline "outperforms humans / online SoTA / GPT-4 agent" is selectively framed -- Synapse (GPT-3.5-turbo) reports 98.5% on the same MiniWoB++ table, higher than WebGUM's 94.2%. The win is genuine vs offline SL and vs RCI/GPT-4, but not an unconditional SoTA.
- Possible data-quality concern: training demos are generated by other LLM policies (WebN-T5, Synapse) rather than humans, and only successful trajectories are kept; evaluation is on the same MiniWoB++ task set the demos cover, so generalization claims rest mainly on the compositional/perturbation and Mind2Web sections, not the headline number.
- MiniWoB++ eval ignores the time limit (p.22), which can inflate success on slow multi-step tasks vs methods evaluated under the limit.
- "38x larger" dataset claim is arithmetically inconsistent with 347K/12K (~29x).

## Reproducibility and artifacts
- Code: Not reported as a single release; pipeline built on public SeqIO/t5x/scenic; Synapse repo and miniwob demos linked. No WebGUM training-code URL stated in the extraction.
- Data: 347K multimodal MiniWoB++ demonstrations released (gresearch/webllm GCS bucket); 54K LLM-generated demos excluded from release for impact reasons.
- Models: reuses public checkpoints (T5, Flan-T5, WebN-T5-3B); WebGUM weights release not explicitly stated.
- Environment: MiniWoB++, WebShop, Mind2Web -- all public.
- License: Not reported.
- Exact commands or setup: partial (batch 128, seq len 4096, TPU-v4 core counts, 1-2 days) -- no full command/config.
- Missing details: random seeds (n=1), exact eval-time limit handling per task, WebGUM checkpoint availability, hyperparameter sweep details.

## Strengths
- Clean, reusable recipe (text+image -> text actions) that drops web-specific architectures and enables foundation-model reuse.
- Demonstrates offline imitation can match/exceed online RL on MiniWoB++ -- a meaningful safety/cost argument.
- Strong data efficiency result (2.8K demos already beats prior SL SoTA).
- Careful ablations isolating perception vs instruction-tuning vs scale.
- Released large multimodal dataset; transfer to a real-world benchmark (Mind2Web).

## Weaknesses and limitations
- Single seed; no statistical reporting.
- Headline SoTA framing omits that an in-context LLM agent (Synapse 98.5%) scored higher on MiniWoB++.
- Real-world transfer numbers (Mind2Web full SR 3-9%) show the approach is far from deployable.
- Training data is self-generated by other LLM policies on the same tasks; limited evidence of broad open-web generalization (authors acknowledge human-level generalization to diverse real sites remains unsolved, Sec 6).
- No explicit planner/verifier/search; reactive policy may cap multi-step memory tasks (authors note guess-number weakness).
- "38x" dataset claim inconsistent with reported counts.
- No safety/permission runtime mechanism (safety argued only via offline training).

## Relationship to prior work
- Directly builds on WebN-T5 (Gur 2022) -- same T5 encoder-decoder, text-action formulation; WebGUM adds Flan-T5 backbone, ViT multimodality, and ~30x more (LLM-generated) data; this is the clearest "what's new" delta.
- Contrasts with CC-Net (Humphreys 2022): online RL + 2.4M demos + billions of frames, fixed categorical actions -- WebGUM matches it offline.
- Contrasts with in-context LLM agents RCI (Kim 2023), AdaPlanner (Sun 2023), Synapse (Zheng 2023): WebGUM finetunes with domain data instead of prompt engineering, and handles long-HTML tasks (book-flight, choose-date-hard) where few-shot agents run out of context.
- WebShop comparison vs ReAct/Act (PaLM-540B, Yao 2022b); Mind2Web vs MindAct (Deng 2023, also Flan-T5-based, enabling an apples-to-apples transfer claim).
- Genuinely new: the combined multimodal + instruction-tuned + scaled-offline recipe and the released multimodal dataset. Incremental relative to WebN-T5 in architecture lineage.

## What I should read
- Must read: Sec 4 (method, Fig 2), Sec 5.1-5.2 (perception + scaling ablations), Table 1, Table 2 (WebShop), Table 3 (Mind2Web).
- Skim: Sec 5.3-5.4 (HTML comprehension, reasoning), Appendix C (implementation), Appendix F/Table 7 (dataset composition).
- Can skip: full reference list, Appendix B extended related work, per-task Table 8.
- Follow-up papers: Gur 2023 (real-world WebAgent / HTML-T5, the deployment successor); Deng 2023 (Mind2Web); Zheng 2023 (Synapse); Humphreys 2022 (CC-Net); Yao 2022a/b (WebShop / ReAct).

## Triage decision
Label: READ_SOON
Rationale: Foundational, frequently-cited reference for the offline-imitation multimodal web-agent recipe directly relevant to a computer-use harness; ablations are the value, headline number needs the Synapse caveat. Evidence is solid but single-seed and benchmark-bound, so not elevated to MUST_READ.
Confidence: high
Reading time estimate: ~45-60 min for method + key ablations + the three result tables.

## Personal notes
The most harness-actionable takeaways: (1) one local token per ViT patch + a 2-step temporal stack matters more than the ViT pretraining choice; (2) instruction-tuned backbone buys robustness to HTML perturbations and compositional tasks, not just raw success; (3) keeping only successful self-generated trajectories is a cheap data-scaling trick but ties generalization claims to the held-out compositional/Mind2Web evals. Watch the "38x"/347K arithmetic and the Synapse 98.5% when citing this paper's SoTA claim.

## Follow-up actions
- Add related paper: Gur 2023 (real-world WebAgent), Deng 2023 (Mind2Web), Zheng 2023 (Synapse)
- Compare with: WebN-T5 (Gur 2022), CC-Net (Humphreys 2022), ReAct (Yao 2022b)
- Re-run after new version: n/a (ICLR 2024 camera-ready; arXiv v4)
- Check code: WebGUM training pipeline / dataset bucket (gresearch/webllm)
- Read benchmark details: Mind2Web evaluation protocol (top-50 candidates, direct QA), WebShop scoring
