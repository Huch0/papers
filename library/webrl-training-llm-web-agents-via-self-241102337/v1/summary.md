# WebRL: Training LLM Web Agents via Self-Evolving Online Curriculum Reinforcement Learning

## Metadata
- Canonical key: arxiv-2411.02337
- Version: v1
- Fetch date: 2026-06-06T07:57:47Z
- Source: arxiv
- PDF: library/webrl-training-llm-web-agents-via-self-241102337/v1/paper.pdf
- Venue: ICLR 2025 (extraction is arXiv:2411.02337v3, "Published as a conference paper at ICLR 2025")
- Year: 2024 (arXiv v1); published ICLR 2025
- Authors: Zehan Qi, Xiao Liu, Iat Long Iong, Hanyu Lai, Xueqiao Sun, Wenyi Zhao, Yu Yang, Xinyue Yang, Jiadai Sun, Shuntian Yao, Tianjie Zhang, Wei Xu, Jie Tang, Yuxiao Dong (Tsinghua University; Zhipu AI)
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

---

# PASS 1 — Triage (bird's-eye, ~5 min)

## One-sentence takeaway
WebRL turns open LLMs (Llama-3.1, GLM-4) into strong WebArena agents by coupling a self-evolving curriculum that mints new tasks from the agent's own past failures with a learned outcome-supervised reward model and a KL-constrained off-policy update plus a confidence-filtered replay buffer, lifting Llama-3.1-8B from 4.8% to 42.4% success on WebArena-Lite (p.1, abstract; Table 1, p.7).

## The Five Cs
- **Category:** New method/system + training framework (reinforcement-learning training pipeline for LLM web agents), with substantial empirical evaluation and ablations.
- **Context:** Builds on WebArena/WebArena-Lite as the online environment (Zhou et al. 2024a; Liu et al. 2024b); competes against imitation-learning web agents (AutoWebGLM, Lai et al. 2024), Filtered BC (Pan et al. 2024), AWR (Peng et al. 2019), and the closest online-RL device-control method DigiRL (Bai et al. 2024). Theoretical basis is max-entropy RL / RLHF-style KL-constrained objectives (Rafailov et al. 2024a; Ouyang et al. 2022), GAE (Schulman et al. 2015), classification-based value learning (Farebrother et al. 2024), and WizardLM-style in-breadth instruction evolution (Xu et al. 2023).
- **Correctness:** Core assumptions look reasonable on a first read: binary outcome reward, KL-to-previous-phase-policy to fight drift, curriculum from failures to fight task scarcity. The derivation (Appendix A.1–A.2) is given with a policy-improvement proof. The biggest dependency is the ORM's ~80% accuracy being good enough to drive eight phases of self-training; errors here could compound, and the curriculum quality leans on GPT-4o for both generation and infeasibility filtering. These are dependencies, not obvious flaws.
- **Contributions:** (1) First systematic RL-from-scratch framework for LLM web agents in WebArena, including the infrastructure and a strong trained ORM (p.3). (2) A self-evolving curriculum + KL-constrained off-policy update + confidence-filtered replay buffer that jointly attack task scarcity, sparse feedback, and policy drift (p.3, §2). (3) State-of-the-art WebArena-Lite results that beat GPT-4-Turbo and prior open-LLM agents by >160% relative (p.3, Table 1).
- **Clarity:** Well written and well evidenced. Method is grounded with equations and a gradient-level "what does the update do" analysis (eq. 6, p.5); ablations cover replay buffer, KL term, curriculum, perplexity band, β, prompt variants, and ORM quality; error bars over four seeds are reported (Figure 13, p.22). Calibrates to high confidence.

## Why this matters to me now
Directly on-target for agent training harnesses: it is one of the first end-to-end online-RL pipelines that makes small open models competitive web agents, with a reusable design (learned ORM as reward, curriculum from failures, KL-constrained off-policy update). Relevant for anyone building self-improving agent training loops where ground-truth reward functions are unavailable for generated tasks.

---

# PASS 2 — Content (what it actually does; section-grounded)

