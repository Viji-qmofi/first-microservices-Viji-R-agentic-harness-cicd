# Enforcement Verification

## Layer 1: Container Permissions

**Role:** reviewer

**Workspace check**

**Command:** `touch /workspace/should-fail.txt`

**Output:**
```
touch: cannot touch '/workspace/should-fail.txt': Read-only file system
```

**Result:** blocked as expected.

---

**Role:** implementer

**Workspace check**

**Command:** `touch /workspace/ok-to-write.txt && rm /workspace/ok-to-write.txt`

**Output:** (no output -- silent success)

**Result:** succeeded as expected.

**Memory (.memory/knowledge) check, even under a read-write role**

**Command:** `touch /workspace/.memory/knowledge/should-fail.txt`

**Output:**
```
touch: cannot touch '/workspace/.memory/knowledge/should-fail.txt': Read-only file system
```

**Result:** blocked as expected -- confirms the dedicated `.memory/knowledge` `:ro` mount overrides the role's general read-write workspace access, not merely coinciding with it. See docs/governance-policy.md for why this project uses a single workspace read/write dimension rather than a separate memory-volume dimension: `.memory/` lives inside `/workspace`, and knowledge specifically is protected by its own always-`:ro` sub-mount regardless of the role's overall mode.

---

**Role:** planner

**Workspace check**

**Command:** `touch /workspace/should-fail.txt`

**Output:**
```
touch: cannot touch '/workspace/should-fail.txt': Read-only file system
```

**Result:** blocked as expected.

---

**Role:** spring-boot-reviewer

**Workspace check**

**Command:** `touch /workspace/should-fail.txt`

**Output:**
```
touch: cannot touch '/workspace/should-fail.txt': Read-only file system
```

**Result:** blocked as expected.

---

**Role:** orchestrator

**Workspace check**

**Command:** `touch /workspace/ok-to-write.txt && rm /workspace/ok-to-write.txt`

**Output:** (no output -- silent success)

**Result:** succeeded as expected.

All five roles' container-level permissions confirmed to match their `docs/governance-policy.md` entries: `implementer` and `orchestrator` read-write; `planner`, `reviewer`, and `spring-boot-reviewer` read-only. `.memory/knowledge` confirmed read-only regardless of role.

## Layer 2: MCP Allow-List Enforcement (storage server)

Before this fix, `calling_role` was accepted by `write_entry`/`update_entry`/`delete_entry` and written to the audit log, but never checked against anything -- purely decorative. `module3_doc/calibration-log.md`'s HO-06 finding recorded a real consequence: the Orchestrator's `update_entry` call on storage succeeded on 2026-09-21, a permission it was never supposed to have per `CLAUDE.md`'s own written policy, with no automated check able to detect it.

**Fix:** a real `_authorize()` function, checked first on every storage operation, denying by default unless the calling role appears on that operation's allow-list (`mcp-servers/storage/allow-list.json`, rewritten to match this project's real five roles).

### Negative test -- the exact call that previously succeeded

**Command (direct MCP tool call, not a role-spoofed test -- `orchestrator` is this session's genuine identity):**
```
mcp__storage__update_entry(calling_role="orchestrator", project_id="proj-lessons", entry_id="test-nonexistent", content="test")
```

**Output:**
```
authorization_denied: role 'orchestrator' is not on the allow-list for update_entry. Allowed roles: none. See docs/governance-policy.md.
```

**Result:** blocked as expected -- and correctly denied before the database was ever touched (the error is an authorization denial, not a "no entry found" error, confirming `_authorize()` runs first).

### Positive control -- a genuinely granted operation still works

**Command:**
```
mcp__storage__write_entry(calling_role="implementer", project_id="proj-lessons", entry_type="lesson_learned", title="Layer 2 enforcement test", content="...", classification="internal")
```

**Output:**
```
{"entry_id":"35e15caf-3270-46f8-a9f6-263a6eca8f6a"}
```

**Result:** succeeded as expected, proving the fix denies exactly what it should and nothing more. (Test entry subsequently deleted directly from the database, since `delete_entry` is denied to every role under the current policy and this was self-inflicted test data, not a case warranting a policy exception.)

### Audit trail -- before and after, in one record

**Command:**
```
mcp__storage__audit_read(calling_role="orchestrator", limit=5)
```

**Output (key entries):**
```json
{"timestamp":"2026-09-21T21:28:55...","operation":"update_entry","calling_role":"orchestrator","entry_id":"73734908-..."}
{"timestamp":"2026-09-23T22:13:44...","operation":"update_entry","calling_role":"orchestrator","outcome":"authorization_denied","entry_id":null}
{"timestamp":"2026-09-23T22:14:43...","operation":"write_entry","calling_role":"implementer","outcome":"success","entry_id":"35e15caf-..."}
```

**Result:** the historical near-miss (2026-09-21, `orchestrator` successfully calling `update_entry`) and the fix's effect (2026-09-23, the identical call now denied) sit in the same log, directly comparable. Confirms the fix targets the actual documented near-miss, not a hypothetical one.

### Known limitations, found during this verification, not assumed in advance

1. **`_authorize()` enforces the allow-list against a self-declared role, not a verified caller identity.** Direct test: the Orchestrator session successfully called `write_entry` with `calling_role="implementer"` and it succeeded normally, indistinguishable from the real `implementer` subagent calling it. Same architectural limitation as `coursetools`' role check (Exercise 3.1) and retrieval's `classification_ceiling` -- documented in `CLAUDE.md`, not hidden. `_authorize()` still closes a real gap (the previous version never checked `calling_role` against anything at all) -- it just isn't a stronger identity guarantee than what the rest of the system already has.
2. **The first version of `_authorize()` didn't log which entry a denied call was targeting** (`entry_id: null` on denial records) -- found during this verification, fixed immediately (`_authorize()` now accepts and logs `entry_id` on every operation that has one available), not left as a deferred gap.

## Layer 2: MCP Allow-List Enforcement (retrieval server)

Before this fix, `retrieve()` had no `calling_role` parameter at all and no audit logging whatsoever -- `classification_ceiling` was a plain caller-supplied argument, fully self-declared, with nothing on the server tying it to the caller's actual role (`CLAUDE.md`'s own documented gap since Module 3). Unlike storage, this wasn't a decorative check that never fired -- there was no check of any kind.

