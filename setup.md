# Agent Sandbox Setup

Baseline container configuration for running a coding agent against this repo (`first-microservices-Viji-R`). Established as part of Exercise 2 ("Build a Sandbox for Your Coding Agent").

## Build

```bash
docker build -t ecom-agent-sandbox .
```

## Run

```bash
# one-time
docker volume create claude-auth

docker run -it --rm \
  -v "$(pwd):/workspace" \
  -v "%cd%\.memory\knowledge:/workspace/.memory/knowledge:ro" \
  -v "%cd%\.memory\reference:/workspace/.memory/reference:ro" \
  -v claude-auth:/root/.claude \
  -e ANTHROPIC_API_KEY \
  ecom-agent-sandbox
```

- **Mounted path:** repo root → `/workspace`. All four Maven modules are needed since `ecom-order-service` calls `ecom-product-service` via Feign, and the agent needs to reason across both.
- **Persistent volume:** `claude-auth` → `/root/.claude`. Persists the Claude Code login across container runs so re-authentication isn't needed every time. On first use it inherits the image's baked-in `settings.json`/`statusline.sh`.
- **Network mode:** default bridge (not restricted). Maven dependencies aren't pre-cached in the image, so `mvn`/`mvnw` need to reach Maven Central on the first build/test run of each service. There's no database or other local service to reach.

## Smoke test

Prompt given to Claude Code inside the container:

> Summarize this repository's architecture and folder structure, then write the summary to /workspace/agent-summary.md.

Output:

```
Here's the repo structure based on what I've found:

Top level
- README.md — project documentation (detailed below)
- Dockerfile, docker-entrypoint.sh — containerization setup
- .project, settings.json, statusline.sh — editor/IDE config
- .metadata/ — Eclipse workspace metadata (not project source code)
- Four Maven-based Spring Boot microservices (each with pom.xml, mvnw/mvnw.cmd, .mvn/, src/)

The four microservices
- ecom-eureka-registry — Netflix Eureka service registry/discovery server (8761)
- ecom-api-gateway — Spring Cloud Gateway, single entry point, routes/filters traffic (9000)
- ecom-product-service — Product catalog, browse/filter products (8081)
- ecom-order-service — Order management, calls product-service via Feign (8082)

Architecture: Client -> ecom-api-gateway -> routes /catalog/** to ecom-product-service and
/purchase/** to ecom-order-service. All services register with ecom-eureka-registry.
ecom-order-service talks to ecom-product-service internally via an OpenFeign client
(IProductServiceFeignClient), using Eureka-based load balancing (lb://).

Package layout (per service):
- ecom-product-service: com.productcatalog -> controllers/, model/, service/, util/
- ecom-order-service: com.productorder -> controllers/, feign/, model/, service/
- ecom-eureka-registry / ecom-api-gateway: single main application class + application.yml

Tech stack: Java 21, Spring Boot, Spring Cloud Gateway (WebMVC), Netflix Eureka, OpenFeign, Maven.
This is described in the README as a beginner-friendly first microservices project by the
author (Viji R).
```

(Full summary: 71 lines, written to `agent-summary.md`.)

**Verification:**
- `agent-summary.md` (71 lines) appeared in the repo root on the host after exiting the container — confirms `/workspace` writes persist.
- Inside the container, `/workspace` showed only the four `ecom-*` service folders plus `README.md`; the host home directory was not visible — confirms the mount boundary held.

## Network egress check

Verified with two paired tests: one under `--network none` (should block all egress), one under the default network (should succeed) — proving the restricted mode genuinely restricts, and that the default mode isn't open by accident.

**Restricted (`--network none`):**
```
C:\Users\vijir\first-microservices-Viji-R>docker run -it --rm --network none -v "%cd%:/workspace" ecom-agent-sandbox
ai-course:/workspace# curl -v --max-time 5 https://api.anthropic.com
* Could not resolve host: api.anthropic.com
* Closing connection
curl: (6) Could not resolve host: api.anthropic.com
ai-course:/workspace# curl https://example.com
curl: (6) Could not resolve host: example.com
```

**Default network:**
```
C:\Users\vijir\first-microservices-Viji-R>docker run --rm ecom-agent-sandbox curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 5 https://api.anthropic.com
HTTP 404

C:\Users\vijir\first-microservices-Viji-R>docker run --rm ecom-agent-sandbox curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 5 https://example.com
HTTP 200
```

`--network none` fails DNS resolution outright — no network interface exists at all, so there's no path for any outbound request regardless of destination. The default network resolves and connects successfully (HTTP 404 on api.anthropic.com is still a real response — DNS, TCP, and TLS all completed; 404 just means that bare path isn't a valid endpoint, which is expected since Claude Code calls specific API paths, not the domain root).