## Motivation — the problem (NOT the novelty)
Training open-LLM web agents online in WebArena breaks on three concrete obstacles (p.2, §1, "Challenges"):
1. **Scarcity of training tasks.** Online benchmarks like WebArena ship only a small test set; even the curated WebArena-Lite fine-tuning set has ~1k instructions with oracle trajectories — far too few to train a strong agent (p.2; p.4, §2.1). Unlike offline GUI datasets, there is no large pool of human-annotated training tasks.
2. **Sparsity and cost of feedback.** Arbitrary web tasks have no built-in success function, and WebArena tasks are long-horizon (oracle solutions average ~10 steps), so the single terminal success signal is extremely sparse during exploration (p.2, §1).
3. **Policy distribution drift in online learning.** Without a fixed training set, the agent must explore online; its policy drifts phase-to-phase, inducing catastrophic forgetting and performance degradation over time (p.2, §1).

Why it matters: high-performing web agents today depend on expensive proprietary APIs (GPT-4) with hand-crafted prompts, while open LLMs lack decision-centric data and imitation-learning approaches "fail to yield consistent, continual improvements" (p.2). The goal is accessible, self-improving open-model web agents.

## Novelty — the genuine delta  ★ the core of a good summary
- **Delta in one sentence (survives deleting "we propose"):** An LLM web agent can bootstrap its own training distribution by generating new tasks from its *own past failures*, filtered to moderate difficulty by a learned critic, while a KL-to-previous-phase off-policy objective and a perplexity-filtered, success-only replay buffer keep the policy from drifting — so a small open model improves monotonically across phases without any external reward function for the new tasks.
- **Mechanistic reason each piece must take its form (derived from why baselines fail):**
  - *Curriculum from failures, gated to critic score 0.05–0.75 (p.4, §2.1).* DigiRL trains on a fixed task set; some tasks are too hard for the current policy, so under sparse terminal reward the agent gets near-zero signal, converges to suboptimal solutions, and stops exploring (p.7, §3.2; Figure 6, p.8). Generating tasks of moderate difficulty *relative to current ability* raises the probability of positive feedback, which is exactly the lever that attacks reward sparsity — the curriculum is not just "more data," it is "data the agent can currently get reward on."
  - *Learned ORM as reward (p.3–4).* Self-generated tasks have no predefined reward function, so the curriculum is impossible without a generalizable success judge; the ORM (compare P(YES) vs P(NO) on instruction + action history + final-state HTML) supplies the binary reward for arbitrary new tasks. The curriculum and the ORM are mutually load-bearing: no ORM, no rewardable new tasks.
  - *KL-constrained off-policy update with MSE-to-target loss (eq. 4–5, p.4–5; Appendix A).* Curriculum learning changes the task distribution every phase, which would normally cause drift/forgetting. The objective constrains πθ toward the *previous-phase* policy πref. The authors deliberately use an MSE-on-log-ratio target (eq. 11) rather than a KL-to-π* target (eq. 13) because eq. 13 (i) requires data drawn from πref, (ii) cannot decrease the probability of negative-advantage actions, so when correct actions are hard to sample it can *increase* the probability of wrong ones (Appendix A.1, p.17–18; Figure 9). The MSE form is off-policy and *does* push down bad actions — essential because web rollouts are mostly failures and discarding them wastes signal.
  - *Success-only replay with actor-confidence (perplexity) filtering, band 1/0.95–1/0.5 (p.6).* Storing failed trajectories poisons advantage estimates (a correct action in a failed trajectory gets negative advantage because reward is terminal), so only successes are kept (Appendix C, Figure 16). Replaying *over-familiar* data (perplexity ≈1) overfits and replaying *too-hard* data shifts the distribution; the band keeps moderately-difficult experiences, mirroring the curriculum's difficulty logic at the data level (Table 2, p.10).
- **Closest prior work and precise difference:**
  - *DigiRL (Bai et al. 2024)* — also actor-critic online RL for device control, but trains on a *fixed* task set and uses AWR-style updates; WebRL adds the self-evolving curriculum and the KL-to-previous-policy MSE objective. Head-to-head, WebRL beats DigiRL (Llama-3.1-8B 42.4 vs 30.3; GLM-4-9B 43.0 vs 31.5, Table 1) and adding WebRL's curriculum to DigiRL improves DigiRL but still trails WebRL (Figure 14, p.23).
  - *AWR (Peng et al. 2019)* — constrains KL to the *behavioral* policy of the data and does not reduce probability of incorrect actions; WebRL constrains to πref and explicitly lowers negative-advantage actions (Appendix A.3, p.19).
  - *DPO (Rafailov et al. 2024b)* — needs pairwise data, infeasible on the web because you cannot backtrack page state to compare two actions from the same state (Appendix A.3, p.19–20).
  - *AutoWebGLM (Lai et al. 2024) / Filtered BC / SFT* — imitation-learning agents that overfit frequent actions (e.g., over-repeating "Scroll Down") and do not improve continually (p.7, §3.2).
  - *Curriculum generation* uses in-breadth evolving (WizardLM, Xu et al. 2023) but seeds from the agent's *own failures* rather than a static seed corpus.
