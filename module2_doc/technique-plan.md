# Technique Plan: Context Management for Order-Service Re-Triage Session

## Explicit context boundaries

**Where:** At the Phase 1 -> Phase 2 transition, exactly when the ship-deadline constraint is introduced.

**Why:** Phase 1's operating rule (surface every issue, classified by severity, favoring completeness) and Phase 2's rule (narrow to the single most production-risky item, excluding anything that needs new tests) are in direct tension. Without an explicit boundary, the agent could blend the two standards instead of switching cleanly -- which is exactly the context-drift failure mode this exercise is designed to surface. Mechanism: a project-level `CLAUDE.md` context boundary policy (restate the goal, list current rules verbatim, state which prior rules no longer apply, identify the artifact, then proceed), triggered by a boundary preamble prepended to the Phase 2 message.

## Proactive summarization

**Where:** At the end of Phase 1, immediately before the Phase 2 constraint change is introduced.

**Why:** Phase 2 has to correctly recall every Phase 1 finding -- especially the still-unapplied `viewAllProducts()` fix -- in order to re-triage it accurately. Requesting a structured summary before the constraint change creates a checkpoint that can be verified directly against the actual Phase 1 output, and gives Phase 2 a clean, complete anchor rather than relying on it re-scanning the full prior conversation. Mechanism: a project skill, `.claude/skills/summarize-session/SKILL.md`, producing a structured summary (task/criteria, decisions so far, rule changes, current artifact state, outstanding work, open questions).

## Compaction

**Plan:** Not scheduled in advance. This session is two phases of review and analysis on one diff, not a long multi-turn editing task -- context volume is expected to stay well under any threshold that would require compaction. Will only invoke `/compact` if the actual session unexpectedly runs long, per the exercise's own guidance not to force it for its own sake.
