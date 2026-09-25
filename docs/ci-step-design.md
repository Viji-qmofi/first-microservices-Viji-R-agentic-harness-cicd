# CI Agentic Step Design

## Step: Policy test suite

- Does: Confirms `docs/governance-policy.md`, MCP allow-lists, skill scopes, and container permissions agree.
- Input: whole repository.
- Produces: `policy-report.json` artifact.
- Classification: gating, permanent.
- Time limit: 5 minutes.
- Credentials: none.

## Step: Evaluation harness

- Does: Runs deterministic and rubric checks on agent-affecting changes.
- Input: whole repository plus changed-file classifier output.
- Produces: `deterministic-report.json` and `rubric-report.json`.
- Classification: gating, conditional.
- Time limit: 10 minutes.
- Credentials: `ANTHROPIC_API_KEY` only for model-backed rubric runs.
- Design note: `test_deterministic.py`/`test_rubric_suite.py` were built to score one transcript passed as an argument, for an interactive, human-approved run -- not to generate fresh evidence unattended on every PR. `scripts/run-eval-gate.py` runs both against a known-good, already-committed transcript (`.eval-artifacts/holdout-run-1/HO-02.json`, which previously passed 13/13 deterministic checks and 4/4 rubric dimensions) as a regression check: confirming the checks themselves still correctly score a known-good run the same way after any code change, rather than launching a live agent session on every commit (slower, costs real API calls per PR, and risks becoming a noisy gate people route around).

## Step: Agent code review

- Does: Reviewer subagent scores changed files and posts an advisory PR comment.
- Input: changed files from the shared classifier.
- Produces: PR comment, `review-output.md`, and review audit log.
- Classification: advisory; not a required status check.
- Time limit: 15 minutes.
- Credentials: `ANTHROPIC_API_KEY`, scoped to the reviewer step only.

## Step: Audit trail

- Does: Combines policy, harness, and review artifacts into one JSON trail and posts a PR summary.
- Input: CI artifacts from earlier jobs.
- Produces: `ci-audit-trail-[sha].json` artifact and PR comment.
- Classification: required operational evidence; always runs.
- Credentials: GitHub token with pull-request comment permission.

## First live pipeline run: real bugs caught (2026-09-24)

The full pipeline (five jobs: `change-type-check`, `policy-gate`, `governed-file-gate`, `eval-gate`, `advisory-review`, plus `audit-trail`) had never actually executed in GitHub Actions before this date -- Actions is disabled by default on forked repositories that already contain workflow files, and this fork's Actions were never explicitly enabled until now. Every job's YAML had been written, reviewed, and locally spot-checked, but never actually run end to end on GitHub's own runners.

The first real run failed twice before passing, on two genuine, previously-invisible bugs:

1. **`policy-gate`, `governed-file-gate`, and `advisory-review` all invoked a bare `python` command** (copied from the lesson's reference repo, a different base image where `python` resolves) rather than `python3` (the only Python interpreter this project's Dockerfile actually installs -- every interactive command throughout this whole course has used `python3` explicitly for exactly this reason). Failed with `exec: python: not found`, exit code 127.
2. **`pytest`/`pytest-json-report` were never added to `requirements.txt`** -- they had only ever been installed interactively, inside an already-running container, back when `test_policy.py` was first verified. A fresh CI image build had no record of that one-off install. Failed with `No module named pytest`.

Both fixed at their root cause (three `python` -> `python3` corrections; both packages added to `requirements.txt`), then reverified with a real, full green run.

This is exactly the scenario this lesson's own opening paragraph describes: *"If the policy tests are only run locally, the mistake can slip through... The policy exists, but nothing is consistently enforcing it."* Two real defects sat invisibly in a fully-written, seemingly-correct pipeline for as long as it was never actually exercised -- caught the moment it finally ran for real, not before.

## First live pipeline run: real bugs caught (2026-09-24)

