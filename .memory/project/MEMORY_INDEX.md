# Project Memory Index

Last updated: 2026-09-24

## Active entries

- decisions/decision-005.md — Bounded retry added to OrderServiceImpl's Feign calls: RetryableException branch now retries up to 3 total attempts (200ms fixed backoff) before falling into decision-004's existing WARN/503 handling; FeignException/NotFound branches untouched. Human-approved retry count/backoff. Recorded 2026-09-16. Review by 2026-12-15. Committed in 70f81a0.
- decisions/decision-001.md — Feign call failures converted to ResponseStatusException with appropriate HTTP status (503/404). Superseded in part by decision-004.md, which narrows the 503 "unreachable" branch to real RetryableException cases only. Review by: 2026-11-11.
- decisions/decision-002.md — API connection approach using service account; API key referenced via ANTHROPIC_API_KEY env var only, never written to memory/knowledge/code. Recorded 2026-08-26. Review by 2026-11-24.
- decisions/decision-003.md — placeOrder endpoint changed from @GetMapping to @PostMapping to fix REST method semantics violation; breaking change for external GET callers bypassing the gateway. Recorded 2026-09-01. Review by 2026-12-01.
- decisions/decision-004.md — Narrowed OrderServiceImpl's Feign exception handling: split the decision-001 catch-all into a `RetryableException` branch (true unreachable -> 503, WARN log) and a genuine `FeignException` branch (real downstream 4xx/5xx -> 502 for 5xx, 500 for other 4xx, ERROR log with call name/status/message, no request/response bodies logged). Applied to both placeOrder() and viewAllProducts(). Added SLF4J logging to OrderServiceImpl (new pattern for this class). Recorded 2026-09-11. Review by 2026-12-10. Build not run by the Implementer role (no shell access); verified afterward from the orchestrating session via ./mvnw test -Dtest=OrderServiceImplTest — 9 tests, 0 failures, 0 errors, BUILD SUCCESS.

## Archived entries

(none yet)

## Pruning schedule

- Workflow-scoped entries: archived when the branch merges to main
- Project-scoped entries: reviewed every 90 days
