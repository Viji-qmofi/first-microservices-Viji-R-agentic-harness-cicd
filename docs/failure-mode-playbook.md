# Failure-Mode Playbook

What to do when the pipeline misbehaves, looked up by symptom. Every entry is a failure this project actually hit or deliberately tested, with the check that caught it, the first response, and the evidence. The stop, escalate, and rollback thresholds are in [`module4_doc/escalation-and-rollback-criteria.md`](../module4_doc/escalation-and-rollback-criteria.md); this file is the lookup by symptom.

**Status tags.** *Exercised* means it was triggered in a real run and the response worked. *Defined only* means the response is specified in `CLAUDE.md` or the policy but has not yet been triggered. Entries that are only partly exercised say which part.

**Three rules apply to every entry.**
- Every response fails toward stopping and asking a human, never toward continuing in a degraded mode (`CLAUDE.md`, Pipeline Reliability and Cost Controls).
- Verify a claim against the real artifact before acting on it, including a failure report (`skills/verify-before-trusting/SKILL.md`).
- Record the incident in [`module3_doc/calibration-log.md`](../module3_doc/calibration-log.md) with evidence (a transcript, an audit-log line, a commit), not a summary.

---

## A. Agent behavior

### 1. An agent does more than it was asked (scope drift)
- **Symptom:** the plan or diff touches things the task never named.
- **Usual cause:** a subagent continues into adjacent design work, or a human adds an unrequested requirement mid-task.
- **Caught by:** `orchestrator_plan_review` (the plan's scope), `orchestrator_diff_review` (`git diff` against the approved plan), and the human checkpoint.
- **First response:** stop, send the plan back naming the specific excess, and never pass it to `implementer` "to save time." After three revisions on one task, ask the human.
- **Prevention:** a task brief that names exact files; plans must name exact files and methods.
- **Evidence:** HO-01 (planner drifted into circuit-breaker design) and HO-06 (a human-added requirement) in `module3_doc/calibration-log.md`.
- **Status:** Exercised.

### 2. The Orchestrator does a subagent's work itself
- **Symptom:** the Orchestrator edits a file, or reasons to a conclusion, instead of delegating.
- **Usual cause:** it read "skip planner for trivial changes" as "skip implementer too." A native edit tool sits outside MCP role-gating, so no server check stops it.
- **Caught by:** the human reading the edit prompt (2026-10-01), and the `required_roles` and `role_order` harness checks (HO-03).
- **First response:** reject the edit and route the task to `implementer`.
- **Prevention:** the "never writes code directly" rule in `CLAUDE.md` (commit `6d4ee27`).
- **Evidence:** HO-03 and the first reliability-controls test (finding 1) in the calibration log.
- **Status:** Exercised. The rule is a policy the Orchestrator follows, not a technical block, because native tools are outside MCP enforcement.

### 3. An agent states something false with confidence
- **Symptom:** a specific, detailed claim (an injection attempt, a restored history) that nothing supports.
- **Usual cause:** reconstruction from incomplete context, or over-vigilance.
- **Caught by:** asking for the verbatim source, and checking the artifact (transcript, git, audit log).
- **First response:** demand the verbatim evidence. If there is none, discard the claim and record it. Do not repair it with a plausible guess.
- **Prevention:** transcripts record only what happened, and the `verify-before-trusting` skill.
- **Evidence:** `eval/red-team-results.md` (the organic finding: `implementer` retracted when pressed for verbatim evidence) and HO-06 (a fresh session confidently reconstructed events that never happened).
- **Status:** Exercised.

### 4. A required source is missing and the agent substitutes another
- **Symptom:** a plan cites files that are not the retrieval corpus.
- **Usual cause:** `planner` had no instruction for a missing `retrieve`, so it improvised.
- **Caught by:** the Orchestrator (2026-10-07); since planner v3, by planner itself.
- **First response:** halt and report. The only options are to start the servers and restart the session, or to abandon the task. Never "proceed anyway."
- **Prevention:** the planner v3 rule (commit `9eaf370`) and the `CLAUDE.md` guard (commit `0a06f01`).
- **Evidence:** the retest and the planner v3 follow-up in the calibration log.
- **Status:** Exercised.

### 5. Two reviewers disagree
- **Symptom:** one approves and one rejects the same section.
- **Caught by:** the Orchestrator's conflict rule. The escalation worked unscripted in HO-05.
- **First response:** escalate to the human with both reasonings, never pick one or average them, and record `escalated_to_human: true`.
- **Prevention:** the Reviewer Conflict Resolution section of `CLAUDE.md`.
- **Evidence:** Entry 1 and HO-05 in the calibration log.
- **Status:** Exercised. The two disagreeing reviewers were temporary calibration roles, since retired (`docs/adr/ADR-006-subagent-scoping-and-routing.md`); the rule stands for any future pair.

### 6. Runaway loops, cost, or stalls
- **Symptom:** a plan keeps bouncing between planner and review, a task's cost or time keeps growing, or a subagent never returns.
- **Caught by:** the post-hoc `cost` and `latency` harness checks ($2.00 and 900 seconds, in `eval/test_deterministic.py`), and the live guards in `CLAUDE.md` (three plan revisions, $2.00 and 900 seconds per task, a 10-minute subagent stall).
- **First response:** stop and ask the human whether to continue, scope down, or abandon.
- **Evidence:** HO-06 failed both `latency` and `cost` in the calibration log.
- **Status:** Partly exercised. The post-hoc checks have fired. The live guards are defined only and have never been triggered.

---

## B. Tools, permissions, and boundaries

### 7. A role calls an operation outside its grant
- **Symptom:** the audit log shows an operation the policy denies for that role.
- **Usual cause:** before 2026-09-23, storage accepted `calling_role` but checked it against nothing.
- **Caught by:** at the time, nothing automatic (it was noticed in review, HO-06). Now the server denies the call and logs `authorization_denied`, and the harness's `forbidden_operations` check flags it in replays.
- **First response:** stop. Do not retry under another role. Read the entry with `audit_read`. Change a grant only with a stated reason (`docs/adr/ADR-007-governance-policy.md`).
- **Evidence:** `eval/enforcement-verification.md` (the identical call before and after the fix) and `.eval-artifacts/holdout-run-1/HO-06.log`.
- **Status:** Exercised.

### 8. A caller claims a role it does not have
- **Symptom:** none at the server; a call succeeds under a borrowed role.
- **Usual cause:** roles are self-declared strings, and subagents share one container (`docs/adr/ADR-005-mcp-boundaries.md`).
- **Caught by:** not blocked. Mitigated by the audit trail, by the red-team result in which the Orchestrator declined to exploit it, and by human review.
- **First response:** treat any unexplained use of another role's identity as an incident and escalate.
- **Prevention:** a real fix needs separate processes with verified identity, which ADR-005 lists as an open risk.
- **Evidence:** Prompt 4 in `eval/red-team-results.md`, and the limitation text in `CLAUDE.md`.
- **Status:** A documented and tested limitation, not closed.

### 9. The allow-list file is missing or unreadable
- **Symptom:** the coursetools server exits with "allow-list not found."
- **Usual cause:** a moved or renamed file. Before the fix, the server silently used a built-in default that granted the Orchestrator `file_write`.
- **Caught by:** the server refusing to start, and `test_coursetools_fails_closed_without_its_allow_list` in `eval/test_governed_files.py`.
- **First response:** restore the file from git. Never add a default list back.
- **Evidence:** finding 5 in the calibration log's CI-gates entry, and the update in ADR-005.
- **Status:** Exercised (reproduced, then fixed).

### 10. The written policy and the configured grants drift apart
- **Symptom:** Governed File Check fails with a list of mismatches.
- **Usual cause:** a grant changed in one place only: an allow-list, an agent's `tools:` line, a harness copy, or the policy.
- **Caught by:** `eval/test_governed_files.py` (14 tests), a required status check.
- **First response:** decide which side is right. Change the policy first, then the copies. Widening a grant needs a stated reason.
- **Evidence:** PR #3: the red commit `d50ab45`, then green `8f87663` and `ff1f03e`.
- **Status:** Exercised.

---

## C. Environment and infrastructure

### 11. An MCP server is down, or its tools are invisible in the session
- **Symptom:** connection refused on port 8001 or 8002, or the `mcp__storage__*` and `mcp__retrieval__*` tools are absent even though `claude mcp list` shows them connected.
- **Usual cause:** the HTTP servers must be started by hand in every container, and a server started mid-session is not seen by that session or its subagents.
- **Caught by:** the Orchestrator guard, which stops and offers only "start and restart" or "abandon."
- **First response:** start both servers, restart `claude`, and confirm with `/mcp`.
- **Evidence:** findings 2 and 3 and the retest in the calibration log's reliability-controls entry.
- **Status:** Exercised.

### 12. A volume mount hides what the image baked in
- **Symptom:** your agents vanish from `claude`'s agent list after a fresh build.
- **Usual cause:** the named volume was mounted at `/root/.claude`, which shadows the baked-in `agents/` and `skills/`.
- **Fix:** mount it at `/claude-auth`. The entrypoint copies only the login credential.
- **Evidence:** the Run section of `setup.md`.
- **Status:** Exercised.

### 13. File permissions do not protect "read-only" memory
- **Symptom:** an agent writes to `.memory/knowledge/` despite `chmod`.
- **Usual cause:** root inside the container ignores `chmod`, and Windows `chmod` also corrupted file metadata.
- **Fix:** a read-only bind mount plus `--cap-drop=DAC_OVERRIDE`.
- **Evidence:** Run 005 in `module2_doc/iteration-log.md`.
- **Status:** Exercised.

### 14. Windows line endings break a Linux script
- **Symptom:** the container fails with "no such file or directory" on an entrypoint that clearly exists.
- **Usual cause:** CRLF line endings after the `#!/bin/bash` shebang.
- **Fix:** convert the file to LF.
- **Evidence:** the `docker-entrypoint.sh` case in `docs/adr/ADR-002-line-ending-noise-detection-deterministic-conversion.md`.
- **Status:** Exercised.

---

## D. Evidence and records

### 15. A stale record is treated as current fact
- **Symptom:** a memory entry or document asserts something that is no longer true, such as "not yet committed."
- **Caught by:** whichever session checks it (three independent rediscoveries in one holdout pass), by `decision-auditor` correcting records against git, and by the `verify-before-trusting` skill.
- **First response:** check the real artifact, correct the record, and note the date and the evidence.
- **Evidence:** HO-01, HO-03, and HO-05 in the calibration log, and `module4_doc/decision-auditor-case-study.md`.
- **Status:** Exercised.

### 16. Cost or time is measured wrongly
- **Symptom:** an implausible cost for a task.
- **Usual cause:** reading `/status` mid-session gives the session's cumulative cost, not the task's.
- **Fix:** bracket each task with `date` and `/status` at the start of a standalone session. Record JSON `null` when unmeasured, never a guess.
- **Evidence:** the calibration log's holdout findings (cost was reliable in only 2 of 6 tasks).
- **Status:** Exercised.

### 17. Evidence is recorded in the wrong shape
- **Symptom:** the harness crashes or misjudges a run. Examples: `cost_usd` written as a string, `expected_path` in the wrong order, `role_order` assuming one step per role.
- **First response:** correct the transcript, using `null` for unmeasured values. The checker crash itself is a known harness-robustness gap.
- **Evidence:** `module4_doc/tool-evolution-drill.md` and the `role_order` finding in the calibration log.
- **Status:** Exercised.

---

## E. CI/CD

### 18. A gate reports success without running
- **Symptom:** a green job that finishes in seconds, with skipped icons on its steps.
- **Usual cause:** the change classifier's filter did not match the changed files. It once watched placeholder folders instead of `agents/` and `skills/`.
- **Caught by:** reading a job's steps, not only its color, and a throwaway PR that touched `agents/planner.md`.
- **First response:** check the filter lines in the classifier step of `.github/workflows/ci.yml`, add the missing path, and re-run on a change that matches.
- **Evidence:** finding 1 and the `be06568` change in the calibration log's CI-gates entry (run #24 skipped, run #25 ran).
- **Status:** Exercised.

### 19. A gate is quietly weakened
- **Symptom:** `pipeline-integrity` fails with a message such as "gating job 'policy-gate' has continue-on-error: true."
- **Caught by:** `pipeline-integrity`, and `policy-gate`'s own test. Both fired on the deliberate test.
- **First response:** do not merge. Revert the workflow change. On `main`, treat it as a P0.
- **Evidence:** the Verified section of `docs/ci-step-design.md` and `module4_doc/impact-report.md`.
- **Status:** Exercised (a deliberate test on a throwaway branch).

### 20. A deterministic conversion regresses
- **Symptom:** a check that passed before the conversion fails after it.
- **First response:** revert the single conversion commit, since each conversion is designed to land as one clean revert.
- **Evidence:** `docs/adr/ADR-001-orchestrator-test-deterministic-conversion.md` and the end-to-end regression entry (no regression found); the rollback note in ADR-002.
- **Status:** Defined only. No regression has occurred, so the revert path has not been exercised.

---

## Adding an entry

When a new failure happens, add an entry with the same fields (symptom, usual cause, caught by, first response, prevention or fix, evidence, status). Cite a transcript, an audit-log line, or a commit, and mark it *Defined only* until the response has actually been used.
