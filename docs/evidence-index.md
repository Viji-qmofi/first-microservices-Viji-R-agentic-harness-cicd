# Evidence Index

Where each requirement of the capstone brief is met in this repository. Each line names the files a reviewer should open. Items not yet met are listed at the end, not hidden.

- **Workstream 1: workflow, stakeholder, trigger, acceptance criteria, failure modes:** module4_doc/workflow-scoping.md
- **README and a stranger-run path:** README.md; setup.md. The fresh-clone 15-minute test has not been run yet.
- **Containerized harness with filesystem, network and credential boundaries:** Dockerfile; docker-entrypoint.sh; setup.md (network egress check, parallel-session isolation, security decisions, residual risks); scripts/run-agent.ps1
- **Module 1: PRD, rubric with levels and thresholds, baseline, iteration log:** docs/prd.md; docs/rubric.md; docs/iteration-log.md; module4_doc/module1-comparison.md
- **Module 2: versioned agents, two or more skills, memory layout, reflection log:** agents/; skills/summarize-session; skills/verify-before-trusting; module2_doc/memory-architecture.md; .memory/project/MEMORY_INDEX.md; reflection entries in module2_doc/iteration-log.md
- **Module 3: orchestration diagram, routing-and-tool-grant map:** docs/orchestration-diagram.md; docs/orchestration-diagram.png; docs/routing-and-tool-grant-map.md
- **Module 3: MCP storage and vector retrieval with schemas, classification tags, citations:** mcp-servers/storage; mcp-servers/retrieval; module3_doc/retrieval-ground-truth.md; module3_doc/retrieval-quality-report.md
- **Module 3: evaluation harness, holdout set, calibration log, run evidence:** eval/; module3_doc/holdout-task-set.md; module3_doc/calibration-log.md; .eval-artifacts/holdout-run-1/ (HO-01 to HO-06); .eval-artifacts/runs/
- **Module 4: governance policy and role-to-tool access matrix:** docs/governance-policy.md; docs/routing-and-tool-grant-map.md; mcp-servers/storage/allow-list.json; mcp-servers/retrieval/allow-list.json; mcp-servers/coursetools/roles.allowlist.json
- **Module 4: CI/CD guardrails:** docs/ci-step-design.md; .github/workflows/ci.yml; scripts/check-pipeline-integrity.py; scripts/run-eval-gate.py
- **Module 4: audit log template, failure-mode playbook:** docs/audit-log-template.md; docs/failure-mode-playbook.md
- **Module 4: agent-vs-deterministic-vs-human decision matrix:** docs/step-classification.md
- **Module 4: deterministic conversion and ADR:** scripts/parse_test_result_deterministic.py; docs/adr/ADR-001-orchestrator-test-deterministic-conversion.md
- **ADRs for rubric design, memory layout, MCP boundaries, subagent routing, governance and the conversion:** docs/adr/
- **Production-like integration with reliability and cost controls, incident runbook:** CLAUDE.md; docs/runbook.md; .eval-artifacts/holdout-run-1/; enforcement demonstrations on throwaway pull requests PR #23 (job timeout, run 38971124589) and PR #24 (cost budget, run 38972843072), both closed without merging
- **Tool-evolution drill:** module4_doc/tool-evolution-drill.md
- **Impact report against the Module 1 baseline, five metrics with proxies:** module4_doc/impact-report.md; module4_doc/module1-comparison.md
- **Escalation and rollback criteria:** module4_doc/escalation-and-rollback-criteria.md; docs/runbook.md
- **Red-team and policy-bypass checks:** eval/red-team-prompts.md; eval/red-team-results.md; eval/enforcement-verification.md
- **Secrets handling and data classification:** scripts/hooks/pre-commit; setup.md (Secret-scanning pre-commit hook); module2_doc/memory-architecture.md (Data Classification); CLAUDE.md (write policy)
- **Architecture write-up:** docs/architecture.md
- **Auditability of agent actions, tool calls, approvals and failures:** docs/audit-log-template.md; the storage and retrieval audit logs in .memory/storage/ (written at runtime, git-ignored); the audit-trail artifact of each CI run; transcripts in .eval-artifacts/

## Not yet complete

- Stakeholder one-pager PDF
- Walkthrough video (10 minutes or less)
- Rubric self-check PDF
- Sanitization note (optional)
- Fresh-clone 15-minute stranger test
