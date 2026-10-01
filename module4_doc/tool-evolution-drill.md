# Tool-Evolution Drill: Converting orchestrator_test From Agentic to Deterministic

Drill type: **convert another step** (one of the four qualifying types named in the capstone rubric).

## What was changed

`orchestrator_test` -- the step where the Orchestrator interprets raw `./mvnw test` output to decide pass/fail -- was converted from LLM narration to a deterministic script (`scripts/parse_test_result_deterministic.py`), per `ADR-001`. This is a real production change to the live orchestration pipeline, not a simulated or isolated exercise: `CLAUDE.md`'s own Orchestrator Instructions were edited to point at the script, and every orchestrated task run since has used the converted version.

## What broke

Nothing in the converted step's own behavior regressed -- confirmed across 4 real end-to-end orchestrated runs (2 holdout-task reruns, 2 genuine new-diff development tasks) after integration. What the regression-check *process* surfaced instead were two real defects in how evidence itself was being recorded, neither caused by the conversion but both found only because the harness was run against real post-integration evidence rather than assumed correct:

1. **A transcript recorded `cost_usd` as the string `"not_measured"` instead of JSON `null`.** Running `eval/test_deterministic.py` against it crashed with an unhandled `TypeError` (`'>' not supported between instances of 'str' and 'float'`) rather than a clean fail -- the harness's own `check_cost` function had no defensive handling for a malformed field type. This is itself a known-gap finding worth carrying into future harness work, even though the fix applied here was correcting the transcript, not hardening the checker.
2. **A second transcript's `expected_path` listed `implementer` before `orchestrator_plan_review`** -- the reverse of what actually happened and of the established review-before-implementation convention used everywhere else in this project. `check_role_order` correctly failed against this, exactly as designed.

Neither defect was caught by manual read-through before the harness ran -- both transcripts looked complete and plausible on inspection. The harness catching them is the real evidence this drill produced: **running the real evaluation harness against real new evidence surfaced two defects that manual review of the same evidence had already missed.**

## What improved

Measured directly, not estimated (`module3_doc/calibration-log.md`, 2026-09-25 entries):

- **Latency:** ~264x reduction (14s/run average, agentic baseline -> 0.053s/run average, deterministic).
- **Cost:** 100% token-cost elimination for this step ($0.173/run -> $0/run).
- **Predictability:** the deterministic version produces byte-identical output across repeated runs on the same input, confirmed via `diff`, not merely a consistent conclusion -- the agentic baseline was only confirmed consistent at the conclusion level, not the full-text level, a real, disclosed limitation of the baseline measurement itself.

## How the eval harness caught regressions (and what it didn't catch automatically)

`eval/test_deterministic.py` run against both new-diff transcripts caught the `expected_path` defect directly (`check_role_order` failing with a precise, correct error naming the actual vs. expected sequence). The `cost_usd` type defect was caught as an unhandled crash rather than a clean, named failure -- a real, acknowledged limitation in the harness's own robustness, not a false negative, since the run genuinely could not be scored until the transcript was corrected. Both required a human to diagnose the root cause and apply the fix; the harness's role was surfacing that *something* was wrong, not diagnosing *why*.

Separately, two of the four regression-check runs (the holdout-task reruns) turned out to require no new implementation at all, since the underlying work already existed from an earlier bulk port. This was itself discovered via the same discipline this drill depends on throughout -- `git diff -w` checked directly rather than trusting `planner`'s "already implemented" claim at face value (see `skills/verify-before-trusting`).

## Final result

`ADR-001`: **Accepted.** Full before/after measurement, integration, and a real 4-run end-to-end regression check are all recorded in `module3_doc/calibration-log.md`, with every number traceable to a specific, named entry rather than summarized from memory.
