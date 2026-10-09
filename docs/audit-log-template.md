# Audit Log Template

This project records agent activity in four places. Together they cover the event types the capstone brief names: agent actions, tool calls, policy decisions, human approvals, failures, retries, and rollbacks. This document defines each record, shows a real example of it, and says plainly what is not recorded.

Every example below is a real record from this project. Long text fields in the transcript excerpts are shortened with `...`.

## 1. Storage audit log

**Where:** `.memory/storage/storage-audit.log`, set by `STORAGE_AUDIT_PATH`. It is runtime data and is gitignored; sanitized excerpts are committed as evidence. **Format:** JSON Lines, one record per operation, appended by the storage server. The docstring in `mcp-servers/storage/server.py` states that agents have no tool that edits it.

**Fields:**
- `timestamp`: UTC, ISO 8601.
- `operation`: `write_entry`, `read_entry`, `list_entries`, `update_entry`, `delete_entry`, or `audit_read`.
- `calling_role`: the role the caller declared, or `unknown` if none was given.
- `project_id`, `entry_id`, `classification`: what the operation targeted. Any of these can be `null`.
- `outcome`: `success` or `authorization_denied`. Records written before the enforcement work of 2026-09-23 have no `outcome` field and are successes.

**A normal write** (no `outcome` field, so it predates enforcement):
```json
{"calling_role": "implementer", "classification": "internal", "entry_id": "2fb930a0-7b61-42aa-9315-647f3ac8aba4", "operation": "write_entry", "project_id": "proj-lessons", "timestamp": "2026-09-16T14:39:21.877117+00:00"}
```

**A record from before roles were checked** (`calling_role` was `unknown`):
```json
{"calling_role": "unknown", "classification": "internal", "entry_id": "870dcc7d-5c3a-4216-8132-857fc0ff12e6", "operation": "write_entry", "project_id": "proj-csv", "timestamp": "2026-09-15T20:02:49.899348+00:00"}
```

**A policy violation that succeeded.** This is the near-miss from the Module 3 Lab (HO-06): the Orchestrator updated an entry that `implementer` had just written. Nothing checked the role at the time, so it succeeded.
```json
{"calling_role": "orchestrator", "classification": "internal", "entry_id": "73734908-960c-4a1b-b16b-98cd9ae67a12", "operation": "update_entry", "project_id": "proj-lessons", "timestamp": "2026-09-21T21:28:55.243078+00:00"}
```

**The same call after enforcement: a policy decision.** The server refused it before touching the database and recorded the denial. This record predates the fix that logs the target entry, so its `entry_id` is `null`:
```json
{"calling_role": "orchestrator", "classification": null, "entry_id": null, "operation": "update_entry", "outcome": "authorization_denied", "project_id": "proj-lessons", "timestamp": "2026-09-23T22:13:44.805960+00:00"}
```

**Reproducing a denial that names its target.** `update_entry`, `read_entry`, and `delete_entry` pass the entry to the check, so a current denial records it. This command writes one such record, under the clearly labeled role `denial-check`. Run it inside the container from the repository root:
```bash
python3 - << 'EOF'
import sys
sys.path.insert(0, "mcp-servers/storage")
import server
try:
    server._authorize("update_entry", "denial-check", "proj-lessons", "test-entry-id")
except Exception as e:
    print("raised:", type(e).__name__)
EOF
tail -1 .memory/storage/storage-audit.log
```

The record it wrote on 2026-10-09 names its target, unlike the 2026-09-23 denial above:
```json
{"calling_role": "denial-check", "classification": null, "entry_id": "test-entry-id", "operation": "update_entry", "outcome": "authorization_denied", "project_id": "proj-lessons", "timestamp": "2026-10-09T20:28:59.081531+00:00"}
```

## 2. Retrieval audit log

**Where:** `.memory/storage/retrieval-audit.log`, set by `RETRIEVAL_AUDIT_PATH` (persisted since commit `73425d0`; before that its default path sat outside the bind mount and was lost when the container exited). **Format:** JSON Lines.

