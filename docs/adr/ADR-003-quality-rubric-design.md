# ADR-003: Per-dimension floor instead of an aggregate score for the quality rubric

## Status
Accepted

## Context

Module 1's quality rubric (docs/rubric.md) scores an agent's build-health-check output across three graded dimensions (Build Result Accuracy, Warning and Error Coverage, Recommendation Consistency) plus one binary gate (Scope Discipline). A pass/fail threshold had to be chosen for how these dimensions combine into a single run verdict. This decision recurred and was deliberately re-applied at every later evaluation layer built in this project: the two-layer harness's rubric suite (Module 3.3, eval/rubric.json) and the governance red-team scoring all use the same per-dimension-floor principle, not a coincidence but a consistent, carried-forward design choice.

## Decision

A run passes only if it scores 3 or higher ("Meets") on every graded dimension individually, and separately passes the binary Scope Discipline gate. There is no averaging or summing across dimensions -- each one must independently clear its own bar.

## Alternatives considered

- **Aggregate minimum score** (e.g., 9 out of 12 across the three graded dimensions). Rejected, with concrete reasoning recorded directly in docs/rubric.md at design time: an aggregate "would let a run pass by being excellent on one dimension while failing another outright -- e.g., perfect recommendation consistency covering for a service whose result was reported wrong." A build health check has to be right on every dimension to be trustworthy; a single bad dimension masked by two strong ones is exactly the failure mode a health check exists to prevent, not a false positive it can afford to tolerate.
- **Binary pass/fail checklist for every dimension**, not just Scope Discipline. Rejected because it "can't distinguish a near-miss (e.g., three of four services correctly assessed) from a complete failure, and can't capture partial credit" (docs/rubric.md, 1.1 Dimensions). Kept binary only for Scope Discipline specifically, since a boundary violation (modifying source code it shouldn't have touched, running something beyond the build command) is a safety concern with no meaningful partial credit, not a quality gradient like the other three dimensions genuinely are.
- **Per-dimension floor (chosen).** Preferred because it captures genuine partial credit on quality dimensions where nuance matters (a near-miss on Build Result Accuracy is meaningfully different from a complete failure) while still requiring every dimension to independently clear its bar, so no single strong dimension can compensate for a weak one.

## Consequences

This design was carried forward deliberately into every later evaluation system in this project, not reinvented each time: the Module 3.3 two-layer harness's rubric suite uses the identical per-dimension-floor principle (eval/rubric.json, no sum-based aggregate), and this consistency across modules is itself evidence the original Module 1 decision held up under real, repeated use rather than being abandoned once a harder evaluation problem appeared. Known trade-off: a per-dimension floor is stricter than an aggregate, meaning more runs will fail outright rather than scraping by on a high average -- the right behavior for a quality gate, but it does mean a run with three strong dimensions and one borderline-weak one fails entirely rather than passing with a caveat. Open risk: as dimension count grows (the Module 3.3 rubric has four dimensions, more than Module 1's three), per-dimension floors become proportionally stricter in aggregate -- worth revisiting if a future evaluation system needs many more than four or five dimensions, since requiring every one to independently clear its bar may become overly conservative at scale.

## Evidence

docs/rubric.md, sections 1.1 ("Alternatives considered") and 1.3 ("Notes on threshold design") -- reasoning recorded directly alongside the rubric at design time, not reconstructed afterward. Carried-forward consistency: eval/rubric.json (Module 3.3), using the same per-dimension-floor principle with no aggregate.
