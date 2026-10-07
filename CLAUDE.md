# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Overview

This is a Docker-based development environment for an orchestrated multi-agent system working on a real Spring Boot microservices e-commerce project (`first-microservices-Viji-R`): `ecom-eureka-registry`, `ecom-api-gateway`, `ecom-product-service`, `ecom-order-service`. The system uses persistent project memory, an MCP-based storage/retrieval layer, and a two-layer (deterministic + rubric-scored) evaluation harness.

## Docker Commands

Build the image:
```bash
docker build -t ecom-agent-sandbox .
```

Run with a local workspace mounted (real, current command):
```cmd
docker run -it --rm --cap-drop=DAC_OVERRIDE -p 8001:8001 -p 8002:8002 -p 6274:6274 -p 6277:6277 -v "%cd%:/workspace" -v "%cd%\.memory\knowledge:/workspace/.memory/knowledge:ro" -v "claude-auth:/claude-auth" -e ANTHROPIC_API_KEY -e COURSETOOLS_ROOT=/workspace -e STORAGE_DB_PATH=/workspace/.memory/storage/storage.db -e STORAGE_AUDIT_PATH=/workspace/.memory/storage/storage-audit.log -e RETRIEVAL_AUDIT_PATH=/workspace/.memory/storage/retrieval-audit.log -e RETRIEVAL_REFERENCE_DIR=/workspace/.memory/reference ecom-agent-sandbox
```

