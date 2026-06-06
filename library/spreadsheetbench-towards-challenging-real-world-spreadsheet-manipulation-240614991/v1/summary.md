# SpreadsheetBench: Towards Challenging Real World Spreadsheet Manipulation

## Metadata
- Canonical key: arxiv-2406.14991
- Version: v1
- Fetch date: 2026-06-06T07:57:29Z
- Source: arxiv
- PDF: library/spreadsheetbench-towards-challenging-real-world-spreadsheet-manipulation-240614991/v1/paper.pdf
- Venue: Neural Information Processing Systems (NeurIPS 2024, Datasets and Benchmarks Track)
- Year: 2024
- Authors: Zeyao Ma, Bohan Zhang, Jing Zhang, Jifan Yu, Xiaokang Zhang, Xiaohan Zhang, Sijia Luo, Xi Wang, Jie Tang
- Tags: foundational
- User status: unread
- Triage label: READ_SOON
- Triage confidence: high

## One-sentence takeaway
SpreadsheetBench is a 912-instruction / 2,729-test-case benchmark of real Excel-forum spreadsheet manipulation tasks, evaluated with an online-judge-style metric (multiple per-instruction spreadsheet test cases), on which the best LLM (GPT-4o) reaches only ~18% overall soft accuracy versus ~71% for human Excel experts (p3, p6 Table 1, p8-9 Table 2).

## Why this paper matters
This is a benchmark/data paper for the office/data-agent space: it targets the specific failure mode where prior spreadsheet benchmarks (SheetCopilot, SheetAgent/SheetRM, InstructExcel) use synthesized instructions over simplified single-table sheets and a single test per instruction, which inflates scores via solutions that overfit one spreadsheet (p1-2, p6 Table 1). The contribution most relevant to a harness builder is the evaluation design: instead of one input/output pair, each instruction gets multiple structurally-similar but value-perturbed spreadsheet test cases, and a code solution must pass them — directly analogous to how SWE/coding harnesses use hidden tests to defeat overfitting. The large measured human–LLM gap (CLAIMED as "substantial," and the EVIDENCE supports it) makes this a useful difficulty anchor for office agents.

## Problem and gap
The paper attacks three limitations of prior LLM spreadsheet benchmarks (p1-2):
1. Instructions are synthetic (self-instruct in SheetCopilot/SheetRM) or simple crowd-written prompts (InstructExcel, avg 9.8 words), unlike real users who supply long context, prior failed attempts, error messages, and output examples (avg 85.7 words here; p6 Table 1).
2. Spreadsheets are over-simplified single relational tables, ignoring real-world structures: multiple tables per sheet, non-standard tables (nested / incomplete / missing headers), free-form text in cells, and non-textual elements (color, bold) (p2).
3. A single test per instruction yields false positives — a solution tailored to one spreadsheet's specific values that does not generalize (p2).

WHY-read: the test-case-perturbation framing (Section 2.2, 2.4) is the load-bearing idea; if you only remember one thing, it is that robustness to value changes is measured, not assumed.

## Core idea
Build the benchmark exclusively from real solved forum/blog posts, condense each into a self-contained instruction with an explicit answer position (cell-level = exact cells like "D2:D6"; sheet-level = full range like "A2:D6"), and for each instruction construct three spreadsheet test cases (the original plus two annotator-perturbed copies that re-run the same solution and target corner cases such as cells that should be empty rather than zero) (p4-5, Fig 2, Fig 13). Evaluation is online-judge style: the LLM produces one code solution from the instruction and a single spreadsheet, and that one solution is applied to all test cases of the instruction; scoring is cell-level exact match of the answer position, with a soft (IOI-style partial credit per passed test case) and a hard (ICPC-style all-or-nothing) variant (p7, Eq. 1 and 2).

