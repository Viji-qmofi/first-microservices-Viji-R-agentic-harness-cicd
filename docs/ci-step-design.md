# CI Agentic Step Design

## How the gates run

The classifier job `change-type-check` decides which conditional gates run, from the files a change touches. It emits `requires-governed-check`, `requires-eval`, and `touches-policy`. The filters cover `agents/`, `skills/`, `CLAUDE.md`, `mcp-servers/`, `eval/`, `docs/governance-policy.md`, `docs/routing-and-tool-grant-map.md`, `module3_doc/routing-and-tool-grant-map.json`, and `scripts/run-agent.ps1` (plus the empty `.agents/` and `.skills/` placeholder folders).

A conditional gate that is not triggered still reports green, with every step skipped. Read a job's step list, not only its color.

Every job that needs the container image builds it with up to three attempts and then once more from an AWS ECR Public mirror of the base image, because Docker Hub rate-limits the shared IP addresses of GitHub's runners (it returned `429 Too Many Requests` on the pull request for the audit-log template update). The fallback still fails closed: if the mirror build fails, so does the job.

Required status checks on `main`, with "Require a pull request before merging" enabled: Policy Test Suite, Evaluation Harness, Governed File Check, and Pipeline Integrity Check. Not required: Advisory Code Review (advisory by design) and Audit Trail (it must always run, whatever else fails).

The time limits below are documented targets. The workflow sets no `timeout-minutes` (see Known gaps).

## Step: Policy test suite

- Does: Runs structural checks on the repository and workflow (`eval/test_policy.py`, 5 tests): the governance policy and this document exist, the workflow exists, the workflow hardcodes no API key, and the `policy-gate` job is not marked `continue-on-error`.
- Input: whole repository.
- Produces: `policy-report.json` artifact.
- Classification: gating, permanent; required status check.
- Time limit: 5 minutes.
- Credentials: none.

## Step: Governed file check

- Does: Compares what `docs/governance-policy.md` declares with what is configured: the three MCP allow-lists, each agent file's `tools:` line and version, the skills under `skills/`, and the evaluation harness's own copies of the grants (`module3_doc/routing-and-tool-grant-map.json` and `FORBIDDEN_OPERATIONS` in `eval/test_deterministic.py`). Also checks that the coursetools server refuses to start without its allow-list. 14 tests in `eval/test_governed_files.py`.
- Input: whole repository.
- Produces: `governed-file-report.json` artifact.
- Classification: gating, conditional (runs when `requires-governed-check` is true); required status check.
- Time limit: 15 minutes (observed 3 to 14 minutes, mostly the container build).
- Credentials: none.
- Evidence: PR #3, red at `d50ab45` and green at `8f87663` and `ff1f03e` (calibration log, CI-gates entry).

## Step: Evaluation harness

- Does: Runs deterministic and rubric checks on agent-affecting changes.
- Input: whole repository plus changed-file classifier output.
- Produces: `deterministic-report.json` and `rubric-report.json`.
- Classification: gating, conditional.
- Time limit: 10 minutes.
- Credentials: `ANTHROPIC_API_KEY` only for model-backed rubric runs.
- Design note: `test_deterministic.py`/`test_rubric_suite.py` were built to score one transcript passed as an argument, for an interactive, human-approved run -- not to generate fresh evidence unattended on every PR. `scripts/run-eval-gate.py` runs both against a known-good, already-committed transcript (`.eval-artifacts/holdout-run-1/HO-02.json`, which previously passed 13/13 deterministic checks and 4/4 rubric dimensions) as a regression check: confirming the checks themselves still correctly score a known-good run the same way after any code change, rather than launching a live agent session on every commit (slower, costs real API calls per PR, and risks becoming a noisy gate people route around).
- Required status check: yes.
- Limits: it replays a frozen, known-good transcript (`HO-02`). It shows the harness still reproduces a known-good result and that the gate fires on prompt-file changes. It does not evaluate the behavior of a changed prompt.

## Step: Agent code review

- Does: Reviewer subagent scores changed files and writes an advisory report.
- Input: changed files from the shared classifier.
- Produces: `review-output.md` and a review audit log, uploaded as the `advisory-review` artifact. No PR comment is posted.
- Classification: advisory; not a required status check; runs only on pull requests and is marked `continue-on-error`.
- Time limit: 15 minutes.
- Credentials: `ANTHROPIC_API_KEY`, scoped to the reviewer step only.

## Step: Audit trail

- Does: Combines the gate results and report summaries into one JSON record per run.
- Input: CI artifacts from earlier jobs.
- Produces: `ci-audit-trail-<sha>.json`, uploaded as the `audit-trail` artifact and kept 90 days. No PR comment is posted.
- Classification: required operational evidence; always runs (`if: always()`), so a failed gate is still recorded.
- Credentials: none beyond the workflow's default token; nothing is posted.

## Step: Pipeline integrity check