- **Motivation-vs-novelty check:** The contribution does NOT end at "prior method fails in scenario Y." The novelty is the specific *mechanism*: failure-seeded, critic-gated task generation + learned ORM + KL-constrained off-policy MSE update + success-only/perplexity-filtered replay, each justified by *why* the sparse-reward/drift failure occurs. This is genuine delta, not motivation dressed up.
- **30-second test:** WebRL lets an open LLM web agent generate its own moderate-difficulty training tasks from its failures, score them with a learned reward model, and learn from them with a drift-resistant off-policy update — closing the loop so success climbs phase over phase without external reward functions.

## Core idea / method
The training loop (Algorithm 1, p.22) has two parts. Part 1: SFT on the WebArena-Lite training set, then roll out the SFT model to seed a replay buffer (successful trajectories) and a failure set (failed instructions). Part 2: for N=8 phases — (a) generate ~500 new instructions per phase with GPT-4o seeded by failure-set tasks, filter by the trained critic to scores in [0.05, 0.75] and by a GPT-4o feasibility prompt (Figure 22); (b) roll out the current actor πn on these instructions; (c) label rollouts with the ORM (no environment reward for generated tasks); (d) draw replay experiences whose actor-computed perplexity lies in [1/0.95, 1/0.5], capped at 2× the interaction data; (e) update actor and critic with the KL-constrained MSE loss (eq. 5) and the cross-entropy value loss (eq. 7), advantage via a next-step/final-step GAE blend with λ=0.5 (eq. 8) and discount γ=0.9; (f) append successes to the buffer and failures to the failure set.

Problem framing is a finite-horizon MDP over (HTML state + action history); reward is 1 on success, 0 otherwise. The policy objective (eq. 1) is max-entropy RL with a β-weighted KL toward πref; its optimal policy (eq. 2) and the derived loss (eq. 5) give an off-policy update whose gradient (eq. 6, p.5) increases probability of positive-advantage actions, decreases negative-advantage ones, and is throttled by the KL term so πθ does not stray from πref (β controls strength).

## Harness relevance
- **Environment / workspace:** WebArena (Zhou et al. 2024a); evaluation on WebArena-Lite (165 human-verified test cases) across five sites — Reddit, GitLab, CMS, Map (OpenStreetMap), OSS (OneStopShop) (p.6, §3.1). Original WebArena has 812 instructions; WebArena-Lite test set is 165.
- **Observation interface:** Simplified HTML of the current page (clickable elements assigned distinct IDs) + user instruction + action history (p.20, Appendix B.1). ORM input keeps only the final-state HTML plus history due to context limits (p.4).
- **Action interface:** Click, Hover, Type, Search, Press, Scroll, Select dropdown option, New tab, Tab focus, Close tab, Goto, Go back, Go forward, Exit (p.20). Actions emitted as one-line `do(action, argument, element)` calls with `# Element:` / `# Note:` comments (Figure 11, p.20–21).
- **Tool / API / shell / GUI layer:** Text/HTML-DOM web interface (no pixels); element-ID grounding rather than coordinates.
- **Planner / executor / verifier / search structure:** Single actor policy (no explicit planner/search tree). The **critic** (value network V, SFT model + randomly initialized value head) gates curriculum difficulty and computes advantages. The **ORM** is the verifier/reward model. No tree search (contrast with WebPilot/Agent Q).
- **Evaluation harness:** WebArena-Lite reward functions for the test set and for labeling ORM training data; ORM substitutes when generated tasks lack a reward function.
- **Training harness (the core):** The self-evolving curriculum RL loop (Algorithm 1) — rollout → ORM labeling → confidence-filtered replay → KL-constrained off-policy actor/critic update. 8 phases, 500 instructions/phase, batch size 128, actor/critic lr 1e-6, rollout temperature 1, cutoff length 16384 (Table 5, p.23). ORM trained at lr 5e-6, 4 epochs (Table 6, p.23).
- **Logging / trace / reproducibility:** Code, model, and data released at https://github.com/THUDM/WebRL (p.1). Hyperparameters and prompts fully listed (Tables 5–6; Figures 17–22). Per-phase, per-site curves and four-seed error bars reported (Figures 12–13).
- **Safety / permission mechanism:** Not reported (sandboxed WebArena sites only; no real-world safety/permission layer described).

