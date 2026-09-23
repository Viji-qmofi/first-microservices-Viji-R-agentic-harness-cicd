"""Deterministic harness checks for this project's orchestration runs.

Adapted from the Module 3 starter (eval/test_deterministic.py) for the
actual Target Codebase System used throughout this course: planner and
implementer are the only implemented subagents; reviewer and tester are
designed but not implemented, and the Orchestrator (top-level session)
stands in for both, recorded as roles "orchestrator_review" and
"orchestrator_test" rather than fictional subagent invocations.

Run from the repository root:
    python3 eval/test_deterministic.py .eval-artifacts/runs/<your_run>.json
"""

import json
import os
import sys

# Artifacts the checks read.
# Audit logs are per-transcript: same directory and basename as the transcript,
# with a .log extension (e.g. HO-02.json -> HO-02.log). In practice this means
# copying the relevant slice of .memory/storage/storage-audit.log alongside
# the transcript when a run is submitted as evidence.
GRANT_MAP_PATH = "module3_doc/routing-and-tool-grant-map.json"

# Values the schema, retrieval, and budget checks compare against.
ALLOWED_CLASSIFICATIONS = {"public", "internal", "confidential", "secret"}
WRITE_OPERATIONS = {"write_entry", "update_entry", "delete_entry"}

# Budgets set from real measured runs (see module3_doc/lessons-learned-workflow-run.md
# and prior iteration logs), not arbitrary defaults. duration_seconds is active
# agent/orchestrator processing time only -- it deliberately excludes time spent
# waiting on the human-approval checkpoint, since that pause is a designed part
# of this system, not automation latency. Observed real runs ranged from about
# 2m41s to 18m41s of active time; 900s gives headroom while still treating the
# 18m41s outlier as a real, worth-investigating result rather than hiding it
# behind an inflated budget.
MAX_DURATION_SECONDS = 900
# Tracked as real dollar cost (cost_usd), not raw token count, matching how
# cost has been measured consistently throughout this course via isolated
# /status checks. Single-role runs have cost $0.30-$1.10; 2.00 covers a full
# multi-role orchestrated run with headroom without being unbounded.
MAX_COST_USD = 2.00
SIMILARITY_FLOOR = 0.65

# planner has no storage-server access at all in this system (retrieval only).
# implementer has write_entry only -- not read_entry/update_entry/delete_entry.
# reviewer/tester are not yet implemented as real subagents; forbidden from
# all storage operations until they are designed with real grants.
# orchestrator_review may retrieve (stands in for reviewer's context-gathering)
# but must not write to storage -- writing is implementer's job alone.
# orchestrator_test performs no storage or retrieval operations at all.
FORBIDDEN_OPERATIONS = {
    "planner": {"write_entry", "read_entry", "list_entries", "update_entry", "delete_entry"},
    "implementer": {"read_entry", "list_entries", "update_entry", "delete_entry"},
    "reviewer": {"write_entry", "read_entry", "list_entries", "update_entry", "delete_entry"},
    "tester": {"write_entry", "read_entry", "list_entries", "update_entry", "delete_entry"},
    "orchestrator_review": {"write_entry", "read_entry", "list_entries", "update_entry", "delete_entry"},
    "orchestrator_test": {"write_entry", "read_entry", "list_entries", "update_entry", "delete_entry", "retrieve"},
}


def load_audit_log(path):
    """Read the audit log. It is JSON Lines: one JSON object per line."""
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def load_json(path):
    """Read a single JSON document, such as the transcript or grant map."""
    with open(path) as f:
        return json.load(f)


def result(check, failure_mode, passed, message):
    """Build a structured outcome for one check."""
    return {
        "check": check,
        "failure_mode": failure_mode,
        "passed": passed,
        "message": message,
    }


