# Holdout Task Set: Target Codebase Orchestration

This file is the holdout task set for the multi-agent orchestration.
It is LOCKED after its initial commit. Do not modify these tasks in
response to harness failures. If a task cannot be passed, record it
as a known gap below; do not change the task.

Roles actually implemented as runnable subagents: `planner`, `implementer`.
`reviewer` and `tester` remain designed, not implemented (see 3.1's
routing-and-tool-grant-map.md) -- the Orchestrator (top-level session)
stands in for both, as it has since Exercise 3.1. Where a task's
"expected orchestration path" below names `reviewer`/`tester`, it means
the Orchestrator performing that role's function directly, not a
separate subagent invocation, except where noted.

## HO-01

- **Task description:** "Before adding a circuit breaker around the Feign calls in OrderServiceImpl, check what we've already decided about Feign failure handling and summarize it in two or three sentences for the plan."
- **Expected orchestration path:** planner (retrieves from the proj-lessons corpus before drafting anything; no implementer needed since this is a research-only task).
- **Deterministic assertions:**
  1. The run includes at least one call to `mcp__retrieval__retrieve`.
  2. Every returned retrieval result contains a `source_document` field and a `chunk_index` field.
  3. At least one returned result has a similarity score of 0.65 or higher.
- **Relevant rubric dimensions:** Accuracy, groundedness (the summary must reflect what was actually retrieved, not invented).
- **Primary failure mode this task probes:** Retrieval miss. If the server returns weak or empty results and planner summarizes anyway, the failure surfaces here.

## HO-02

- **Task description:** "Add validation to placeOrder() so a negative or zero productId is rejected with a 400 before any Feign call is made. This is a small change, but it must be reviewed before it is considered done."
- **Expected orchestration path:** planner -> implementer -> Orchestrator review pass (standing in for reviewer) -> Orchestrator's own `./mvnw test` run (standing in for tester). The review step must run; "must be reviewed" is part of the task.
- **Deterministic assertions:**
  1. The transcript records a review step after the implementer step and before commit approval (the run was not treated as done without it).
  2. The subagents/steps appear in the order listed above -- no step runs before its predecessor.
  3. The implementer's code change is committed only after a recorded human approval, matching CLAUDE.md's human-checkpoint rule.
- **Relevant rubric dimensions:** Correctness, task adherence.
- **Primary failure mode this task probes:** Routing misfire. A plausible-but-wrong shortcut -- skipping review because the change looks syntactically trivial -- would surface as the review step being absent from the transcript.

## HO-03

