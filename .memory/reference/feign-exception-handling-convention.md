---
classification: internal
project: proj-lessons
doc_type: decision
---

# Feign Failures Are Converted to ResponseStatusException, Not Left Unhandled

What happened: `OrderServiceImpl`'s `placeOrder()` and `viewAllProducts()` originally handled Feign client failures against `product-service` inconsistently -- one method threw a `ResponseStatusException`, the other manually built a `ResponseEntity<String>` with matching status codes but a different mechanism. A repeated review finding (`spring-boot-reviewer`, multiple runs) also showed the original handling mislabeled any non-404 failure as "unreachable," swallowing the real cause with no logging.

What was learned: both methods now catch `feign.RetryableException` specifically for a true unreachable-service case (timeout, connection refused, no HTTP response at all) -- logged at WARN, mapped to 503 -- and catch the general `FeignException` separately for cases where a real HTTP status *was* returned, logged at ERROR with the actual status code, mapped to 502 for downstream 5xx or 500 for other non-404 4xx. Downstream response detail is never echoed back to the caller. This distinguishes a truly unreachable downstream service (no response received at all) from a case where a real HTTP error response was received.

How to apply it: any new Feign-calling code in this project should follow this same pattern -- distinguish "no response received" from "a real error response was received," log the real cause, and never collapse every failure into one generic status code. This convention is recorded formally in `.memory/project/decisions/decision-001.md` and `decision-004.md`, and as a standing rule in `.memory/knowledge/coding-standards.md`.
