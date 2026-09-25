#!/usr/bin/env python3
"""Deterministic replacement for the Orchestrator's narrative interpretation
of `./mvnw test` output.

Reads the raw text output of a Maven test run, finds the real Surefire
summary counts, and writes a structured pass/fail result. No language
model is involved.

Usage:
    python3 scripts/parse_test_result_deterministic.py \\
        --input maven-output.txt --output result.json
"""

import argparse
import json
import re
import sys

# Matches Maven Surefire's own summary line, e.g.:
#   Tests run: 38, Failures: 0, Errors: 0, Skipped: 0
# Deliberately does NOT match on the presence of the words "ERROR" or
# "WARN" anywhere else in the log -- Eureka stack traces from tests that
# deliberately exercise failure paths, and WARN lines from retry-logic
# tests, must not be mistaken for a real failure. Only this exact summary
# line format is treated as evidence of the real result.
SUMMARY_PATTERN = re.compile(
    r"Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+),\s*Skipped:\s*(\d+)"
)


def load_text(path):
    """Read a text file from disk and return its content."""
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def parse(output_text):
    """Return a structured result from raw Maven test output.

    Maven prints one summary line per module in a multi-module build, plus
    a final aggregate line. The last matching line in the output is always
    the correct total to report -- taking the first would misreport a
    multi-module build's real total.

    If no summary line is found at all (e.g. a compilation failure before
    any test could run), the result is explicitly invalid, not silently
    treated as passing by default.
    """
    matches = list(SUMMARY_PATTERN.finditer(output_text))
    if not matches:
        return {
            "valid": False,
            "tests_run": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "problems": ["no test summary line found in output -- build may have failed before tests ran"],
        }

    last = matches[-1]
    tests_run, failures, errors, skipped = (int(g) for g in last.groups())

    problems = []
    if failures > 0:
        problems.append(f"{failures} test failure(s)")
    if errors > 0:
        problems.append(f"{errors} test error(s)")
    if tests_run == 0:
        problems.append("summary line reported zero tests run")

    return {
        "valid": len(problems) == 0,
        "tests_run": tests_run,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "problems": problems,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="path to the raw Maven test output")
    parser.add_argument("--output", required=True, help="path to write the structured result")
    args = parser.parse_args()

    output_text = load_text(args.input)
    result = parse(output_text)

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)

    if not result["valid"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
