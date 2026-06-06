# SWE-bench: Can Language Models Resolve Real-World GitHub Issues?

## Metadata
- Canonical key: arxiv-2310.06770
- Version: v1 (arXiv v3)
- Fetch date: 2026-06-06
- Source: arxiv
- PDF: library/swe-bench-can-language-models-resolve-real-231006770/v1/paper.pdf
- Venue: ICLR 2024 (accepted)
- Year: 2024
- Authors: Carlos E. Jimenez, John Yang, Alexander Wettig, Shunyu Yao, Kexin Pei, Ofir Press, Karthik Narasimhan
- Tags: foundational, benchmark, swe-agent, execution-based-eval, test-based-eval, environment, evaluation-harness
- User status: unread
- Triage label: MUST_READ
- Triage confidence: high

## One-sentence takeaway
SWE-bench turns 2,294 real merged GitHub issue→pull-request pairs from 12 Python repos into an execution-based benchmark where a model must edit a whole codebase to make the hidden, issue-resolving tests pass — and shows frontier models of the time resolved almost none of them.

## Why this paper matters
This is the foundational artifact that reframed "coding agent" evaluation from
function-level synthesis (HumanEval/MBPP) to **repository-level, execution-validated
issue resolution**. It defines the task formulation, the test-based evaluator, and the
contamination-resistant "issues after training cutoff" idea that essentially every
later SWE-agent harness (ACI/agent-computer-interface work, SWE-agent, and the
leaderboard ecosystem) builds on. For my software_engineering_agents and agent_harness
interests it is necessary context, not optional — most current papers report on a
SWE-bench variant.

## Problem and gap
Prior code benchmarks (self-contained functions, short contexts, single files) had
saturated and did not test what real software engineering demands: long-context code
understanding, cross-file/cross-function edits, and interaction with an execution
environment. The gap: a *realistic, scalable, and hard-to-game* benchmark whose ground
truth is grounded in real developer behavior rather than hand-written prompts.

## Core idea
Mine merged PRs that (a) close/resolve a GitHub issue and (b) modify the repo's test
files. The PR's gold patch is the reference solution; the touched tests become the
evaluator. A task instance gives the model the issue text + the repo at the pre-PR
commit; the model must produce a patch. Success = applying the model's patch makes the
relevant **fail-to-pass** tests pass while **pass-to-pass** tests stay green. Because
instances can be drawn continuously from new issues, the benchmark can refresh to dodge
training-data contamination.

## Harness relevance
- Environment/workspace: a real Python repository checked out at the pre-fix commit;
  the model operates on the full codebase.
- Observation interface: issue description + repository contents (paper's main
  experiments feed code via a BM25 **retrieval** step to fit context windows; an
  "oracle" retrieval setting supplies the gold files).
- Action interface: produce a unified-diff **patch file** applied with `patch`/git.
- Tool/API/shell layer: execution happens by installing the repo and running its test
  suite (per-repo install + test harness); this is the benchmark's core machinery.
- Planner/executor/verifier structure: the *verifier* is the repo's own tests
  (fail-to-pass + pass-to-pass) — the paper's most durable contribution. No agent loop
  is prescribed here; SWE-bench is the environment+evaluator, and agent scaffolds came
  later (SWE-agent).
- Evaluation harness: percentage of resolved task instances; execution-based, not
  similarity-based.
- Training harness: SWE-Llama is fine-tuned on 19k non-test task instances from 37
  repos (separate from the eval repos).
- Reproducibility: dockerized per-repo environments; instances dated for contamination
  control.