def check_write_classifications(audit_entries):
    """Schema validation: every storage write carries a valid classification."""
    bad = [
        e for e in audit_entries
        if e.get("operation") in WRITE_OPERATIONS
        and e.get("classification") not in ALLOWED_CLASSIFICATIONS
    ]
    if bad:
        return result(
            "write_classifications", "schema validation", False,
            f"{len(bad)} write(s) had a missing or invalid classification.",
        )
    return result(
        "write_classifications", "schema validation", True,
        "All storage writes carried a valid classification.",
    )


def check_retrieval_citations(transcript):
    """Schema validation: every retrieval result includes its citation fields."""
    missing = []
    for event in transcript.get("events", []):
        if event.get("type") == "tool_call" and event.get("tool") == "retrieve":
            for r in event.get("result", {}).get("results", []):
                if "source_document" not in r or "chunk_index" not in r:
                    missing.append(r)
    if missing:
        return result(
            "retrieval_citations", "schema validation / retrieval miss", False,
            f"{len(missing)} retrieval result(s) were missing source_document or chunk_index.",
        )
    return result(
        "retrieval_citations", "schema validation / retrieval miss", True,
        "Every retrieval result carried source_document and chunk_index.",
    )


# check_output_schema (and REQUIRED_OUTPUT_FIELDS) from the starter file were
# removed rather than adapted. The starter assumed every subagent produces a
# structured output_document dict with fixed fields (summary, citation_list).
# planner and implementer in this system produce free-text prose per their
# actual agent definitions (a numbered plan + file list; a change summary),
# not a structured document -- retrofitting a rigid schema onto prose isn't a
# good fit right now. check_retrieval_citations already covers this project's
# "schema validation / retrieval result" requirement on its own.


def check_no_unknown_caller(audit_entries):
    """Traceability: every audited operation names the role that made it."""
    unknown = [e for e in audit_entries if e.get("calling_role") in (None, "unknown")]
    if unknown:
        return result(
            "no_unknown_caller", "traceability", False,
            f"{len(unknown)} audit entr(ies) had calling_role 'unknown'.",
        )
    return result(
        "no_unknown_caller", "traceability", True,
        "Every audited operation identified its calling role.",
    )


def check_audit_matches_writes(transcript, audit_entries):
    """Traceability: one audit entry per write the transcript reports."""
    writes_in_transcript = [
        e for e in transcript.get("events", [])
        if e.get("type") == "tool_call" and e.get("tool") in WRITE_OPERATIONS
    ]
    writes_in_audit = [e for e in audit_entries if e.get("operation") in WRITE_OPERATIONS]
    if len(writes_in_transcript) != len(writes_in_audit):
        return result(
            "audit_matches_writes", "traceability", False,
            f"transcript reports {len(writes_in_transcript)} write(s) but the "
            f"audit log records {len(writes_in_audit)}.",
        )
    return result(
        "audit_matches_writes", "traceability", True,
        "Audit log entries match the writes in the transcript.",
    )


def check_tool_grants(transcript, grant_map):
    """Security: no subagent/orchestrator step called a tool outside its grant list.

    This check is a permanent fixture. Every tool grant added in any future
    calibration cycle is re-verified here, on every run. This is the same
    category of check that caught the real gap found during Exercise 3.2's
    Step 6 -- coursetools' file_read/file_write/codebase_search reaching
    .memory/ directly -- so the grant map should list coursetools operations
    as well as storage/retrieval ones wherever a role legitimately has them.

    Known limitation: current transcript recording (CLAUDE.md's Evaluation
    Transcript Recording section) only asks for retrieve/write_entry tool_call
    events to be captured explicitly. coursetools calls (file_read,
    file_write, codebase_search) are not yet reliably recorded as tool_call
    events, so this check cannot yet verify those grants from a transcript
    alone -- recorded as a known gap, not silently assumed solved.
    """
    violations = []
    for event in transcript.get("events", []):
        if event.get("type") != "tool_call":
            continue
        role = event.get("role")
        tool = event.get("tool")
        if tool not in grant_map.get(role, []):
            violations.append(f"{role} called {tool}")
    if violations:
        return result(
            "tool_grants", "over-broad tool grant", False,
            "tool call(s) outside the grant list: " + "; ".join(violations) + ".",
        )
    return result(
        "tool_grants", "over-broad tool grant", True,
        "Every recorded tool call was within the calling role's grant list.",
    )


