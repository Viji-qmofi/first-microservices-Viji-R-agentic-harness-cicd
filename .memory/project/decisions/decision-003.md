# Decision 003 - placeOrder Endpoint Method Corrected to POST

**Date:** 2026-09-01

**Review by:** 2026-12-01

**Status:** Active

**Decision:** `OrderController.placeOrder` is now mapped with `@PostMapping("/orders/place-order/{productId}")` instead of `@GetMapping`, so the HTTP method matches its mutating effect (it creates an order).

**Rationale:** This was a known, standing violation of the "REST method semantics" standard in coding-standards.md, which requires GET for read-only operations and POST/PUT for anything that mutates state. `placeOrder` mutates state (creates an order) but was mapped as GET. Fixed to bring the endpoint into compliance. No existing test depended on the GET mapping — the only test covering `placeOrder` (`OrderServiceImplTest`) exercises the service layer directly via Mockito, not the HTTP layer, and the API gateway route to order-service uses a generic `Path` predicate with no `Method` restriction — so no test changes were required. Verified with `./mvnw test`: `BUILD SUCCESS`, 4 tests run, 0 failures, 0 errors.

**Alternatives rejected:** Leaving the mapping as GET was rejected since it was already flagged as a known violation of an established standard, with no justification for the exception.

**Breaking-change consequence:** Any external caller hitting the order-service directly on `/order-service/v1/orders/place-order/{productId}` (bypassing the API gateway) with a GET request will now receive a 405 Method Not Allowed and must switch to POST. Callers going through the API gateway route (`/purchase/place-order/{id}`) are unaffected at the routing-config level, since that route has no method predicate — but any such caller must still send POST for the request to succeed against order-service.
