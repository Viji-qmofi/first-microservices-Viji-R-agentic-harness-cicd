# ADR-007: Governance policy structured around near-miss evidence, not generic best practice

## Status
Accepted

## Context

By Module 4.1, this project had two real, documented access-control failures already in its history (the `coursetools` `.memory/` bypass, and the Orchestrator's `update_entry` near-miss) before any formal governance policy document existed. A policy could have been written as a generic least-privilege template, or built specifically around what this project's own history showed actually goes wrong.

## Decision

Structure `docs/governance-policy.md` so every denial traces to one of two sources, stated explicitly per role: a specific, cited near-miss from `module3_doc/calibration-log.md`, or plain least-privilege reasoning when no incident applies -- never a denial justified by habit or by copying a generic template. Default every role to no access; widening requires the same evidence standard as a denial does: a stated reason, tied to the role's actual job, not asserted without justification.

## Alternatives considered

- **A generic least-privilege policy template**, applied uniformly without connecting denials to this project's own history. Rejected: a template justifies every denial the same generic way ("least privilege"), which is defensible but weaker evidence than a denial that can point to a real incident -- and it would have missed the chance to make the Orchestrator's `update_entry` denial carry its full weight, since that denial exists specifically *because* of a documented, real failure, not as a precaution against a hypothetical one.
- **Grant `decision-auditor` broad `.memory/` access from the start**, reasoning that its whole job is checking memory records so it should simply be able to read and write freely. Rejected -- and this rejection is itself the policy's own best real example of least-privilege-with-justification-to-widen in action: `decision-auditor` v1 was scoped narrowly to storage's `update_entry` only, discovered during real use to be insufficient (plain git-tracked files like `MEMORY_INDEX.md` are a different system `update_entry` can't reach at all), and widened to v2 specifically and only to `file_read`/`file_write` on `.memory/project/` -- not opened to all of `.memory/`, and not granted to any other role. The widening is documented with its exact justification (module3_doc/decision-auditor-case-study.md) and was verified against a path-traversal attempt (`project/../storage/`) before being trusted.
- **Policy structured around real evidence, narrow by default, justified widening only (chosen).** Preferred because every grant and every denial in the resulting document can be defended by pointing at something specific that actually happened, not by asserting a best practice in the abstract.

## Consequences

The policy's own real history now demonstrates both halves of "least-privilege defaults, justification-to-widen" working as designed, not just stated: a role was denied broadly at first (correctly, since its full needs weren't yet known), the gap it caused was discovered through genuine use (not anticipated in advance), and the widening that followed was narrow, specific, and tested -- not a blanket re-grant. Known trade-off: this means the governance policy was never complete on day one and required real iteration to reach its current state -- a reviewer expecting a single, fully-specified policy document written once would instead find a document with its own documented evolution. Open risk: the policy's evidence-grounded structure depends on `module3_doc/calibration-log.md` continuing to be a reliable, honestly-maintained record -- if that log's own completeness or accuracy degraded, the policy's citations would lose their grounding.

## Evidence

docs/governance-policy.md: orchestrator's `write_entry`/`update_entry` denials, explicitly citing the HO-06 near-miss. module3_doc/decision-auditor-case-study.md: the full v1-to-v2 widening story, including the real infrastructure bugs found and the path-traversal verification. module3_doc/calibration-log.md: the original near-miss evidence both denials and the widening trace back to.
