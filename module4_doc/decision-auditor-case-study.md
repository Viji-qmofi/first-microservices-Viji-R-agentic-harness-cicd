# decision-auditor: Case Study (4.1 Exercise 1 Deliverable)

This is a companion record to `eval/red-team-results.md`. That file documents what `decision-auditor` correctly *declined* to do. This one documents what it *did* -- its actual job, working end to end, against a real, long-standing bug.

## Why this role

`decision-005.md`'s "Not yet committed" staleness was independently rediscovered **four separate times** across this project -- holdout tasks HO-01, HO-03, HO-05, and again during the Module 4 activation exercise -- by four different agents, from four different angles, none of whom had the job of noticing or fixing it. `decision-001.md`'s placeholder review date in `MEMORY_INDEX.md` was a live instance of the exact same pattern, still uncorrected. No role in this project had ever been given the specific job of checking existing project-memory records against reality and correcting them. `decision-auditor` was designed to close that gap directly, not incidentally.

## Building it surfaced two real infrastructure bugs

Neither was anticipated in the original design -- both were found only by actually trying to use the role for its real job, not by review.

**Bug 1 -- a stale hardcoded default silently defeated prior governance work.** `mcp-servers/coursetools/coursetools_server.py`'s `ALLOWLIST_PATH` defaulted to `mcp/roles.allowlist.json`, a path that hasn't existed since the Module 4 port (the real file lives at `mcp-servers/coursetools/roles.allowlist.json`). With no file at the default path, the server silently fell back to a hardcoded `DEFAULT_ALLOWLIST` that happened to include every role tested *before* this one -- meaning it went undetected through the entire storage/retrieval Layer 2 build-out and the four-prompt red-team series. `decision-auditor` was the first role added since the port that wasn't in that stale fallback, which is exactly what exposed it. **Real consequence:** the commit that first enforced `decision-auditor` in the coursetools allow-list never actually took effect at runtime -- it updated a file the server wasn't loading. Fixed by resolving the path relative to the script's own location (`Path(__file__).parent / "roles.allowlist.json"`), matching the pattern `storage`/`retrieval` already used correctly.

**Bug 2 -- the role's original scope couldn't reach the files it needed to fix.** `decision-auditor` v1 was granted `update_entry` on the storage server -- but `decision-001.md` and `MEMORY_INDEX.md` are plain, git-tracked markdown files, never storage-server entries. `update_entry` had nothing to act on. Closed by adding a narrowly scoped exception to `coursetools`' `file_read`/`file_write` -- `.memory/project/` only, `decision-auditor` only -- verified directly (including a `project/../storage/` path-traversal attempt, correctly blocked) before being wired into the live allow-list. Versioned to v2 in both the agent definition and `docs/governance-policy.md`, with the original v1 design's incompleteness documented plainly rather than quietly overwritten.

## Red-team result (see eval/red-team-results.md for full detail)

Directly invited to infer a stale value "from what similar decisions have used before" -- a `retrieve`-shaped temptation, and `decision-auditor` has no `retrieve` grant specifically to prevent this. It declined the inference, correctly citing that every correction must trace to something it verified itself, not a remembered or researched example.

## The real fix

Once both infrastructure gaps were closed, `decision-auditor` was given this instruction:

> "Check MEMORY_INDEX.md for any stale or placeholder entries and correct them against the real decision files."

**Result -- two real corrections, both independently verified against the actual decision files afterward:**

1. `decision-001`'s review-date line changed from the placeholder `[90 days from decision-001's date]` to `2026-11-11` -- the real date stated in `decision-001.md` itself.
2. `decision-004`'s entry changed from "Build not verified... run `./mvnw test` before merge" to the actual recorded result: `OrderServiceImplTest`, 9 tests, 0 failures, `BUILD SUCCESS`.

`decision-002`, `003`, and `005` were checked and correctly left untouched -- already accurate. One separate, out-of-scope issue was found and correctly *not* auto-corrected: `decision-002.md`'s own heading still reads `# Decision 099 - API Connection Approach`, a leftover from its original Exercise 2.4 filename (`decision-bad.md`) before renaming -- flagged for a human decision rather than silently edited, since `decision-auditor` has no grant to modify decision file content directly, only `MEMORY_INDEX.md`.

## What this demonstrates

A role built specifically to close one well-evidenced, four-times-repeated gap did exactly that -- but only after two real infrastructure defects, neither visible from documentation review alone, were found by actually trying to make the role work and were fixed at their root cause rather than worked around. The bug that finally got fixed here had outlasted four separate human/agent encounters across this entire course; a fifth encounter, this time backed by a role with the specific job and the correctly-scoped access to act, closed it.
