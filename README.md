# E-Commerce Microservices Application — Agentic Development Harness

A Spring Boot microservices e-commerce application, developed and maintained by an orchestrated multi-agent system with persistent memory, MCP-based tool governance, an evaluation harness, and a CI/CD pipeline that gates on all of the above. Built incrementally across LaunchCode's Agentic Engineering course.

## Quick Start

```bash
docker build -t ecom-agent-sandbox .
```

```cmd
docker run -it --rm --cap-drop=DAC_OVERRIDE -p 8001:8001 -p 8002:8002 -p 6274:6274 -p 6277:6277 -v "%cd%:/workspace" -v "%cd%\.memory\knowledge:/workspace/.memory/knowledge:ro" -v "claude-auth:/claude-auth" -e ANTHROPIC_API_KEY -e COURSETOOLS_ROOT=/workspace -e STORAGE_DB_PATH=/workspace/.memory/storage/storage.db -e STORAGE_AUDIT_PATH=/workspace/.memory/storage/storage-audit.log -e RETRIEVAL_REFERENCE_DIR=/workspace/.memory/reference ecom-agent-sandbox
```

Note the mount: `claude-auth:/claude-auth`, not `/root/.claude`. The two paths are not interchangeable -- see "Two separate credentials" below.

Inside the container, start the two HTTP-transport MCP servers and register them (full detail in `setup.md`):
```bash
python3 mcp-servers/storage/server.py --port 8001 --host 0.0.0.0 &
python3 mcp-servers/retrieval/server.py --port 8002 --host 0.0.0.0 &
claude mcp add --scope project --transport http storage http://localhost:8001/mcp
claude mcp add --scope project --transport http retrieval http://localhost:8002/mcp
```

`coursetools` (stdio transport) registers automatically each session. Then run `claude` and log in (`/login`) the first time -- see below.

### Two separate credentials -- don't conflate them

1. **Claude Code's own login**, used for interactive sessions. Persisted across container restarts via the `claude-auth` named volume. Run `/login` once; it survives future containers as long as you exit cleanly (`exit`, not `Ctrl+C`) so the entrypoint's save step runs.
2. **A real `ANTHROPIC_API_KEY`**, needed for anything that calls the model *without* an interactive login present -- specifically `eval-gate` in CI, which runs headless (`claude -p`). Get one at console.anthropic.com (Settings -> API Keys); it has its own separate billing from a Claude subscription. Without this, CI's `eval-gate` job fails with "Not logged in," not a connection error.

## The Target Codebase

Four Spring Boot services:

| Service | Port | Role |
|---|---|---|
| `ecom-eureka-registry` | 8761 | Service discovery |
| `ecom-api-gateway` | 9000 | Routes public traffic (`/purchase/**`) to services via Eureka |
| `ecom-product-service` | 8081 | Product catalog |
| `ecom-order-service` | 8082 | Order placement, Feign calls to product-service, bounded retry on unreachable failures |

No database, no secrets. Java 21, Maven.

## The Agentic System

**Roles** (`agents/` -- copied to `/root/.claude/agents/` at build time; editing one requires a rebuild):

| Agent | Responsibility |
|---|---|
| `planner` | Reads a task, retrieves relevant prior lessons, produces a plan. Read-only. |
| `implementer` | Writes code exactly per an approved plan; may record one new lesson learned. |
| `reviewer` | Independent diff review -- correctness, test coverage, scope discipline. Read-only. |
| `spring-boot-reviewer` | Reviews git diffs for exception handling, REST conventions, Feign usage, missing tests. |
| `decision-auditor` | Checks and corrects `.memory/project/` records against real git state. First (and only) role granted `update_entry`. |

**Skills** (`skills/`):

| Skill | Purpose |
|---|---|
| `summarize-session` | Structured session summary at a context boundary. |
| `verify-before-trusting` | Formalizes this project's most-repeated lesson: verify a claim against the real artifact (git log, a real file, a real test run) before acting on it. |

The Orchestrator (the top-level Claude Code session) delegates to these per the rules in `CLAUDE.md`, independently re-verifies their output rather than trusting self-reports, and requires human approval before any commit. Full diagram: `docs/orchestration-diagram.md`.

**MCP servers** (`mcp-servers/`), each enforcing a deny-by-default, per-role allow-list server-side (`ADR-005`):

| Server | Transport | Purpose |
|---|---|---|
| `coursetools` | stdio | General file/search tools, role-gated, blocked from `.memory/` except narrow role-scoped exceptions |
| `storage` | HTTP :8001 | Schema-bound project-memory writes, real classification + role enforcement, audit logging |
| `retrieval` | HTTP :8002 | Vector + keyword search, per-role classification ceiling enforced server-side, not caller-declared |

**Memory** (`.memory/`): `project/` (decisions, agent-writable), `knowledge/` (coding standards, human-authored, read-only), `reference/` (lessons-learned corpus, append-only).

## The Evaluation Harness

Two layers (`eval/`): deterministic checks (`eval/test_deterministic.py`) gate a rubric-scored LLM-judge suite (`eval/test_rubric_suite.py`). `module3_doc/holdout-task-set.md` -- six locked tasks; `module3_doc/calibration-log.md` -- the full record of induced faults, fixes, and measurement results across every module.

## Governance, CI/CD, and Deterministic Conversion

- **Governance policy**: `docs/governance-policy.md` -- every denial traces to a real near-miss or least-privilege reasoning, not a generic template (`ADR-007`).
- **CI/CD** (`.github/workflows/ci.yml`): six gating jobs -- change classification, policy tests, governed-file consistency, the evaluation harness (as a regression check, `ADR` note in `docs/ci-step-design.md`), advisory AI code review, and pipeline-integrity (verifies the pipeline's own safety invariants haven't been weakened -- `scripts/check-pipeline-integrity.py`). All results roll into a permanent audit trail (`scripts/build-audit-trail.py`).
- **Deterministic conversion**: `docs/step-classification.md` tracks which agentic steps have been evaluated for conversion. `orchestrator_test` has been converted (`ADR-001`, real measured ~264x latency reduction and complete token-cost elimination). A second step was evaluated and correctly kept agentic (`ADR-002`) based on a real counterexample in this project's own history.
- **Red-team results**: `eval/red-team-results.md` -- governance boundaries tested directly, including one organic finding (a subagent fabricating a false security claim, caught under pressure to produce evidence).

## Where Things Live

```
agents/, skills/          real agent/skill definitions (build-time copy convention)
.memory/                  project memory (decisions, knowledge, reference corpus)
mcp-servers/              coursetools, storage, retrieval MCP servers + allow-lists
eval/                     deterministic + rubric evaluation harness, policy tests, red-team results
.eval-artifacts/          per-run evaluation transcripts and evidence (selectively git-tracked)
scripts/                  CI support scripts (pipeline integrity, audit trail, eval-gate, advisory review) + run-agent.ps1
.github/workflows/ci.yml  the full CI/CD pipeline
docs/                     governance policy, orchestration diagram, routing map, ADRs (docs/adr/), CI step design
module2_doc/              Module 2 artifacts (agent iteration, context management, memory architecture)
module3_doc/              Module 3 artifacts (orchestration design, retrieval validation, calibration log)
module4_doc/              Module 4 artifacts (decision-auditor case study)
setup.md                  detailed environment/container setup instructions
CLAUDE.md                 orchestrator policy, memory configuration, agent/tool reference
```

See `setup.md` for full container setup detail (including first-time GitHub Actions and branch-protection steps if you've forked this repo), and `CLAUDE.md` for the orchestration policy governing every agent run.