## Harness relevance
Adapted to a data/office-agent BENCHMARK:
- Artifact under manipulation: an XLSX spreadsheet file (chosen for cross-software portability across Excel, Google Sheets, LibreOffice, WPS; p5-6). The output artifact is the modified spreadsheet.
- Environment / workspace: a spreadsheet file plus the instruction, an `instruction_type` flag, an `answer_position`, and the first few rows of content rendered as a pandas-style preview in the prompt (p37 Fig 25/26). No live application GUI for the LLM track — interaction is via generated Python code.
- Observation interface: text only — instruction text plus the initial N rows (default 5) of the sheet; in the multi-round setting the model can additionally emit code to read more of the file and receives execution output / error tracebacks (p8, p37-38 Fig 25/26).
- Action interface / editing granularity: the agent writes a code-based solution (Python via openpyxl/pandas is shown; forum-native solutions are formulas or VBA) that edits cells or ranges. Granularity is explicitly cell-level (specific cells/ranges) vs sheet-level (a bounded range covering whole-sheet edits) (p3 Section 2.1, p4). It is software-independent code, not Excel-API calls.
- Tool/API/shell layer: a Python execution environment that runs the generated code against each test-case input and produces an output XLSX (p8). Spreadsheet-specific products (SheetCopilot, Copilot in Excel) are instead driven manually by the authors inside Google Sheets / Excel (p8).
- Planner/executor/verifier structure: single-round = one-shot code generation; multi-round = ReAct + code-execution feedback over up to 5 rounds, where the model chooses between "acquire spreadsheet info" and "emit final solution," with error tracebacks fed back for refinement (p8, p38 Fig 26). The verifier is the OJ harness.
- Evaluation harness (online-judge style with multiple spreadsheet test cases): one model inference produces one solution, applied to all (avg 3) test cases per instruction; a test case is ACCepted if the resulting spreadsheet's answer-position cells exactly match ground truth. Soft = mean fraction of test cases passed; hard = 1 only if all test cases pass (p7, Eq. 1/2). Crucially, only one inference per instruction is needed (contrast with per-sample-perturbation TQA robustness benches; p7).
- Are output artifacts structurally validated? Partially. Validation is exact-match on the annotated answer-position cells only, NOT a full-workbook structural diff. The authors report this causes false negatives when correct solutions emit extra content (e.g., extra rows or re-added headers): test-case-level false omission rate 3.8%, instruction-level false negative 4%; false discovery / false positive rates are 0% (p19-20 Appendix D.3, Fig 20/21). So the harness never wrongly accepts but can wrongly reject when the artifact has extraneous structure.
- Training harness: none — this is an eval-only benchmark; no models are trained.
- Logging / trace / reproducibility: prompts for both settings are given verbatim (Fig 25/26), hyperparameters (temperature 1, top_p 1) and hardware (8x A100 80GB) are reported (p17 Appendix C). No error bars in the main Table 2 (Checklist 3c: omitted due to API cost), though the supplementary Table 5 reports ±std over 4 runs for two GPT models on a 200-sample subset.
- Contamination / aging: explicitly addressed via three anti-leakage perturbations — GPT-4-plus-human instruction rewriting (so models cannot memorize forum question text), spreadsheet value modification (cannot memorize original sheets), and answer-position relocation (the original forum solution cannot be reused verbatim) (p5). UNCLEAR how durable this is: the underlying forum content is public web text and the benchmark is static; the soft-vs-hard gap and the corner-case design mitigate but do not eliminate aging risk as models improve. The forums themselves ban AI-generated Q&A, which the authors cite as supporting authenticity (p15 B.1).

## Method
Four-stage construction pipeline (p3-5, Fig 2):
1. Data sourcing — four Excel forums/blogs (ExcelForum, Chandoo, MrExcel, ExcelGuru) chosen via Google Search, Feedspot, Deskbright; target categories include General, Formula, VBA/Macros, Formatting, Pivot Table, Power Query.
2. Data filtering — keep posts that are (i) solved (explicit tag, else GPT-4 classifies), (ii) purely spreadsheet manipulation (drop software/UI questions like input boxes, buttons, forms via keywords + annotators), (iii) feasible and testable (must have an attachment, not excessive replies, unambiguous), (iv) representative (high view counts; keep both easy and hard).
3. Data formatting — GPT-4 condenses dispersed replies into a self-contained instruction, annotators verify; annotators derive the answer by applying the forum solution to the sheet and annotate the answer position (cell-level exact cells or sheet-level full range).
4. Test-case construction — derive the original input/output pair, then annotators modify the input sheet twice (focusing on real corner cases, e.g., empty-vs-zero), re-running the solution to get new answers, yielding three test cases per instruction. Dataset thus shifts from D = {(q, c, a)} to D = {(q, {(c_ij, a_ij)})}.

