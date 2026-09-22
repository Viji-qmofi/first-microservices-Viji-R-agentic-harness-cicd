# Lessons Learned Workflow Run and Verification (3.2 Exercise 1, Steps 5-6)

## Task

Real project work: add a bounded retry to `OrderServiceImpl`'s Feign calls. Before this change, a `feign.RetryableException` (true unreachable-service case) failed on the first attempt and returned 503 immediately, with no retry. This is a small, genuinely useful addition directly related to the existing Feign-handling convention (`decision-001.md`/`decision-004.md`), chosen specifically because it gives `planner` a real reason to retrieve prior lessons rather than finding nothing.

Given to the top-level session without naming any subagent:

> "Add a bounded retry to OrderServiceImpl's Feign calls - if a call fails with RetryableException (a true unreachable-service case), retry a couple of times with a short backoff before giving up and returning 503, instead of failing immediately on the first attempt. Apply this to both placeOrder() and viewAllProducts()."

## Run narrative

1. **Planner retrieved relevant prior lessons before proposing an approach** (required responsibility 1). Called `mcp__retrieval__retrieve` with `project_id="proj-lessons"`, `classification_ceiling="internal"`. Retrieved `feign-exception-handling-convention.md` and cited it directly in its plan, explicitly verifying that the retrieved lesson's documented `RetryableException`/`FeignException` split matched what it found in the live code, rather than just quoting the document.
2. **Orchestrator evaluated the plan** and caught a real gap: the initial plan left exact retry count and backoff duration undecided ("left to the implementer"), which the orchestrator correctly identified as a decision-of-substance a plan shouldn't defer. Sent back for revision with the CLAUDE.md rule cited directly ("do not pass an inadequate plan to implementer to save time").
3. **Orchestrator separately flagged an externally-visible behavior change** (an outage that previously failed instantly would now take longer, or resolve transparently) and held for explicit human approval before proceeding -- a second, distinct checkpoint from the plan-quality gap above.
4. Human approved with concrete values: 3 attempts, 200ms fixed backoff.
5. **Implementer completed the code change and recorded one new lesson learned through the storage server** (required responsibility 2). `mcp__storage__write_entry`, `project_id="proj-lessons"`, `classification="internal"`. Content of the entry captures the non-obvious reasoning behind the architectural choice (a manual retry loop instead of a Feign `Retryer` bean, because the existing test suite mocks the Feign client directly with Mockito and would never exercise a `Retryer`-SPI-based fix) and a secondary constraint for future maintainers (no logging inside the retry loop, or existing `hasSize(1)` log-assertion tests break).
6. **Orchestrator independently verified the implementer's work** rather than trusting its self-report: ran `./mvnw test` directly (25/25 on the target test class, 26/26 full module suite, `BUILD SUCCESS`), checked `git diff` against the claimed scope, and independently fetched the stored entry via `read_entry` rather than trusting the implementer's reported `entry_id`.
7. **Orchestrator retrieved relevant standards or prior lessons while evaluating the result** (required responsibility 3) -- initially skipped, caught when explicitly asked, then performed for real: two retrieval queries ("reviewing a retry implementation", "Thread.sleep in unit tests / flaky timing tests"). No directly relevant prior lesson existed in the corpus for this specific concern; reported as a genuine "nothing relevant" finding rather than manufacturing a match. Surfaced one unprompted secondary observation (the new tests use real `Thread.sleep(200)`, adding real wall-clock time to the test suite) as its own finding, independent of retrieval.
8. Human approved and the change was committed: `9d332ed` (4 files: `OrderServiceImpl.java`, `OrderServiceImplTest.java`, `decision-005.md`, `MEMORY_INDEX.md`).

## Step 6 verification results

### 1. Retrieval results include citations identifying source documents and chunks

Confirmed throughout -- every `retrieve` call in this run and in the ground-truth validation (`retrieval-quality-report.md`) returned `source_document` and `chunk_index` fields alongside content.

### 2. The Implementer's new lesson was written through the storage MCP server

