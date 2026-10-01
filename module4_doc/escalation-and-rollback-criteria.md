# Escalation and Rollback Criteria

Explicit thresholds connecting this system's quality gates to specific required actions, not left implicit in "a human reviews everything."

## Escalation triggers (stop and involve a human; do not proceed automatically)

| Trigger | Required action | Where enforced |
|---|---|---|
| A plan proposes an externally-visible behavior change (API response, status code, new endpoint) | Stop before implementation; present the specific change for explicit approval | `CLAUDE.md`, Evaluating results |
| Two reviewers return contradictory verdicts on the same section | Escalate to human; never self-resolve by picking a verdict or averaging | `CLAUDE.md`, Reviewer Conflict Resolution; verified `eval/red-team-results.md` Prompt 4 |
| `orchestrator_test` (deterministic) reports `valid: false` | Stop; report the `problems` list; do not proceed to commit | `CLAUDE.md`, post-`ADR-001` integration |
| Any MCP operation returns `authorization_denied` | Stop; do not attempt a workaround or retry under a different claimed role | Server-enforced, `ADR-005` |
| A memory-record correction is proposed by `decision-auditor` | Flagged in the run summary for human awareness even though the role is authorized to act -- "fixing" doesn't get a lighter review standard than "creating" | `docs/governance-policy.md`, decision-auditor entry |

## Rollback criteria (when and how to revert, with specific quality thresholds)

| Condition | Rollback action |
|---|---|
| A deterministic-conversion regression check (per `ADR-001`'s pattern) shows a check that previously passed now failing, attributable to the conversion itself | Revert the single commit that performed the conversion -- every conversion is designed to land as one commit touching only the new script, its tests, and the `CLAUDE.md` instruction change, specifically so a clean `git revert` fully restores the prior agentic behavior (`ADR-002`'s rollback note states this design requirement explicitly, even though that conversion was never built) |
| `pipeline-integrity` fails on `main` (not a throwaway branch) | Treat as a P0: a real gating job has been weakened or removed. Do not merge anything else until the specific failure named in `integrity-report.json` is corrected |
| A governance allow-list change widens a role's access and a near-miss is later traced to that widening | Revert the specific allow-list commit; re-apply only with the same evidence standard `ADR-007` requires for any widening (a stated, cited reason tied to the role's actual job) |
| `eval-gate`'s regression check fails on `main` | Do not merge further agent-affecting changes until the regression is diagnosed as either a real defect (fix before proceeding) or a known, pre-existing, unrelated gap (document and proceed, per the precedent in `module3_doc/calibration-log.md`'s regression-check entries -- never silently ignored either way) |

## What "quality threshold" means concretely here

Not a single number -- the thresholds already built into the evaluation harness itself: `eval/test_deterministic.py`'s per-check pass/fail (budgets: $2.00/run cost ceiling, 900s latency ceiling, among others), `eval/rubric.json`'s per-dimension floor (every dimension must independently score >=3, no averaging), and `scripts/check-pipeline-integrity.py`'s three structural invariants. A rollback trigger is any case where a real run crosses one of these already-defined thresholds in a way traceable to a specific recent change, not a new, separately-invented bar.
