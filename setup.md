# Agent Sandbox Setup

Baseline container configuration for running a coding agent against this repo (`first-microservices-Viji-R-agentic-harness-cicd`). Established as part of Exercise 2 ("Build a Sandbox for Your Coding Agent"), extended through Module 4's governance and CI/CD work.

## If you forked this repository

Two things don't transfer automatically via `git fork` and need doing once, before anything else works:

1. **GitHub Actions is disabled by default on a fork that already contains workflow files.** Go to the **Actions** tab on your fork; you'll see a banner -- click "I understand my workflows, go ahead and enable them." Nothing will run, not even a failed check, until this is done.
2. **Branch protection rules do not transfer via fork.** If you want `main` genuinely protected (required status checks actually blocking a merge, not just visible), go to **Settings -> Branches**, add a rule for `main`, enable "Require a pull request before merging" and "Require status checks to pass before merging," and select "Policy Test Suite," "Evaluation Harness," and "Pipeline Integrity Check." Skipping this doesn't break local use -- it only means a direct push to `main` isn't actually blocked by any of the CI checks, regardless of what the workflow file says.

## Build

```bash
docker build -t ecom-agent-sandbox .
```

## Run

```bash
docker volume create claude-auth
```

```cmd
docker run -it --rm --cap-drop=DAC_OVERRIDE -p 8001:8001 -p 8002:8002 -p 6274:6274 -p 6277:6277 -v "%cd%:/workspace" -v "%cd%\.memory\knowledge:/workspace/.memory/knowledge:ro" -v "claude-auth:/claude-auth" -e ANTHROPIC_API_KEY -e COURSETOOLS_ROOT=/workspace -e STORAGE_DB_PATH=/workspace/.memory/storage/storage.db -e STORAGE_AUDIT_PATH=/workspace/.memory/storage/storage-audit.log -e RETRIEVAL_AUDIT_PATH=/workspace/.memory/storage/retrieval-audit.log -e RETRIEVAL_REFERENCE_DIR=/workspace/.memory/reference ecom-agent-sandbox
```

