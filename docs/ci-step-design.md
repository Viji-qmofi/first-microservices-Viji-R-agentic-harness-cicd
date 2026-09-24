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

