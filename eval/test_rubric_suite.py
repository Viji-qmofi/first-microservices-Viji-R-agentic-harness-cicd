"""Rubric-scored suite checks for this project's orchestration runs.

Adapted from the Module 3 starter (eval/test_rubric_suite.py). The judge
mechanism (claude -p, headless print mode) needed no adaptation -- it
already matches this project's actual tooling rather than the lesson's
OpenRouter-based orchestrator.py. The only real change is the pass/fail
logic: the starter used a sum-based aggregate threshold (a design this
project's Module 1 rubric explicitly rejected, since a sum lets one
excellent dimension paper over one broken one). This version uses a
per-dimension floor instead -- every dimension must individually clear
its own pass_threshold, with no aggregate check that could average a
failure away.

Run from the repository root:
    python3 eval/test_rubric_suite.py .eval-artifacts/runs/<your_run>.json
"""

import json
import sys
import subprocess

from test_deterministic import run_all_checks, load_json

RUBRIC_PATH = "eval/rubric.json"


def load_rubric(path):
    with open(path) as f:
        return json.load(f)


def call_judge(prompt):
    """Send a prompt to the agent-as-judge through Claude Code; return reply text.

    The container may have no internet egress for a general task, but Claude
    Code itself always needs real network access to reach the Anthropic API
    (see module3_doc's handbook entry on this) -- the judge runs through
    Claude Code in print mode either way, not a separate model API call.
    """
    completed = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"judge invocation failed: {completed.stderr.strip()}")
    envelope = json.loads(completed.stdout)
    return envelope["result"]


def parse_score(reply):
    """Extract the JSON score object from the judge's reply."""
    start = reply.find("{")
    if start == -1:
        raise ValueError(f"no JSON object found in judge reply: {reply[:200]}")
    depth = 0
    for i, ch in enumerate(reply[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(reply[start:i + 1])
    raise ValueError(f"unterminated JSON object in judge reply: {reply[:200]}")


def build_judge_prompt(dimension, transcript_text):
    """Compose the instruction the judge receives for one dimension."""
    return (
        "You are scoring the output of a multi-agent software workflow against "
        "one quality dimension. Read the run transcript and the dimension "
        "definition below, then score the output from 1 to 4 using the level "
        "descriptions. Base your score only on what the transcript actually "
        "shows -- do not assume something happened that isn't recorded in it. "
        "Return only a JSON object with the fields "
        '"dimension", "score" (an integer from 1 to 4), and "justification" '
        "(one or two sentences). Return nothing else.\n\n"
        f"DIMENSION: {dimension['name']}\n"
        f"WHAT IT MEASURES: {dimension['description']}\n"
        f"LEVELS:\n{json.dumps(dimension['levels'], indent=2)}\n\n"
        f"RUN TRANSCRIPT:\n{transcript_text}\n"
    )


def check_dimension(dimension, transcript_text):
    reply = call_judge(build_judge_prompt(dimension, transcript_text))
    score_obj = parse_score(reply)
    score = int(score_obj["score"])
    justification = score_obj.get("justification", "")
    passed = score >= dimension["pass_threshold"]
    return {
        "check": f"rubric:{dimension['name']}",
        "failure_mode": "quality (rubric)",
        "passed": passed,
        "score": score,
        "message": f"scored {score}/4 (needs {dimension['pass_threshold']}). {justification}",
    }


def collect_rubric_results(transcript_path):
    """Score every rubric dimension and return the structured results unprinted.

    No aggregate/sum check is added here -- per-dimension floor only. Overall
    pass/fail (computed in run_rubric_suite) is "every dimension individually
    passed," not a total score.
    """
    rubric = load_rubric(RUBRIC_PATH)
    transcript = load_json(transcript_path)
    transcript_text = json.dumps(transcript, indent=2)
    return [check_dimension(d, transcript_text) for d in rubric["dimensions"]]


def run_rubric_suite(transcript_path):
    # Gate: the rubric suite runs only if the deterministic checks all pass.
    if run_all_checks(transcript_path) != 0:
        print("\nDeterministic checks failed; skipping the rubric suite.")
        print("Fix the deterministic failures first. A rubric score on a malformed run is not meaningful.")
        return 1

    print("\nRunning rubric suite (each dimension is one model call)...\n")
    results = collect_rubric_results(transcript_path)
    passed = sum(r["passed"] for r in results)
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"[{mark}] {r['check']}: {r['message']}")
    print(f"\n{passed}/{len(results)} rubric dimensions passed (per-dimension floor -- all must pass individually).")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: test_rubric_suite.py <transcript_path>")
        sys.exit(2)
    sys.exit(run_rubric_suite(sys.argv[1]))
