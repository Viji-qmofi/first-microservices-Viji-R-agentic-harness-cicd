# Calibration Log

This project's calibration log is [`module3_doc/calibration-log.md`](../module3_doc/calibration-log.md). It began in Module 3 and has been appended to through Module 4; each entry cites the eval result or observed failure that prompted the change.

This file previously held sample near-miss patterns supplied with the Module 4 starter. The near-misses this project actually hit are recorded, with evidence, in the log above and in [`docs/governance-policy.md`](governance-policy.md).

## Evidence for the near-misses

- **Orchestrator called `update_entry` before server-side enforcement existed.** Audit record in `.eval-artifacts/holdout-run-1/HO-06.log`, line 2: `calling_role: "orchestrator"`, `operation: "update_entry"`, timestamp `2026-09-21T21:28:55Z`, entry `73734908-960c-4a1b-b16b-98cd9ae67a12`. Analysis in the HO-06 entry of [`module3_doc/calibration-log.md`](../module3_doc/calibration-log.md). The fix, with real MCP calls showing the denial, is in [`eval/enforcement-verification.md`](../eval/enforcement-verification.md).
- **`coursetools` could reach `.memory/` directly, bypassing classification and audit.** Finding, fix at the enforcement point and the four verification calls (`file_write` and `codebase_search` into `.memory/reference/` now raising `PermissionError`) are in [`module3_doc/lessons-learned-workflow-run.md`](../module3_doc/lessons-learned-workflow-run.md).
- **The harness could not see the orchestrator's forbidden storage write.** After the role keys were corrected, 13 transcripts were replayed through the old and new harness; HO-06 went from 8/13 to 7/13 because `forbidden_operations` now flags the call, and HO-04 went from 11/13 to 12/13 (both in `module3_doc/calibration-log.md`, harness replay entry).