## Experimental setup
- **Benchmark:** WebArena-Lite, 165 test cases, average success rate (SR) over five sites (p.6).
- **Models trained:** Llama-3.1-8B, Llama-3.1-70B, GLM-4-9B; actor/critic initialized from the SFT model.
- **Baselines:** Proprietary prompting — GPT-4-Turbo-2024-04-09, GPT-4o, plus literature numbers AWM+GPT-4-0613 and WebPilot+GPT-4o (these two are on *full* WebArena, marked with *). Open-model — AutoWebGLM, base GLM-4-Chat / Llama-3.1-Instruct, SFT(BC), Filtered BC, AWR, DigiRL.
- **ORM training data:** WebArena-Lite has 1,186 training samples (instruction + trajectory + reward function); augmented by instruction rewrites and rollouts from all baselines, totaling 12,200 labeled samples (Appendix B.3, p.21).
- **Metric:** Task success rate (binary, per task).
- **Compute / cost:** Not reported in detail (Zhipu AI sponsored compute and annotation, p.11). No GPU-hours given.
- **Artifacts:** Code/model/data public (THUDM/WebRL).

## Key results — read the figures, not just the prose
- **Headline (Table 1, p.7):** Llama-3.1-8B 4.8% → **42.4%**; GLM-4-9B 6.1% → **43.0%**; Llama-3.1-70B 12.7% → **49.1%** (and 26.1 points over its own SFT, p.8). All beat GPT-4-Turbo (17.6%) and GPT-4o (13.9%) and prior open-model SOTA AutoWebGLM (18.2%). Abstract numbers match the table.
- **Per-site (Table 1):** Llama-3.1-8B+WebRL — Reddit 63.2, GitLab 46.7, CMS 54.3, Map 36.7, OSS 31.1. GLM-4-9B+WebRL — Reddit 57.9, GitLab 50.0, CMS 48.6, Map 36.7, OSS 37.8.
- **Beats nearest RL baseline:** WebRL > DigiRL on both backbones (8B: 42.4 vs 30.3; 9B: 43.0 vs 31.5). RL methods beat imitation methods, which over-repeat high-frequency actions (e.g., "Scroll Down" loops in CMS) (p.7).
- **Ablations (Figure 5, p.9):** Full WebRL 42.4%; w/o replay buffer 32.7%; w/o KL 34.5%; w/o KL & replay 20.0%; w/o curriculum (CL) 24.8% (vs init 20.6%). All four components contribute; removing replay/KL degrades over phases (forgetting). REINFORCE-with-baseline (w/o KL) overfits the current phase and falls below its initial value.
- **Perplexity band (Table 2, p.10):** [1/0.95, 1/0.5] → 31.5%, beating [1,1/0.95] 27.9, [1,∞] 29.1, [1/0.5,∞] 23.0 — moderate-difficulty replay is best.
- **β sweep (Figure 7, p.10):** too-small β (0.01) overfits; without replay, large β over-restricts; with replay, performance stays high even at large β.
- **ORM quality (Table 3, p.10):** ORM (8B) reaches 80.8% on the test set and 79.4% on rollouts, beating GPT-4 (71.9/71.2), Captioner+GPT-4 (72.6/73.3), and GPT-4V (71.2/70.5) — ~80% vs ~70%.
- **Robustness:** Four-seed error bars show consistent upward trend and final SR above all baselines (Figure 13, p.22), though WebRL/DigiRL-w-CL show higher variance from random task generation (Figure 15). Prompt-variant stability: 42.4 / 40.6 / 43.6 across three generation prompts (Table 7, p.24).
- **Critical read:** AWM+GPT-4-0613 (35.5) and WebPilot+GPT-4o (37.2) are on *full* WebArena, not WebArena-Lite, so they are not strictly comparable to the 42.4/43.0/49.1 WebArena-Lite numbers — the paper marks this with * but the abstract's "significantly surpass" framing emphasizes the directly-comparable GPT-4-Turbo/GPT-4o numbers. The Map site shows a rise-then-decline across phases (Figure 12), a real non-monotonic failure mode the authors attribute to a trade-off with OSS/CMS gains.

