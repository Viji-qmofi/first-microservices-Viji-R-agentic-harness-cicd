#!/usr/bin/env python3
"""CI eval-gate: run the Module 3 evaluation harness as a regression check
against a known-good, already-committed transcript. This is deliberately
NOT a live agent run -- test_deterministic.py/test_rubric_suite.py score a
single transcript passed as an argument; they were built to evaluate an
interactive, human-approved orchestration run, not to generate fresh
evidence unattended on every PR. Running them here against a fixed,
already-verified transcript confirms the checks themselves still correctly
score a known-good run the same way after any code change -- a real
regression check, not a live re-run.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REGRESSION_TRANSCRIPT = ".eval-artifacts/holdout-run-1/HO-02.json"
DETERMINISTIC_REPORT = Path("ci-artifacts/deterministic-report.json")
RUBRIC_REPORT = Path("ci-artifacts/rubric-report.json")


def run(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def main() -> int:
    Path("ci-artifacts").mkdir(parents=True, exist_ok=True)

    if not Path(REGRESSION_TRANSCRIPT).exists():
        report = {
            "transcript": REGRESSION_TRANSCRIPT,
            "exitcode": 1,
            "error": f"regression transcript not found at {REGRESSION_TRANSCRIPT}",
        }
        DETERMINISTIC_REPORT.write_text(json.dumps(report, indent=2))
        print(f"FAIL: {report['error']}")
        return 1

    det_code, det_output = run(["python3", "eval/test_deterministic.py", REGRESSION_TRANSCRIPT])
    det_report = {
        "transcript": REGRESSION_TRANSCRIPT,
        "exitcode": det_code,
        "output": det_output,
        "mode": "regression-check-against-known-good-transcript",
    }
    DETERMINISTIC_REPORT.write_text(json.dumps(det_report, indent=2))
    print(det_output)

    if det_code != 0:
        print("FAIL: deterministic regression check did not reproduce a clean result "
              "on a transcript that previously passed 13/13.")
        rub_report = {
            "transcript": REGRESSION_TRANSCRIPT,
            "exitcode": None,
            "skipped": True,
            "reason": "deterministic checks failed; rubric suite gates on a clean deterministic pass",
        }
        RUBRIC_REPORT.write_text(json.dumps(rub_report, indent=2))
        return 1

    rub_code, rub_output = run(["python3", "eval/test_rubric_suite.py", REGRESSION_TRANSCRIPT])
    rub_report = {
        "transcript": REGRESSION_TRANSCRIPT,
        "exitcode": rub_code,
        "output": rub_output,
        "mode": "regression-check-against-known-good-transcript",
    }
    RUBRIC_REPORT.write_text(json.dumps(rub_report, indent=2))
    print(rub_output)

    if rub_code != 0:
        print("FAIL: rubric regression check did not reproduce a clean result "
              "on a transcript that previously scored 4/4.")
        return 1

    print("PASS: eval-gate regression check reproduced the known-good result.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
