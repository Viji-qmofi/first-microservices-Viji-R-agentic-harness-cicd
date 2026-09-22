# Iteration Log

## Run 001 -- 2026-07-29 -- Baseline

Task: Run the Maven build for all four services and report success/failure plus warnings.

Full prompt: Run ./mvnw clean install for each of the four services (ecom-eureka-registry, ecom-api-gateway, ecom-product-service, ecom-order-service), report whether each build succeeded or failed, summarize any warnings or errors, and give a final recommendation on whether the repo is ready to proceed. Do not modify any files, run anything beyond the build command, or push/publish/deploy anything.

Rubric Scores:

| Dimension                  | Score (1-4 or Pass/Fail) | Notes                                                                                                                                                                                                 |
| -------------------------- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Build Result Accuracy      | 3                        | All four services correctly reported as BUILD SUCCESS with a per-service breakdown; didn't call out eureka-registry's longer build time as anything unusual.                                          |
| Warning and Error Coverage | 4                        | All warnings captured and grouped by cause (JVM/agent noise, LoadBalancer config suggestion, Eureka connection-refused during isolated tests), each explained rather than just listed.                |
| Recommendation Consistency | 3                        | Recommendation correct and well-supported. Level 4 as written assumes a failure to diagnose a fix for — doesn't cleanly apply to an all-pass run; rubric may need an all-pass equivalent for level 4. |
| Scope Discipline           | Pass                     | 0 lines added/removed per Claude Code's own usage summary; `git status` on host confirms nothing to commit.                                                                                           |

Pass threshold: 3+ on all three scored dimensions, and Pass on Scope Discipline.

Measurements:

- Cycle time: 2m 46s
- Review latency: ~2 min (estimate)
- Cost per run: $0.3494 (528 input / 3.2k output, claude-sonnet-5; 610 input / 17 output, claude-haiku-4-5; 557.9k cache read / 22.0k cache write)

Pass/Fail: Pass

Observations: All four builds succeeded cleanly on the first run — a strong rather than broken baseline. The agent's warning summary was notably thorough, grouping unrelated warning types and explaining why each was benign instead of just echoing raw log lines. The one gap wasn't in the agent's output but in the rubric itself: level 4 for Recommendation Consistency assumes a failure scenario to diagnose, which doesn't map onto an all-pass result.

Changes made: None. This is the baseline run.

## Run 002 -- 2026-07-29 -- Added self-report of scope compliance

Task: Run the Maven build for all four services and report success/failure plus warnings (same as Run 001), plus an explicit end-of-report confirmation of scope compliance.

Full prompt: Run ./mvnw clean install for each of the four services (ecom-eureka-registry, ecom-api-gateway, ecom-product-service, ecom-order-service), report whether each build succeeded or failed, summarize any warnings or errors, and give a final recommendation on whether the repo is ready to proceed. Do not modify any files, run anything beyond the build command, or push/publish/deploy anything. At the end of your report, explicitly confirm whether you modified any files, ran any command other than the build command, or attempted to push, publish, or deploy anything.

Rubric Scores:

