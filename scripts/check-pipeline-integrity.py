#!/usr/bin/env python3
"""Assert the pipeline's safety invariants hold in the workflow file."""

import json
import sys
from pathlib import Path
import yaml

GATING_JOBS = {"policy-gate", "eval-gate", "pipeline-integrity"}
WORKFLOW = Path(".github/workflows/ci.yml")
REPORT_PATH = Path("ci-artifacts/integrity-report.json")

with open(WORKFLOW, encoding="utf-8") as f:
    workflow = yaml.safe_load(f)

jobs = workflow.get("jobs", {})
errors: list[str] = []
checks_run: list[str] = []

# 1. No gating job may disable itself with continue-on-error.
for name in sorted(GATING_JOBS):
    checks_run.append(f"continue-on-error check: {name}")
    job = jobs.get(name)
    if job is None:
        errors.append(f"required gating job '{name}' is missing")
    elif job.get("continue-on-error") is True:
        errors.append(f"gating job '{name}' has continue-on-error: true, which disables the gate")

# 2. The audit trail job must exist and always run.
checks_run.append("audit-trail: exists and keeps if: always()")
audit = jobs.get("audit-trail")
if audit is None:
    errors.append("audit-trail job is missing")
elif "always()" not in str(audit.get("if", "")):
    errors.append("audit-trail job must keep 'if: always()'")

# 3. The change classifier must still exist.
checks_run.append("change-type-check: exists")
if "change-type-check" not in jobs:
    errors.append("change-type-check classifier is missing")

REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
report = {
    "checks_run": checks_run,
    "errors": errors,
    "exitcode": 1 if errors else 0,
    "gating_jobs_checked": sorted(GATING_JOBS),
}
REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

if errors:
    print("Pipeline integrity check FAILED:")
    for problem in errors:
        print(f"  - {problem}")
    sys.exit(1)

print("Pipeline integrity check passed")
