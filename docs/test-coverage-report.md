# Test Coverage Report

Estimated by comparing classes/public methods in each service's `src/main` against what is actually exercised in `src/test`. No source or test files were modified to produce this report.

## ecom-eureka-registry

**Main:** 1 class — `EcomEurekaRegistryApplication` (a `@SpringBootApplication` + `@EnableEurekaServer` bootstrap class with only a `main()` method; no custom business logic).

**Test:** 1 class — `EcomEurekaRegistryApplicationTests`, containing a single `contextLoads()` test with an empty body.

**Estimate: No meaningful tests (trivial coverage only).** The only test verifies the Spring context boots. There is no custom code in `src/main` beyond the bootstrap class, so there is effectively nothing else *to* unit test — this service is a thin wrapper around Eureka server auto-configuration.

## ecom-api-gateway

**Main:** 1 class — `EcomApiGatewayApplication` (a `@SpringBootApplication` bootstrap class with only a `main()` method; no custom controllers, filters, or route beans in Java — routing is presumably config-driven).

**Test:** 1 class — `EcomApiGatewayApplicationTests`, containing a single `contextLoads()` test with an empty body.

**Estimate: No meaningful tests (trivial coverage only).** Same situation as eureka-registry: the only test is a context-load smoke test, and there is no custom business logic in `src/main` for it to miss.

## ecom-product-service

**Main classes:** `EcomProductServiceApplication` (bootstrap), `ProductController` (3 endpoints: `viewProducts`, `getProductById`, `getProductByCategory`), `IProductService`/`ProductServiceImpl` (`getAll`, `getById`, `getByCategory`), `ProductRepo` (`showProducts`, a hardcoded fake DB), `Product` (POJO with getters/setters/`toString`).

**Test classes:**
- `ProductControllerTest` — 6 tests via `@WebMvcTest` + `MockMvc`, covering all 3 controller endpoints including empty-list and not-found paths.
- `ProductServiceImplTest` — 7 tests via Mockito, covering `getAll`, `getById` (found / not found / empty repo), and `getByCategory` (case-insensitive match, exact match, no match).
- `EcomProductServiceApplicationTests` — generic `contextLoads()`.

**Estimate: ~85–90% coverage, strong.** All public methods on `ProductController` and `ProductServiceImpl` are exercised, including several edge cases (empty results, not-found, case-insensitive category filtering). Gaps: `ProductRepo.showProducts()` (trivial hardcoded fake DB) and the `Product` model's getters/setters/`toString()` have no direct unit tests, though they are indirectly exercised as data carriers in the other tests. This is the best-covered service.

## ecom-order-service

**Main classes:** `EcomOrderServiceApplication` (bootstrap), `OrderController` (2 endpoints: `placeOrder`, `viewProducts`), `IOrderService`/`OrderServiceImpl` (`placeOrder` — has an if/else branch on whether the product exists; `viewAllProducts`), `IProductServiceFeignClient` (declarative Feign client: `getAllProducts`, `getById`), `Product` (POJO).

**Test:** 1 class — `EcomOrderServiceApplicationTests`, containing only a `contextLoads()` test.

**Estimate: No tests of business logic (~0% for actual logic, only a context-load smoke test).** Unlike the registry/gateway, this service has real business logic — `OrderController` and `OrderServiceImpl` — and none of it is exercised by any test. In particular, the conditional branch in `OrderServiceImpl.placeOrder()` (product found vs. not found) and the Feign client integration are completely untested.

## Weakest-Covered Service: ecom-order-service

**ecom-eureka-registry** and **ecom-api-gateway** also have "no tests" beyond `contextLoads()`, but neither has any custom business logic in `src/main` to begin with — there's nothing of substance those tests are missing. **ecom-order-service**, by contrast, has real logic with a decision point (`placeOrder`'s success/failure branching) and an external service integration (the Feign client), and none of that logic has a single dedicated test. It carries the same "no tests" status as the other two but with meaningfully more untested risk, making it the weakest-covered service overall.

The highest-value first addition would be a `OrderServiceImplTest` (mocking `IProductServiceFeignClient`) covering both branches of `placeOrder()` (product found / not found) and `viewAllProducts()`, mirroring the pattern already established in `ProductServiceImplTest`.

## Summary Table

| Service | Test Files | Coverage Estimate |
|---|---|---|
| ecom-eureka-registry | 1 (context-load only) | No tests (no business logic to cover) |
| ecom-api-gateway | 1 (context-load only) | No tests (no business logic to cover) |
| ecom-product-service | 3 (13 real test methods + context-load) | ~85–90% (strong) |
| ecom-order-service | 1 (context-load only) | No tests — **weakest**, has real untested business logic |