def check_forbidden_operations(audit_entries):
    """Over-broad grant: some role and operation pairs are always forbidden."""
    violations = [
        f"{e.get('calling_role')} performed {e.get('operation')}"
        for e in audit_entries
        if e.get("operation") in FORBIDDEN_OPERATIONS.get(e.get("calling_role"), set())
    ]
    if violations:
        return result(
            "forbidden_operations", "over-broad tool grant", False,
            "forbidden operation(s) in the audit log: " + "; ".join(violations) + ".",
        )
    return result(
        "forbidden_operations", "over-broad tool grant", True,
        "no role performed a forbidden operation.",
    )


def check_required_roles(transcript, expected_path):
    """Routing: every required subagent/orchestrator step appears in the run."""
    roles_seen = [
        e["role"] for e in transcript.get("events", [])
        if e.get("type") in ("subagent", "orchestrator_step")
    ]
    missing = [r for r in expected_path if r not in roles_seen]
    if missing:
        return result(
            "required_roles", "routing misfire", False,
            f"required role(s) absent from the run: {missing}.",
        )
    return result("required_roles", "routing misfire", True, "All required steps ran.")


def check_role_order(transcript, expected_path):
    """Routing: required steps ran in the expected order.

    Assumes each required role runs once on the expected path.
    """
    roles_seen = [
        e["role"] for e in transcript.get("events", [])
        if e.get("type") in ("subagent", "orchestrator_step")
    ]
    filtered = [r for r in roles_seen if r in expected_path]
    if filtered != expected_path:
        return result(
            "role_order", "routing misfire", False,
            f"expected order {expected_path} but saw {filtered}.",
        )
    return result("role_order", "routing misfire", True, "Steps ran in the expected order.")


def check_no_context_bleed(transcript):
    """Context bleed: a canary must not surface in later handoffs or outputs."""
    canary = transcript.get("canary")
    if not canary:
        return result(
            "context_bleed", "context bleed", True,
            "no canary planted; bleed check not exercised this run.",
        )
    origin_step = transcript.get("canary_origin_step", 1)
    leaked = []
    for event in transcript.get("events", []):
        if event.get("type") not in ("subagent", "orchestrator_step") or event.get("step", 0) <= origin_step:
            continue
        text = (event.get("handoff", "") or "") + " " + str(event.get("output", ""))
        if canary in text:
            leaked.append(event.get("role"))
    if leaked:
        return result(
            "context_bleed", "context bleed", False,
            f"planted marker leaked into later step(s): {leaked}.",
        )
    return result(
        "context_bleed", "context bleed", True,
        "planted marker did not leak past its origin step.",
    )


def check_no_reviewer_conflict(transcript):
    """Conflicting reviewers: opposite verdicts require human escalation.

    Trivially passes under the current single-reviewer (Orchestrator-
    standing-in) implementation -- fewer than two reviewers ever run, so no
    conflict is possible. This is a true but uninformative result, not
    evidence the system handles a real conflict correctly; see
    module3_doc/holdout-task-set.md's Known Gaps section (HO-05). Genuinely
    exercising this check requires the upcoming lab's temporary
    reviewer_strict/reviewer_lenient setup.
    """
    reviews = [
        e for e in transcript.get("events", [])
        if e.get("type") == "subagent" and e.get("role", "").startswith("reviewer")
    ]
    if len(reviews) < 2:
        return result(
            "reviewer_conflict", "conflicting reviewers", True,
            "fewer than two reviewers ran; no conflict possible.",
        )
    verdicts = {}
    for r in reviews:
        for item in r.get("review_items", []):
            verdicts.setdefault(item["section"], set()).add(item["verdict"])
    conflicts = [s for s, v in verdicts.items() if "approve" in v and "reject" in v]
    if conflicts and not transcript.get("escalated_to_human", False):
        return result(
            "reviewer_conflict", "conflicting reviewers", False,
            f"unresolved contradictory verdicts on: {conflicts}.",
        )
    return result(
        "reviewer_conflict", "conflicting reviewers", True,
        "no unresolved reviewer conflicts.",
    )


