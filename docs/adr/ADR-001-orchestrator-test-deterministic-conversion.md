# ADR-001: Convert orchestrator_test result interpretation from LLM judgment to deterministic code

## Status
Proposed

## Context

Every orchestrated task run ends with the Orchestrator running `./mvnw test` and interpreting the raw Maven output to decide pass or fail -- narratively, in the transcript's `orchestrator_test` step. `docs/step-classification.md` marks this step a strong candidate on all four signals: stable behavior across dozens of real runs in Modules 3-4 (DEV-02, HO-02, HO-04, HO-06, CAL-01-after), a Maven test result that is itself fully deterministic, a specification simple enough to write in one paragraph, and the highest run rate of any step in the whole system. The classification also names the edge case a deterministic version must preserve: Maven's output sometimes contains unrelated noise (Eureka stack traces from tests that deliberately exercise failure paths, WARN/ERROR log lines from retry-logic tests) that the Orchestrator has always correctly distinguished from a real failure by reading context, not by keying on the presence of certain words. "Did the build pass" has exactly one correct answer for any given Maven run; there is no genuine ambiguity for a language model to resolve here, only a well-defined parsing task currently being done by inference instead of code.

## Decision

Replace the Orchestrator's narrative interpretation of `./mvnw test` output with a small script that runs the tests, parses the Surefire summary line for the real pass/fail/error counts, and returns a structured result -- with no language model involved in deciding whether the build passed.

## Alternatives considered

- Keep the Orchestrator's narrative interpretation. Rejected. This step runs on effectively every orchestrated task -- the highest-frequency step in the system -- and each run costs real tokens and adds real latency for a question ("did the tests pass") that has exactly one correct answer, independent of any language understanding. The calibration log's own before/after pattern (e.g. HO-04's 338s duration, largely test-and-interpretation time) suggests real, recurring cost for zero judgment value.
- Convert to deterministic code. Preferred. A script that parses Maven's own Surefire summary line is expected to run with no added latency beyond the test suite itself, zero token cost, and identical output every time for identical test results. The quality bar it must clear before integration: it must correctly classify every real Maven output this project has actually produced, including the noisy cases (Eureka stack traces, retry-logic WARN/ERROR lines) without misclassifying any of them as failures. Acceptance will wait until it is integrated into the running workflow and the full workflow passes an end-to-end regression check. The measured comparison will be recorded later in this ADR.
- Have the Orchestrator run a regex check itself instead of full narrative interpretation, without a dedicated script. Rejected. This still routes a purely structural question through an LLM call, keeping the token cost and non-zero variance risk this conversion exists to remove, for no benefit over a real script -- it is a smaller version of the same problem, not a different one.

## Consequences

Expected benefits: zero added latency for interpreting a result that Maven itself already computed, zero token cost, perfectly repeatable classification of the same test output, and a step a reviewer can fully verify by reading a few lines of code rather than a transcript. Known trade-off: if a future testing framework changes Maven's Surefire output format, or if the project ever needs the Orchestrator to reason about *why* a specific test failed (not just whether the suite passed), this narrow script would not cover that -- a more capable step, or a return to LLM interpretation for that specific sub-case, would need to be considered separately. To watch before integration: confirm the measured latency, cost, and correctness match these expectations, especially against the known noisy-output edge case. To accept the ADR later, also confirm the integrated workflow passes an end-to-end regression check with no new failures.

## Evidence

docs/step-classification.md, orchestrator_test entry, strong candidate. Before/after measurement and integration evidence pending (this ADR stays Proposed).
