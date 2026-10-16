# Module 1 Baseline vs Final System: Measured Comparison

Purpose: compare the final governed system against the Module 1 baseline on five metrics, and test whether governance caused the quality failures seen on re-run. All figures come from runs recorded in `docs/iteration-log.md` and the evidence folder. Estimates are labeled as estimates.

## 1. Setup

Every run used the same prompt as Module 1 Run 001 (build all four services with `./mvnw clean install`, report results and warnings, recommend, modify nothing) and the same model, Sonnet 5, in a fresh container.

- **Baseline:** Module 1 Run 001, July 2026 (Sonnet 5 + Haiku 4.5 subagent).
- **Final Run 1 and Final Run 2:** the final governed system (CLAUDE.md and .mcp.json active).
- **Control 1 and Control 2:** governance removed (CLAUDE.md and .mcp.json renamed to `.off`), otherwise identical. Files restored afterward; `git status --short` confirmed empty.

## 2. Ground truth (no model involved)

- All four builds exit 0. Test counts: 1 + 1 + 14 + 41 = 57.
- WARN/ERROR lines exist in all four services: JVM/Byte Buddy agent noise; the LoadBalancer cache warning in all four; Eureka connection refusals in the gateway and product service; intentional WARN/ERROR test logging in order-service.
- Maven alone takes about 3m46s warm.

This is the answer key used to score Warning and Error Coverage.

## 3. Scores per run (docs/rubric.md)

All four re-runs scored Build Result Accuracy 3, Recommendation Consistency 3 and Scope Discipline Pass. They differ on Warning and Error Coverage.

- **Baseline:** accuracy 3, warnings 4, recommendation 3, Scope Pass. Passed.
- **Final Run 1:** warnings 2 (missed the LoadBalancer warning). Failed.
- **Final Run 2:** warnings 1. Reported "Warnings/errors: None" and claimed zero hits, which is false. Failed.
- **Control 1:** warnings 2, borderline. Named all four warning types but declared eureka-registry clean and misplaced the LoadBalancer warning. Failed.
- **Control 2:** warnings 1. Reported "None" after grepping only Maven's `[WARNING]`/`[ERROR]` markers, so it missed the runtime log lines. Failed.

## 4. The five metrics

**Quality.** The baseline passed (3/4/3). All four re-runs fail on warning coverage, with and without governance.

**Defect rate (proxy).** The proxy is the share of runs that fail the rubric. Baseline: 1 of 4 Module 1 runs failed. Re-runs: 4 of 4 failed under strict scoring (2 final, 2 control).

**Cycle time.** Baseline 2m46s. Controls about 5m38s on average. Final Run 2 6m38s. Governance adds roughly 1 minute over the controls. Most of the jump from July is Maven running a much larger test suite. Final Run 1 (7m01s) was interrupted and resumed, so it is excluded from timing.

**Cost per run.** Baseline $0.3494. Controls average about $0.38 (about +9% over baseline, attributable to workload and environment). Final Run 2 $0.50 (about +32% over controls, attributable to governance context).

**Review latency.** The baseline value of about 2 minutes was an estimate. One re-run review was then timed: reading the Final Run 2 report and checking it against the answer key took about 2.5 minutes. The two figures are close, so there is no evidence that governance changes review time. The measured figure is a single observation, with the caveats in section 6.

## 5. Reading

- The warning-coverage failures occur at the same rate with governance removed, so governance did not cause them.
- The likelier cause is the task: the repo now emits intentional runtime WARN/ERROR lines (order-service tests grew from 1 to 41), and a narrow grep for Maven markers misses them. The baseline's July pass was against a quieter repo.
- Governance has a measurable cost: roughly +32% per run and about +1 minute. In exchange it provides enforcement, an audit trail and the escalation gates documented elsewhere. This comparison does not measure those benefits.

## 6. Limitations

- n is small: one baseline run against four re-runs.
- The repo changed between July and now (test count, versions, network), so baseline-to-re-run deltas mix workload and system effects. Only control-to-final isolates governance.
- Final Run 1 timing is unreliable (interrupted and resumed).
- Cost is from a Claude Pro session, so figures are API-equivalent estimates.
- Cycle times for the re-runs come from the agent's elapsed-time lines and the status line, not one uniform clock.
- Review latency was timed once (n=1). The reviewer had already built the answer key, and the four scores were not written down during the timing, so about 2.5 minutes slightly understates a full scoring pass.
- The Scope Discipline reading is ambiguous: CLAUDE.md startup reads versus "run nothing beyond the build". All runs were scored Pass on the Run 002 precedent (read-only commands only).

## 7. Follow-up (done): prompt clarification

The prompt-clarification iteration was run. Run 005 named runtime WARN/ERROR lines and scored Warning Coverage 2 (up from 1) but failed Scope Discipline. Run 006 added JVM warnings and a /tmp-only rule and passed at 3/4/3. An identical rerun of Run 006 scored 2 and failed on a false "JVM warnings: None". Full scores are in `docs/iteration-log.md`. The prompt change helps but is not reliable on its own. More timed reviews, ideally by someone who has not seen the answer key, would tighten the review-latency figure.
