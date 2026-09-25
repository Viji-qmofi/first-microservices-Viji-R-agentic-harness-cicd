# ADR-002: Convert line-ending-noise categorization during diff review from agent judgment to deterministic code (partial)

## Status
Proposed

## Context

Before every commit, the Orchestrator judges whether a modified file's diff represents real content change or only line-ending/whitespace churn, by running `git diff --ignore-all-space` and reasoning about the result. This has happened with completely consistent underlying logic 15+ times across this course (Module 1's build-check commits, Module 3's holdout reviews, the Module 4 port's repo-wide CRLF/LF noise, this module's own recent commits) -- among the highest-frequency judgments in the entire system. `docs/step-classification.md`'s entry for this step marks it a weak candidate, not a strong one: the routine case (unrelated, incidental noise) is fully specifiable, but a real, already-encountered counterexample from this project's own history -- `docker-entrypoint.sh`'s CRLF-to-LF fix during the Module 4 activation exercise -- shows the same mechanical signal (an empty `--ignore-all-space` diff) needing different handling depending on task context a diff alone doesn't carry. That commit's entire point was a line-ending change; a rule that silently treats every line-ending-only diff as safe-to-exclude noise would have discarded the actual fix.

## Decision

Do not fully automate the decision of what to do with a line-ending-only diff. Instead, build a narrower deterministic script that only categorizes and labels diffs (line-ending-only vs. contains-real-content) and surfaces that categorization explicitly in the run summary for human/Orchestrator review -- never silently auto-excluding a file from a commit based on the category alone.

## Alternatives considered

- Keep full agentic judgment for both categorization and the accept/exclude decision. Rejected as the sole option, though not fully -- the routine categorization step (does this diff have real content, ignoring whitespace) runs the same mechanical check 15+ times with completely consistent outcomes, and repeating full LLM reasoning for a question `git diff --ignore-all-space`'s emptiness already answers mechanically wastes cost and latency on the 95% of cases where no contextual judgment is actually needed.
- Fully automate both categorization and the accept/exclude decision (treat every line-ending-only diff as automatically safe to exclude). Rejected, with concrete evidence: the docker-entrypoint.sh case is a real, already-occurred instance where this would have discarded the actual deliberate fix, not a hypothetical risk. Full automation here would have caused a real regression in this exact project's own history had it existed at the time.
- Partial conversion: deterministic categorization, human/Orchestrator judgment retained for the accept/exclude decision. Preferred. This captures the mechanizable part (is this diff pure whitespace) with a script, while preserving judgment specifically at the one point evidence shows it's needed (deciding what a line-ending-only categorization should mean for this particular task). No implementation, measurement, or integration is planned as part of this readiness package -- this ADR stays Proposed.

## Consequences

Expected benefits, if implemented: faster, cheaper categorization for the routine 95% of diffs, freeing the Orchestrator's own reasoning for the cases that genuinely need it (deciding what a line-ending-only label means for this specific task) rather than re-deriving the category from scratch every time. Known trade-off: this conversion is deliberately incomplete -- it does not remove judgment from the workflow, only from the mechanical labeling step, so the token-cost/latency savings are smaller than a full conversion like orchestrator_test's. To watch if ever implemented: confirm the categorization script never silently causes a deliberate line-ending fix to be excluded without the human seeing it labeled as such first.

## Evidence

- Classification: docs/step-classification.md, "Line-ending-noise detection during diff review" entry, weak candidate.
- Real counterexample motivating the "partial" design: docker-entrypoint.sh CRLF-to-LF fix, Module 4 activation exercise (see conversation history and module3_doc/calibration-log.md's related discussion of that fix).
- Evidence still to gather before any future revision: whether the deliberate-line-ending-fix pattern recurs in future calibration cycles (see step-classification.md's pressure-test note) -- a recurrence would strengthen the partial-conversion design; continued absence would strengthen the case for fuller automation given the existing unconditional human checkpoint.
