# Step Classification

This document is updated after every calibration cycle. Steps that cross the stability threshold are promoted to candidate status. A step that has been a candidate for more than two calibration cycles without meeting all four signals is reviewed for re-scoping.

## All steps in the workflow (from CLAUDE.md, Orchestrator Instructions)

| Step | Kind | Notes |
|---|---|---|
| `planner` | Agentic | Retrieves prior lessons, produces a plan |
| `orchestrator_plan_review` | Orchestrator judgment | Evaluates plan adequacy before handoff |
| `implementer` | Agentic | Writes code per approved plan |
| `orchestrator_diff_review` | Orchestrator judgment | Confirms diff matches plan/scope |
| `orchestrator_test` | Deterministic | Converted 2026-09-25, ADR-001 |
| Reviewer Conflict Resolution | Orchestrator judgment, conditional | Only fires when 2+ reviewers disagree |
| `reviewer` | Agentic | Diff review, general |
| `spring-boot-reviewer` | Agentic | Diff review, Spring Boot conventions |
| `decision-auditor` | Agentic | Checks/corrects project memory records against git reality |
| `_authorize()` role checks (storage/retrieval/coursetools) | Already deterministic | Built in 4.1 |
| `validate_classification()` (storage writes) | Already deterministic | Built in Module 3.2 |
| Human checkpoint (pre-commit) | Human | Unconditional |
| Evaluation transcript recording | Orchestrator, mechanical | Writes structured JSON |

## Step: orchestrator_test (Maven test-result interpretation)

- Status: Converted to deterministic (ADR-001, 2026-09-25).
- Preserved edge case: Maven output noise (Eureka stack traces, retry-logic WARN/ERROR lines) is not mistaken for a real failure -- the deterministic script keys strictly on the Surefire summary line's own counts, never on the presence of certain words elsewhere in the output. Covered by eval/test_deterministic_step.py's test_noisy_output_still_passes.
- Measured result: ~264x latency reduction (14s -> 0.053s average), 100% token-cost elimination, byte-identical output confirmed via diff (module3_doc/calibration-log.md, 2026-09-25 entries).
- Integrated and regression-checked: 4 real orchestrated runs, no regression attributable to the conversion (module3_doc/calibration-log.md, end-to-end regression check entry).

## Step: planner

- Recommendation: not a candidate. Requires judgment and synthesis to retrieve relevant prior lessons and form a plan; output is not specifiable in advance -- genuinely different reasoning per task.
- Next review: 2027-03-25.

## Step: implementer

- Recommendation: not a candidate. Writes code per an approved plan, which inherently requires judgment about how to implement a spec in context; not reducible to a fixed rule.
- Next review: 2027-03-25.

## Step: orchestrator_plan_review

- Recommendation: not a candidate. Evaluating whether an open-ended plan is concrete, correctly scoped, and stays in-role requires reading and judging free text -- not specifiable as a fixed rule the way orchestrator_test's numeric comparison was.
- Next review: 2027-03-25.

## Step: orchestrator_diff_review

- Recommendation: weak candidate. Uses concrete tooling (`git diff --ignore-all-space`, audit-log cross-checks) similar in spirit to orchestrator_test, but still requires judging whether a diff's *content* matches an open-ended plan's intent -- not yet reducible to a fixed rule. Worth watching, though: orchestrator_test's successful conversion is a real precedent for narrower sub-parts of this step (e.g. the "is the diff scoped to only the claimed files" check, which is closer to purely mechanical) potentially becoming separable candidates later.
- Candidate since: 2026-09-25 (noted as adjacent to a real conversion precedent). Next review: 2026-12-25.

## Step: Reviewer Conflict Resolution

- Recommendation: not a candidate. Exists specifically to route a genuine ambiguity (two reviewers disagreeing) to a human -- the entire point is that no fixed rule should resolve it automatically.
- Next review: 2027-03-25.

## Step: reviewer

- Recommendation: not a candidate. General-purpose diff review requires judgment across arbitrary changes; not specifiable as a fixed rule.
- Next review: 2027-03-25.

## Step: spring-boot-reviewer

- Recommendation: not a candidate. Domain-specific review judgment (exception handling, REST conventions) requires reading and evaluating code in context.
- Next review: 2027-03-25.

## Step: decision-auditor

- Recommendation: weak candidate, narrowly. The role's current scope (checking multiple different decision records, each needing different verification logic against different git evidence) is not specifiable as one simple rule -- not a strong candidate as currently scoped. However, a genuinely narrow sub-case -- e.g. "does MEMORY_INDEX.md's stated review-by date match decision-NNN.md's own frontmatter date" -- is a single, well-specified comparison that could become a real deterministic candidate if that exact narrow pattern recurs often enough to be worth isolating.
- Candidate since: 2026-09-25. Next review: 2026-12-25.

## Step: Evaluation transcript recording

- Recommendation: weak candidate. Writing structured fields (task_id, events list, durations) is mechanical, but synthesizing natural-language summaries of what each step did still involves some compression/judgment -- not fully specifiable yet.
- Candidate since: 2026-09-25. Next review: 2027-01-25.

---

This document is updated after every calibration cycle. Steps that cross the stability threshold are promoted to candidate status. A step that has been a candidate for more than two calibration cycles without meeting all four signals is reviewed for re-scoping.

