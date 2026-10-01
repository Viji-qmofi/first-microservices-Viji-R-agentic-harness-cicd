# ADR-004: Three-layer memory architecture, split by volatility and write permission

## Status
Accepted

## Context

Agents working on this repository need information to persist across sessions -- recurring findings, stabilized conventions, repo-specific quirks, and historical review detail. module2_doc/memory-architecture.md documents what the workflow needs to remember and what must never persist (credentials, a single session's raw transcript, task-specific state no longer relevant once the task closes). A single undifferentiated memory store cannot serve this well: evolving task state needs to be agent-writable so the system can update itself as work happens, while stabilized project conventions need to require deliberate human review before changing, the same standard already applied to agent definition changes -- one write-permission model cannot satisfy both needs at once.

## Decision

Split persistent memory into three layers by volatility and write permission: Layer 1 (project memory directory, `.memory/project/`) -- evolving, task-linked state, agent-writable, pruned/archived once a finding resolves or on a 90-day review for project-wide items. Layer 2 (knowledge files, `.memory/knowledge/`) -- stable, human-maintained conventions and standards, agent-read-only, changed only via deliberate human-reviewed commit, reviewed only when the underlying policy actually changes rather than on a timer. Layer 3 (indexed reference, `.memory/reference/`) -- large historical/archival material, agent-append-only, never rewritten, consulted on demand rather than loaded by default.

## Alternatives considered

- **A single, undifferentiated memory store.** Rejected: a single store cannot simultaneously be freely agent-writable (needed for evolving task state) and require human review before any change (needed for stable conventions like the Feign-exception-handling pattern) -- one write-permission model would have to compromise on one need or the other.
- **Placing the Feign-exception-handling convention in Layer 1 as mutable state, indefinitely.** This was the convention's actual original placement, not a hypothetical -- it started in Layer 1 as a one-off decision for a single method (`placeOrder()`). It was deliberately *not* left there once reapplied to a second method (`viewAllProducts()`) rather than solved differently each time; module2_doc/memory-architecture.md records the real reasoning: treating a repeated pattern as mutable state risks a future session reasoning its way to a different approach and silently drifting, whereas graduating it to Layer 2 (human-governed, agent-read-only) makes changing it require the same deliberate review as any other project convention.
- **Three layers (chosen), with an explicit, evidenced graduation criterion.** Preferred specifically because it gives a concrete trigger for when something should move from Layer 1 to Layer 2 -- not "whenever it feels stable," but "once a decision has actually been reapplied, not re-decided, a second time." This is a testable rule, not a judgment call made fresh each time.

## Consequences

The three-layer split, plus a pre-commit hook (scripts/hooks/pre-commit) that scans .memory/ for credential patterns before every commit, gives this project a working, enforced data-classification boundary (Public/Internal/Confidential/Secret, documented in the same file) -- not just a policy statement. This has held up under real, adversarial testing: Module 2 Exercise 2.4 deliberately attempted to store a fake secret in memory and the guardrail caught it. Known trade-off: a three-way split adds real complexity an agent must reason about correctly every time it writes (which layer does this belong in) -- mitigated by the allocation decision table in memory-architecture.md giving concrete worked examples rather than only an abstract rule. Open risk: the graduation criterion ("reapplied, not re-decided, a second time") is itself a judgment call about what counts as the "same" pattern being reapplied versus a genuinely new, superficially similar decision -- this has not yet been tested against a genuinely ambiguous case.

## Evidence

module2_doc/memory-architecture.md -- "Alternatives considered" section (the Layer 1-to-Layer 2 graduation story) and "Allocation decision table," both written at design time, not reconstructed afterward. Guardrail enforcement confirmed working under adversarial test: Module 2 Exercise 2.4's sensitive-data storage test, caught by the pre-commit hook before any secret reached a committed memory file.