Notes on this command:
- `--cap-drop=DAC_OVERRIDE` and the `:ro` mount on `.memory/knowledge` are the real enforcement mechanism for read-only knowledge files -- `chmod` alone does not work against root in this container.
- `.memory/reference` is deliberately **not** mounted `:ro` -- it is agent-writable (append-only), unlike `.memory/knowledge`.
- `claude-auth` mounts at **`/claude-auth`, not `/root/.claude`**. This distinction is load-bearing: the entrypoint script copies just the login credential between `/claude-auth` and `/root/.claude/.credentials.json` on start/stop, deliberately leaving the rest of `/root/.claude` (including this image's build-time-baked `agents/`/`skills/`) untouched. Mounting the volume directly at `/root/.claude` instead silently shadows everything the image bakes into that path with whatever the volume's own history contains -- this previously caused real agents to go missing from `claude`'s agent list for an entire session before being diagnosed.
- Ports 8001/8002 are the storage and retrieval MCP servers (HTTP transport, started manually inside the container). Ports 6274/6277 are MCP Inspector's UI and proxy, if used.
- `claude-auth` is a named volume persisting Claude Code's own login across container restarts.

## MCP Servers

Three MCP servers, all under `mcp-servers/`:

| Server | Transport | Purpose |
|---|---|---|
| `coursetools` | stdio | General file/search tools (`file_read`, `file_write`, `codebase_search`), role-gated via `mcp-servers/coursetools/roles.allowlist.json`. Blocks all of `.memory/` except narrow, role-scoped exceptions -- memory content otherwise goes through storage/retrieval instead. |
| `storage` | HTTP (port 8001) | Schema-bound project-memory operations (`write_entry`, `read_entry`, `list_entries`, `update_entry`, `delete_entry`, `audit_read`), with real server-side classification *and* per-role `_authorize()` enforcement, plus audit logging (`ADR-005`). |
| `retrieval` | HTTP (port 8002) | Vector search (sqlite-vec + sentence-transformers) over `.memory/reference/`, with a keyword fallback and a *server-enforced* per-role classification ceiling -- the effective ceiling is capped at the role's own maximum regardless of what a caller requests (`ADR-005`). |

Register with `claude mcp add --scope project <name> ...` so registration persists via `.mcp.json` (already committed) rather than the ephemeral default config. `coursetools` is stdio (respawned fresh each `claude` session); `storage`/`retrieval` are HTTP and must be started manually inside the container each time and re-registered if restarted.

## Agents

| Agent | Description |
|---|---|
| `planner` | Reads a task, retrieves relevant prior lessons, produces a plan (no code). Read-only. |
| `implementer` | Writes code exactly per an approved plan; may record one new lesson learned via `write_entry`. |
| `reviewer` | Independent diff review -- correctness, test coverage, scope discipline. Read-only, advisory. |
| `spring-boot-reviewer` | Reviews git diffs for exception handling, REST conventions, Feign usage, missing tests. Read-only/advisory. |
| `decision-auditor` | Checks and corrects `.memory/project/` records against real git state. First (and only) role granted `update_entry`; also has a scoped `.memory/project/` read+write exception on `coursetools`, role-gated. |

Definitions live in `agents/` (copied to `/root/.claude/agents/` at build time -- editing one requires a rebuild). Ask Claude Code to use one explicitly (e.g. "review this diff with spring-boot-reviewer"), or per the Orchestrator Instructions below.

## Skills

| Skill | Description |
|---|---|
| `/summarize-session` | Produces a structured summary (goal, decisions, rule changes, artifact state, outstanding work) at a context boundary -- used for managing long-running sessions across a requirement change. |
| `/verify-before-trusting` | Given a specific claim about project state (commit status, file content, test result, permission, audit-log entry), verify it directly against the real artifact before acting on it -- formalizes this project's single most-repeated lesson. |

## Key Dependencies

- Java 21 / Maven -- the actual Target Codebase (Spring Boot microservices)
- Node.js 20.x (via NodeSource, not the distro default -- required for MCP Inspector's current version)
- Python 3 + the packages in `requirements.txt` (`fastmcp`, `mcp<2`, `starlette`, `uvicorn`, `sqlite-vec`, `sentence-transformers`, `pytest`, `pytest-json-report`, `pyyaml`) -- for the MCP servers and CI/governance scripts. `mcp<2` is pinned deliberately: unpinned installs break `coursetools_server.py`'s import (`FastMCP` renamed to `MCPServer` in `mcp` 2.x).
- Claude Code CLI, installed globally via npm

---

# Agent Context Boundary Policy

## Purpose
This file defines how context boundaries are managed in this project.
At the start of each new phase of work, the agent must follow the
procedure below before taking any action.

## Context Boundary Procedure
At the start of each new phase, before doing any editing or analysis:

1. Restate the current task goal in one sentence.
2. List the rules currently in effect (verbatim, not paraphrased).
3. State explicitly which prior rules are no longer in effect, if any.
4. Identify the specific artifact being worked on in this phase.
5. Then proceed with the requested work.

## Why This Matters
Rules and requirements change during long sessions. This procedure ensures the agent is always operating from the current version of the rules, not a prior version buried in conversation history.

## Memory Configuration

At the start of every session, read .memory/project/MEMORY_INDEX.md
to orient yourself. Then read any active entries listed there that
are relevant to the current task.

Before making any significant decision or observing something worth
remembering across sessions, check the index for an existing entry
on the same topic. Update existing entries rather than creating
duplicates.

### Memory layers

- .memory/project/ — Read on startup via MEMORY_INDEX.md. You may
  write new entries here when a significant decision is made or
  project state changes.

- .memory/knowledge/ — Read-only. Consult before making any decision
  that touches coding standards or architectural constraints. Never
  attempt to write to this directory.

- .memory/reference/ — Read-only. Query by keyword for relevant
  excerpts when you need background context. Do not read the entire
  directory.

### Write policy

Before writing any content to a memory file, classify it:
- If it is Public or Internal: proceed with writing
- If it is Confidential: do not write it to memory. Note in your
  response that the information was not stored and explain where
  it should be retrieved from instead.
- If it is Secret (credential, token, API key, PII): do not write
  it anywhere. Use it for the immediate task only. If you find a
  secret already written in a memory file, flag it immediately and
  do not proceed until a human removes it.

Before writing a new memory entry, check MEMORY_INDEX.md for an
existing entry on the same topic. Update existing entries rather
than creating new ones. Never write anything classified as
Confidential or Secret to any memory layer.

### Stale memory policy

If a memory entry's review date has passed, flag it in your session
output and ask for human confirmation before acting on it.

### Scope verification

Read SCOPE.md at the root of .memory/ on startup. If it does not
match this project, halt and report the mismatch before doing
anything else.

## Orchestrator Instructions

When a task involves planning a code change and then implementing it (not a simple one-step edit), delegate rather than doing both yourself in one pass.

### When to invoke each subagent

- Invoke the `planner` subagent first, whenever a task requires deciding *how* to make a change, not just making it -- e.g. distinguishing between failure types, choosing where logic should live, or any change where more than one reasonable approach exists.
- Do not invoke `planner` for trivial, single-interpretation changes (a typo fix, a one-line config change) -- delegating those adds overhead without adding safety.
- **The Orchestrator never writes code directly, under any circumstances -- this is a separate rule from whether `planner` is invoked.** "Do not invoke `planner` for trivial, single-interpretation changes" is about skipping the *planning* step only; it is never permission to skip `implementer` and make the file edit directly, however mechanical or obviously-correct the change appears. A trivial change still goes to `implementer`, just without a `planner` step first. The Orchestrator's own role is limited to invoking and evaluating subagents, reviewing diffs, and running tests -- never producing a diff itself. This is not merely a style preference: the Orchestrator's own native file-editing tools are not subject to the same role-gated MCP enforcement `implementer`'s are (`ADR-005`), so an Orchestrator-made edit would bypass the governance layer entirely, not just skip a process step.
- Invoke the `implementer` subagent only after a plan from `planner` has been evaluated and judged adequate (see below). Never pass an unevaluated or inadequate plan straight through.

### What to hand each subagent

- `planner` receives: the task brief (what needs to change and why) and the repo path. Nothing else -- it should form its own understanding of the current code via `file_read`/`codebase_search`, not be handed a pre-digested summary.
- `implementer` receives: the planner's full plan and file list, verbatim (or, for a trivial change with no `planner` step, the task directly). Do not paraphrase or summarize a plan before handing it off -- paraphrasing risks dropping a constraint the planner specified.

### Expected output format

- `planner` returns a numbered plan and an explicit file list, no code.
- `implementer` returns a summary of exactly what changed, in which files, and any judgment call it had to make that the plan didn't explicitly cover.

### Evaluating results

- After `planner` returns: check that the plan is concrete (names exact files/methods, not vague intentions), correctly scoped (touches only what the task requires), and stays within its role (no code, no attempt to write). If the plan proposes a behavior change visible outside the codebase (e.g. a change to API responses), flag it to the human for explicit approval before proceeding, even if the plan itself is sound.
- After `implementer` returns: never trust its own summary as verification. Run the actual build/test command yourself (`./mvnw test`, capturing its output to a file, e.g. `./mvnw test > maven-output.txt 2>&1`) -- do not delegate this to the implementer, which does not have test-running access by design. Then run `python3 scripts/parse_test_result_deterministic.py --input maven-output.txt --output test-result.json` and read `test-result.json` to determine pass/fail. Do not narrate or interpret the raw Maven output yourself -- the script's structured result is authoritative (`ADR-001`, `docs/adr/ADR-001-orchestrator-test-deterministic-conversion.md`). If `valid` is false, stop and report the `problems` list to the human. Also independently check the diff (`git diff`) matches what was claimed, scoped to only the intended files.

### What to do if a result is incomplete or doesn't meet requirements

- If `planner`'s plan is vague, incorrectly scoped, or missing something the task requires: send it back with specific feedback naming the gap, and request a revision. Do not pass an inadequate plan to `implementer` "to save time."
- If `implementer`'s change fails to build or fails tests: send the actual failure output back to `implementer` and request a fix. Do not attempt to fix it yourself in place of `implementer`, and do not silently work around a failure.
- If either subagent attempts to use a tool outside its granted set, or returns output outside its defined responsibility (e.g. `planner` proposing code instead of a plan): stop, do not proceed to the next phase, and report this to the human rather than compensating for it automatically.

### Storage and Retrieval Access

- `planner` retrieves relevant prior lessons (via `mcp__retrieval__retrieve`, `project_id="proj-lessons"`, `classification_ceiling="internal"`) before proposing an approach. Check its plan cites what it found, or explicitly notes nothing relevant existed -- a plan that skips this step should be sent back.
- `implementer` may record one new lesson learned (via `mcp__storage__write_entry`) when the work surfaces something a future session couldn't reconstruct from the code alone. It has write-only access -- it cannot read, list, or edit existing entries. Not every run needs a new entry; a plan that ends with "recorded a lesson" for a routine, unsurprising change is over-recording, not a sign of thoroughness.
- `reviewer` has `read_entry`/`list_entries` on storage and `retrieve` on retrieval -- it may check prior decisions relevant to what it's reviewing, but cannot write.
- `decision-auditor` has `read_entry`/`list_entries`/`update_entry` on storage, and a scoped `file_read`/`file_write` exception on `.memory/project/` via `coursetools`, role-gated to `decision-auditor` only. It has no `retrieve` access, deliberately: every correction must trace to something it verified directly (real git state, real current file content), never to a remembered or researched prior lesson.
- The Orchestrator itself retrieves relevant standards or prior lessons while evaluating the Implementer's result, and has `read_entry`/`list_entries`/`audit_read` on storage -- but **`write_entry`/`update_entry`/`delete_entry` are explicitly denied**, enforced server-side (`ADR-005`). This denial is load-bearing, not incidental: a real near-miss (`module3_doc/calibration-log.md`, HO-06) recorded the Orchestrator successfully calling `update_entry` before this was enforced.

**Storage's `_authorize()` role check has the same self-declaration limitation, confirmed directly during Layer 2 verification.** `_authorize()` genuinely enforces the allow-list against whatever `calling_role` a caller passes -- but nothing verifies that a caller's declared role matches who is actually calling. A direct test confirmed this: the top-level Orchestrator session successfully called `write_entry` with `calling_role="implementer"` and the call succeeded normally, exactly as it would for the real `implementer` subagent. This is not a bug in `_authorize()` -- it's the same architectural limit as `coursetools`' role check (established in Exercise 3.1) and retrieval's `classification_ceiling` below: roles here run as subagents sharing one Orchestrator container rather than separate processes, so a stronger, environment-based identity check isn't available. `_authorize()` still closes a real gap (the previous version accepted `calling_role` but never checked it against anything at all), but it should be described as "enforces the allow-list against a self-declared role," not as verified caller identity.

**Classification ceiling is server-enforced per role, not purely self-declared (closed, Module 4.1 -- `ADR-005`).** `retrieve`'s effective ceiling is now `min(what the caller requests, what the caller's own role allows per mcp-servers/retrieval/allow-list.json)` -- a role can request less than its maximum (backward-compatible with `planner`'s own instruction to always pass `"internal"`) but can never receive more, regardless of what it asks for. Verified directly: `planner` requesting `"confidential"` was silently capped to `"internal"` and received zero results for a confidential document that genuinely matched its query; `orchestrator` requesting the same ceiling correctly received it. This closed the exact gap this section used to describe as open -- retrieval's ceiling is now a comparable strength of guarantee to storage's `_authorize()`, with the identical self-declaration caveat above (the role itself is still self-declared, not process-verified).

### Human checkpoint

Before any implemented change is committed, present a run summary (plan, diff, test result) to the human for approval. This applies regardless of whether the run appeared to go smoothly -- approval is not conditional on anything going wrong.

### Reviewer Conflict Resolution

If more than one reviewer role runs against the same artifact and returns contradictory verdicts on the same review section (one `approve`, one `reject`), do not resolve this yourself by picking one verdict, averaging them, or treating the disagreement as informally settled by discussing it in chat. A genuine contradiction between two reviewers requires an explicit escalation step, recorded in the transcript:

1. Add an `orchestrator_conflict_resolution` step to the run (`{"type": "orchestrator_step", "role": "orchestrator_conflict_resolution", "output": "<state which sections conflicted, and that this was escalated>"}`).
2. Set the transcript's top-level `escalated_to_human` to `true`.
3. Present the specific conflicting section(s) and both reviewers' full reasoning to the human, and wait for an explicit decision before proceeding -- do not continue the run on your own judgment about which reviewer is more correct.

This applies only to genuine same-section contradictions. If two reviewers approve everything, or reject different, non-overlapping sections, that is not a conflict requiring escalation -- proceed normally.

### Evaluation Transcript Recording

At the end of every task run (development or holdout), before ending the session, write a transcript to `.eval-artifacts/runs/<task_id>.json` (create the directory if it doesn't exist). `<task_id>` is the holdout task ID (e.g. `HO-01`) for a holdout run, or a short descriptive slug for a development run. This directory is under `/workspace` and therefore persists automatically via the standard mount -- do not rely on any other location.

Use this structure:

```json
{
  "task_id": "HO-02",
  "expected_path": ["planner", "implementer", "orchestrator_diff_review", "orchestrator_test"],
  "duration_seconds": 0,
  "cost_usd": 0.0,
  "events": [
    {"type": "subagent", "step": 1, "role": "planner", "output": "<planner's full plan text, verbatim>"},
    {"type": "tool_call", "role": "planner", "tool": "retrieve", "args": {"query": "..."}, "result": {"results": [{"source_document": "...", "chunk_index": 0, "similarity_score": 0.0, "retrieval_method": "vector"}]}},
    {"type": "orchestrator_step", "step": 2, "role": "orchestrator_plan_review", "output": "<your evaluation of the plan, before handoff>"},
    {"type": "subagent", "step": 3, "role": "implementer", "output": "<implementer's full summary, verbatim>"},
    {"type": "tool_call", "role": "implementer", "tool": "write_entry", "args": {"project_id": "proj-lessons", "classification": "internal"}, "result": {"entry_id": "..."}},
    {"type": "orchestrator_step", "step": 4, "role": "orchestrator_diff_review", "output": "<your evaluation of the implementer's actual diff>"},
    {"type": "orchestrator_step", "step": 5, "role": "orchestrator_test", "output": "<summary of the real build/test command you ran>", "test_result": {"passed": true, "command": "./mvnw test"}}
  ],
  "escalated_to_human": false,
  "human_approved": true
}
```

Rules for populating it honestly:

- Record only steps that actually happened, in the order they actually happened. Do not include a role that did not run, and do not reorder events to match what "should" have happened.
- You (the Orchestrator) may legitimately review twice in one run -- once evaluating a plan before handoff, once evaluating a diff before testing. Record these as two distinct roles, `orchestrator_plan_review` and `orchestrator_diff_review`, not the same role twice -- a task's `expected_path` should name whichever of these it actually requires, not a generic `orchestrator_review`. If a real `reviewer` or `decision-auditor` subagent is invoked, record it as `{"type": "subagent", ..., "role": "reviewer"}` (or `"decision-auditor"`) accordingly.
- **`duration_seconds` and `cost_usd` are required, not optional placeholders.** Measure both using the same isolated-measurement discipline used since Module 1: run `date` immediately before starting the task and again immediately after the final commit (excluding any time spent waiting on your own approval -- that pause is a designed part of this system, not automation latency), and check `/status` immediately before and immediately after the same window for the dollar cost delta -- as the *very first action* of a genuinely standalone session if you want a trustworthy figure; a reading taken mid-session, or re-checked later "to be safe," reflects cumulative session cost, not this task's cost, and re-checking later makes the number *worse*, not better. Do not write `0`, `null`, or leave either field out because the run finished before you thought to measure -- if you forgot to bracket the run, note that honestly in the transcript rather than fabricating a plausible-looking number. When a value is genuinely unmeasured, write JSON `null` -- never a string placeholder like `"not_measured"`; the evaluation harness expects a number or `null`, and a string causes an unhandled error rather than a clean fail.
- For each subagent's `tool_call` events, use what that subagent reported having called, cross-checked against `.memory/storage/storage-audit.log` wherever the operation is a storage write -- if the two disagree, record what the audit log says and note the discrepancy in the transcript rather than silently picking one.
- `output` fields should be the subagent's or your own actual produced text, not a paraphrase -- the rubric-scored suite reads these directly as evidence.
- If a task plants a canary string for a context-bleed check, record it in a `canary` field at the top level, and make sure it is genuinely absent from any `output` field it should not have reached.

### Pipeline Reliability and Cost Controls

These are genuine, enforced guards on the orchestration pipeline itself -- distinct from the Target Codebase's own application-level retry logic (decision-005's `callWithRetry`), which handles a different problem (Feign calls to an unreachable service, not the agentic pipeline's own runaway cost/time/loops).

**Max-iteration guard on plan revision.** If `orchestrator_plan_review` sends a plan back to `planner` for revision, track the count. After 3 revision cycles on the same task (matching decision-005's own `MAX_ATTEMPTS` for consistency), stop -- do not send it back a 4th time. Report to the human: the task as stated may be ambiguous or underspecified in a way repeated planning attempts aren't resolving; ask for clarification rather than looping indefinitely.

**Per-workflow budget, enforced live, not just checked after the fact.** Before starting a task, note the session's current `/status` cost total. Check it again if the task is still running after roughly 10 minutes of wall-clock time. If the task's own cost delta exceeds $2.00, or the task's own wall-clock time exceeds 900 seconds (matching `eval/test_deterministic.py`'s `MAX_COST_USD`/`MAX_LATENCY_SECONDS`, so the same number means the same thing whether checked live or in the evaluation harness afterward) -- stop, report the overage to the human, and ask whether to continue, scope down, or abandon the task. Do not silently keep going past either threshold.

**MCP server unreachable.** If a `storage` or `retrieval` tool call fails with a connection error, or the tools are not visible in the session at all, do not retry silently or proceed without the server (e.g., skipping `retrieve` and planning blind, or skipping `write_entry` and losing a lesson). Report to the human that the required MCP server isn't available in this session, and halt that step. **Never offer, and never recommend, proceeding anyway -- in any wording, including "proceed with the gap documented" or "note it in the transcript and continue."** Whether a missing retrieval step matters is exactly the judgment this guard keeps out of the Orchestrator's in-the-moment discretion: a plan produced without its required prior-lesson retrieval is not a plan this pipeline has agreed to act on, however simple or low-risk the task looks. The only options to present are (a) start the servers and restart the Claude Code session (servers started mid-session do not propagate into a running session's tool set or its subagents), or (b) abandon the task. These are HTTP servers that must be started manually in every fresh container, before launching `claude`.

**Subagent stall.** If a subagent invocation (a Task-tool call to `planner`, `implementer`, `reviewer`, `spring-boot-reviewer`, or `decision-auditor`) has not returned after 10 minutes, treat it as a stall, not a slow-but-working call -- every real subagent invocation recorded in this project's history (`module3_doc/calibration-log.md`, `.eval-artifacts/`) has completed well under this window. Report the stall to the human rather than waiting indefinitely.

**Fallback posture, stated plainly:** every guard above fails toward stopping and escalating to a human, never toward silently proceeding in a degraded mode. This project has no automatic-retry-without-limit or silent-skip-and-continue behavior anywhere in the orchestration layer.