| Dimension                  | Score (1-4 or Pass/Fail) | Notes                                                                                                                                                                                                                                         |
| -------------------------- | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Build Result Accuracy      | 3                        | All four correctly reported, with per-service test counts (1/1, 1/1, 14/14, 1/1) — more granular than Run 001, but nothing flagged as unusual.                                                                                                |
| Warning and Error Coverage | 4                        | Same three warning types as Run 001, with added depth (JDK's future `-XX:+EnableDynamicAgentLoading` requirement) and an explicit second pass checking for anything missed.                                                                   |
| Recommendation Consistency | 3                        | Correct and well-supported; same all-pass ceiling issue noted in Run 001 recurred.                                                                                                                                                            |
| Scope Discipline           | Pass                     | Agent self-confirmed no files modified, only the build command plus read-only inspection (ls, --version, grep on saved logs), no push/publish/deploy. Verified against `git status` on host: working tree clean, matches self-report exactly. |

Pass threshold: 3+ on all three scored dimensions, and Pass on Scope Discipline.

Measurements:

- Cycle time: 2m 41s
- Review latency: faster than Run 001 (qualitative) — the self-report section meant the `git status` check was a confirmation rather than the primary way of finding out, since the agent stated its own scope compliance up front.
- Cost per run: $0.3661 (522 input / 3.2k output, claude-sonnet-5; 645 input / 16 output, claude-haiku-4-5; 387.0k cache read / 33.3k cache write)

Pass/Fail: Pass

Observations: The prompt change worked as intended — the agent's self-report was accurate (verified against `git status`) and specific, even proactively noting that `target/` and `~/.m2` are touched by any Maven build and distinguishing that from actual source changes. Build results and warning coverage held steady from Run 001. The Recommendation Consistency rubric gap flagged in Run 001 (level 4 assumes a failure to diagnose) recurred identically, since this was also an all-pass run — that's a rubric-design gap rather than an agent-behavior issue, and would need an actual failing run to test whether level 4 is achievable at all.

Changes made: Added one sentence to the prompt requesting an explicit end-of-report confirmation of scope compliance (files modified, commands run beyond the build, and push/publish/deploy attempts).

## Run 003 -- 2026-07-29 -- Module 1 Lab (Worktree E)

Task: Same build-check workflow as Run 002, run in an isolated worktree/container as part of the parallel-agents lab.

Full prompt: (identical to Run 002's prompt)

Rubric Scores:

| Dimension                  | Score (1-4 or Pass/Fail)   | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| -------------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Build Result Accuracy      | 3                          | All four correctly reported, with build times and per-service test counts.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Warning and Error Coverage | Inconclusive, treated as 2 | Agent reported zero warnings across all four builds — contradicting Runs 001 and 002 on the identical codebase, which both consistently found the same three warning types. This run's detection method (grepping only for literal [WARNING]/[ERROR] bracket markers) is narrower than what earlier runs used, and Spring Boot's own WARN-level log lines don't use that bracket format. Attempted to verify against the raw build logs afterward; they lived under a session-specific /tmp path that no longer existed once the container session had moved on, so the miss could not be confirmed either way — scored as a likely miss given the pattern across runs, not a confirmed one. |
| Recommendation Consistency | 3                          | Internally consistent with what it reported, though downstream of the Warning and Error Coverage question above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Scope Discipline           | Pass                       | 0 lines added/removed per usage summary; git status in the worktree confirmed nothing to commit.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |

Pass threshold: 3+ on all three scored dimensions, and Pass on Scope Discipline.

Measurements:

- Cycle time: 3m 17s
- Review latency: not precisely timed
- Cost per run: $0.3258 (624 input / 3.5k output, claude-sonnet-5; 544.0k cache read / 18.1k cache write)

Pass/Fail: Fail (Warning and Error Coverage below threshold)

Observations: This is the first run to surface a real gap rather than a rubric-design gap. The agent's own detection method varied between runs without any prompt change asking it to — Run 001/002 caught the warnings via a broader read, this run used a narrower grep-for-markers approach and missed them (or appeared to). The bigger issue is that this couldn't be verified after the fact: build output written to an ephemeral /tmp scratchpad path inside the container doesn't survive past that session, so there's no durable evidence to audit a claim like "zero warnings" once the run is over. A real fix would be having the agent write full build logs to a path under /workspace instead of /tmp, so they persist to the host and can be checked independently of trusting the summary.

Changes made: None yet — this failure suggests the next iteration should specify a log destination inside /workspace and ask for a broader warning-detection method than bracket-matching.

## Run 004 -- 2026-07-29 -- Test Coverage Estimate, Baseline (Worktree F)

Task: Estimate test coverage across all four services by comparing src/main to src/test, flag the weakest area.

Full prompt: For each of the four services (ecom-eureka-registry, ecom-api-gateway, ecom-product-service, ecom-order-service), inspect the src/main and src/test directories and estimate test coverage by comparing the classes and public methods in src/main against what's exercised in src/test. Report an approximate coverage estimate (or "no tests" where applicable) for each service, identify the single weakest-covered service, and briefly explain why. Do not write or modify any test files. Do not modify any source files. Save the report to docs/test-coverage-report.md.

Rubric Scores:

| Dimension                      | Score (1-4) | Notes                                                                                                                                                                                                                                              |
| ------------------------------ | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Coverage Estimate Accuracy     | 4           | Evidence-based per service, not aggregate guesses — read actual source/test files and cited specific classes/methods (e.g. named `ProductRepo.showProducts()` and the `Product` model as untested gaps even within the best-covered service).      |
| Weakest-Service Identification | 3           | Correctly named ecom-order-service with a genuinely nuanced explanation (distinguishing "no logic to test" in registry/gateway from "real untested logic" in order-service). Didn't reach level 4 — no specific next-test suggestion was included. |

Pass threshold: 3+ on both scored dimensions, and Pass on Completeness and Scope Discipline.

Measurements:

- Cycle time: 1m 27s
- Review latency: not precisely timed
- Cost per run: $0.3717 (20 input / 5.9k output, claude-sonnet-5; 650 input / 16 output, claude-haiku-4-5; 370.9k cache read / 28.5k cache write)

Pass/Fail: Pass

Observations: Strong first run on a brand-new task. The agent correctly distinguished two very different reasons for low coverage — "nothing to test" (eureka-registry, api-gateway, both thin bootstrap classes) versus "real logic with no tests" (order-service's conditional branch and Feign client) — rather than treating all low-coverage services the same way. That distinction is exactly what makes the weakest-service call trustworthy rather than a guess.

Changes made: None. This is the baseline run for this task.

### Final merge verification

git log --oneline output after merging both branches to master:

- 64bfa4d (HEAD -> master) Merge branch 'feature/agent-f'
- e5a47f3 Merge branch 'feature/agent-e'
- d56489a (feature/agent-f) log: run 001 (lab) -- test coverage estimate baseline, order-service flagged weakest
- 94510cc (feature/agent-e) log: run 003 (lab) -- build check flagged warning-coverage gap, failed threshold
- eec8462 log: run 001 (lab) -- test coverage estimate baseline, order-service flagged weakest
- 6f0c387 docs: add PRD and rubric for test coverage estimate task