def check_similarity_floor(transcript):
    """Retrieval miss: weak vector results should not be returned as matches.

    Uses similarity_score, matching this project's actual retrieval server
    field name (confirmed empirically during Exercise 3.2 ground-truth
    testing) -- the starter file's "similarity" field name does not match
    what this server actually returns.
    """
    offenders = []
    for event in transcript.get("events", []):
        if event.get("type") == "tool_call" and event.get("tool") == "retrieve":
            for r in event.get("result", {}).get("results", []):
                score = r.get("similarity_score")
                if r.get("retrieval_method") == "vector" and score is not None and score < SIMILARITY_FLOOR:
                    offenders.append(score)
    if offenders:
        return result(
            "similarity_floor", "retrieval miss", False,
            f"{len(offenders)} vector result(s) below the {SIMILARITY_FLOOR} floor were returned without fallback.",
        )
    return result(
        "similarity_floor", "retrieval miss", True,
        "no sub-floor vector results were returned as matches.",
    )


def check_latency(transcript):
    """Latency: the run's active processing time stayed within budget.

    duration_seconds is expected to exclude time spent waiting on the
    human-approval checkpoint -- see the module docstring.
    """
    duration = transcript.get("duration_seconds")
    if duration is None or duration > MAX_DURATION_SECONDS:
        return result(
            "latency", "latency", False,
            f"run duration {duration}s is missing or over the {MAX_DURATION_SECONDS}s budget.",
        )
    return result("latency", "latency", True, f"run took {duration}s, within budget.")


def check_cost(transcript):
    """Cost: the run stayed within the configured dollar budget."""
    cost = transcript.get("cost_usd")
    if cost is None or cost > MAX_COST_USD:
        return result(
            "cost", "cost", False,
            f"cost ${cost} is missing or over the ${MAX_COST_USD} budget.",
        )
    return result("cost", "cost", True, f"run cost ${cost}, within budget.")


def collect_results(transcript_path):
    """Run every deterministic check and return the structured results unprinted."""
    audit_log_path = os.path.splitext(transcript_path)[0] + ".log"
    audit_entries = load_audit_log(audit_log_path)
    transcript = load_json(transcript_path)
    grant_map = load_json(GRANT_MAP_PATH)
    expected_path = transcript["expected_path"]
    return [
        check_write_classifications(audit_entries),
        check_retrieval_citations(transcript),
        check_no_unknown_caller(audit_entries),
        check_audit_matches_writes(transcript, audit_entries),
        check_tool_grants(transcript, grant_map),
        check_forbidden_operations(audit_entries),
        check_required_roles(transcript, expected_path),
        check_role_order(transcript, expected_path),
        check_no_context_bleed(transcript),
        check_no_reviewer_conflict(transcript),
        check_similarity_floor(transcript),
        check_latency(transcript),
        check_cost(transcript),
    ]


def run_all_checks(transcript_path):
    """Print the deterministic report and return 0 if all checks passed."""
    results = collect_results(transcript_path)
    passed = sum(r["passed"] for r in results)
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"[{mark}] {r['check']} ({r['failure_mode']}): {r['message']}")
    print(f"\n{passed}/{len(results)} deterministic checks passed.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: test_deterministic.py <transcript_path>")
        sys.exit(2)
    sys.exit(run_all_checks(sys.argv[1]))
