# PRD: Test Coverage Estimate Across Services

**Workflow description:** This workflow estimates test coverage for each of the four services by comparing their source and test directories, then identifies the weakest-covered service.

**Trigger:** A developer invokes `claude "[task prompt]"` from the repo root.

## Decision Events

- If a service has no test directory or no test files, the agent reports it as having no coverage.  
- If a service has test files, the agent estimates rough coverage by comparing the classes/methods present in `src/main` against what's exercised in `src/test`.  
- If multiple services tie for weakest coverage, the agent reports all tied services rather than arbitrarily picking one.

## Actions

1. List the four service modules (`ecom-eureka-registry`, `ecom-api-gateway`, `ecom-product-service`, `ecom-order-service`).  
2. For each service, inspect `src/main` to identify classes and public methods, and `src/test` to identify what's exercised.  
3. Produce an approximate coverage estimate per service (or "no tests" where applicable).  
4. Identify the single weakest-covered service and explain why.  
5. Save the report to `docs/test-coverage-report.md`.

## Acceptance Criteria

- The agent reports a coverage estimate (or "no tests") for all four services, not a subset.  
- The identified weakest service is actually the one with the least test coverage among the four, based on what's in each `src/test` directory.  
- The report is saved to `docs/test-coverage-report.md` and nowhere else.  
- The agent did not create, modify, or delete any test file or any source file.

