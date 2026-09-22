# Pre-Session Plan: Re-Triage Order-Service Fixes Under a Ship Deadline

## Real project task

Across Runs 001-003 of `spring-boot-reviewer`, two Critical findings have been repeated but never applied: unhandled generic `FeignException` failures in both `placeOrder()` and `viewAllProducts()` in `ecom-order-service`. This session applies one of those fixes, then uses the agent to catalog everything still outstanding, and finally forces it to re-triage that catalog under a real urgency constraint introduced mid-session.

## Agent used

`spring-boot-reviewer` (currently v2, `.claude/agents/spring-boot-reviewer.md`). No revision planned before this session — this exercise tests it under a new kind of load (sustained, multi-phase, decision-revisiting) rather than changing its definition.

## Phases

**Phase 1 — Broad review.** Apply the `placeOrder()` Feign-handling fix (the snippet already verified in Run 003), then have the agent review the current full diff and catalog every outstanding issue across all four checklist areas (exception handling, REST conventions, Feign usage, missing test coverage) — same scope as prior runs. Active rule: completeness. Every real issue should be surfaced and classified, regardless of how much effort fixing it would take.

**Phase 2 — Re-triage under a ship deadline.** Introduce the constraint: the team needs to ship by end of day. Ask the agent to re-prioritize its own Phase 1 findings down to the single most production-risky item, and explicitly exclude any recommendation that would require adding new test coverage, since there's no time to also write and verify tests before the deadline. Active rule: urgency and mergeability outrank completeness; test-requiring fixes are out of scope for this pass.

## Requirement that changes

Between Phase 1 and Phase 2, the review standard shifts from "surface everything, classified by severity" to "narrow to the one fix that's safe and fast enough to ship today, excluding anything that needs new tests." This is a realistic shift — the underlying code and its problems don't change, but what counts as "the right recommendation" does.

## Artifact revisited

The Phase 1 findings list (and the still-unapplied `viewAllProducts()` fix specifically) is what Phase 2 must re-evaluate under the new constraint, not re-derive from scratch.

## Evidence for evaluation

- Does Phase 2's answer correctly reference the actual findings from Phase 1 (e.g., does it correctly recall that `viewAllProducts()` was already identified as Critical, rather than rediscovering or misremembering it)?
- Does Phase 2 correctly exclude any test-requiring recommendation once that constraint is stated, rather than including one anyway?
- Does the final single-item recommendation hold up as genuinely the most production-risky one, given what Phase 1 actually found?
- Do Phase 1 and Phase 2 read as one coherent session, or does Phase 2 contradict or ignore anything Phase 1 established?
