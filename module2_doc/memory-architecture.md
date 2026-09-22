# Memory Architecture

## What this workflow needs to remember

Across sessions, the agents working on this repo (`spring-boot-reviewer`, plus general Claude Code sessions) perform recurring code review, fix triage, and multi-phase context-managed work on the same four-service Spring Boot codebase. What needs to carry over from one session to the next: findings that keep resurfacing until actually resolved (e.g., `viewAllProducts()`'s missing Feign handling, flagged across four separate review runs before being fixed), established conventions once they've stabilized (e.g., converting Feign failures to `ResponseStatusException` with 503, now used consistently in two methods), known repo-specific quirks that would otherwise be rediscovered the hard way (e.g., git commands run inside the Docker container fail against worktrees created via Windows Command Prompt, due to absolute-path git links), and genuinely still-outstanding decisions (e.g., `ecom-order-service` still has zero real test coverage, repeatedly flagged Critical and not yet actioned). What must not carry over: credentials (`ANTHROPIC_API_KEY`, any git auth), the raw content of a single review's full output once it's been distilled into a decision, and task-specific state that's no longer relevant once that task is done (e.g., "currently investigating the `viewAllProducts()` diff" once that diff has been reviewed and merged).

## Layer 1: Project memory directory



# Belongs here
- decisions/decision-001.md: Feign call failures are converted to ResponseStatusException with an appropriate HTTP status — the concrete record of the convention described in Layer 2 below.
- Resolved decision (kept for context, not action): `viewAllProducts()`'s Feign-handling gap was fixed in commit `27895c4`, using the same `ResponseStatusException`/503 pattern as `placeOrder()`
- Known repo quirk: git commands run inside the Docker container fail against a worktree created via Windows Command Prompt, because the worktree's `.git` pointer file stores an absolute Windows path the Linux container can't resolve
- Open question: whether to narrow the catch-all `FeignException` handling to distinguish true unreachable/5xx errors from other non-404 failures, and whether to add logging (flagged as a Warning, not yet decided)

# Does not belong here
- The actual contents of `application.yml` or any config file (already in the repo; memory shouldn't duplicate it)
- `ANTHROPIC_API_KEY` or any other credential
- The full raw text of a single `spring-boot-reviewer` report (that's the historical record in the iteration log, not active working memory — this layer holds the distilled current state, not a transcript)

- **Scope:** Project-scoped. This memory is for this repository only.
- **Write permissions:** The agent can write new entries and update existing ones as it discovers or resolves issues.
- **Pruning policy:**
  - Entries tied to a specific finding or fix are archived once that fix is committed and merged (e.g., the `viewAllProducts()` entry above becomes an archived decision, not an open item, now that `27895c4` is merged).
  - Entries about the project as a whole (repo-wide quirks, standing outstanding decisions) are reviewed every 90 days or whenever a major dependency or structural change occurs.

## Layer 2: Knowledge files

# Belongs here
- `CLAUDE.md`'s Context Boundary Procedure — a fixed, human-authored process for managing phase transitions
- `spring-boot-reviewer.md`'s review checklist (exception handling, REST conventions, Feign usage, missing test coverage) — a stable standard the agent should apply consistently, not something that should silently drift run to run
- The project convention that Feign call failures are converted to `ResponseStatusException` with an appropriate HTTP status, now that it's been applied consistently across two real fixes rather than being a one-off choice

# Does not belong here
- A single review run's specific findings (that's Layer 1 — evolving, task-linked state)
- Large reference material like full framework documentation (Layer 3)

- **Scope:** Project-scoped.
- **Write permissions:** Human-maintained only. The agent may read these files but must not modify them autonomously — every change (e.g., the `spring-boot-reviewer` v1 -> v2 revision) happens as a deliberate, human-reviewed commit, the same way agent definition changes have been handled throughout this project.
- **Pruning policy:** Reviewed only when the underlying convention or policy actually changes, not on a timer — these are meant to be stable, and reviewing them on a schedule regardless of whether anything changed would undermine that stability.

## Layer 3: Indexed reference documents

# Belongs here
- The full run-by-run `iteration-log.md` history (Module 1 and Module 2 logs) — large and append-only; consulted on demand ("has this issue come up before?") rather than loaded into every session by default
- The complete text of past `spring-boot-reviewer` reports (Runs 001-004) — useful for deep investigation into exactly what was said and when, not needed as default context

# Does not belong here
- A currently-active, still-relevant decision (that belongs in Layer 1)
- Anything that needs to be known by default in every session — putting it here would defeat the purpose of "indexed, consulted only when relevant"

- **Scope:** Project-scoped.
- **Write permissions:** The agent can append new entries (new run logs); it should not rewrite or delete historical entries.
- **Pruning policy:** Not pruned by deleting content — raw entries are kept indefinitely as the historical record — but periodically re-indexed or summarized (the Lesson Learned entries already added to the Module 2 log are an example of this in practice) so retrieval stays efficient as the log grows.

## Allocation decision table

| Information type | Where it goes | Reason |
|---|---|---|
| How to build/test a service (`./mvnw clean install`) | Agent definition / skill | Procedural steps are not memory; they belong in a skill or agent definition |
| `ANTHROPIC_API_KEY` | Environment variable | Secrets must never be written to any memory layer |
| The specific diff currently under review | Context window only | No value once the session ends |
| Full history of all `spring-boot-reviewer` runs | Indexed reference (Layer 3) | Too many to load every session; retrieved on demand |
| `viewAllProducts()` Feign-handling status | Project memory directory (Layer 1), until resolved | Actively relevant during the open period; archived once merged |
| `spring-boot-reviewer`'s review checklist | Knowledge file (Layer 2) | Stable, human-maintained standard the agent reads but doesn't rewrite |

## Alternatives considered

The convention that Feign call failures should be converted to `ResponseStatusException` with an appropriate HTTP status could reasonably have gone in either Layer 1 (project memory directory, as evolving state) or Layer 2 (knowledge files, as a stable rule). It started as a Layer 1 item — a decision made once, for one method (`placeOrder()`). Once the same pattern was deliberately reapplied to a second method (`viewAllProducts()`) rather than solved differently each time, it graduated to Layer 2: treating it as a stable, human-governed convention rather than mutable state signals that changing it later should require a deliberate, reviewed decision — the same standard already applied to the review checklist itself — rather than something that could quietly drift if a future session reasoned its way to a different pattern.

**Current status:** Empty by design. This project doesn't yet have reference material large or stable enough to warrant indexing separately — the iteration logs described above are the intended future occupant of this layer, but haven't been moved here yet. This will be revisited if the logs grow large enough that loading them by default becomes impractical, or if external framework/API documentation becomes a recurring need.

## Data Classification

Before writing anything to a memory file, classify it:

- **Public** — Safe to commit to the repo and share broadly. Most project decisions and coding standards fall here.

- **Internal** — Safe within the team but not for public repos. Store in a non-committed volume or .gitignore the containing folder.

- **Confidential** — Sensitive business data. Do not store in agent memory. Retrieve from secure systems on demand.

- **Secret** — Credentials, tokens, API keys, PII. Must never appear in any memory file. If the agent encounters a secret during a run, use it for the immediate task only and explicitly do not write it to any memory layer. Reference the environment variable name instead.

### Guardrails

A pre-commit hook (scripts/hooks/pre-commit, activated via core.hooksPath) scans .memory/ for common credential patterns before each commit. If a pattern is found, the commit is blocked.