(Windows Command Prompt syntax, matching how this project has been operated throughout. If you're on macOS/Linux or Git Bash, translate `%cd%` to `$(pwd)` and the line-continuation caret `^` to `\` -- do not mix the two conventions in one command.)

- **Mounted path:** repo root -> `/workspace`. All four Maven modules are needed since `ecom-order-service` calls `ecom-product-service` via Feign.
- **Persistent volume:** `claude-auth` -> **`/claude-auth`, not `/root/.claude`.** This distinction matters and has caused a real, previously-debugged failure: the entrypoint script copies just the login credential between `/claude-auth` and `/root/.claude/.credentials.json` on start/stop, deliberately leaving the rest of `/root/.claude` (including this image's build-time-baked `agents/`/`skills/`) untouched. Mounting the volume directly at `/root/.claude` instead silently shadows everything the image bakes into that path with whatever the volume's own history contains -- if you ever see your real agents missing from `claude`'s agent list despite a fresh build, check this mount path first.
- **`.memory/knowledge` mounted `:ro` separately**, even though it also lives inside `/workspace`: this is what actually makes it read-only to agents, overriding the general workspace mode -- `--cap-drop=DAC_OVERRIDE` alone is not sufficient, since a plain mount without the override flag can still be written to by root inside the container.
- **Ports:** 8001/8002 for the storage/retrieval MCP servers (HTTP transport, started manually inside the container -- see below); 6274/6277 for MCP Inspector, if used.
- **Network mode:** default bridge. Maven dependencies aren't pre-cached in the image, so `mvn`/`mvnw` need to reach Maven Central on first build. Claude Code itself cannot function at all without reaching `api.anthropic.com` -- see Network Egress Check below for the full policy and verification evidence.

## Two separate credentials

1. **Claude Code's interactive login**, persisted via the `claude-auth` volume above. Run `claude`, then `/login` the first time; subsequent containers using the same volume won't need it again, as long as you `exit` cleanly rather than killing the container.
2. **A real `ANTHROPIC_API_KEY`**, separate from the above, needed anywhere the model is called *without* an interactive login -- specifically CI's `eval-gate` job, which runs `claude -p` headlessly. Get one at console.anthropic.com -> Settings -> API Keys; it has its own billing, distinct from a Claude subscription. To use it in CI (not just locally), add it as a GitHub Actions repository secret: **Settings -> Secrets and variables -> Actions -> New repository secret**, named `ANTHROPIC_API_KEY`.

## Starting the MCP servers

`coursetools` (stdio) registers automatically each `claude` session. `storage` and `retrieval` (HTTP) do not -- start and register them manually, every fresh container, before they're needed:

```bash
python3 mcp-servers/storage/server.py --port 8001 --host 0.0.0.0 &
python3 mcp-servers/retrieval/server.py --port 8002 --host 0.0.0.0 &
claude mcp add --scope project --transport http storage http://localhost:8001/mcp
claude mcp add --scope project --transport http retrieval http://localhost:8002/mcp
```

Then run `claude` (or restart it, if already running, so it picks up the new registrations) and confirm with `/mcp`. If a tool call reports "connection refused" on port 8001/8002 mid-session, the servers were never started in this container -- start them, then restart `claude`.

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
C:\Users\<you>\first-microservices-Viji-R>docker run -it --rm --network none -v "%cd%:/workspace" ecom-agent-sandbox
ai-course:/workspace# curl -v --max-time 5 https://api.anthropic.com
* Could not resolve host: api.anthropic.com
* Closing connection
curl: (6) Could not resolve host: api.anthropic.com
ai-course:/workspace# curl https://example.com
curl: (6) Could not resolve host: example.com
```

**Default network:**
```
C:\Users\<you>\first-microservices-Viji-R>docker run --rm ecom-agent-sandbox curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 5 https://api.anthropic.com
HTTP 404

C:\Users\<you>\first-microservices-Viji-R>docker run --rm ecom-agent-sandbox curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 5 https://example.com
HTTP 200
```

`--network none` fails DNS resolution outright — no network interface exists at all, so there's no path for any outbound request regardless of destination. The default network resolves and connects successfully (HTTP 404 on api.anthropic.com is still a real response — DNS, TCP, and TLS all completed; 404 just means that bare path isn't a valid endpoint, which is expected since Claude Code calls specific API paths, not the domain root).

**Network policy:**
- **Default posture: restricted.** Any container session that doesn't need to invoke Claude Code itself (e.g., a plain shell for manual file inspection) runs with `--network none`.
- **Documented exception: routine agent sessions.** Claude Code is a client for the Anthropic API — it cannot function at all without reaching `api.anthropic.com`, regardless of what the underlying task needs. This isn't a task-specific exception — it's a tooling requirement of the agent runtime itself, so every Claude Code invocation runs on the default network, not `--network none`.
- **No broader exception granted.** The default network is not scoped further (e.g., to an allowlist of `api.anthropic.com` + `repo.maven.apache.org`) yet — see Residual Risks below.

## Security decisions

- **Local services expected:** four independent Spring Boot apps (Eureka registry, API gateway, product-service, order-service). No database, no message broker, no other local service.
- **Env vars/credentials referenced:** `ANTHROPIC_API_KEY` (model access) and the paths listed in the run command above (internal MCP server config, not secrets). No `.env` file and no hardcoded secrets in any `application.yml`.
- **Smallest safe mount:** the repo root — `ecom-order-service`'s Feign client depends on `ecom-product-service`, so the agent needs both visible to reason about the integration.
- **Network access:** restricted by default (`--network none`), with a documented exception for sessions that invoke Claude Code — see Network Egress Check above for the policy and verification evidence.
- **Install/build/test commands already defined:** `./mvnw spring-boot:run` per service; each service has its own test class runnable via `mvn test`.
- **Runtime/tools baked into the image, each tied to a concrete need:**
  - `maven:3.9-eclipse-temurin-21` (base image) — Java 21 + Maven, required to build and test all four services.
  - `git` — required for `spring-boot-reviewer`/`reviewer` and any diff-based task.
  - `curl` — required to install Claude Code/OpenCode via npm registry calls, and used directly for the egress check above.
  - `ca-certificates` — required for any HTTPS connection to succeed at all (Maven Central, npm registry, Anthropic API).
  - `bash` — the container's shell and entrypoint.
  - `nodejs`/`npm` — required to install and run Claude Code (and OpenCode), independent of the project's own Java stack.
  - `python3`/`pip3` — required for the three MCP servers and the CI/governance scripts; see `requirements.txt` for the pinned dependency set (`mcp<2` specifically, since unpinned installs break `coursetools_server.py`'s import).
  - `nano`, `procps` — minor interactive/debugging conveniences; kept but not exercised by any automated workflow to date.
  - `opencode-ai` — course-provided alternative agent CLI; not exercised in this project's workflows so far, kept in case a later module specifically requires it.
  - **Removed:** `ngrok`. The original course Dockerfile installs it, but no task across this entire project has needed to expose a local port or tunnel.
- **Persistent vs. ephemeral:** source changes persist through the `/workspace` mount; the `claude-auth` volume persists login only, mounted at `/claude-auth` (see Run, above). Nothing else is retained.

## Residual risks and mitigations

| Risk | Mitigation |
|---|---|
| Network access is open (not just to Maven Central/Anthropic, but the whole default bridge) during any Claude Code session. | Verified restrictive baseline via the egress check above, and documented the exception explicitly rather than leaving it silently open. Concrete next step: scope the default-network case to an explicit allowlist via a custom Docker network with DNS/firewall rules. Not yet implemented. |
| Container runs as root (no `USER` directive in the Dockerfile). | Concrete next step, drafted but not yet validated: add `RUN useradd -m -u 1000 agent` and `USER agent` near the end of the Dockerfile, after all root-owned installs complete. Deferred pending a build-and-run test confirming the Maven wrapper and npm global installs still work under a non-root user. |
| `claude-auth` volume is a long-lived credential — valid indefinitely until explicitly revoked. | `docker volume rm claude-auth` fully revokes it locally. Concrete practice: treat it as short-lived by deleting and re-creating it periodically rather than letting one login persist indefinitely. |
| Every task mounts the full repo root, even when a task only needs to touch one service. | Already mitigated for governed roles via `scripts/run-agent.ps1` (Module 4.1), which launches read-only-workspace containers for roles that don't need write access (`planner`, `reviewer`, `spring-boot-reviewer`, `decision-auditor`), and a scoped `.memory/project/` read+write exception for `decision-auditor` specifically rather than full workspace access. |
| MCP role/classification checks authorize against a self-declared `calling_role`, not a verified caller identity. | Documented explicitly, not hidden, in `CLAUDE.md` and `docs/routing-and-tool-grant-map.md`. Architecturally forced by subagents sharing one Orchestrator container rather than running as separately-identifiable processes (`ADR-005`); would need a different process architecture to close fully. |

**Note:** these decisions are expected to continue evolving as the project does — see `module3_doc/calibration-log.md` for the full record of changes and the evidence behind each one.
