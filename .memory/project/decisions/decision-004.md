# Decision 004 - Narrowed Feign Exception Handling in OrderServiceImpl

**Date:** 2026-09-11

**Review by:** 2026-12-10

**Status:** Active

**Supersedes/narrows:** decision-001.md's "503 for unreachable/general failures" convention. decision-001 established that Feign failures should become a `ResponseStatusException` rather than propagate raw or be built manually -- that convention is unchanged. What changes here is what counts as "unreachable": decision-001's catch-all `catch (FeignException ex)` block treated every non-404 Feign failure (timeouts, DNS failures, connection refused, but also real 4xx/5xx HTTP responses from the downstream product-service) identically, as 503 "Product service is currently unreachable, please try again later".

**Decision:** In both `placeOrder(int)` and `viewAllProducts()` in `OrderServiceImpl`, the single catch-all `catch (FeignException ex)` block is split into two:

1. `catch (RetryableException ex)` (feign.RetryableException, a `FeignException` subtype thrown only when no HTTP response was received at all -- connection refused, timeout, DNS failure) -- logged at WARN (treated as an expected, self-resolving operational condition, not a bug), including the downstream call name, the productId (for `placeOrder`), and `ex.getMessage()`. This is now the only branch that produces `HttpStatus.SERVICE_UNAVAILABLE` ("Product service is currently unreachable, please try again later").
2. `catch (FeignException ex)` (now only reached for genuine non-404 HTTP responses from the downstream service) -- logged at ERROR (a real downstream failure/misbehavior worth surfacing loudly), including the downstream call name, the relevant id where applicable, `ex.status()`, and `ex.getMessage()`. Request/response bodies and headers are deliberately not logged, to avoid leaking sensitive data (e.g. auth tokens) into logs. The resulting status is mapped from `ex.status()`:
   - 5xx from downstream -> `HttpStatus.BAD_GATEWAY` (502), "Product service returned an error, please try again later"
   - other 4xx (i.e. not already handled by the existing `FeignException.NotFound` branch in `placeOrder`) -> `HttpStatus.INTERNAL_SERVER_ERROR` (500), generic "Unable to process request due to an internal error" -- the downstream 4xx reason is deliberately not echoed back to the order-service's own caller, since a 400/401 on an internal Feign call is an order-service bug, not something the external caller can act on.

A `private static final Logger logger` (SLF4J `org.slf4j.Logger`/`LoggerFactory`) field was added to `OrderServiceImpl` -- the first use of structured logging in this class. No new logging dependency was added; SLF4J is already on the classpath transitively via Spring Boot.

**Rationale:** The decision-001 catch-all was mislabeling all non-404 failures -- including real 4xx/5xx responses actually returned by the downstream product-service -- as "unreachable", which is both misleading to operators (a 500 from the downstream service is not the same operational condition as it being unreachable) and swallowed the real cause of the failure (no logging existed at all before this change, and the status code returned to the caller was always 503 regardless of what actually happened).

**Alternatives rejected:** Introducing a custom exception hierarchy or a `@ControllerAdvice`-based global handler was rejected as out of scope -- the fix is kept localized to the two existing catch blocks, consistent with the existing pattern of catching in the service layer and throwing `ResponseStatusException` directly (per decision-001). The `FeignException.NotFound` handling itself (already flagged in `module2_doc/iteration-log.md` as possibly dead code, since product-service returns 200-with-null rather than a real 404 for a missing product) was left untouched -- that is a separately tracked, pre-existing issue, not part of this change's scope.

**Test coverage:** `OrderServiceImplTest` was updated:
- The previous `placeOrder_throwsServiceUnavailable_whenProductServiceUnreachable` test (which actually exercised a mocked 500, via `FeignException.errorStatus`) was renamed to `placeOrder_throwsBadGateway_whenProductServiceReturns500` and its expected status changed from `SERVICE_UNAVAILABLE` to `BAD_GATEWAY`, reflecting the new mapping.
- A new `placeOrder_throwsServiceUnavailable_whenProductServiceUnreachable` test was added that mocks a real `feign.RetryableException` (constructed via `new RetryableException(-1, "connection timed out", Request.HttpMethod.GET, (Long) null, request)`) and asserts `SERVICE_UNAVAILABLE` -- this is the true "unreachable" case now.
- A new `placeOrder_throwsInternalServerError_whenProductServiceReturnsOther4xx` test asserts a mocked 400 response maps to `INTERNAL_SERVER_ERROR`, not 503 -- the concrete regression test for the "no longer mislabeled as unreachable" fix.
- `viewAllProducts()` previously had zero dedicated test coverage in this file; four tests were added: success, unreachable (`RetryableException` -> 503), 5xx (-> 502), and other 4xx (-> 500).

**Build verification:** Not run by the Implementer role (no shell/`test_runner` access in this workflow, by design). Verified afterward from the orchestrating session via `./mvnw test -Dtest=OrderServiceImplTest`: `Tests run: 9, Failures: 0, Errors: 0, Skipped: 0` -- `BUILD SUCCESS`. This confirms the `feign.RetryableException` 5-argument constructor `(int, String, Request.HttpMethod, Long, Request)` used in the new test compiles and resolves correctly against this project's actual Feign version (transitively pulled in via `spring-cloud-starter-openfeign` / spring-cloud 2025.1.1), and the WARN/ERROR log lines fire as designed (confirmed in test output: ERROR for 400/500 downstream responses, WARN for the `RetryableException`/unreachable case).