Quality control: 20 Excel-specialist annotators (all bachelor's), two validators, plus two author master's-level secondary checks (p6). Software-independence enforced via software-independent instruction selection, XLSX files, and code-based (not Excel-API) inference (p5-6).

Statistics (p3, p6): 912 instructions, 2,729 test cases (avg ~3); 10 primary manipulation categories (find, extract, sum, highlight, remove, modify, count, delete, calculate, display); tables exceeding 100 columns and 20,000 rows; 35.7% multiple tables; 42.7% non-standard relational tables. Note a minor internal inconsistency: the abstract/intro say multiple tables 35.7% / non-standard 42.7% (p3) while p6 Section 2.3 says "more than one-third" multiple and "nearly half" non-standard; Table 1 lists 2,019 single-sheet vs 710 multiple-sheet files.

## Experimental setup
- Benchmark: SpreadsheetBench (this paper).
- Baselines across 5 categories (p8): TableQA — TaPEx (400M), TaPas (340M), Binder (GPT-3.5); open code — CodeQwen1.5 (7B), DeepseekCoder (33B); open general — Mixtral-8x7B (47B), Llama-3 (70B); closed — GPT-3.5, GPT-4o; spreadsheet products — SheetCopilot (GPT-4) and Copilot in Excel.
- Models / metrics: soft restriction and hard restriction, each split into cell-level / sheet-level / overall (p9 Table 2).
- Inference: single-round (one-shot code from instruction + 5 rows) and multi-round (ReAct + execution feedback, max 5 rounds); unified temperature 1, top_p 1.
- Human performance: 4 Excel-expert annotators on a 50-instruction × 3-test-case subset, providing formula/VBA solutions, completed in one day (p8).
- Sampling caveats: spreadsheet products (SheetCopilot, Copilot in Excel) evaluated manually on only 50 instructions with 1 test case each due to cost (p8, p17); product numbers are therefore not directly comparable to the full-benchmark LLM numbers.
- Compute: 8× NVIDIA A100 80GB, Ubuntu 22.04, vLLM/transformers (p17). Code/data: GitHub site referenced (spreadsheetbench.github.io); license CC BY-SA 4.0 (p14 A.4).

## Key results
Verified against extraction (p9 Table 2, percentages):
- GPT-4o (SOTA LLM), single-round: soft cell 15.03 / sheet 23.65 / overall 18.35; hard cell 11.94 / sheet 19.94 / overall 15.02. Multi-round slightly lower (soft overall 16.96), attributed to GPT-4o redundantly re-reading already-provided rows (p9).
- Human performance: soft cell 75.56 / sheet 65.00 / overall 71.33; hard overall 62.00 — far above every model (CLAIMED "substantial gap"; EVIDENCE strongly supports).
- Score range across all methods: 0.05% (Binder sheet-level soft, the floor) to 23.65% (GPT-4o sheet-level soft) per p3 / Table 2. TaPEx and TaPas score zero across all metrics (omitted from table), underscoring TableQA ≠ spreadsheet manipulation (p8).
- Products (sampled, 50 instr / 1 test case): Copilot in Excel overall 20.00 (cell 23.33 / sheet 15.00); SheetCopilot (GPT-4) overall 14.00 (cell 16.67 / sheet 10.00) — note these are not on the full 912 set.
- Multi-round helps most weaker LLMs substantially (some ~10x, e.g., GPT-3.5 overall soft 2.34 → 7.09), but not GPT-4o (p9).
- Analysis (p8-9 Table 3, GPT-4o soft): performance drops with complexity — Rows ≤50: 20.63 vs >50: 11.50; Cols ≤10: 22.50 vs >10: 10.51; single table 21.12 vs multiple 13.71; relational 19.50 vs non-standard 16.95. Increasing prompt rows from 5→10 does not help (excess context); GPT-4o gains little from rounds.
- Metric reliability (p19-20): false discovery 0%, false positive 0%, false omission 3.8%, false negative 4% — the metric under-credits but never over-credits.
- Supplementary (p18 Table 5, 200-sample subset, 4 runs): GPT-4o single 12.79±1.71 soft; best multi setting (Execution Feedback + 5 rows) 16.08±1.08; here GPT-4o DOES benefit from multi-round on average, reconciling the main-table anomaly as run-to-run variance (UNCLEAR which presentation should be treated as canonical; authors call the averaged one more reliable).

## Evidence quality
Strong on the central claims. The human–LLM gap is large and consistent across soft/hard and cell/sheet, so the "substantial gap" claim is well supported. The OJ-metric reliability study (DS-1000-style FDR/FOR indices, p19-20) is a genuine strength and quantifies the harness's bias direction (under-credit only). Weaknesses: (1) main Table 2 has no error bars (acknowledged, cost-driven), and the GPT-4o single>multi result is shown in the appendix to be within run variance — so single-vs-multi conclusions from Table 2 alone are fragile. (2) Product numbers (SheetCopilot, Copilot in Excel) come from a hand-evaluated 50-instruction / 1-test-case subset, breaking the OJ multi-test-case premise for exactly those systems and making cross-comparison apples-to-oranges. (3) Closed-model versions/dates are thin (GPT-4o dated 2024-05-13 only via figure paths; GPT-3.5 unversioned). (4) Anti-leakage is plausible but unmeasured — no contamination probe is reported, only the design argument.

## Reproducibility and artifacts
- Code: referenced via project site spreadsheetbench.github.io / GitHub (p1, p14); not inspected here.
- Data: 912 instructions, 2,729 test-case XLSX pairs; raw forum data will NOT be redistributed (copyright), only the processed benchmark (p14 A.3-A.4).
- Models: all baselines listed with sizes and HF/GitHub URLs (p17 Table 4).
- Environment: 8× A100 80GB, Ubuntu 22.04, PyTorch/transformers/vLLM; products evaluated on Windows 10 / macOS in Google Sheets and Excel (p17).
- License: CC BY-SA 4.0 (p14).
- Exact commands/setup: prompts verbatim (Fig 25/26); hyperparameters temperature 1 / top_p 1; max 5 rounds.
- Missing details: no per-model seeds/error bars in main results; product-evaluation protocol only loosely specified; exact GPT-3.5 snapshot unspecified.

## Strengths
- Real-world sourcing with long, context-rich instructions (avg 85.7 words) and genuinely messy spreadsheets (multiple/non-standard tables, formatting, color).
- The multi-test-case online-judge metric is the standout contribution for harness design — it directly tests value-robustness with a single inference per instruction.
- Software-independent (code-based, XLSX) so results are not tied to Excel's API.
- Quantified metric reliability and explicit anti-leakage measures.
- Clear difficulty signal: large human gap, near-zero scores for TableQA models, monotone degradation with complexity.

## Weaknesses and limitations
- Author-stated (p14 A.1): data selection discards posts lacking acknowledged answers or hard to formalize (potential coverage bias); corner cases are not exhaustively engineered per question given the large size (weaker than true OJ rigor).
- Inferred: no error bars in the headline table; the single-vs-multi GPT-4o story is unstable across runs; product baselines evaluated on a tiny non-OJ subset; cell-level exact match under-credits structurally-correct-but-noisy outputs (4% instruction-level false negatives); static benchmark with public-web provenance carries residual contamination/aging risk despite perturbations.
- Minor internal stat inconsistency between abstract (35.7% / 42.7%) and Section 2.3 prose ("more than one-third" / "nearly half").

## Relationship to prior work
Closest: SheetCopilot/SheetCopilotBench [11] and SheetAgent/SheetRM [12] (self-instruct queries, simple single-table sheets, single test, exact match) and InstructExcel [14] (crowd instructions, avg 9.8 words, Excel-API/TypeScript, single test). SpreadsheetBench is genuinely new in (a) exclusively real forum-sourced, context-rich instructions, (b) flexibly-organized multi/non-standard-table spreadsheets, and (c) the multi-test-case OJ metric — versus prior single-test exact match. It deliberately excludes TableQA/Table-to-text/table-analysis benchmarks (CSV/JSON, QA-oriented) as out of scope. The OJ metric borrows IOI/ICPC scoring conventions and DS-1000's reliability indices.

## What I should read
- Must read: Section 2.2 (construction + anti-leakage) and Section 2.4 (OJ metric, Eq. 1/2) — the core harness ideas; Table 1 (p6) and Table 2 (p9) for positioning and the human gap.
- Skim: Appendix D.1-D.3 (inference-setting ablations and metric reliability) — important for trusting the numbers; Fig 25/26 prompts.
- Can skip: Appendix B.1 forum descriptions; case-study figures (6-21) unless you want qualitative failure modes.
- Follow-up papers: SheetCopilot [11], SheetAgent/SheetRM [12], InstructExcel [14]; DS-1000 [23] for the reliability-index methodology.

## Triage decision
Label: READ_SOON
Rationale: Directly relevant to office/data-agent harness design — its multi-test-case online-judge evaluation and cell/range editing granularity are reusable patterns, and the human-vs-LLM gap is a strong difficulty anchor. Not MUST_READ because it is an eval-only benchmark (no new agent/method) and some headline numbers lack error bars; evidence does not strongly differ from the assigned label.
Confidence: high
Reading time estimate: ~45 min for the must-read sections; ~90 min full with appendices.

## Personal notes
Key reusable harness idea: one code solution evaluated against multiple value-perturbed copies of the same artifact, scored soft (partial) and hard (all-or-nothing). The metric under-credits (0% false positive, ~4% false negative) because it exact-matches only the annotated answer range, not the whole workbook — worth noting if adapting for output-artifact structural validation. Numbers to remember: 912 instructions / 2,729 test cases (~3 each); GPT-4o ~18.35% overall soft vs human ~71.33%.

## Follow-up actions
- Add related paper: SheetCopilot (NeurIPS 2023), SheetAgent (2403.03636), InstructExcel (EMNLP Findings 2023).
- Compare with: coding harnesses using hidden tests (SWE-bench-style) — same overfitting-defense logic.
- Re-run after new version: arXiv v2 (17 Oct 2024) is the extracted version; check site for benchmark updates.
- Check code: spreadsheetbench.github.io / GitHub for the OJ evaluation harness implementation.
- Read benchmark details: Appendix D.3 metric reliability before reusing the metric.