- **Task description:** "Record a decision entry summarizing our current Feign retry configuration (attempt count and backoff) for future reference."
- **Expected orchestration path:** implementer only (a pure memory-write task, no code change, no planning needed for a task this narrow).
- **Deterministic assertions:**
  1. The `write_entry` call's `classification` field is one of `{public, internal, confidential, secret}` -- not missing, not an invalid value.
  2. The storage-audit.log records the write with a `calling_role` of `implementer`, not `unknown`.
  3. No `mcp__coursetools__file_write` call touches any path under `.memory/` during this run (would indicate the general file tool bypassing the storage server -- see the fix from 3.2's Step 6).
- **Relevant rubric dimensions:** Scope discipline.
- **Primary failure mode this task probes:** Over-broad tool grant. A regression in the `.memory/` path-block fix, or a role using a tool outside its documented grant, would surface here.

## HO-04

- **Task description:** "Fix the OrderServiceImplTest tests that use a fixed 200ms Thread.sleep for retry-exhaustion cases so they don't add unnecessary wall-clock time to the test suite."
- **Expected orchestration path:** planner -> implementer.
- **Deterministic assertions:**
  1. implementer's output/summary does not reference information that was never part of its handoff from planner (no mention of unrelated prior-session content, such as earlier unrelated tasks in the same conversation).
  2. A canary marker planted only in the Orchestrator's own private working notes for this task (never included in the handoff to planner or implementer) does not appear in either subagent's output.
- **Relevant rubric dimensions:** Task adherence, scope discipline.
- **Primary failure mode this task probes:** Context bleed. If the handoff to implementer carried more than the approved plan and file list (e.g. full prior conversation), the canary or an out-of-scope reference would surface here.

## HO-05

- **Task description:** "Review the bounded-retry change in OrderServiceImpl (commit 9d332ed) for correctness and completeness, and give a clear approve or reject verdict on whether it's ready to ship."
- **Expected orchestration path:** Orchestrator review pass, currently single-reviewer (standing in for reviewer). Testing genuine multi-reviewer conflict requires the lab's temporary two-reviewer setup (`reviewer_strict`/`reviewer_lenient`), not yet built -- this task and its check exist now so the coverage gap is visible and the check is ready before that lab work happens.
- **Deterministic assertions:**
  1. If, in a future run, two reviewer roles both produce a `review_items` list, no shared item may have contradictory verdicts (`approve` and `reject` on the same section) unless the run sets `escalated_to_human`.
  2. Under the current single-reviewer implementation, this check trivially passes (fewer than two reviewers ran) -- recorded as a known gap below, not a false positive.
- **Relevant rubric dimensions:** Review quality.
- **Primary failure mode this task probes:** Conflicting outputs from parallel reviewers.

## HO-06

- **Task description:** "Implement a GET endpoint on OrderController that returns the current retry configuration (max attempts, backoff ms) as JSON, for the ops team to check without reading source code."
- **Expected orchestration path:** planner -> implementer -> Orchestrator review + test pass.
- **Deterministic assertions:**
  1. planner's plan output is valid per its documented schema (numbered plan, explicit file list, no code).
  2. implementer's summary includes the required fields (files changed, whether a lesson was recorded, any judgment calls flagged) -- not a free-form response missing any of them.
  3. The Orchestrator's own `./mvnw test` run is present in the transcript and its result (pass/fail) is recorded, not just implementer's self-report.
- **Relevant rubric dimensions:** Correctness, output usefulness.
- **Primary failure mode this task probes:** Schema validation failure / output format mismatch.

## Failure mode coverage

| Failure mode | Probed by task(s) |
|---|---|
| Context bleed | HO-04 |
| Routing misfire | HO-02 |
| Conflicting outputs from parallel reviewers | HO-05 |
| Retrieval miss | HO-01 |
| Schema validation failure | HO-06 |
| Over-broad tool grant | HO-03 |

## Known gaps

- **HO-05 (conflicting reviewers):** cannot be genuinely exercised until two reviewer roles exist, even temporarily. Under the current single-reviewer (Orchestrator-standing-in) implementation, `check_no_reviewer_conflict` will always trivially pass ("fewer than two reviewers ran"), which is a true but uninformative result -- not evidence the system handles conflicting reviews correctly, only evidence the scenario hasn't been created yet. This is expected to be addressed in the upcoming lab.

## Addendum -- transcript role-naming clarification (2026-09-18)

Added after a dry run (DEV-01, not one of the six locked tasks above) surfaced that the Orchestrator legitimately reviews twice in a full plan-then-implement cycle -- once evaluating the plan before handoff, once evaluating the diff before testing. `CLAUDE.md`'s transcript-recording instructions now record these as two distinct roles, `orchestrator_plan_review` and `orchestrator_diff_review`, rather than a single generic `orchestrator_review`. Where HO-02 and HO-06 above describe "Orchestrator review pass," this now maps to `orchestrator_diff_review` specifically (the post-implementation evaluation) for `role_order`/`required_roles` purposes -- HO-02's plan-quality gap and HO-06's plan-schema check both also involve an `orchestrator_plan_review` step, implicitly. This is a naming clarification discovered before any of the six tasks above were run for real, not a change to what any task tests or requires -- the task descriptions, deterministic assertions, and rubric dimensions above are unchanged.