**Fields:** `timestamp`, `operation` (always `retrieve`), `calling_role`, `project_id`, `query` (first 200 characters only), `requested_ceiling`, `effective_ceiling` (the ceiling actually applied, capped by the role's own maximum; `null` on a denial), `result_count` (`null` on a denial), and `outcome` (`success` or `authorization_denied`).

**A record** (a labeled test entry written on 2026-10-07 to prove the log now persists):
```json
{"calling_role": "persistence-check", "effective_ceiling": "internal", "operation": "retrieve", "outcome": "success", "project_id": "proj-lessons", "query": "env var check, not a real retrieval", "requested_ceiling": "internal", "result_count": 0, "timestamp": "2026-10-07T21:14:18.236896+00:00"}
```

The real retrieval denial and ceiling-capping records from the Module 4 enforcement testing are quoted in `eval/enforcement-verification.md`. They were written before the log persisted, so the files themselves are gone.

## 3. Run transcript

**Where:** `.eval-artifacts/runs/<task_id>.json` (holdout runs are in `.eval-artifacts/holdout-run-1/`). **Written by:** the Orchestrator at the end of every task, per `CLAUDE.md`. The matching `.log` file next to it holds the storage-log records for that run.

**What it records:**
- `events`: every step in order, each with a `type` (`subagent`, `tool_call`, or `orchestrator_step`), a `role`, and the actual output. This is where agent actions, tool calls, test results, and failures appear.
- `escalated_to_human` and `human_approved`: the human-in-the-loop outcome.
- `duration_seconds` and `cost_usd`: a number, or JSON `null` when the run was not measured.
- `follow_up_items`, `measurement_caveat`, and similar notes for anything the run left open.

**A human approval**, from `.eval-artifacts/runs/dev-retry-fail-once-then-succeed.json`:
```json
{
  "type": "orchestrator_step",
  "step": 6,
  "role": "orchestrator_human_checkpoint",
  "output": "Presented run summary (plan, diff, test result) to human. Human decision: (1) Approved -- commit the test file only. (2) viewAllProducts fail-once-then-succeed test is ou..."
}
```

**An escalation**, from `.eval-artifacts/runs/CAL-01-after.json` (`"escalated_to_human": true`). Two reviewers contradicted each other, and the Orchestrator stopped instead of choosing:
```json
{
  "type": "orchestrator_step",
  "step": 4,
  "role": "orchestrator_conflict_resolution",
  "output": "Genuine same-section contradictions between reviewer_strict and reviewer_lenient on two sections: wiring_test_coverage (strict: reject, lenient: appro..."
}
```

14 committed transcripts record `"human_approved": true`.

## 4. CI audit trail

**Where:** a `ci-audit-trail-<sha>.json` file uploaded as the `audit-trail` artifact on every run and kept 90 days. The job runs `if: always()`, so a failed gate is recorded too. **Written by:** `scripts/build-audit-trail.py`. A real record, from the run that blocked PR #3, is kept at [`module4_doc/evidence/ci-audit-trail-5c91e35.json`](../module4_doc/evidence/ci-audit-trail-5c91e35.json).

**Fields:** `metadata` (commit, event, pull request number, timestamp), `change_classification` (changed files, and whether the change touched policy or required the governed check), `results` (the outcome of each gate), `reports_present`, and a summary per report (exit code, test counts, and for the integrity check the checks it ran).

**A policy decision at the pipeline level.** From that record, the change that added the policy-versus-enforcement tests was recorded as failing the governed-file gate while every other gate passed:
```json
"results": {
  "policy_gate": "success",
  "governed_file_gate": "failure",
  "eval_gate": "success",
  "pipeline_integrity": "success",
  "advisory_review": "success"
},
"governed_report_summary": { "exitcode": 1, "tests": 12 }
```

## Event coverage

- **Agent actions:** transcript `events`; storage writes in the storage log.
- **Tool calls:** transcript `tool_call` events; every storage and retrieval operation in their server logs, including denied ones. Coursetools calls are not logged by the server (see limits).
- **Policy decisions:** `authorization_denied` records in the storage and retrieval logs; the `results` block of the CI trail.
- **Human approvals:** `human_approved` and the `orchestrator_human_checkpoint` event in transcripts; pull request merges on GitHub.
- **Failures:** failed steps and test results in transcripts; failing gates in the CI trail; the harness reports uploaded with each run.
- **Retries:** not recorded. The application's own retry loop (`callWithRetry`) is covered by unit tests in `OrderServiceImplTest`, and MCP calls are deliberately not retried.
- **Rollbacks:** not recorded in any audit log. A rollback is a `git revert` in the repository history. The only rollback exercised so far was deleting a deliberately weakened throwaway branch, which leaves no audit-log record.

## What must never appear in a log

Secrets, tokens, and personal data. Queries are cut to 200 characters. The CI trail records only that an API key was present (`"anthropic_key_present": true`), never its value. Storage records carry a `classification`, and the storage server rejects `secret`-classified writes outright (the classification scheme is in `docs/adr/ADR-004-memory-layout.md`).

## Known limits

- **Roles are self-declared.** A record's `calling_role` is what the caller claimed, not a verified identity (`docs/adr/ADR-005-mcp-boundaries.md`).
- **Append-only by convention, not tamper-evident.** No record is hashed or chained. Agents have no tool that edits the logs, but that is a property of their tool grants, not of the files.
- **Coursetools has no audit log.** Its file and search calls, and its denials, are not recorded server-side. They appear only in transcripts, which the Orchestrator writes from what each subagent reported.
- **The schema changed over time.** Older storage records lack `outcome`, and denials logged `entry_id: null` until the fix that passes the target through. The retrieval log has persisted only since 2026-10-07.
- **The CI trail names the failing gate but not the failing tests.** The detail is in the Actions log, which expires. For pull request runs, `sha` is GitHub's temporary merge commit, not the branch head, so match a record to a change by pull request number and timestamp.
