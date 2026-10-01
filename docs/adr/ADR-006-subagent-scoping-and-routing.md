# ADR-006: Role count and routing kept to the smallest set that maps to a real, distinct responsibility

## Status
Accepted

## Context

This project's orchestration graph grew incrementally: `planner`/`implementer` (Module 3.1), `spring-boot-reviewer` (Module 2, predating the MCP layer), two temporary calibration-only roles `reviewer_strict`/`reviewer_lenient` (Module 3 Lab, built specifically to force a reviewer-conflict scenario), and `decision-auditor` (Module 4.1). At each point, the question was whether a new responsibility needed its own subagent, or belonged inside an existing role's scope -- including the Orchestrator's own.

## Decision

Keep exactly as many subagents as there are genuinely distinct, independently-scoped responsibilities, and retire a role the moment its reason for existing ends -- rather than accumulating roles indefinitely or collapsing distinct responsibilities into one for convenience. `orchestrator_test` (interpreting test results) stays part of the Orchestrator's own behavior rather than becoming a dedicated `tester` subagent. The temporary `reviewer_strict`/`reviewer_lenient` pair was deliberately retired once its calibration purpose was served, replaced by one real `reviewer` -- not kept on as a permanent two-reviewer default.

## Alternatives considered

- **Add a dedicated `tester` subagent for test execution/interpretation**, matching the course's own suggested role list. Rejected: the Orchestrator already independently runs and verifies tests as part of evaluating `implementer`'s result (CLAUDE.md, "never trust its own summary as verification"); a separate `tester` subagent would duplicate work the Orchestrator must do anyway to independently confirm a diff before approving it, adding a role boundary with no real independence benefit, since the Orchestrator would still need to re-verify a `tester`'s report the same way it re-verifies `implementer`'s. This is itself now a converted, deterministic step (ADR-001), reinforcing that it was never agentic judgment requiring its own role in the first place.
- **Keep `reviewer_strict`/`reviewer_lenient` as a permanent two-reviewer default**, since the infrastructure already existed after the calibration cycle. Rejected directly, with reasoning recorded at the time: their own agent definitions stated "TEMPORARY, for Module 3 Lab calibration cycle only," and running two full reviewer passes by default would double model cost for every review with no corresponding benefit once the specific calibration purpose (forcing a conflict to test the escalation policy) was served. Retired in favor of implementing the single real `reviewer` role that had been designed back in Module 3.1 but left as "standing in via the Orchestrator" until this point.
- **Current role set (chosen): `planner`, `implementer`, `reviewer`, `spring-boot-reviewer`, `decision-auditor`, plus the Orchestrator itself** -- six responsibilities, each mapping to a genuinely distinct concern (deciding how to change something; making the change; independently evaluating it generically; independently evaluating it against Spring Boot-specific conventions; correcting stale project-memory records against git reality; coordinating and holding ultimate accountability).

## Consequences

Routing stays simple to reason about precisely because role count stays minimal: `docs/routing-and-tool-grant-map.md` has six rows, not an ever-growing list accumulated for convenience. Retiring `reviewer_strict`/`reviewer_lenient` meant real git history work (deleting the agent files, removing their coursetools allow-list entries) rather than just leaving unused scaffolding in place -- a small cost, paid once, in exchange for a routing map that reflects what the system actually does rather than its full history of experiments. Known trade-off: collapsing `orchestrator_test` into the Orchestrator's own behavior means this step is not independently swappable or scoped the way a true subagent would be -- it inherits whatever tool access and context the Orchestrator session has, rather than a narrower, purpose-built grant. Open risk: as the system grows, a currently-reasonable "fold into the Orchestrator" decision (like `orchestrator_test`'s) could become harder to justify if the Orchestrator's own responsibilities keep accumulating -- worth revisiting if the Orchestrator's own instructions grow substantially larger than they are today.

## Evidence

agents/reviewer_strict.md and agents/reviewer_lenient.md's own frontmatter (`"TEMPORARY, for Module 3 Lab calibration cycle only"`), git history showing their deletion and `reviewer`'s real implementation in the same commit (Module 4.1). ADR-001 (docs/adr/ADR-001-orchestrator-test-deterministic-conversion.md), confirming `orchestrator_test` was agentic judgment and not an independent role, now converted. CLAUDE.md, Orchestrator Instructions, "never trust its own summary as verification" -- the actual, standing reason a separate `tester` role was never necessary.