Confirmed. `write_entry` call returned `entry_id: "2fb930a0-7b61-42aa-9315-647f3ac8aba4"`. Independently re-fetched via `read_entry` (not trusted from the implementer's self-report alone) -- content matched exactly.

### 3. The new storage entry remains available after restarting the storage process and in a new Claude Code conversation

Confirmed via both methods at once: the `storage` server process was killed and relaunched, then `claude` was exited and restarted fresh (no `--continue`/`--resume`). In that new session, `read_entry` for the same `entry_id` returned the full, correct content -- proving persistence via the storage system itself, not via any carried-over conversation context.

### 4. The audit log records the storage activity

Confirmed. `grep "2fb930a0-..." .memory/storage/storage-audit.log` returned:
```
{"calling_role": "implementer", "classification": "internal", "entry_id": "2fb930a0-7b61-42aa-9315-647f3ac8aba4", "operation": "write_entry", "project_id": "proj-lessons", "timestamp": "2026-09-16T14:39:21.877117+00:00"}
```
`calling_role: "implementer"` confirms the updated agent definition is genuinely passing its real role, not the `"unknown"` seen in earlier Phase 2 throwaway testing.

### 5. A role operating with an internal classification ceiling cannot retrieve the higher-classified document

Confirmed during ground-truth validation (Q5, `retrieval-quality-report.md`): `agentic-run-cost-tracking.md` (classification: confidential) never appeared in results under `classification_ceiling="internal"`, across every query variant tried, including `top_k=10`.

### 6. No role bypassed the MCP servers by accessing the storage database or reference files directly

**Initially failed, then fixed and reverified.** This is the most significant finding of the exercise.

**Finding:** `planner` and `implementer` both retain `mcp__coursetools__file_read` (and `implementer` also `file_write`) from Exercise 3.1, scoped to `COURSETOOLS_ROOT=/workspace` -- which covers the entire project, including `.memory/storage/storage.db` and every file under `.memory/reference/`. `file_read`'s authorization check only verified that the calling role was on its own allow-list; it had no concept of document classification, and nothing bridged it to the retrieval server's classification-ceiling logic. Direct test (`file_read`, `role="planner"`, path to the confidential document) returned the full plaintext content, including its own `classification: confidential` frontmatter, with no rejection.

**A methodological detour worth recording honestly, not smoothing over:** the first attempt to retest this after the initial fix asked the orchestrator to call the tool with a fabricated `role="planner"` identity (the orchestrator's actual role). The orchestrator correctly declined, on two independent grounds: (a) the justification given for needing a spoofed role was logically inconsistent with the fix's own design (a path-based check is role-independent, so an honest role exercises the identical code path -- there was no technical reason to require a false one), and (b) an independent safety classifier flagged the equivalent honest-role call as "Credential Exploration" without seeing any of the surrounding discussion, which the orchestrator correctly treated as a signal to stop rather than an obstacle to route around. Both objections were correct and are recorded as-is rather than omitted.

**Resolution:** retested by calling the actual Python functions directly (`python3 -c "from coursetools_server import file_read; ..."`), outside Claude Code and outside any tool-calling/role-declaration path entirely -- equivalent to a developer testing their own authorization code, with no identity question involved at all.

**Fix, at the enforcement point, per the exercise's own rule** ("make the change at the enforcement point rather than adding another instruction telling the agent what it should do"): added a path check to `file_read`, `file_write`, and `codebase_search` in `mcp/coursetools_server.py` -- any resolved path under `.memory/` raises `PermissionError` directing the caller to the storage/retrieval servers instead, regardless of role. `codebase_search` needed a second pass: the first fix only blocked an explicit `root` under `.memory/`, but the tool's actual default (`root="."`) would still walk into `.memory/` as an ordinary subdirectory via `rglob`, since it wasn't in `ignored_dirs`. Added `.memory` to `ignored_dirs` to close the realistic default-scope case, not just the artificially narrowed one tested first.

**Verified clean**, again via direct Python calls (no role-spoofing, no classifier interaction):
- `file_read` on the confidential document -> `PermissionError`
- `file_write` into `.memory/reference/` -> `PermissionError`
- `codebase_search` with an explicit `.memory/reference` root -> `PermissionError`
- `codebase_search` with the realistic default root, searching a term unique to the confidential document -> 1 total result, zero touching `.memory/`

Committed: `fix: block file_read/file_write/codebase_search from accessing .memory/ - closes MCP-bypass gap found during step 6 verification`.
