---
name: agent-computer-interface-aci
title: Agent-Computer Interface (ACI)
aliases:
- ACI
tags:
- agent-harness
- swe-agent
related_papers:
- arxiv-2405.15793
- arxiv-2310.06770
related_concepts:
- planner-executor-verifier
created: '2026-06-06T06:51:11Z'
updated: '2026-06-06T06:51:11Z'
---

# Agent-Computer Interface (ACI)

## Intuition
Think of an ACI as the "keyboard, screen, and house rules" you hand an LLM so it can
operate a computer without tripping over itself. A human SWE uses an IDE tuned for
humans; an LLM does better with a *different* interface tuned for a model — compact
commands, guardrails that prevent malformed edits, and feedback short enough to fit in
context. The ACI is that model-facing interface layer, and designing it well often
matters more than swapping the underlying model.

## Details
- The ACI sits between the agent (the LLM policy) and the environment (a repo, shell,
  browser, OS). It defines the **action space** (e.g. `open`, `scroll`, `edit`,
  `search_file`) and the **observation format** (what the agent sees back).
- Good ACI design principles from SWE-agent (`arxiv-2405.15793`): compact, guarded
  commands (an edit command that lint-checks and rejects a broken patch instead of
  silently corrupting the file); concise observations (paginated file views, not whole
  files); informative feedback (show the error and the relevant lines).
- The idea generalizes beyond code: a browser ACI exposes click/type/scroll; an OS ACI
  exposes shell + file ops. The interface choice (GUI vs CLI vs API) is itself an ACI
  decision and strongly affects success rates.

## Q&A
### Q: Why not just let the model use the same tools a human uses?
A: Human tools optimize for human perception and motor loops (rich GUIs, big screens).
Models have different bottlenecks — limited context, no persistent visual memory, and a
tendency to emit malformed actions. An ACI trades human-friendliness for model-friendly
properties: small action vocabularies, validation that fails loudly, and short
structured observations. SWE-agent showed this interface design alone moved SWE-bench
resolution rates substantially with the same base model.

### Q: How does this relate to the benchmark (SWE-bench)?
A: SWE-bench (`arxiv-2310.06770`) defines the *task and evaluator* (resolve a real issue,
judged by hidden tests) and deliberately does **not** prescribe an agent loop. The ACI
is the *scaffold* you build on top to actually attempt those tasks — so the benchmark
and the ACI are complementary layers of the same harness.

## See also
[[planner-executor-verifier]]
