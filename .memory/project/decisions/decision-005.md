# Decision 005 - Bounded Retry for RetryableException in OrderServiceImpl

**Date:** 2026-09-16

**Review by:** 2026-12-15

**Status:** Active

**Builds on:** decision-004.md's `RetryableException` branch (true unreachable-service case -> WARN log -> 503). That branch's *classification* and *terminal outcome* are unchanged; what changes is that the Feign call itself is now retried a bounded number of times before falling into that branch.

**Decision:** In both `placeOrder(int)` and `viewAllProducts()` in `OrderServiceImpl`, the Feign call (`feignClient.getById(...)` / `feignClient.getAllProducts()`) is routed through a new private helper `callWithRetry(Supplier<T>)`. The helper retries only on `feign.RetryableException` (no HTTP response received at all), up to `MAX_ATTEMPTS = 3` total attempts (1 initial + 2 retries), with a fixed `RETRY_BACKOFF_MS = 200` (200ms) `Thread.sleep` between attempts -- no exponential backoff or jitter. Once attempts are exhausted, the last `RetryableException` is rethrown unchanged and flows into the existing decision-004 `catch (RetryableException ex)` block (WARN log, 503) exactly as before. `FeignException.NotFound` and general `FeignException` (real HTTP responses) are not retried -- they are not `RetryableException` subtypes, so they propagate out of the helper on the first attempt, unretried, and their decision-004 handling/status-mapping is completely untouched.

**Why a manual loop instead of a Feign `Retryer` bean:** `OrderServiceImplTest` mocks `IProductServiceFeignClient` directly with Mockito, which bypasses Feign's `SynchronousMethodHandler`/`Retryer` SPI entirely -- a `Retryer`-based fix would never be exercised by the existing test suite and would require new Spring-context/WireMock integration tests this module doesn't otherwise have. The retry is instead implemented as a plain bounded loop at the call site in `OrderServiceImpl`, kept verifiable with the same Mockito approach already established.

**No logging inside the retry loop:** the single WARN log for an exhausted retry sequence still fires exactly once, from the existing outer `catch (RetryableException ex)` block, only after retries are exhausted -- preserving the existing `listAppender.list).hasSize(1)` test assertions unmodified.

**Externally-visible behavior change (flagged and approved by the human before implementation):** a downstream outage that previously returned 503 on the very first failed attempt now takes up to ~400ms longer before returning 503, and a transient (self-resolving within ~400ms) outage may now succeed transparently instead of failing. Retry count (3) and backoff (200ms fixed) were explicit human-approved values, not left to implementer discretion.

**Test coverage:** `OrderServiceImplTest` updated -- two new tests (`placeOrder_succeedsAfterRetries_...`, `viewAllProducts_succeedsAfterRetries_...`) cover retry-then-succeed (2 failures + 1 success, `verify(times(3))`). All pre-existing `RetryableException`-unreachable tests gained `verify(feignClient, times(3))` (confirms full retry exhaustion, not just one attempt). All pre-existing plain-`FeignException` tests (`NotFound`, 4xx, 5xx, boundary, error-log cases) gained `verify(feignClient, times(1))` (confirms no retry occurs on non-`RetryableException` paths).

**Build verification:** Run directly by the orchestrating session (not delegated to Implementer, which has no shell access by design): `./mvnw test -Dtest=OrderServiceImplTest` -> `Tests run: 25, Failures: 0, Errors: 0` -- `BUILD SUCCESS`. Full module suite `./mvnw test` -> `Tests run: 26, Failures: 0, Errors: 0` -- `BUILD SUCCESS`. Diff independently reviewed against the implementer's claimed summary via `git diff` and confirmed scoped to exactly the two named files (other working-tree changes present in the repo at session start are pre-existing line-ending-only diffs in unrelated files, confirmed via `git diff --ignore-all-space`, not touched by this change).

**Not yet done:** change has not been committed -- pending human approval per the CLAUDE.md human-checkpoint requirement.
