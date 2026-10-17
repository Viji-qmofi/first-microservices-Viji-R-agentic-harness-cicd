# Runbook: Operating the Governed Pipeline

For the operator of this system: how to start it, what to watch, what to do when something goes wrong, when to stop, and how to roll back. Each incident points to its entry in [`failure-mode-playbook.md`](failure-mode-playbook.md), which holds the evidence. Every response fails toward stopping and asking the human, never toward continuing in a degraded mode.

**Owner and escalation.** There is one operator, who is also the person who approves commits. Anything below that says "stop" means stop and decide yourself; no one else is paged.

## 1. Start a session

1. Build the image if needed and run the container with the command in the `README.md` Quick Start. Mount `claude-auth` at `/claude-auth`, not `/root/.claude`.
2. Inside the container, start the two HTTP MCP servers and register them (commands in `README.md`). They must be running before `claude` starts, and a server started mid-session is not seen by that session.
3. Run `claude`, check the header names the intended model, and run `/mcp` to confirm `storage`, `retrieval` and `coursetools` are connected.
4. End with `exit`, not Ctrl+C, so the login is saved.

## 2. What to watch

**Each run:**
- Cost and time against the budgets: $2.00 and 900 seconds per task (status line and a `date` before and after).
- The saved transcript in `.eval-artifacts/runs/<task>.json` and its `.log`.
- The audit logs in `.memory/storage/`: `storage-audit.log` and `retrieval-audit.log`. Denied calls are recorded there. The Orchestrator can read the storage log with `audit_read`.

**Each pull request:**
- The four required checks: Policy Test Suite, Governed File Check, Evaluation Harness, Pipeline Integrity Check. Open a job's step list, not only its color, because a conditional gate that is not triggered still shows green with every step skipped.
- The `audit-trail` artifact (`ci-audit-trail-<sha>.json`, kept 90 days), which records what each gate did.
- The `advisory-review` artifact. A green advisory job proves nothing until the review text is read.

## 3. Incidents: what you see, what to do first

- **An agent says something false, or does more than asked** (playbook 1, 3). Do not accept its summary. Check the raw artifact: the diff, the log, the file. Use the `verify-before-trusting` skill. If it went beyond scope, stop the run.
- **A call is denied with `authorization_denied`** (7). Stop. Do not retry under another role. Read the audit log. Widen a grant only by a pull request with a stated reason (`ADR-007`).
- **A caller claims a role it is not** (8). This is a known limit: roles are self-declared. Treat an unexpected claim as an escalation.
- **The allow-list file is missing** (9). `coursetools` refuses to start. Restore the file from git and restart.
- **An MCP server is down or its tools are missing** (11). Start both servers, restart `claude`, confirm with `/mcp`. Do not continue without them.
- **Agents or skills missing from the session** (12). The `claude-auth` volume is mounted at the wrong path. Mount it at `/claude-auth`.
- **A shell script fails on Windows line endings** (14). Check `.gitattributes` (`eol=lf`) and re-checkout the file.
- **A record is stale and treated as fact** (15). Run `decision-auditor` to check records against git state.
- **A gate is green but did nothing** (18). Read its steps. Check the classifier's path filter in `.github/workflows/ci.yml`.
- **A gate is weakened** (19). Do not merge. Revert the workflow change. On `main`, treat it as a P0.
- **The image will not pull, `429 Too Many Requests`** (21). Re-run the job later. The build already retries and falls back to a mirror. Do not bypass a required check.
- **The model API credit runs out** (22). Add credit in the Anthropic Console, then re-run all jobs. Do not bypass the required check.
- **The advisory review is green but contains an error** (23). Read the artifact. Fix the cause, usually the entry above.
- **A CI job is cancelled at its time limit** (24). Find the step that was running. Re-run once if the cause is a slow registry or runner. If it recurs, raise the ceiling in `ci.yml` with a stated reason. Do not bypass a required check. Note that a cancelled Policy Test Suite also skips Governed File Check, Evaluation Harness and Advisory Code Review.
- **Cost or time runs over, or a subagent does not return** (6). Stop and ask: continue, scope down, or abandon.

## 4. When to stop and escalate

Stop and involve the human, and do not proceed automatically, when:
- a plan proposes a change visible outside the codebase;
- two reviewers contradict each other on the same section;
- the test step returns `valid: false`;
- any MCP call returns `authorization_denied`;
- `decision-auditor` proposes a correction (it is flagged even though the role may act);
- the diff does not match the claimed scope;
- a plan has been revised three times;
- a required MCP server is unreachable;
- the task exceeds $2.00 or 900 seconds, or a subagent has not returned in 10 minutes.

Details: [`module4_doc/escalation-and-rollback-criteria.md`](../module4_doc/escalation-and-rollback-criteria.md) and `CLAUDE.md`.

## 5. Rollback

`main` requires a pull request, so every rollback is a revert pull request with the required checks.

- **A deterministic conversion regresses.** Revert the single conversion commit: `git revert <sha>`, push on a branch, open the PR.
- **`pipeline-integrity` fails on `main`.** P0. Merge nothing else until the failure named in `integrity-report.json` is fixed.
- **A widened grant is later tied to a near-miss.** Revert that allow-list commit. Re-apply only with the evidence standard in `ADR-007`.
- **`eval-gate` fails on `main`.** Do not merge more agent-affecting changes until it is diagnosed as a real defect (fix first) or a known unrelated gap (document it and proceed). Never ignore it silently.
- **A memory entry is wrong or obsolete.** Do not delete it. Move it to `.memory/project/archived/` with the reason, and update `MEMORY_INDEX.md`.

## 6. Reliability and cost controls, and their honest status

- **Job timeouts.** Configured on all seven CI jobs (`timeout-minutes`). Exercised on a throwaway pull request: with the Policy Test Suite limit set to 1 minute, GitHub cancelled the job mid-build (PR #23, run 38971124589). The limits are fixed ceilings, not tuned to measured run times.
- **Build retry and mirror fallback.** Three attempts, then the AWS ECR Public mirror. Exercised on a throwaway PR with a simulated failure (PR #10). A real registry rate limit cannot be triggered on demand.
- **Fail closed.** Exercised by a real incident: the Evaluation Harness stayed red when the API credit ran out (playbook 22).
- **Per-task budget ($2.00, 900 seconds).** The after-the-fact check in the evaluation harness has fired on a real run (HO-06). It also fired in CI on a deliberately lowered ceiling: HO-02's real cost of $0.95 against a $0.50 budget failed the required Evaluation Harness (PR #24, run 38972843072). The live guard in `CLAUDE.md` is defined only.
- **Plan-revision limit (three) and subagent stall (10 minutes).** Defined only.
- **MCP server unreachable.** Exercised: the Orchestrator halted and offered only "start and restart" or "abandon" (playbook 11).

## 7. After any incident

1. Record it in `module3_doc/calibration-log.md` with evidence: a transcript, an audit-log line, or a commit, not a summary.
2. Add or update the playbook entry with the same fields, and mark it Defined only until the response has actually been used.
3. If a grant changes, follow `ADR-007`: a stated, cited reason tied to the role's job.