- Does: Inspects `.github/workflows/ci.yml` itself (not the code change) and confirms the pipeline's own safety invariants haven't been quietly weakened. Three checks: (1) none of `policy-gate`, `eval-gate`, `governed-file-gate`, or `pipeline-integrity` itself has `continue-on-error: true`; (2) `audit-trail` still exists and keeps `if: always()`; (3) `change-type-check` (the classifier) still exists.
- Input: the workflow YAML file itself, parsed with `pyyaml` -- not the diff, not any other job's output.
- Produces: `ci-artifacts/integrity-report.json` (`checks_run`, `errors`, `exitcode`, `gating_jobs_checked`), uploaded as the `integrity-report` artifact -- same naming convention as `policy-report.json`/`governed-file-report.json`.
- Classification: gating, permanent. Same reasoning as `policy-gate`: this protects an invariant the team has agreed must always hold (the pipeline's own guardrails staying intact), so it is never a candidate for demotion to advisory -- an advisory integrity check would let exactly the kind of silent weakening it exists to catch slip through undetected.
- Time limit: under 1 minute (no Docker build, no model call -- pure static YAML inspection).
- Credentials: none.
- **Deliberately has no `needs:`.** Runs independently of every other job's success or failure, by design -- if it depended on, say, `policy-gate` succeeding, weakening `policy-gate` itself could cause `pipeline-integrity` to be skipped exactly when it's most needed. This is what "runs regardless of whether the other jobs succeeded or failed" (Step 1's own requirement) actually means in practice, not just no `continue-on-error`.
- Required status check: yes (confirmed 2026-10-08).
- Wired into `audit-trail`: added to `needs: [...]`, its result passed via `--integrity-result`, and `build-audit-trail.py` reads `integrity-report.json` into `results.pipeline_integrity` and `integrity_report_summary`.
- **Verified:** yes, 2026-09-25 (see below).

### Verified (2026-09-25)

Deliberately added `continue-on-error: true` to `policy-gate` on a throwaway branch (`test-weaken-guardrail`), opened a PR into `main`, confirmed the failure, then deleted the branch (PR auto-closed, never merged).

**Result: two independent mechanisms caught the identical weakening, for two different, correct reasons:**

1. `policy-gate` itself failed -- `eval/test_policy.py::test_policy_gate_is_not_continue_on_error` (a check that already existed, asserting this exact job never carries `continue-on-error: true`) failed on its own, unrelated to `pipeline-integrity` running at all.
2. `pipeline-integrity` failed with a precise, correctly-attributed message: `gating job 'policy-gate' has continue-on-error: true, which disables the gate`.

`change-type-check` and `eval-gate` passed normally, as expected -- neither has any dependency on `policy-gate`'s outcome, confirming the weakening's blast radius was correctly isolated to the two checks actually watching for it.

Reverted by deleting the throwaway branch; the pipeline returned to a clean, fully green state on `main` with no lasting change.

## First live pipeline run: real bugs caught (2026-09-24)

The full pipeline (five jobs: `change-type-check`, `policy-gate`, `governed-file-gate`, `eval-gate`, `advisory-review`, plus `audit-trail`) had never actually executed in GitHub Actions before this date -- Actions is disabled by default on forked repositories that already contain workflow files, and this fork's Actions were never explicitly enabled until now. Every job's YAML had been written, reviewed, and locally spot-checked, but never actually run end to end on GitHub's own runners.

The first real run failed twice before passing, on two genuine, previously-invisible bugs:

1. **`policy-gate`, `governed-file-gate`, and `advisory-review` all invoked a bare `python` command** (copied from the lesson's reference repo, a different base image where `python` resolves) rather than `python3` (the only Python interpreter this project's Dockerfile actually installs -- every interactive command throughout this whole course has used `python3` explicitly for exactly this reason). Failed with `exec: python: not found`, exit code 127.
2. **`pytest`/`pytest-json-report` were never added to `requirements.txt`** -- they had only ever been installed interactively, inside an already-running container, back when `test_policy.py` was first verified. A fresh CI image build had no record of that one-off install. Failed with `No module named pytest`.

Both fixed at their root cause (three `python` -> `python3` corrections; both packages added to `requirements.txt`), then reverified with a real, full green run.

This is exactly the scenario this lesson's own opening paragraph describes: *"If the policy tests are only run locally, the mistake can slip through... The policy exists, but nothing is consistently enforcing it."* Two real defects sat invisibly in a fully-written, seemingly-correct pipeline for as long as it was never actually exercised -- caught the moment it finally ran for real, not before.

## Gate audit (2026-10-07 to 2026-10-08)

A review of what each gate actually did, recorded in the CI-gates entry of `module3_doc/calibration-log.md`:

- `eval-gate` could report green with every step skipped, because the classifier filter watched placeholder folders instead of `agents/` and `skills/`. Fixed in `be06568` and proven on a throwaway pull request where the harness built the container and reproduced `HO-02` at 13/13.
- `governed-file-gate` previously asserted only that files exist. It now runs 14 policy-versus-configuration tests (PR #3).
- Governed File Check was made a required status check, and a pull request is now required before merging to `main`.

## Known gaps

- The workflow sets no `timeout-minutes`, so a hung job would run until GitHub's default limit. The time limits above are targets, not enforcement.
- The workflow has no explicit `permissions:` block, so jobs use the repository's default token permissions instead of a stated least-privilege set.