The full pipeline (five jobs: `change-type-check`, `policy-gate`, `governed-file-gate`, `eval-gate`, `advisory-review`, plus `audit-trail`) had never actually executed in GitHub Actions before this date -- Actions is disabled by default on forked repositories that already contain workflow files, and this fork's Actions were never explicitly enabled until now. Every job's YAML had been written, reviewed, and locally spot-checked, but never actually run end to end on GitHub's own runners.

The first real run failed twice before passing, on two genuine, previously-invisible bugs:

1. **`policy-gate`, `governed-file-gate`, and `advisory-review` all invoked a bare `python` command** (copied from the lesson's reference repo, a different base image where `python` resolves) rather than `python3` (the only Python interpreter this project's Dockerfile actually installs -- every interactive command throughout this whole course has used `python3` explicitly for exactly this reason). Failed with `exec: python: not found`, exit code 127.
2. **`pytest`/`pytest-json-report` were never added to `requirements.txt`** -- they had only ever been installed interactively, inside an already-running container, back when `test_policy.py` was first verified. A fresh CI image build had no record of that one-off install. Failed with `No module named pytest`.

Both fixed at their root cause (three `python` -> `python3` corrections; both packages added to `requirements.txt`), then reverified with a real, full green run.

This is exactly the scenario this lesson's own opening paragraph describes: *"If the policy tests are only run locally, the mistake can slip through... The policy exists, but nothing is consistently enforcing it."* Two real defects sat invisibly in a fully-written, seemingly-correct pipeline for as long as it was never actually exercised -- caught the moment it finally ran for real, not before.

## Step: Pipeline integrity check