- Safety/permissions: not a focus (sandboxing of arbitrary repo test execution is
  implied but not the paper's emphasis).

## Method
Benchmark construction (p.3–4, §2.1): scrape PRs across 12 popular Python repos → keep
PRs that resolve an issue and edit tests → validate that the repo installs and that
there exist tests which go fail→pass with the gold patch → filter noise. Task
formulation (§2.2): input = issue + codebase; output = patch; metric = % resolved via
the test gates. Retrieval settings handle long contexts (BM25 vs. oracle file sets).
SWE-Llama (§4): CodeLlama fine-tuned on 19k held-out-repo instances to study whether
open models can be adapted to the patch-generation format.

## Experimental setup
- Dataset/benchmark: 2,294 test task instances (12 repos); ~19,000 training instances
  (37 repos) for SWE-Llama.
- Baselines/models: proprietary Claude 2, GPT-4 (and GPT-3.5), plus fine-tuned
  SWE-Llama 7B/13B. (Exact per-model table in the paper; some numbers below are the
  headline ones I verified in text.)
- Metrics: % of task instances resolved; also analysis of patch size, context length,
  and difficulty.
- Compute/cost: long-context inference is a stated practical constraint; precise
  $/compute not the focus — treat as Not reported in detail.
- Artifacts: benchmark, code, fine-tuned models, and leaderboard released.

## Key results
- Best-performing setting in the paper: **Claude 2 with a BM25 retriever resolves only
  1.96%** of issues — i.e., frontier models of late 2023 essentially fail the
  benchmark. This is the headline I confirmed verbatim in the text (§1, §5).
- Even the "oracle"/assisted-retrieval and best proprietary configurations remain in
  the low single-to-low-double-digit percent range; the exact per-model/per-setting
  breakdown is in the results table (read the table for precise numbers — I mark the
  individual cell values as "verify in Table" rather than restate from memory).
- Difficulty scales with context length and patch span; multi-file edits are
  especially hard.

## Evidence quality
Strong where it matters most: the evaluator is **execution-based** (real tests), which
is the right call and the paper's main methodological strength — it resists the
similarity-metric gaming that plagues code benchmarks. Claims about model weakness are
well supported by near-zero resolution rates. Caveats the reader should hold:
- Test-derived ground truth can be **under- or over-specified**: a model patch
  different from the gold patch may still be correct, and fail-to-pass tests may not
  fully characterize the issue (false negatives/positives are possible).
- Python-only, 12 repos → conclusions may not transfer across languages/ecosystems.
- Retrieval confound: low scores partly reflect the BM25 retrieval bottleneck, not only
  reasoning/editing ability; the oracle setting partially isolates this.
- Contamination is mitigated by date-based refresh in principle, but the released
  static split can still leak over time (a known, later-documented issue for the
  ecosystem).

## Reproducibility and artifacts
- Code: released (benchmark construction + evaluation harness).
- Data: 2,294 eval instances + ~19k train instances released.
- Models: SWE-Llama checkpoints released.
- Environment: per-repo install + dockerized execution.
- License: Not reported here (check the repo).
- Exact commands/setup: in the repo, not the PDF.
- Missing details: full compute/cost accounting; exhaustive per-setting tables live in
  the appendix.

## Strengths
- Defines the now-standard repository-level, test-validated SWE evaluation.
- Execution-based evaluator that is hard to game.
- Contamination-aware design (date-based, refreshable).
- Real developer-grounded tasks at meaningful scale; released artifacts + leaderboard.

## Weaknesses and limitations
- Ground-truth tests may not capture issue intent fully (specification gap).
- Python/12-repo scope limits external validity.
- Retrieval bottleneck conflates context access with reasoning in the headline numbers.
- No prescribed agent loop here (by design) — interactive scaffolding is future work.
- Static released split is contamination-susceptible over time.

## Relationship to prior work
Supersedes function-level benchmarks (HumanEval, MBPP, APPS) in realism by moving to
whole-repo, execution-validated tasks. Directly enables the SWE-agent / ACI line and
the many SWE-bench-Lite / Verified / Multimodal / multilingual derivatives. Genuinely
new at publication: the issue→PR→test mining pipeline and the test-gated metric;
incremental aspects are mostly in the modeling (SWE-Llama is a competent but not
central contribution).

## What I should read
- Must read: §2 (benchmark construction + task formulation + evaluation metric) and §5
  (results / why models fail) — these are the reusable ideas.
- Skim: §4 SWE-Llama fine-tuning; appendix construction filters.
- Can skip: per-repo distribution figures unless you need dataset statistics.
- Follow-up papers: SWE-agent (ACI), SWE-bench Verified, SWE-bench Multimodal, and
  current terminal/coding-agent harnesses that report SWE-bench numbers.

## Triage decision
Label: MUST_READ
Rationale: Foundational, accepted at ICLR 2024 (A*), defines the execution-based SWE
evaluation harness that nearly all of my software_engineering_agents and agent_harness
interests depend on; the recency penalty is intentionally bypassed via the
`foundational` tag.
Confidence: high
Reading time estimate: 60–90 min for §2 + §5 + skim of the rest.

## Personal notes
Free-form notes for later.

## Follow-up actions
- Add related paper: SWE-agent (ACI), SWE-bench Verified.
- Compare with: terminal-bench, OSWorld (for the broader computer-use harness lineage).
- Re-run after new version: track SWE-bench variants as separate canonical papers.
- Check code: princeton-nlp/SWE-bench repo for the evaluation harness internals.
- Read benchmark details: fail-to-pass vs pass-to-pass test selection logic.
