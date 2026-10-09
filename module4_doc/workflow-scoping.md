# Workflow Scoping: Governed Ticket-to-Implementation Support

This supersedes `docs/prd.md` in scope (that document remains as the historical record of the narrower Module 1 "build health check" exercise). The capstone's actual workflow is the one this project has genuinely operated for most of its life: an orchestrated pipeline that takes a real development task through planning, implementation, independent review, testing, and governed commit, with a human approving every commit.

## Workflow description

A developer states a task (a feature, a fix, a test addition) to the Orchestrator. The system plans the change, implements it, independently reviews the diff against the plan and against Spring Boot conventions, verifies it builds and passes tests (deterministically, `ADR-001`), and presents a complete run summary for human approval before any commit. Every subagent's tool access is scoped and server-side enforced (`ADR-005`); every decision traces to a reason, not habit (`ADR-007`).

## Stakeholder

A developer (or small team) maintaining a Spring Boot microservices codebase who wants routine implementation work handled with less manual overhead, without giving up independent verification or review.

## Trigger

A developer states a task in natural language to a running Orchestrator session (e.g., "Add validation to placeOrder() so a negative or zero productId is rejected with a 400 before any Feign call is made").

## Inputs

The task description; the current state of the four-service codebase; prior project memory (`.memory/project/`, `.memory/reference/`); coding standards (`.memory/knowledge/`).

## Outputs

A reviewed, tested, human-approved commit (or an explicit, reasoned stop if the task can't be completed safely); a structured evaluation transcript (`.eval-artifacts/runs/`) recording every step, decision, and piece of evidence.

## Acceptance criteria

- The plan names exact files/methods and stays within the requested scope (`planner`, evaluated by `orchestrator_plan_review`).
- The diff matches the approved plan -- confirmed via `git diff --ignore-all-space`, not asserted.
- Tests pass, verified deterministically (`scripts/parse_test_result_deterministic.py`), not narrated.
- No MCP tool call occurs outside the calling role's allow-list (server-enforced, `ADR-005`).
- The human sees a complete run summary -- plan, diff, test result -- before any commit, every time, regardless of whether the run appeared to go smoothly.

These are tight enough to pass/fail a run without asking the author for clarification: either the diff matches the plan or it doesn't; either the deterministic parser reports `valid: true` or it doesn't; either the human approved or didn't.

## Failure modes (each with a real, observed instance, not hypothetical)

- **Scope drift** -- `planner`/`implementer` doing more than asked. Observed: `HO-01`'s unprompted circuit-breaker planning, Module 3.
- **Role boundary violation** -- a role attempting an operation outside its grant. Observed and now blocked server-side: the Orchestrator's `update_entry` near-miss, `HO-06`; re-verified denied after the `ADR-005` fix.
- **Self-declaration exploitation** -- a role claiming an identity it isn't. Documented as an accepted, architecturally-forced limitation (`CLAUDE.md`), not silently assumed safe -- confirmed in a real test where the Orchestrator declined to exploit a known gap even though it technically could (`eval/red-team-results.md`, Prompt 4).
- **Stale evidence treated as current fact** -- `decision-005.md`'s commit status, wrong and independently rediscovered four separate times before being fixed.

## Demo requirements

A real task run, start to finish, showing: the plan, an independent review catching or confirming something specific, the deterministic test step, and the human approval gate -- plus one instance of governance correctly blocking an out-of-scope attempt (`eval/red-team-results.md` provides several real candidates).

## Delivery path

**Job-seeker / no-deployment path.** The pipeline runs on a representative workload: the four-service Spring Boot e-commerce application built in this course (`ecom-*`), taken through real engineering tasks against it (validation, retry logic, test coverage, endpoints). No internal, customer, or production data is used, so no approvals were required.

**Constraints, stated honestly.** There is no live team and no real ticket queue, so there is no pre-existing manual process to baseline against (see "Baseline pain" below). The human checkpoint is a single developer, not a reviewer pool. Run volume is small, dozens of runs rather than thousands, and cost and latency figures come from single-developer sessions.

**What would change in a real deployment.** Roles would become verified process identities instead of self-declared strings (`ADR-005`). The allow-lists and audit logs would live in shared infrastructure, not a local container. Tasks would arrive from a ticket system and results would return as pull requests. A team baseline (review turnaround, defect escape rate) would replace the cited industry context. Approvals for any internal data would be documented before the first run.

## Why a custom orchestrated pipeline, not simpler automation or a prebuilt agent

A single-shot prebuilt coding agent (no planning/review split, no persistent memory, no governance layer) was considered and rejected implicitly through this project's own evolution: Module 1-2's early, simpler agent definitions were specifically found to need the plan/implement/review split once self-reports proved unreliable without independent verification (handbook, Module 1-2 sections: "an agent's own closing summary is a claim, not evidence"). A simpler CI linter or static-analysis-only tool was rejected because the actual, recurring failure modes observed in this project (scope drift, role-boundary violations, stale-evidence-treated-as-fact) are about *agentic judgment and process*, not static code properties a linter can catch.

## Baseline pain

**No live team's pre-existing manual process exists for this specific project to measure against** -- this is a learning project, not an automation retrofit of an established team workflow. Two separate, clearly-labeled kinds of evidence are used instead of inventing a false "before" number:

**Cited industry context** (external, not measured by this project): published industry data consistently shows code review and related coordination overhead consumes a substantial share of developer time -- Google's own internal engineering-productivity research reports developers spending an average of 6.4 hours per week on code review activities; separate industry surveys (SonarSource, Infragistics) report that routine coding itself is typically only 20-40% of a developer's working time, with the remainder spent on review, coordination, and verification overhead. These figures describe the general category of work this workflow addresses -- they are not claims about this specific project's own prior state.

**Our own measured evidence** (real, from this project): the `orchestrator_test` conversion (`ADR-001`) measured a ~264x latency reduction and complete token-cost elimination for one concrete, high-frequency verification step, by replacing LLM narration with deterministic parsing -- real, repeatable numbers from `module3_doc/calibration-log.md`, not estimated. This is offered as direct evidence of what rigorous measurement *within* this system looks like, distinct from the external context above.
