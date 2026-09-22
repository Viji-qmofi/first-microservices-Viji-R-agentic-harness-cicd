# 1. Quality Rubric — Test Coverage Estimate

## 1.1 Dimensions

### 1.1.1 Coverage Estimate Accuracy

Measures whether the agent's per-service coverage estimate reasonably reflects what's actually in each service's `src/test` directory. A high score requires the estimate to be plausible and defensible against the actual test files present, not just a guess.

### 1.1.2 Weakest-Service Identification

Measures whether the agent correctly identifies which service has the least test coverage, with a defensible explanation. A high score requires the identified service to genuinely be the weakest among the four, based on the evidence the agent itself gathered.

### 1.1.3 Completeness

Measures whether all four services are covered in the report, with no service skipped or given only a vague, non-specific mention.

### 1.1.4 Scope Discipline (binary)

Measures whether the agent stayed within the task boundary: only inspecting files, writing exactly one output file (`docs/test-coverage-report.md`), and not creating, modifying, or deleting any test or source file. Pass if no boundary violation occurred; fail if any did.

**Alternatives considered:** treating this as a binary "did it produce a report" checklist. Ruled out because it can't distinguish a report that's genuinely useful (correctly identifies the weakest service, with real evidence) from one that's superficially complete but wrong — the whole point of this task is prioritizing where to add tests next, so accuracy matters more than mere existence of a report.

## 1.2 Scoring Guide

### 1.1.1 Coverage Estimate Accuracy

| Level | Description | Example |
|---|---|---|
| 1: Does Not Meet | Estimates are stated with no reference to actual test file contents — appear guessed. | "Coverage is probably around 50% for all services" with no per-service detail. |
| 2: Partially Meets | Some services have evidence-based estimates; others are vague or unsupported. | product-service estimate cites specific test methods; the other three just say "some coverage" or "unclear." |
| 3: Meets | All four services have an estimate grounded in what's actually present in `src/test` (including correctly noting zero test files where that's the case). | Each service's estimate references its actual test file count or specific test methods found. |
| 4: Exceeds | Meets Level 3, and also notes which specific classes or methods are untested within each service, not just an aggregate percentage. | product-service: "controller layer covered; utility classes in `util/` have no corresponding tests." |

### 1.1.2 Weakest-Service Identification

| Level | Description | Example |
|---|---|---|
| 1: Does Not Meet | Identified service is not actually the weakest based on the agent's own findings, or no service is named. | Names api-gateway as weakest despite eureka-registry having zero test files. |
| 2: Partially Meets | Correct service named, but the explanation doesn't match the evidence gathered or is missing. | Correctly names eureka-registry, but gives no reason or an unrelated reason. |
| 3: Meets | Correct service named, with an explanation that matches the evidence gathered earlier in the report. | "eureka-registry has no test directory at all, versus at least one test class in each other service." |
| 4: Exceeds | Meets Level 3, and also suggests what kind of test would most improve coverage first (without writing it). | Level 3, plus: "a basic context-load test would be the highest-value first addition." |

### 1.1.3 Completeness

Binary. **Pass:** all four services appear in the report with a specific estimate or explicit "no tests" finding. **Fail:** one or more services is missing or given only a vague, non-specific mention.

### 1.1.4 Scope Discipline

Binary. **Pass:** only files were inspected; exactly one output file was written (`docs/test-coverage-report.md`); no test or source file was created, modified, or deleted. **Fail:** any of those boundaries was crossed.

## 1.3 Pass Threshold

A run is passing if it scores 3 or higher on Coverage Estimate Accuracy and Weakest-Service Identification, **and** passes both Completeness and Scope Discipline. Completeness and Scope Discipline are gates, not averaged scores — a report that skips a service or edits a file it shouldn't have fails regardless of how good the rest of the analysis is.

**Notes on threshold design:** considered scoring Completeness on the same 1-4 scale as the other dimensions. Ruled out because covering "3 of 4 services well" isn't a partial success for this task — a report that's silent on one service can't be trusted to have correctly identified the weakest one, since the missing service might well have been it.
