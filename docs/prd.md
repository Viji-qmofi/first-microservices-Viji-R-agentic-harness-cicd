# PRD: Multi-Service Build Health Check

**Workflow description:** This workflow reviews the repository's build health by running each of the four services' documented Maven build command, reporting the outcome, and recommending whether the repo is ready to proceed.

**Trigger:** A developer invokes `claude "[task prompt]"` from the repo root.

## Decision Events

- If a service's build succeeds, the agent summarizes any warnings and includes that service in the "ready" set.
- If a service's build fails, the agent reports the error output for that service and excludes it from the "ready" set. It does not attempt a fix.
- If all four services succeed, the agent recommends proceeding.
- If any service fails, the agent recommends against proceeding until that failure is resolved.

## Actions

1. Identify the four service modules (`ecom-eureka-registry`, `ecom-api-gateway`, `ecom-product-service`, `ecom-order-service`) and their documented build command (`./mvnw clean install`).
2. Run the build command for each of the four services in turn, inside the sandbox.
3. Capture the output from each build.
4. Evaluate each build's result (success or failure).
5. Summarize any warnings or errors present in each service's output.
6. Produce a final recommendation — ready to proceed or not ready — with a brief rationale listing which services (if any) failed.

## Acceptance Criteria

- The agent correctly identifies the success/failure outcome for each of the four services.
- The summary includes all warnings and errors present in each service's build output; it does not omit any.
- The final recommendation is consistent with the actual build results (recommends against proceeding if any service failed).
- The agent did not modify any source file, run anything beyond the build command, or push/publish/deploy anything.
