# AgentBench: Evaluating LLMs as Agents

## Metadata
- Canonical key: arxiv-2308.03688
- Version: v1
- Fetch date: 2026-06-06T07:57:30Z
- Source: arxiv
- PDF: library/agentbench-evaluating-llms-as-agents-230803688/v1/paper.pdf
- Venue: International Conference on Learning Representations (ICLR 2024)
- Year: 2023 (arXiv v1 Aug 2023; ICLR 2024 camera-ready; extraction shows arXiv v3 Oct 2025)
- Authors: Xiao Liu, Hao Yu, Hanchen Zhang, Yifan Xu, Xuanyu Lei, Hanyu Lai, Yu Gu, Hangliang Ding, Kaiwen Men, Kejuan Yang, Shudan Zhang, Xiang Deng, Aohan Zeng, Zhengxiao Du, Chenhui Zhang, Sheng Shen, Tianjun Zhang, Yu Su, Huan Sun, Minlie Huang, Yuxiao Dong, Jie Tang (Tsinghua, Ohio State, UC Berkeley)
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
AgentBench is the first systematic, multi-environment benchmark (8 interactive text environments across code/game/web groundings) that evaluates 29 API-based and open-source LLMs purely by CoT prompting as autonomous agents, exposing a large gap between top commercial models (gpt-4, OA 4.01) and the best sub-70B open model (codellama-34b, OA 0.96).

## Why this paper matters
This is a foundational reference point for the "LLM-as-agent" evaluation lineage. It predates and motivates much of the later agent-harness work (SWE-bench, WebArena, OSWorld, tau-bench) by establishing the template of running prompted LLMs inside real executable environments (Docker bash, MySQL, Freebase, ALFWorld, WebShop, Mind2Web) and scoring them on task success rather than text similarity. For anyone building or studying agent harnesses, it is useful both as a design precedent (server/client architecture, per-env observation/action interfaces, Docker isolation) and as a historical anchor for how weak open models were in 2023. Its central empirical claim -- a sharp commercial-vs-OSS gap and that the dominant failure mode is the agent failing to finish within the round budget (Task Limit Exceeded) -- remains a recurring theme in current agent benchmarks.

## Problem and gap
- CLAIMED (p.2): There was no systematic, standard benchmark for evaluating LLMs *as agents* in interactive environments at the time.
- Prior text-game environments (TextWorld, Jericho, LIGHT) had closed/discrete action spaces and narrow commonsense focus (p.2, p.9). Embodied/multimodal simulators were complex but did not reflect practical LLM use and excluded text-only LLMs (p.2). Most existing agent benchmarks targeted a single environment, giving no cross-domain view (p.2).
- The gap AgentBench fills: a *multi-environment*, text-only, executable benchmark that scores LLMs on real task success across diverse groundings under a single toolkit.