- Does: Inspects `.github/workflows/ci.yml` itself (not the code change) and confirms the pipeline's own safety invariants haven't been quietly weakened. Three checks: (1) none of `policy-gate`, `eval-gate`, or `pipeline-integrity` itself has `continue-on-error: true`; (2) `audit-trail` still exists and keeps `if: always()`; (3) `change-type-check` (the classifier) still exists.
- Input: the workflow YAML file itself, parsed with `pyyaml` -- not the diff, not any other job's output.
- Produces: `ci-artifacts/integrity-report.json` (`checks_run`, `errors`, `exitcode`, `gating_jobs_checked`), uploaded as the `integrity-report` artifact -- same naming convention as `policy-report.json`/`governed-file-report.json`.
- Classification: gating, permanent. Same reasoning as `policy-gate`: this protects an invariant the team has agreed must always hold (the pipeline's own guardrails staying intact), so it is never a candidate for demotion to advisory -- an advisory integrity check would let exactly the kind of silent weakening it exists to catch slip through undetected.
- Time limit: under 1 minute (no Docker build, no model call -- pure static YAML inspection).
- Credentials: none.
- **Deliberately has no `needs:`.** Runs independently of every other job's success or failure, by design -- if it depended on, say, `policy-gate` succeeding, weakening `policy-gate` itself could cause `pipeline-integrity` to be skipped exactly when it's most needed. This is what "runs regardless of whether the other jobs succeeded or failed" (Step 1's own requirement) actually means in practice, not just no `continue-on-error`.
- Required status check: [confirm once added in branch protection settings for `main`].
- Wired into `audit-trail`: added to `needs: [...]`, its result passed via `--integrity-result`, and `build-audit-trail.py` reads `integrity-report.json` into `results.pipeline_integrity` and `integrity_report_summary`.
- **Verified:** [pending Step 4 -- deliberately weaken a guardrail on a throwaway branch and confirm the check fails for the right reason]


## First live pipeline run: real bugs caught (2026-09-24)

The full pipeline (five jobs: `change-type-check`, `policy-gate`, `governed-file-gate`, `eval-gate`, `advisory-review`, plus `audit-trail`) had never actually executed in GitHub Actions before this date -- Actions is disabled by default on forked repositories that already contain workflow files, and this fork's Actions were never explicitly enabled until now. Every job's YAML had been written, reviewed, and locally spot-checked, but never actually run end to end on GitHub's own runners.

The first real run failed twice before passing, on two genuine, previously-invisible bugs:

1. **`policy-gate`, `governed-file-gate`, and `advisory-review` all invoked a bare `python` command** (copied from the lesson's reference repo, a different base image where `python` resolves) rather than `python3` (the only Python interpreter this project's Dockerfile actually installs -- every interactive command throughout this whole course has used `python3` explicitly for exactly this reason). Failed with `exec: python: not found`, exit code 127.
2. **`pytest`/`pytest-json-report` were never added to `requirements.txt`** -- they had only ever been installed interactively, inside an already-running container, back when `test_policy.py` was first verified. A fresh CI image build had no record of that one-off install. Failed with `No module named pytest`.

Both fixed at their root cause (three `python` -> `python3` corrections; both packages added to `requirements.txt`), then reverified with a real, full green run.

This is exactly the scenario this lesson's own opening paragraph describes: *"If the policy tests are only run locally, the mistake can slip through... The policy exists, but nothing is consistently enforcing it."* Two real defects sat invisibly in a fully-written, seemingly-correct pipeline for as long as it was never actually exercised -- caught the moment it finally ran for real, not before.

## Step: Pipeline integrity check

- Does: Inspects `.github/workflows/ci.yml` itself (not the code change) and confirms the pipeline's own safety invariants haven't been quietly weakened. Three checks: (1) none of `policy-gate`, `eval-gate`, or `pipeline-integrity` itself has `continue-on-error: true`; (2) `audit-trail` still exists and keeps `if: always()`; (3) `change-type-check` (the classifier) still exists.
- Input: the workflow YAML file itself, parsed with `pyyaml` -- not the diff, not any other job's output.
- Produces: `ci-artifacts/integrity-report.json` (`checks_run`, `errors`, `exitcode`, `gating_jobs_checked`), uploaded as the `integrity-report` artifact -- same naming convention as `policy-report.json`/`governed-file-report.json`.
- Classification: gating, permanent. Same reasoning as `policy-gate`: this protects an invariant the team has agreed must always hold (the pipeline's own guardrails staying intact), so it is never a candidate for demotion to advisory -- an advisory integrity check would let exactly the kind of silent weakening it exists to catch slip through undetected.
- Time limit: under 1 minute (no Docker build, no model call -- pure static YAML inspection).
- Credentials: none.
- **Deliberately has no `needs:`.** Runs independently of every other job's success or failure, by design -- if it depended on, say, `policy-gate` succeeding, weakening `policy-gate` itself could cause `pipeline-integrity` to be skipped exactly when it's most needed. This is what "runs regardless of whether the other jobs succeeded or failed" (Step 1's own requirement) actually means in practice, not just no `continue-on-error`.
- Required status check: [confirm once added in branch protection settings for `main`].
- Wired into `audit-trail`: added to `needs: [...]`, its result passed via `--integrity-result`, and `build-audit-trail.py` reads `integrity-report.json` into `results.pipeline_integrity` and `integrity_report_summary`.
- **Verified:** [pending Step 4 -- deliberately weaken a guardrail on a throwaway branch and confirm the check fails for the right reason]

### Verified (2026-09-25)

Deliberately added `continue-on-error: true` to `policy-gate` on a throwaway branch (`test-weaken-guardrail`), opened a PR into `main`, confirmed the failure, then deleted the branch (PR auto-closed, never merged).

**Result: two independent mechanisms caught the identical weakening, for two different, correct reasons:**

1. `policy-gate` itself failed -- `eval/test_policy.py::test_policy_gate_is_not_continue_on_error` (a check that already existed, asserting this exact job never carries `continue-on-error: true`) failed on its own, unrelated to `pipeline-integrity` running at all.
2. `pipeline-integrity` failed with a precise, correctly-attributed message: `gating job 'policy-gate' has continue-on-error: true, which disables the gate`.

`change-type-check` and `eval-gate` passed normally, as expected -- neither has any dependency on `policy-gate`'s outcome, confirming the weakening's blast radius was correctly isolated to the two checks actually watching for it.

Reverted by deleting the throwaway branch; the pipeline returned to a clean, fully green state on `main` with no lasting change.