---

# PASS 3 — Critique (challenge every assumption)

## Does the evidence actually support the claims?
- **Claim "self-evolving curriculum drives continual improvement" (verifies novelty):** Supported. w/o CL plateaus at 24.8% vs 42.4% full (Figure 5); adding CL to DigiRL helps DigiRL but still trails WebRL (Figure 14); per-complexity and per-step-length analyses show WebRL holds up on long/complex tasks where DigiRL (fixed task set) degrades (Figures 4, 6). These test the mechanism, not just the problem's existence.
- **Claim "KL-constrained MSE objective beats alternatives" (verifies novelty):** Supported by ablation (w/o KL 34.5 vs 42.4) and the eq.11-vs-eq.13 experiment (Figure 9) plus the AWR/DPO/PPO comparison table (Table 4). Theoretical policy-improvement proof in Appendix A.2.
- **Claim "ORM is good enough" (verifies a load-bearing dependency):** Supported — ~80% vs GPT-4's ~70% (Table 3). But ~80% still mislabels ~1 in 5 trajectories; the paper does not quantify how ORM error compounds over 8 phases of self-training, which is the central reliability question.
- **Claim "beats proprietary and prior open SOTA":** Supported for directly-comparable GPT-4-Turbo/GPT-4o and AutoWebGLM (all WebArena-Lite). The AWM/WebPilot comparison is cross-benchmark (full WebArena) and should be read with caution.
- **What merely confirms the motivation:** The error-type distribution (Figure 3) and the step-length/complexity degradation of SFT/Filtered BC mostly re-demonstrate that imitation learning and fixed-task RL fail on long-horizon sparse-reward tasks — i.e., they re-show the problem. They support the framing but are not the novelty test.

## Hidden assumptions & failure modes
- **GPT-4o is in the loop** for both task generation and feasibility filtering — so "open-model agent" still depends on a proprietary model at *training* time (not inference). Curriculum quality is bounded by GPT-4o's generation and the manually-derived feasibility rules (Figure 22).
- **ORM reliability assumption:** the whole self-training loop trusts the ORM's binary label on tasks with no ground-truth reward. Systematic ORM bias would silently corrupt the curriculum; ~80% accuracy is the ceiling on label quality.
- **Critic-gated difficulty band [0.05, 0.75] and perplexity band [1/0.95, 1/0.5]** are hand-tuned; sensitivity beyond the single-phase Table 2 sweep is not fully explored.
- **Non-monotonic per-site behavior** (Map declines, Figure 12) suggests inter-site interference — improving some sites can cost others. No mechanism prevents this.
- **Narrow domain:** five WebArena sites, sandboxed, HTML-only. No real, live, or visual websites; generalization to open-web or pixel-based agents is untested.
- **Cost/compute opacity:** 70B training and 8 phases of rollouts are expensive; no GPU-hours or wall-clock reported.

## Could I reconstruct it? (reproducibility)
- **Code:** Released — https://github.com/THUDM/WebRL.
- **Data:** WebArena-Lite training set (1,186 samples) + ORM training set (12,200 samples) described; instruction-rewrite augmentation described qualitatively. Released per the repo statement.
- **Models:** Llama-3.1-8B/70B, GLM-4-9B — open weights; SFT-initialized actor/critic.
- **Environment:** WebArena (public, dockerized sandboxes).
- **License:** Not reported in the paper text (check repo).
- **Exact commands or setup:** Algorithm 1 + full hyperparameter tables (Tables 5–6) + all prompts (Figures 17–22) given. β value used in main runs is not explicitly stated in the extracted tables (Table 5 omits β; only the β-sweep figure is shown) — Unclear which β the headline runs use.
- **Missing details (what blocks reconstruction):** Exact main-run β; precise GPT-4o version/prompt-temperature for generation; how many generated instructions are discarded by filtering to net 500/phase; ORM input truncation specifics for very long HTML; compute budget. Otherwise reconstruction looks feasible given the released code.

