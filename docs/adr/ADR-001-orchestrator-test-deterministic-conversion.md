# ADR-001: Convert orchestrator_test result interpretation from LLM judgment to deterministic code

## Status
Accepted

## Context

Every orchestrated task run ends with the Orchestrator running `./mvnw test` and interpreting the raw Maven output to decide pass or fail -- narratively, in the transcript's `orchestrator_test` step. `docs/step-classification.md` marks this step a strong candidate on all four signals: stable behavior across dozens of real runs in Modules 3-4 (DEV-02, HO-02, HO-04, HO-06, CAL-01-after), a Maven test result that is itself fully deterministic, a specification simple enough to write in one paragraph, and the highest run rate of any step in the whole system. The classification also names the edge case a deterministic version must preserve: Maven's output sometimes contains unrelated noise (Eureka stack traces from tests that deliberately exercise failure paths, WARN/ERROR log lines from retry-logic tests) that the Orchestrator has always correctly distinguished from a real failure by reading context, not by keying on the presence of certain words. "Did the build pass" has exactly one correct answer for any given Maven run; there is no genuine ambiguity for a language model to resolve here, only a well-defined parsing task currently being done by inference instead of code.

## Decision

Replace the Orchestrator's narrative interpretation of `./mvnw test` output with a small script that runs the tests, parses the Surefire summary line for the real pass/fail/error counts, and returns a structured result -- with no language model involved in deciding whether the build passed.

## Alternatives considered

- Keep the Orchestrator's narrative interpretation. Rejected. Measured: averages ~14s/run active API time and ~$0.173/run in token cost (3-run baseline, module3_doc/calibration-log.md, 2026-09-25), on a step that runs on effectively every orchestrated task in the system -- the highest-frequency step measured anywhere in this project. Confirmed conclusion-level consistency across 3 runs, though full response text was not compared for structural variance.
- Convert to deterministic code. Preferred. Measured: averages ~0.053s/run with zero token cost (3-run measurement, same log entry), a ~264x latency reduction and complete elimination of token cost versus the agentic baseline. Predictability confirmed byte-identical across all 3 runs via diff, not merely conclusion-consistent. 5/5 unit tests passing, including the named noisy-output edge case and a genuine-failure case. No quality regression found in isolation; the integrated end-to-end regression check is still pending before acceptance.
- Have the Orchestrator run a regex check itself instead of full narrative interpretation, without a dedicated script. Rejected. This still routes a purely structural question through an LLM call, keeping the token cost and non-zero variance risk this conversion exists to remove, for no benefit over a real script -- it is a smaller version of the same problem, not a different one.

## Consequences

Measured benefits: ~264x lower latency and 100% token-cost elimination for a question ("did the tests pass") that has exactly one correct answer, plus perfectly repeatable output (confirmed via diff, not assumed) and a step fully auditable by reading under 90 lines of Python rather than a transcript. Known trade-off, unchanged from the original context: if a future testing framework changes Maven's Surefire output format, or if the Orchestrator ever needs to reason about *why* a specific test failed rather than just whether the suite passed, this narrow script would not cover that. Still to watch: confirm no regression appears once the script is integrated into the live workflow and a real end-to-end run passes -- isolated measurement alone is not sufficient grounds to accept this ADR.

## Evidence

- Classification: docs/step-classification.md, orchestrator_test entry, strong candidate.
- Before-conversion measurement: module3_doc/calibration-log.md, "orchestrator_test deterministic conversion" entry, 2026-09-25.
- After-conversion measurement in isolation: same log entry -- ~264x latency reduction, 100% token-cost elimination, byte-identical output confirmed via diff.
- Integrated end-to-end regression check: module3_doc/calibration-log.md, "orchestrator_test conversion, end-to-end regression check" entry, 2026-09-25 -- 4 real orchestrated runs (2 holdout reruns, 2 genuine new-diff development tasks), no regression attributable to the conversion. All findings traced to pre-existing, unrelated gaps (retrieval citation fidelity, a third independent instance of DEV-02's documented gap) or measurement discipline, not to the converted step's own behavior.