**Network policy:**
- **Default posture: restricted.** Any container session that doesn't need to invoke Claude Code itself (e.g., a plain shell for manual file inspection) runs with `--network none`.
- **Documented exception: routine agent sessions.** Claude Code is a client for the Anthropic API — it cannot function at all without reaching `api.anthropic.com`, regardless of what the underlying task needs. This isn't a task-specific exception (a "coverage estimate" task doesn't itself need network any more than a "build check" task doesn't need it) — it's a tooling requirement of the agent runtime itself, so every Claude Code invocation runs on the default network, not `--network none`.
- **No broader exception granted.** The default network is not scoped further (e.g., to an allowlist of `api.anthropic.com` + `repo.maven.apache.org`) yet — see Residual Risks below.

## Security decisions

- **Local services expected:** four independent Spring Boot apps (Eureka registry, API gateway, product-service, order-service). No database, no message broker, no other local service.
- **Env vars/credentials referenced:** none. No `.env` file and no hardcoded secrets in any `application.yml` — nothing needed mocking or omitting.
- **Smallest safe mount:** the repo root — `ecom-order-service`'s Feign client depends on `ecom-product-service`, so the agent needs both visible to reason about the integration.
- **Network access:** restricted by default (`--network none`), with a documented exception for sessions that invoke Claude Code — see Network Egress Check above for the policy and verification evidence.
- **Install/build/test commands already defined:** `./mvnw spring-boot:run` per service; each service has its own test class runnable via `mvn test`.
- **Runtime/tools baked into the image, each tied to a concrete need:**
  - `maven:3.9-eclipse-temurin-21` (base image) — Java 21 + Maven, required to build and test all four services.
  - `git` — required for `spring-boot-reviewer` and any diff-based task, which start with `git diff`.
  - `curl` — required to install Claude Code/OpenCode via npm registry calls, and used directly for the egress check above.
  - `ca-certificates` — required for any HTTPS connection to succeed at all (Maven Central, npm registry, Anthropic API).
  - `bash` — the container's shell and entrypoint.
  - `nodejs`/`npm` — required to install and run Claude Code (and OpenCode), independent of the project's own Java stack.
  - `nano`, `procps` — minor interactive/debugging conveniences (manual file edits, process inspection); kept but not exercised by any automated workflow to date.
  - `opencode-ai` — course-provided alternative agent CLI; not exercised in this project's workflows so far, kept in case a later module specifically requires it.
  - **Removed:** `ngrok`. The original course Dockerfile installs it, but no task across this entire project has needed to expose a local port or tunnel — it added an external repo/install step with no corresponding use, so it's been dropped from the build.
- **Persistent vs. ephemeral:** source changes persist through the `/workspace` mount; the `claude-auth` volume persists login only. Nothing else is retained — no separate scratch volume needed yet.

## Residual risks and mitigations

| Risk | Mitigation |
|---|---|
| Network access is open (not just to Maven Central/Anthropic, but the whole default bridge) during any Claude Code session. | Verified restrictive baseline via the egress check above, and documented the exception explicitly rather than leaving it silently open. Concrete next step: scope the default-network case to an explicit allowlist (`api.anthropic.com`, `repo.maven.apache.org`) via a custom Docker network with DNS/firewall rules, instead of the full default bridge. Not yet implemented. |
| Container runs as root (no `USER` directive in the Dockerfile). | Concrete next step, drafted but not yet validated: add `RUN useradd -m -u 1000 agent` and `USER agent` near the end of the Dockerfile, after all root-owned installs (npm globals, Maven) complete. Deferred from this submission because it needs a real build-and-run test to confirm the Maven wrapper and npm global installs still work under a non-root user before relying on it. |
| `claude-auth` volume is a long-lived credential — valid indefinitely until explicitly revoked. | `docker volume rm claude-auth` fully revokes it locally. Concrete practice: treat it as short-lived by deleting and re-creating it periodically (e.g., monthly) rather than letting one login persist indefinitely; the volume never leaves the local machine, so there's no remote exposure surface beyond that. |
| Every task mounts the full repo root, even when a task only needs to touch one service. | Already mitigated in practice, not just planned: the parallel-agent exercises (Module 1) scoped each container to a single git worktree via `-v` mounts, so a given agent session could only see and write to its own branch's checkout rather than the whole repo. That pattern is the template for narrowing future single-task sessions the same way. |

**Note:** these are first-pass decisions for this project and are expected to evolve, per the residual risks above.