## Core idea
Cast agent evaluation as a Partially Observable Markov Decision Process (S, A, T, R, U, O) (p.3), then instantiate it as 8 distinct interactive environments grouped into three "groundings": Code (OS, DB, KG), Game (Digital Card Game, Lateral Thinking Puzzles, House-Holding), Web (Web Shopping, Web Browsing). Five of the eight are newly created for this benchmark (p.2). Each environment exposes a textual observation stream and a per-environment action interface; the LLM agent interacts over multiple rounds using only primitive Chain-of-Thought prompting (Thought + Action in one round, adapted from ReAct), with temperature 0 and no reflection/search/ensemble (p.3, p.6-7). Per-task raw scores are normalized (each task's mean across all models rescaled to 1) and averaged into a single weighted "Overall AgentBench" (OA) score so that easy high-scoring tasks like Web Shopping do not dominate (p.7).

## Harness relevance
This is a multi-environment BENCHMARK harness, not a single agent. Mapping to the template:

- Environment / workspace: 8 isolated environments (p.4-5, Table 2 p.6). Code-grounded: Operating System (Ubuntu bash inside Docker), Database (real MySQL), Knowledge Graph (Freebase, >45M entities / 3B facts, partially observable). Game-grounded: Digital Card Game (Aquawar turn-based fish-battle from THUAC 2021), Lateral Thinking Puzzles (yes/no/irrelevant riddle host system), House-Holding (ALFWorld / TextWorld text simulator). Web-grounded: Web Shopping (WebShop simulated e-commerce site), Web Browsing (Mind2Web real-website actions, adapted to prompting without fine-tuning).
- Observation interface (per env, Figure 4 p.19): OS = system stdout; DB = MySQL CLI output; KG = query results; DCG = battle process and fish status; LTP = "Yes"/"No"/"Irrelevant"; HH = result after the action; WS = product descriptions / webpage; WB = page HTML (optional screenshot, but evaluation is text-only).
- Action interface (per env, Figure 4 p.19 + Appendix B): OS = any valid bash command, plus commit/answer to finish (two action types: bash and commit, p.22); DB = any valid SQL; KG = basic KG-querying tools; DCG = play one of four fish cards + Assertion; LTP = any binary question; HH = a list of allowed actions in the room/accessible rooms; WS = Search (generate keywords) + Click (clickable buttons); WB = pick one HTML element then Click/Type/Select.
- Tool/API/shell/GUI layer: real shell (Docker bash), SQL interface, Freebase KG query tools, web-action APIs. Interaction is text-only; no real GUI/vision is used.
- Planner/executor/verifier/search structure: none beyond single-round CoT (Thought+Action). Authors deliberately use the "most primitive CoT" with no ensemble, reflection, or tree search (p.3) to measure base capability.
- Evaluation harness: a Server-Client toolkit (Appendix A, p.20-21). Decoupled Task Server, Agent Server, and Evaluation Client communicate over HTTP so they can run on different machines. Each task runs in an isolated Docker worker. The Evaluation Client builds an agent-task bipartite graph and uses the Edmonds-Karp max-flow algorithm (O(|V||E|^2)) to schedule agent/task workers efficiently; evaluation is resumable. Metrics per env (Table 2 p.6): OS=SR, DB=SR, KG=F1, DCG=Reward (win rate), LTP=Game Progress, HH=SR, WS=Reward, WB=Step SR. Overall = weighted average via fixed reciprocal-mean weights (Table 2 Weight^-1 row).
- Training harness: none. All models are evaluated by prompting only; OSS models are off-the-shelf.
- Logging / trace / reproducibility: interaction trajectories recorded as conversation history (u0,a0,...,uk,ak); long histories truncated to keep token count <= 3500 with a "[NOTICE] 2r messages are omitted" marker (p.6). Greedy decoding (temperature=0) for reproducibility. Datasets split into Dev (269) and Test (1,014); all public. Code/data/toolkit released at github.com/THUDM/AgentBench.
- Safety / permission mechanism: no explicit safety or sandbox-permission framing beyond Docker environment isolation (used for conflict avoidance and resource isolation, not as a security boundary). Not reported as a safety mechanism.

What makes it age: it is text-only (no real GUI/vision; WB screenshots are optional and unused for scoring), uses only primitive CoT (no tool-augmented planning/reflection that modern harnesses assume), the model roster is entirely 2023-era (gpt-4-0613, claude-2, llama-2, vicuna, codellama; claude-3-opus and glm-4 added later as starred/post-hoc), and OSS is capped at <=70B. The fixed normalization weights are tied to this specific 2023 model pool, so OA scores are not directly comparable to a different model set. Several environments are static snapshots (Freebase, WebShop, Mind2Web pages) that drift over time.

## Method
Benchmark construction (Section 3, Appendices B-I):
- OS: 144 test samples; mix of human-annotated Stack Overflow-derived problems and gpt-4-generated QA filtered by unit tests; QA and Operation task types unified through a checking pipeline of scripts that must all exit 0 (p.21-22).
- DB: authentic SQL over real tables; data augmentation used; SR metric (Appendix C).
- KG: question answering over Freebase via KG tools; F1 metric (Appendix D).
- DCG (Aquawar): agent controls four fish vs an algorithmic opponent; win-rate/Reward metric (Appendix E).
- LTP: automatic host system answers yes/no/irrelevant; difficulty-leveled web puzzles simplified into plot points; Game Progress metric (Appendix F).
- HH (ALFWorld): household tasks ("put a pan on the dining table"); SR metric (Appendix G).
- WS (WebShop): search/view/choose items; Reward metric (Appendix H).
- WB (Mind2Web): cross-domain web tasks via click/type/select on HTML elements; Step SR metric, adapted to prompted LLMs without fine-tuning (Appendix I).

Evaluation protocol: two-role dialogue (user = instruction+environment feedback, agent), CoT Thought+Action in one round, 1-shot format demonstration in the instruction, greedy decoding, history truncated to ~3500 tokens. Five finish-reason categories defined (p.3-4): Context Limit Exceeded (CLE), Invalid Format (IF), Invalid Action (IA), Task Limit Exceeded (TLE), and Complete.

Overall score: per-task average rescaled to 1 across all evaluated models, fixed reciprocal-mean weights stored for reuse, OA = mean of weighted per-task scores (p.7). Total inference ~3k (Dev) + ~11k (Test) calls, calibrated to be comparable to MMLU's call count (p.6).

## Experimental setup
- Benchmarks: the 8 AgentBench environments (Dev 269 / Test 1,014 samples).
- Models: 29 LLMs (Table 1 p.3). API-based: gpt-4 (0613), gpt-3.5-turbo (0613), text-davinci-002/003, claude-3 (opus, starred), claude-2, claude (v1.3), claude-instant (v1.1), chat-bison-001, glm-4 (starred). OSS (<=70B): llama-2-7b/13b/70b, codellama-7b/13b/34b, vicuna-7b/13b/33b, guanaco-33b/65b, wizardlm-13b/30b, openchat-13b, koala-13b, oasst-12b, dolly-12b, chatglm-6b, codegeex2-6b. Models marked * (claude-3, glm-4) were evaluated after the task weights were already fixed (p.3).
- Baselines: no method-level baseline; the comparison is across the 29 models themselves under identical prompting.
- Metrics: per-env SR/F1/Reward/Game Progress/Step SR (Table 2); OA weighted aggregate.
- Compute/cost: Not reported in dollar/GPU terms; acknowledgement notes Zhipu AI covered all GPU and API cost (p.9). OSS capped at <=70B due to compute limits.
- Artifacts: datasets, environments, and integrated toolkit released (github.com/THUDM/AgentBench).

## Key results
Test set (standard) OA scores, Table 3 p.7 (VERIFIED against extraction):
- gpt-4 = 4.01 (best overall); claude-3 = 3.11; glm-4 = 2.89; claude-2 = 2.49; claude = 2.44; gpt-3.5-turbo = 2.32; text-davinci-003 = 1.71; claude-instant = 1.60; chat-bison-001 = 1.39; text-davinci-002 = 1.25.
- Best OSS <=70B = codellama-34b = 0.96 (CLAIMED p.8 as most capable OSS, but still clearly below gpt-3.5-turbo's 2.32). Next OSS: vicuna-13b 0.93, llama-2-70b 0.78, llama-2-13b 0.77.
- Average OA: API-based 2.32 vs OSS 0.51 (VERIFIED, p.8 and Figure 1b). This is the headline commercial-vs-OSS gap. All API-based LLMs scored above 1.00 (p.7).
- gpt-4 per-environment (Table 3): OS 42.4, DB 32.0, KG 58.8, DCG 74.5, LTP 16.6, HH 78.0, WS 61.1, WB 29.0. gpt-4 is best on 6 of 8 environments (CLAIMED p.7); on House-Holding it reaches 78% SR (EVIDENCE Table 3).
- Failure analysis (Table 4 p.8, portions averaged across all models): the dominant failure is Task Limit Exceeded (e.g., LTP 82.5, KG 67.9, WB 35.0, WS 27.8, OS 23.9), indicating weak long-term reasoning/decision-making. Invalid Format dominates in DB (53.3) and DCG (38.5) due to strict formatting; Invalid Action dominates in HH (64.1) where models generate out-of-space actions.
- Analyses (Section 4.3): code training is "a double-edged sword" -- codellama edges llama-2 on procedural tasks (Web Shopping) but underperforms on Digital Card Game and OS (CLAIMED p.8; comparative, no significance testing). High-quality alignment helps: vicuna-13b (ShareGPT/gpt-4-distilled data) beats llama-2-13b and rivals 3x-larger codellama-34b (CLAIMED p.8). Surprisingly llama-2-13b and llama-2-70b score similarly (0.77 vs 0.78), attributed to possible under-training/under-alignment of the 70B (CLAIMED p.8, re-run to confirm).

## Evidence quality
- Strong: real executable environments and outcome-based metrics (SR/F1/reward) rather than text overlap; broad model coverage (29); a documented, reproducible protocol (greedy decoding, fixed weights, public splits, released toolkit); a structured failure taxonomy backed by Table 4.
- Weak/uncertain: no statistical significance, no variance/error bars (greedy single-run means n=1 per item, so no run-to-run variance) -- UNCLEAR how stable small score differences (e.g., llama-2-13b vs -70b) are despite the "re-ran experiments" remark (p.8). The mechanistic claims (code training double-edged, alignment helps) are pairwise model comparisons, not controlled ablations, so they are suggestive rather than causal. The OA metric depends on a model-pool-specific normalization, so absolute OA numbers are not portable. claude-3 and glm-4 were scored after weights were fixed (starred), a minor inconsistency. Possible train/test leakage is not deeply audited for adapted datasets (WebShop, Mind2Web, Freebase), though tasks are interactive which mitigates pure memorization.

## Reproducibility and artifacts
- Code: Released -- github.com/THUDM/AgentBench (Server-Client toolkit, HTTP-based).
- Data: Dev (269) + Test (1,014) splits, stated publicly available.
- Models: 29 listed in Table 1; API model versions pinned (e.g., gpt-4-0613); OSS versions/sizes given.
- Environment: Docker images per task; isolated workers; resumable evaluation; max-flow scheduling.
- License: Not reported in extraction.
- Exact commands or setup: Not in paper body; users set up an HTTP-accessible model server (p.6). Prompt templates given in Appendices B-I.
- Missing details: dollar/GPU compute budget; per-item variance; exact license; full leakage audit.

## Strengths
- First systematic multi-environment LLM-as-agent benchmark with a clean POMDP framing.
- Realistic, executable, outcome-graded environments (bash/SQL/KG/web) instead of static QA.
- Engineering quality: decoupled HTTP S/C toolkit, Docker isolation, max-flow scheduling, resumable runs -- genuinely reusable harness design.
- Broad, well-documented model roster and a useful failure taxonomy (TLE/IF/IA) that identifies actionable weaknesses.

## Weaknesses and limitations
- Author-stated: even gpt-4 is not a practically usable agent; OSS capped at <=70B for compute; only primitive CoT used (no advanced reasoning strategies).
- Inferred: text-only (ignores GUI/vision; WB screenshots unused); OA normalization is model-pool dependent and non-portable; no significance/variance reporting; mechanistic claims are uncontrolled pairwise comparisons; environments are 2023 snapshots subject to drift; starred post-hoc models break the fixed-weight assumption slightly.

## Relationship to prior work
- Builds directly on ReAct (Yao 2023b) for the Thought+Action prompting format, and reuses/adapts WebShop (Yao 2022), Mind2Web (Deng 2023), and ALFWorld/TextWorld (Shridhar 2020b / Cote 2019).
- Contrasts with single-environment or text-game-only agent benchmarks and with code-only functional benchmarks (HumanEval, APPS, MBPP) that lack multi-round interaction.
- Concurrent InterCode (Yang 2023) covers interactive Bash/SQL, overlapping with AgentBench's OS/DB but narrower in scope (p.9).
- Genuinely new: the multi-grounding aggregation into one benchmark + reusable HTTP/Docker/max-flow toolkit + the cross-model commercial-vs-OSS gap quantification. The individual web/household environments are adapted rather than novel.

## What I should read
- Must read: Section 3 (environment composition), Section 4.1-4.2 (setup + Table 3 main results), Table 4 + Section 4.3 (failure taxonomy and analyses), Figure 4 p.19 (per-env observation/action interfaces).
- Skim: Appendix A (S/C framework + max-flow) for harness-design ideas; Appendix B (OS construction) as a representative environment build.
- Can skip: per-environment prompt dumps (Appendices C-I) unless reproducing a specific task; the reference list.
- Follow-up papers: ReAct, WebShop, Mind2Web, ALFWorld; later harnesses WebArena, SWE-bench, OSWorld, tau-bench for how this template evolved.

## Triage decision
Label: READ_SOON
Rationale: Foundational, frequently cited reference for agent-harness design and LLM-as-agent evaluation; directly relevant to harness/benchmark interests. Evidence is solid for its headline gap claim (API avg 2.32 vs OSS 0.51; gpt-4 4.01 vs best OSS codellama-34b 0.96) though analyses are correlational and numbers are dated. Worth reading soon for design precedent rather than for current SOTA numbers; not elevated to MUST_READ because the model roster and text-only scope are now superseded.
Confidence: high
Reading time estimate: ~60-75 min for main text + Appendix A and Figure 4; full appendix several hours.

## Personal notes
The reusable bits are the harness architecture (decoupled HTTP servers, Docker-isolated workers, max-flow scheduling, resumable eval) and the per-env action/observation table (Figure 4). The OA weighting trick is clever but locks comparisons to the 2023 model pool -- treat OA as ordinal within this paper, not as an absolute scale.

## Follow-up actions
- Add related paper: WebArena, SWE-bench, OSWorld, tau-bench (successor harnesses).
- Compare with: InterCode (interactive Bash/SQL), Mind2Web (web-agent grounding).
- Re-run after new version: extraction is arXiv v3 (Oct 2025) of a v1 dir -- check whether later versions add models/environments.
- Check code: github.com/THUDM/AgentBench (toolkit, Docker images, scheduling).
- Read benchmark details: Appendix B (OS) and Appendix I (Web Browsing/Mind2Web) for interface specifics.