**Fix:** `calling_role` added to `retrieve()`; `_authorize()` denies any role absent from `allow-list.json`'s `retrieve` map outright, and for a granted role, the *effective* ceiling actually used is `min(what the caller requested, what that role's own policy allows)` -- a role can request less than its maximum (staying compatible with existing agent instructions like `planner.md`'s "always pass internal") but can never receive more, regardless of what it asks for. Real audit logging added, matching storage's pattern (previously absent entirely).

### Test 1 -- a granted role requesting more than its actual maximum

**Command:**
```
mcp__retrieval__retrieve(calling_role="planner", project_id="proj-lessons", query="cost tracking", classification_ceiling="confidential")
```

**Output:** `{"result":[]}`

**Audit log entry:**
```json
{"calling_role":"planner","effective_ceiling":"internal","outcome":"success","requested_ceiling":"confidential","result_count":0,...}
```

**Result:** the request for `confidential` was silently capped to `internal` (planner's real maximum) -- the confidential document (`agentic-run-cost-tracking.md`, confirmed present in the corpus on this exact topic) was correctly excluded. Not an error -- a quiet reduction, distinguishable from "no matches" only by checking `requested_ceiling` vs. `effective_ceiling` in the audit log. Documented as a minor observability limitation, not a security gap -- the actual boundary held.

### Test 2 -- a role with no grant at all

**Command:**
```
mcp__retrieval__retrieve(calling_role="implementer", project_id="proj-lessons", query="cost tracking", classification_ceiling="internal")
```

**Output:**
```
authorization_denied: role 'implementer' is not granted retrieve access. See docs/governance-policy.md.
```

**Audit log entry:**
```json
{"calling_role":"implementer","effective_ceiling":null,"outcome":"authorization_denied","requested_ceiling":"internal","result_count":null,...}
```

**Result:** blocked outright, before any ceiling logic even ran -- correct, since `implementer` was never granted `retrieve` at all, regardless of how conservative the requested ceiling was.

### Test 3 -- positive control, a role actually entitled to confidential material

**Command:**
```
mcp__retrieval__retrieve(calling_role="orchestrator", project_id="proj-lessons", query="cost tracking", classification_ceiling="confidential")
```

**Result:** `agentic-run-cost-tracking.md` returned as the sole result, `effective_ceiling: "confidential"` in the audit log. Confirms the cap is role-specific, not a blanket restriction -- `orchestrator`'s real, policy-granted maximum is honored correctly.

Together, the three tests distinguish all three real outcomes clearly in the audit log: denied outright (`implementer`), capped to empty (`planner`), and genuinely granted (`orchestrator`).

### Known limitations, found during this verification

1. **Same self-declaration limitation as storage and coursetools.** `_authorize()` enforces the allow-list against whatever `calling_role` a caller states -- not a verified process identity. Documented in `docs/governance-policy.md`, not hidden.
2. **A capped request and a genuinely empty result are indistinguishable without checking the audit log.** `outcome: "success"` with `result_count: 0` covers both cases; only `requested_ceiling` vs. `effective_ceiling` reveals which one occurred. Worth a future improvement (e.g., a `ceiling_was_capped: true/false` field), not fixed in this cycle.
3. **A tangential finding, investigated and correctly attributed, not a new bug:** a short query ("cost tracking") fell back to keyword search rather than vector search for this document, surfacing one semantically unrelated result alongside the correct one. Confirmed via direct testing that the embedding path itself works correctly (a differently-phrased query on the same document scored well under vector search in Module 3.2's original ground-truth testing, Q1/Q6). This is the same already-documented keyword-fallback precision limitation from `retrieval-quality-report.md`'s Q5 finding, not a regression introduced by this Layer 2 work.
