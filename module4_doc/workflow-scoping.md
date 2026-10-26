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

**Job-seeker / no-deployment path.** The pipeline runs on a representative workload: the four-service Spring Boot e-commerce application built in this course (`ecom-*`), taken through real engineering tasks against it (validation, retry logic, test coverage, endpoints). The orchestrated roles (planner and implementer) are scoped to its order service, and the Module 1 build check covers all four services. No internal, customer, or production data is used, so no approvals were required.

**Constraints, stated honestly.** There is no live team and no real ticket queue, so there is no pre-existing manual process to baseline against (see "Baseline pain" below). The human checkpoint is a single developer, not a reviewer pool. Run volume is small, dozens of runs rather than thousands, and cost and latency figures come from single-developer sessions.

**What would change in a real deployment.** Roles would become verified process identities instead of self-declared strings (`ADR-005`). The allow-lists and audit logs would live in shared infrastructure, not a local container. Tasks would arrive from a ticket system and results would return as pull requests. A team baseline (review turnaround, defect escape rate) would replace the cited industry context. Approvals for any internal data would be documented before the first run.

## Why a custom orchestrated pipeline, not simpler automation or a prebuilt agent

Three alternatives were weighed against this project's own evidence.

**A single-shot prebuilt coding agent (no planning and review split, no persistent memory, no governance layer).** Rejected, with evidence from this project:
- The agent's own closing summary is a claim, not evidence. In the Module 1 re-runs, the ungoverned control (governance removed) also reported "Warnings/errors: None" falsely (Control 2). A single agent has no independent check to catch that, and the human reviewer caught it only with an answer key (`module4_doc/module1-comparison.md`).
- Nothing in an unrestricted agent stops a role from acting outside its job. The Orchestrator's `update_entry` call succeeded in a real run because nothing checked who was calling (`HO-06`, `.eval-artifacts/holdout-run-1/HO-06.log`, line 2). The scoped roles and server-side allow-lists exist because of that incident.
- The price of the extra control is measured and small: governance cost about 32% more per run (about $0.12) and about 1 more minute (`module4_doc/module1-comparison.md`). This task does not show governance improving accuracy, and we do not claim it does. What it buys is blocked actions, an audit trail and a human checkpoint, which the red-team results show (`eval/red-team-results.md`).

**Simpler automation (a CI step, a lint, a static-analysis tool, or a script).** Partly accepted, and this is the right-tool argument itself. Wherever a fixed rule is enough, this project uses one: the test-result check was converted to deterministic code (`ADR-001`, about 264x faster at zero token cost), the role checks are deterministic (`_authorize()`), and the CI gates are deterministic. A script cannot do the planning, implementing and independent review steps, which require judgment on open-ended input (`docs/step-classification.md` classifies each as not a conversion candidate). The recurring failures seen here, such as scope drift, role-boundary violations and stale records treated as fact, are about process and judgment, not static code properties a linter can catch. The Module 1 warning scan is itself a candidate for a fixed-rule script, and is recorded as one.

**A human doing the work by hand.** This is the before-state: 45 minutes or more per check (estimate), against 2.5 minutes of review plus about 3.6 minutes of unattended agent time (measured).

## Baseline pain

**No live team's pre-existing manual process exists for this specific project to measure against** -- this is a learning project, not an automation retrofit of an established team workflow. Two separate, clearly-labeled kinds of evidence are used instead of inventing a false "before" number:

**The reviewer's own estimate for the Module 1 check.** Running the four builds, reading the logs and listing warnings and a recommendation by hand takes the reviewer 45 minutes or more. This is an estimate, not a timed figure, and it is a lower bound.

**Measured with the pipeline** (`module4_doc/module1-comparison.md`, `docs/iteration-log.md`): agent cycle time 3m22s to 3m48s on the final system, one timed human review of about 2.5 minutes (n=1), and a cost of $0.35 to $0.81 per run across recorded runs.

**Cited industry context** (external, not measured by this project): published industry data consistently shows code review and related coordination overhead consumes a substantial share of developer time -- Google's own internal engineering-productivity research reports developers spending an average of 6.4 hours per week on code review activities; separate industry surveys (SonarSource, Infragistics) report that routine coding itself is typically only 20-40% of a developer's working time, with the remainder spent on review, coordination, and verification overhead. These figures describe the general category of work this workflow addresses -- they are not claims about this specific project's own prior state.

**Our own measured evidence** (real, from this project): the `orchestrator_test` conversion (`ADR-001`) measured a ~264x latency reduction and complete token-cost elimination for one concrete, high-frequency verification step, by replacing LLM narration with deterministic parsing -- real, repeatable numbers from `module3_doc/calibration-log.md`, not estimated. This is offered as direct evidence of what rigorous measurement *within* this system looks like, distinct from the external context above.

## Projected value (assumptions stated, not measured)

These figures are projections. The hourly rate and the volume are assumptions, since this project has no live team. The time figures come from the estimates and measurements above.

- **Assumptions:** a loaded developer cost of $75 per hour, and 20 build checks per week.
- **If every report passes:** about 42.5 minutes of human time saved per check, which is about 14 hours and about $1,060 per week, less about $10 of model cost.
- **At the measured pass rate for the clarified prompts (1 in 3, n=3):** about 12.5 minutes saved per check, which is about 4 hours and about $310 per week. This figure assumes every failing report is caught at review and redone by hand.
- **What neither figure covers:** a failing report that is not caught. Its cost is a wrong decision, not minutes, and the project has no dollar figure for it.

The gap between the two projections is the reason reliability, not speed, is the main open problem for this task.