## Strengths
- Tackles three coupled problems (task scarcity, reward sparsity, drift) with mechanistically-justified, mutually-reinforcing components rather than one bolt-on module.
- Strong, directly-comparable results: 4.8%→42.4% (8B), →49.1% (70B), beating GPT-4-Turbo with an 8B open model.
- Unusually thorough ablations and analysis (component ablation, perplexity band, β, eq.11-vs-13, ORM quality, prompt-variant stability, four-seed error bars).
- A learned ORM that beats GPT-4/GPT-4V as a trajectory judge while being open and cheap — independently useful.
- Released code/model/data and full prompts/hyperparameters.

## Weaknesses and limitations
- Self-training reliability hinges on an ~80%-accurate ORM with no analysis of error compounding over phases.
- GPT-4o dependency at training time partially undercuts the "open-LLM" narrative.
- Cross-benchmark comparison (AWM/WebPilot on full WebArena) blurs some headline claims; absolute SR (~40%) is still far from solved.
- Per-site interference (Map regression) and high variance from stochastic task generation.
- HTML-only, five-site, sandboxed scope; no compute/cost reporting; main-run β unspecified in tables.

## Relationship to prior work
Genuinely new vs the closest systems: (i) failure-seeded, critic-gated self-evolving curriculum (vs DigiRL's and other RL agents' fixed task sets); (ii) KL-to-previous-phase MSE-on-log-ratio off-policy objective chosen over KL-to-π* (eq. 13), DPO (needs infeasible pairwise web data), AWR (constrains to behavioral policy, can't suppress wrong actions), and PPO (on-policy, sample-inefficient for expensive web rollouts); (iii) success-only, perplexity-filtered replay tied to advantage-estimation validity. Incremental/borrowed pieces: actor-critic with GAE, classification-based value learning (Farebrother et al. 2024), in-breadth instruction evolution (WizardLM), and the RLHF KL framing — assembled into a novel closed self-improvement loop for web agents.

---

# Decision

## What I should read
- Must read: §2 (method), eq. 1–8 and the gradient analysis (p.4–6); §3.7 ablations and §3.8 ORM evaluation; Algorithm 1 (p.22).
- Skim: Appendix A.1–A.3 (derivation, proof, algorithm comparison) for the eq.11-vs-13 and DPO/PPO/AWR distinctions; Appendix B (training/observation/action details).
- Can skip: Appendix E qualitative site examples; prompt figures unless reimplementing.
- Follow-up papers / references to chase: DigiRL (Bai et al. 2024); WebArena & WebArena-Lite (Zhou et al. 2024a; Liu et al. 2024b); AutoWebGLM (Lai et al. 2024); Pan et al. 2024 (autonomous eval/refinement, Filtered BC); Rafailov et al. 2024a ("r to Q*"); Farebrother et al. 2024 (classification value learning); WizardLM (Xu et al. 2023).

## Triage decision
Label: READ_SOON
Rationale: New method/system with a clean, mechanistically-justified novelty (self-improvement loop closing task scarcity + sparse reward + drift), strong directly-comparable results (open 8B beats GPT-4-Turbo; 4.8%→42.4%), high clarity and thorough ablations, and released artifacts. Directly relevant to agent training-harness interests. Not MUST_READ only because the domain is narrow (sandboxed WebArena, HTML-only) and the self-training loop's central dependency (ORM error compounding) is unexamined. Evidence quality is high.
Confidence: high
Reading time estimate: ~60–90 minutes for a careful read of §2–§3 + Appendix A.

## Personal notes
The reusable idea is the closed loop: failures → critic-gated generated tasks → ORM-labeled rollouts → KL-constrained off-policy update → success-only/perplexity-filtered replay. The deliberate choice of MSE-on-log-ratio over KL-to-π* (because the web is failure-heavy and you must be able to push down wrong actions) is the subtlest and most transferable insight. Watch the GPT-4o-in-training-loop caveat and the ~80% ORM ceiling.

## Follow-up actions
- Add related paper: DigiRL (arXiv:2406.11896); WebArena-Lite / VisualAgentBench (Liu et al. 2024b).
- Compare with: DigiRL and AutoWebGLM head-to-head on WebArena-Lite; AWR/DPO/PPO objective trade-offs.
- Re-run after new version: this is arXiv v3 / ICLR 2025 camera-ready; recheck if a newer version adds compute/β details.
- Check code: https://github.com/THUDM/WebRL (confirm license, exact β, instruction-filter yield).
- Read benchmark details: WebArena-Lite construction (165 test cases) and reward functions.
