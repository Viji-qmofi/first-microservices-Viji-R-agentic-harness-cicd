# Step Classification

This document is updated after every calibration cycle. Steps that cross the stability threshold are promoted to candidate status. A step that has been a candidate for more than two calibration cycles without meeting all four signals is reviewed for re-scoping.

## All steps in the workflow (from CLAUDE.md, Orchestrator Instructions)

| Step | Kind | Notes |
|---|---|---|
| `planner` | Agentic | Retrieves prior lessons, produces a plan |
| `orchestrator_plan_review` | Orchestrator judgment | Evaluates plan adequacy before handoff |
| `implementer` | Agentic | Writes code per approved plan |
| `orchestrator_diff_review` | Orchestrator judgment | Confirms diff matches plan/scope |
| `orchestrator_test` | Orchestrator judgment | See classification below -- strong candidate |
| Reviewer Conflict Resolution | Orchestrator judgment, conditional | Only fires when 2+ reviewers disagree |
| `reviewer` | Agentic | Diff review, general |
| `spring-boot-reviewer` | Agentic | Diff review, Spring Boot conventions |
| `decision-auditor` | Agentic | Checks/corrects project memory records against git reality |
| `_authorize()` role checks (storage/retrieval/coursetools) | Already deterministic | Built in 4.1 |
| `validate_classification()` (storage writes) | Already deterministic | Built in Module 3.2 |
| Human checkpoint (pre-commit) | Human | Unconditional |
| Evaluation transcript recording | Orchestrator, mechanical | Writes structured JSON |

## Step: orchestrator_test (Maven test-result interpretation)

- Stability: run identically across dozens of real orchestrated tasks in Modules 3-4 (DEV-02: 36 tests; HO-02, HO-04: 38 tests; HO-06: 38 tests; CAL-01-after: 32 tests). Consistent behavior every time -- run Maven, report pass/fail.
- Repeatability: Maven's own test runner is itself deterministic; the same code and tests always produce the same result. Interpreting that result requires no run-to-run variance.
- Specifiability: one-paragraph spec -- run `./mvnw test`, parse the Surefire summary line for `Tests run: X, Failures: Y, Errors: Z`, exit non-zero if either is nonzero. A developer could implement this without any clarifying questions.
- Run rate: effectively every orchestrated task this course has included this step -- the highest run-rate candidate in the system.
- Known agent judgment / edge-case input the deterministic version must preserve: Maven's output sometimes includes unrelated noise -- Eureka stack traces from tests deliberately exercising failure paths, or WARN/ERROR log lines from retry-logic tests (e.g. decision-005's bounded-retry WARN on exhausted retries). The Orchestrator has correctly distinguished "expected noise from a passing test" from "an actual failure" by reading context. A naive regex keying on the presence of "ERROR"/"WARN" text anywhere in the log would misfire on this. The deterministic version must key strictly on the Surefire summary line's own pass/fail counts, never on the presence of certain words elsewhere in the output.
- Recommendation: strong candidate.
