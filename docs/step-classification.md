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


## Step: Line-ending-noise detection during diff review (readiness package, not implemented)

**Description:** Before including a modified file in a commit, the Orchestrator currently judges whether the file's diff represents real content change or only line-ending/whitespace churn -- by running `git diff --ignore-all-space` and reasoning about the result. Input: a set of modified file paths from `git status`. Output: a decision about which files to stage/commit and how to describe them in the run summary. This sits inside `orchestrator_diff_review`, invoked on nearly every commit this course.

### Four-signal classification

- **Stability:** run with completely consistent underlying logic 15+ times across this whole course (Module 1's build-check commits, Module 3's DEV-02/holdout reviews, the Module 4 port's repo-wide CRLF/LF noise, this module's own recent commits) -- always the same pattern: run `git diff --ignore-all-space`, empty means noise, non-empty means real content.
- **Repeatability:** `git diff --ignore-all-space` is itself fully deterministic -- same files, same output every time. The routine judgment applied on top (empty diff = safe to note as noise) has been completely consistent in every one of the 15+ observed instances.
- **Specifiability:** the routine case is trivially specifiable -- "run `git diff --ignore-all-space -- <files>`; empty output means line-ending/whitespace noise only; non-empty output means real content change requiring review." A real, documented counterexample breaks full specifiability, though -- see the edge case below.
- **Run rate:** effectively every commit-review step this entire course has included this judgment -- among the highest run-rate candidates in the whole system, likely higher than orchestrator_test since it fires on every diff review, not only every test-verification step.

**Known agent judgment / edge-case input the deterministic version must preserve:** a real, already-encountered case from this project's own history -- `docker-entrypoint.sh`'s CRLF-to-LF conversion during the Module 4 activation exercise. That diff, when checked with `git diff --ignore-all-space`, would show as empty (pure line-ending change) -- but it was in fact the *entire, deliberate point* of that commit (the CRLF encoding was breaking the container's `ENTRYPOINT` shebang). A rule that automatically treats every line-ending-only diff as safe-to-ignore-and-exclude would have been wrong in exactly this case. The current agentic judgment correctly distinguishes "incidental, pre-existing noise unrelated to this task" from "a line-ending change that is itself the substantive fix," but a simple boolean check on `git diff --ignore-all-space`'s emptiness cannot make that distinction on its own -- it requires knowing whether the line-ending change was the actual intent of the current task, which is contextual information outside the diff itself.

### Recommendation: weak candidate

This step passes stability, repeatability, and run rate cleanly, but specifiability has a genuine, evidenced gap, not a hypothetical one. The routine 95% case (unrelated pre-existing noise sitting alongside real changes elsewhere) is fully mechanizable. But the docker-entrypoint.sh case proves the same mechanical signal (an empty `--ignore-all-space` diff) needs different handling depending on task context a diff alone doesn't carry. Full automation that silently excludes every line-ending-only diff would have missed exactly the fix that mattered most in this project's own history. The right design, if this were converted, is narrower than full automation: a deterministic script can correctly categorize and label diffs (flagging which files show line-ending-only changes), but the decision of what to do with that category must still surface to a human or the Orchestrator's own judgment, not be silently auto-excluded. This is not the savings-driven case the lesson warns against -- the honest evidence caps how far automation can safely go here.

## ADR-002 test plan, measurement plan, and rollback note (readiness only -- not implemented)

### Test plan (named, not written)

1. **Normal case -- pure noise:** input is a diff where every changed line differs only in line-ending characters (e.g. a file converted CRLF->LF with no content change). Expected output: categorized as "line-ending-only," non-blocking. Protects the routine, high-frequency case this conversion is meant to speed up.
2. **Invalid/failure case -- mixed diff:** input is a diff where some lines are genuine content changes and others in the same file are line-ending-only. Expected output: categorized as "contains real content," never silently collapsed into the noise category just because most of the file's lines are line-ending changes. Protects against a partial-noise file being wrongly waved through.
3. **Named edge case -- deliberate line-ending fix:** input is a diff that is 100% line-ending changes (would categorize as "line-ending-only" by the mechanical rule), on a file where the task's own stated goal was to fix a line-ending problem (e.g. the docker-entrypoint.sh case). Expected output: the script still correctly labels it "line-ending-only" at the mechanical level -- but the categorization must be surfaced to the human/Orchestrator explicitly, not auto-excluded from the commit, precisely because a mechanical label alone cannot know this diff was the deliberate point of the task. This is the test that would catch a design that silently discards exactly the kind of change this project's own history shows mattering.

### Measurement plan

- **Latency:** current agentic judgment latency (LLM reasoning time) per diff-review invocation, versus a script's near-instant `git diff --ignore-all-space` parse.
- **Token cost:** current cost of the Orchestrator's own reasoning about noise-vs-content per invocation, versus zero for a script.
- **Predictability:** run the categorization three times on the same set of modified files; confirm identical categorization output via diff, the same discipline used for orchestrator_test.
- **Audit clarity:** whether a reviewer can fully understand the categorization logic by reading the script versus needing to read Orchestrator reasoning/transcript text.
- **Quality/harness:** no existing rubric dimension scores this specific judgment directly (same situation as orchestrator_test) -- would need to confirm no regression via an end-to-end run where at least one mixed-diff and one deliberate-line-ending-fix case both occur, confirming neither gets miscategorized.
- **Rubric dimensions likely not applicable:** none of the four rubric dimensions (correctness, task_adherence, groundedness, clarity) meaningfully score a structured categorization list the way they score prose output -- any of them scoring low against structured output should be marked not-applicable rather than read as a regression, the same caveat orchestrator_test's measurement plan named.

### Rollback note

The conversion, if implemented, should land as a single commit touching only: the new categorization script, its unit tests, the `CLAUDE.md` instruction pointing the Orchestrator at it (replacing the current judgment-based instruction), and `docs/routing-and-tool-grant-map.md`/`docs/governance-policy.md` if any grant needs updating. No production code in `ecom-*-service/` would be touched. A single `git revert` of that one commit would fully restore the current agentic-judgment behavior, since the script would be net-new and the CLAUDE.md edit would be a pure text replacement, not an interleaved change. Given the recommendation is "weak candidate" rather than "strong candidate," this rollback note stays hypothetical -- no implementation is planned from this readiness package alone.

## Optional stretch: pressure-test the recommendation

**Strongest argument for converting anyway (arguing against my own "weak candidate" call):** the deliberate-line-ending-fix edge case is genuinely rare -- it has happened exactly once in this entire project's history (docker-entrypoint.sh), against 15+ routine instances where the mechanical rule was completely correct. A human reviewer already has to look at the run summary before approving any commit regardless of what a script labels; a categorization script that's wrong in a rare case doesn't cause silent harm, since the human checkpoint is unconditional either way (CLAUDE.md). Under that framing, full automation of even the categorization decision (not just labeling) might be acceptable, since the human backstop already exists and this step never bypasses it.

**What evidence would settle this:** whether the deliberate-line-ending-fix pattern recurs. If it happens again in a future task, that's real evidence the edge case is a recurring category, not a one-off, strengthening the "weak candidate, human-in-the-loop required" position. If it never recurs across several more calibration cycles, that would be real evidence toward the stronger, fuller-automation counter-argument. Added to ADR-002's Evidence section as something to gather before any future revision of this classification.
