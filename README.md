# E-Commerce Microservices Application — Agentic Development Harness

A Spring Boot microservices e-commerce application, developed and maintained by an orchestrated multi-agent system with persistent memory, MCP-based tool governance, and a two-layer evaluation harness. Built incrementally across LaunchCode's Agentic Engineering course.

## Quick Start

Build the image:
```bash
docker build -t ecom-agent-sandbox .
```

Run with a local workspace mounted:
```cmd
docker run -it --rm --cap-drop=DAC_OVERRIDE -p 8001:8001 -p 8002:8002 -p 6274:6274 -p 6277:6277 -v "%cd%:/workspace" -v "%cd%\.memory\knowledge:/workspace/.memory/knowledge:ro" -v "claude-auth:/root/.claude" -e ANTHROPIC_API_KEY -e COURSETOOLS_ROOT=/workspace -e STORAGE_DB_PATH=/workspace/.memory/storage/storage.db -e STORAGE_AUDIT_PATH=/workspace/.memory/storage/storage-audit.log -e RETRIEVAL_REFERENCE_DIR=/workspace/.memory/reference ecom-agent-sandbox
```

Inside the container, start the two HTTP-transport MCP servers manually and register them (see `setup.md` for full detail):
```bash
python3 mcp-servers/storage/server.py --port 8001 --host 0.0.0.0 &
python3 mcp-servers/retrieval/server.py --port 8002 --host 0.0.0.0 &
claude mcp add --scope project storage http://localhost:8001/mcp
claude mcp add --scope project retrieval http://localhost:8002/mcp
```

`coursetools` (stdio transport) registers automatically each session.

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

**Roles** (`agents/` -- copied to `/root/.claude/agents/` at build time):

| Agent | Responsibility |
|---|---|
| `planner` | Reads a task, retrieves relevant prior lessons, produces a plan. Read-only. |
| `implementer` | Writes code exactly per an approved plan; may record one new lesson learned. |
| `spring-boot-reviewer` | Reviews git diffs for exception handling, REST conventions, Feign usage, missing tests. |
| `reviewer_strict` / `reviewer_lenient` | Temporary, for calibration/testing reviewer-conflict handling -- see `module3_doc/calibration-log.md`. |

The Orchestrator (the top-level Claude Code session) delegates to these per the rules in `CLAUDE.md`, evaluates their output independently rather than trusting self-reports, and requires human approval before any commit.

**MCP servers** (`mcp-servers/`):

| Server | Transport | Purpose |
|---|---|---|
| `coursetools` | stdio | General file/search tools, role-gated, blocked from all of `.memory/` |
| `storage` | HTTP :8001 | Schema-bound project-memory writes, real classification enforcement, audit logging |
| `retrieval` | HTTP :8002 | Vector + keyword search over `.memory/reference/`, classification-ceiling filtered |

**Memory** (`.memory/`):

- `.memory/project/` -- decision entries, agent-writable, indexed via `MEMORY_INDEX.md`
- `.memory/knowledge/` -- coding standards, human-authored, read-only to agents (`:ro` mount + `--cap-drop=DAC_OVERRIDE`)
- `.memory/reference/` -- curated lessons-learned corpus, agent-writable (append-only), searched by the retrieval server

## The Evaluation Harness

### Two layers (`eval/`):

1. **Deterministic checks** (`eval/test_deterministic.py`) -- structural, objective: role routing, tool grants, classification enforcement, audit-log consistency, budgets. Must pass 100% before the rubric suite runs at all.
2. **Rubric-scored suite** (`eval/test_rubric_suite.py`, `eval/rubric.json`) -- an LLM-as-judge scores correctness, task adherence, groundedness, and clarity, each against its own pass floor (no averaging across dimensions).

`module3_doc/holdout-task-set.md` -- six locked tasks covering the six failure modes (context bleed, routing misfire, conflicting reviewers, retrieval miss, schema validation, over-broad tool grant). `module3_doc/calibration-log.md` -- the full record of induced faults, fixes, and holdout measurement results.

## Where Things Live

```
agents/, skills/          real agent/skill definitions (build-time copy convention)
.memory/                  project memory (decisions, knowledge, reference corpus)
mcp-servers/              coursetools, storage, retrieval MCP servers
eval/                     deterministic + rubric evaluation harness
.eval-artifacts/          per-run evaluation transcripts and evidence (selectively git-tracked)
docs/                     Module 1 artifacts (PRD, rubric, iteration log, memory architecture)
module2_doc/              Module 2 artifacts (agent iteration, context management)
module3_doc/              Module 3 artifacts (orchestration design, retrieval validation, calibration log)
setup.md                  detailed environment/container setup instructions
CLAUDE.md                 orchestrator policy, memory configuration, agent/tool reference
```

See `setup.md` for full container setup detail, and `CLAUDE.md` for the actual orchestration policy governing every agent run.
