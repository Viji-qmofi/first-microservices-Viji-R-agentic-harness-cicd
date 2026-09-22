# Service Discovery & Request Routing

How `ecom-eureka-registry` and `ecom-api-gateway` work together to let clients
reach `product-service` and `order-service` without hardcoded hosts or ports.

## 1. Eureka registry (`ecom-eureka-registry`)

A plain Netflix Eureka server, enabled via `@EnableEurekaServer` on
`EcomEurekaRegistryApplication` (`ecom-eureka-registry/src/main/java/com/ecom/EcomEurekaRegistryApplication.java`).

Its `application.yml` (`ecom-eureka-registry/src/main/resources/application.yml`):

```yaml
server:
  port: 8761

spring:
  application:
    name: eureka-registry
eureka:
  client:
    register-with-eureka: false
    fetch-registry: false
```

- Listens on port `8761` and serves the registry dashboard at `http://localhost:8761`.
- `register-with-eureka: false` and `fetch-registry: false` mean the registry
  doesn't register itself as a client or pull a peer registry — it's a
  standalone server, not part of a Eureka peer-replication cluster.

## 2. How services register

`ecom-api-gateway`, `product-service`, and `order-service` each pull in the
`spring-cloud-starter-netflix-eureka-client` dependency and, on startup, send
periodic heartbeats to `http://localhost:8761/eureka/` (the client's default
`defaultZone`, so the gateway doesn't need to set it explicitly). Eureka
tracks each instance under the id set by that service's
`spring.application.name` (e.g. `api-gateway`, `product-service`,
`order-service`). Once registered and reporting `UP`, an instance becomes
resolvable by that logical name instead of a fixed host:port.

## 3. Gateway routing (`ecom-api-gateway`)

The gateway is a Spring Cloud Gateway (WebMVC) app — `EcomApiGatewayApplication`
has no custom routing code; all routing is declarative config in
`ecom-api-gateway/src/main/resources/application.yml`. It listens on port `9000`
and defines two routes:

```yaml
- id: productService
  uri: lb://product-service
  predicates:
    - Path= /catalog/**
  filters:
    - AddRequestHeader=X-catalog-header,catalogofproducts
    - AddResponseHeader=X-catalog-responsetime,"#{T(java.time.LocalDate).now()}"
    - RewritePath=/catalog/(?<segment>.*),/catalog-service/v1/${segment}

- id: orderService
  uri: lb://order-service
  predicates:
    - Path= /purchase/**
  filters:
    - AddRequestHeader=X-order-header,orderingitems
    - AddResponseHeader=X-order-responsetime,"#{T(java.time.LocalDate).now()}"
    - RewritePath=/purchase/(?<segment>.*),/order-service/v1/orders/${segment}
```

For each incoming request the gateway:

1. Matches the request path against a route's `Path` predicate
   (`/catalog/**` or `/purchase/**`).
2. Applies the route's filters — adding a custom request/response header, and
   rewriting the public path to the internal path the downstream service
   actually exposes (e.g. `/catalog/products` → `/catalog-service/v1/products`).
3. Resolves the target via the route's `lb://` URI.

## 4. `lb://` load balancing

`uri: lb://product-service` and `uri: lb://order-service` are not real
hostnames — the `lb` scheme tells Spring Cloud Gateway to resolve the
following segment (`product-service`, `order-service`) as a Eureka service
name rather than a DNS host. At request time, Spring Cloud LoadBalancer:

1. Asks the Eureka client for all `UP` instances registered under that
   service name.
2. Picks one instance (client-side load balancing — the choice happens in
   the gateway process, not behind a separate load balancer).
3. Rewrites `lb://product-service/...` to that instance's real
   `http://host:port/...` and forwards the (already path-rewritten,
   header-modified) request.

Because resolution happens by service name at request time, the gateway
never hardcodes `product-service`'s or `order-service`'s host/port, and it
keeps working if an instance restarts on a different port or multiple
instances of a service are scaled up — Eureka and the load balancer handle
picking a live one.

## End-to-end example

```
GET http://localhost:9000/catalog/products/productId/1
  → gateway matches Path=/catalog/**
  → adds X-catalog-header / X-catalog-responsetime
  → rewrites to /catalog-service/v1/products/productId/1
  → resolves lb://product-service via Eureka → e.g. http://<host>:8081
  → forwards to http://<host>:8081/catalog-service/v1/products/productId/1
```

The same flow applies to `/purchase/**` requests routed to `order-service`.
