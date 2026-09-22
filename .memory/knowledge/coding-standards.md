# Coding Standards

Last reviewed: 2026-08-13
Maintained by: Viji

These standards apply to all code in this project. The
agent should consult this file before writing or reviewing
any code. These rules are set by humans and the agent
should never modify this file.

## Feign failure handling
Feign call failures are converted to a ResponseStatusException with an appropriate HTTP status (503 for unreachable/general failures, 404 for confirmed not-found), never left to propagate unhandled or returned as a raw error body. Established via decision-001.md, applied consistently in OrderServiceImpl.

## Dependency injection style
Prefer constructor injection over field @Autowired. It makes dependencies explicit and unit testing significantly easier, matching the pattern already used in ProductServiceImpl.

## Test coverage for new logic
Any new service-layer or controller method containing real logic (not just a pass-through) requires a corresponding unit test before merge. Boilerplate context-load tests alone do not satisfy this.

## Test structure and style
New tests follow the existing pattern rather than inventing a new style: MockMvc for controller tests, Mockito for service-layer tests, matching ProductControllerTest and ProductServiceImplTest.

## REST method semantics
The HTTP method on an endpoint must match its actual effect — GET for read-only operations, POST or PUT for anything that mutates state. 

## No orphaned code after exception-handling changes
When restructuring a try/catch, remove any code path that becomes unreachable as a result, in the same change — don't leave dead branches behind for a later cleanup.

## Module structure
New services or modules follow the existing per-service structure (their own pom.xml and mvnw wrapper) rather than introducing a root aggregator pom, to stay consistent with the current four services.