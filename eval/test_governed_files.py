"""Governed-file checks.

The first four tests are structural: required files exist.

The rest compare what the governance policy DECLARES against what is actually
CONFIGURED elsewhere: the three MCP allow-lists, each agent's tools: line, the
skills directory, and the evaluation harness's own copies of the grants
(module3_doc/routing-and-tool-grant-map.json and FORBIDDEN_OPERATIONS in
eval/test_deterministic.py). The policy is the single source of truth; every
other place that encodes a grant must agree with it exactly.

Limits, stated plainly: this checks declared-versus-configured grants, not
runtime behavior, and roles are still self-declared strings (ADR-005).
"""
import ast
import json
import re
from pathlib import Path


ROOT = Path(".")

STORAGE_OPS = ["write_entry", "read_entry", "list_entries", "update_entry", "delete_entry", "audit_read"]
RETRIEVAL_OPS = ["retrieve"]
COURSETOOLS_OPS = ["file_read", "file_write", "codebase_search"]
ORCHESTRATOR_REVIEW_STEPS = ["orchestrator_plan_review", "orchestrator_diff_review"]
ORCHESTRATOR_TEST_STEP = "orchestrator_test"


# --------------------------------------------------------------------------
# Structural checks (original)
# --------------------------------------------------------------------------

def test_governed_artifacts_exist():
    required = [
        "docs/governance-policy.md",
        "docs/ci-step-design.md",
    ]

    missing = [path for path in required if not (ROOT / path).exists()]
    assert not missing, f"Missing governed artifacts: {missing}"


def test_governed_directories_are_versioned_when_present():
    # These do not all have to exist in every starter repo, but if they do,
    # they should be real directories rather than generated CI output.
    optional_dirs = [
        ".agents",
        ".skills",
        "mcp-servers",
        "eval",
        "scripts",
    ]

    for dirname in optional_dirs:
        path = ROOT / dirname
        if path.exists():
            assert path.is_dir(), f"{dirname} should be a directory"


def test_reviewer_script_exists():
    assert (ROOT / "scripts" / "run-reviewer.py").exists(), (
        "Missing scripts/run-reviewer.py"
    )


def test_audit_script_exists():
    assert (ROOT / "scripts" / "build-audit-trail.py").exists(), (
        "Missing scripts/build-audit-trail.py"
    )


# --------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------

def _read(path):
    return (ROOT / path).read_text(encoding="utf-8").replace("\r\n", "\n")


def _json(path):
    return json.loads(_read(path))


def _section(body, heading):
    """Text under '### <heading>' up to the next '### ' heading (or the end)."""
    m = re.search(
        r"^### " + re.escape(heading) + r"[ \t]*\n(.*?)(?=^### |\Z)", body, re.M | re.S
    )
    return m.group(1) if m else ""


OP_ROW = re.compile(r"^\|\s*([a-z_]+)\s*\|\s*([a-z]+)\s*\|\s*(YES|NO)\s*\|", re.M)
SKILL_ROW = re.compile(r"^\|\s*([a-z0-9-]+)\s*\|\s*(YES|NO)\s*\|", re.M)


def load_policy():
    """Parse docs/governance-policy.md into {role: {...}}."""
    text = _read("docs/governance-policy.md")
    parts = re.split(r"^## Role: (.+?)[ \t]*$", text, flags=re.M)
    roles = {}
    for name, body in zip(parts[1::2], parts[2::2]):
        body = re.split(r"^## (?!Role:)", body, flags=re.M)[0]  # stop at the next non-role "## " heading
        grants, duplicates = {}, []
        for op, server, yn in OP_ROW.findall(_section(body, "MCP server and operation access")):
            if (server, op) in grants:
                duplicates.append(f"{server}.{op}")
            grants[(server, op)] = (yn == "YES")
        version = re.search(r"\*\*Version:\*\*\s*(v[\w.]+)", body)
        defined = re.search(r"\*\*Defined in:\*\*\s*(.+)", body)
        ceiling = re.search(r"\*\*Maximum level:\*\*\s*([A-Za-z/]+)", body)
        agent_file = re.search(r"`agents/([\w-]+\.md)`", defined.group(1)) if defined else None
        roles[name.strip()] = {
            "grants": grants,
            "duplicates": duplicates,
            "version": version.group(1) if version else None,
            "defined_in": defined.group(1).strip() if defined else None,
            "agent_file": agent_file.group(1) if agent_file else None,
            "ceiling": ceiling.group(1).lower() if ceiling else None,
            "skills": {s: yn == "YES" for s, yn in SKILL_ROW.findall(_section(body, "Skill activation scope"))},
        }
    return roles


def load_frontmatter(path):
    text = Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fm = {}
    if m:
        for line in m.group(1).split("\n"):
            km = re.match(r"([A-Za-z_]+):[ \t]*(.*)$", line)  # top-level keys only; indented lines are ignored
            if km:
                fm[km.group(1)] = km.group(2).strip()
    return fm


def load_forbidden_operations():
    """Read FORBIDDEN_OPERATIONS from the harness source without importing it."""
    tree = ast.parse(_read("eval/test_deterministic.py"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "FORBIDDEN_OPERATIONS" for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("FORBIDDEN_OPERATIONS not found in eval/test_deterministic.py")


def _granted_ops(role):
    return {op for (_server, op), yes in role["grants"].items() if yes}


def _denied_storage_retrieval_ops(role):
    return {op for (server, op), yes in role["grants"].items() if server in ("storage", "retrieval") and not yes}


def _fail_if(problems, header):
    assert not problems, header + "\n  - " + "\n  - ".join(problems)


# --------------------------------------------------------------------------
# Declared policy vs configured enforcement
# --------------------------------------------------------------------------

def test_policy_structure_is_parseable():
    """Shape guard: if the policy's format changes, fail loudly instead of comparing nothing."""
    policy = load_policy()
    problems = []
    if len(policy) < 6:
        problems.append(f"expected at least 6 '## Role:' sections, found {len(policy)}: {sorted(policy)}")
    expected_rows = [("storage", op) for op in STORAGE_OPS] + [("retrieval", op) for op in RETRIEVAL_OPS]
    for name, role in policy.items():
        if not role["version"]:
            problems.append(f"{name}: no '**Version:**' line found")
        if not role["defined_in"]:
            problems.append(f"{name}: no '**Defined in:**' line found")
        missing = [f"{s}.{o}" for s, o in expected_rows if (s, o) not in role["grants"]]
        if missing:
            problems.append(f"{name}: missing policy rows for {missing}")
        if role["duplicates"]:
            problems.append(f"{name}: duplicate policy rows for {role['duplicates']}")
        if role["grants"].get(("retrieval", "retrieve")) and not role["ceiling"]:
            problems.append(f"{name}: retrieve is granted but no '**Maximum level:**' is stated")
    _fail_if(problems, "Policy document does not have the structure these tests rely on:")


def test_storage_policy_matches_allow_list():
    policy = load_policy()
    allow = _json("mcp-servers/storage/allow-list.json")
    problems = []
    for name, role in policy.items():
        for op in STORAGE_OPS:
            declared = role["grants"].get(("storage", op), False)
            enforced = name in allow.get(op, [])
            if declared != enforced:
                problems.append(f"{name} / {op}: policy says {'YES' if declared else 'NO'}, storage allow-list says {'granted' if enforced else 'denied'}")
    for op, roles in allow.items():
        if op not in STORAGE_OPS:
            problems.append(f"storage allow-list has operation '{op}' that the policy does not cover")
        for r in roles:
            if r not in policy:
                problems.append(f"storage allow-list grants {op} to '{r}', which has no policy section")
    _fail_if(problems, "Storage policy and allow-list disagree:")


def test_retrieval_policy_matches_allow_list():
    policy = load_policy()
    allow = _json("mcp-servers/retrieval/allow-list.json").get("retrieve", {})
    problems = []
    for name, role in policy.items():
        declared = role["grants"].get(("retrieval", "retrieve"), False)
        entry = allow.get(name, {})
        enforced = bool(entry.get("granted"))
        if declared != enforced:
            problems.append(f"{name} / retrieve: policy says {'YES' if declared else 'NO'}, retrieval allow-list says {'granted' if enforced else 'denied'}")
        elif declared and role["ceiling"] != str(entry.get("classification_ceiling", "")).lower():
            problems.append(f"{name}: policy ceiling '{role['ceiling']}', allow-list ceiling '{entry.get('classification_ceiling')}'")
    for r in allow:
        if r not in policy:
            problems.append(f"retrieval allow-list names '{r}', which has no policy section")
    _fail_if(problems, "Retrieval policy and allow-list disagree:")


def test_coursetools_policy_matches_allow_list():
    policy = load_policy()
    allow = _json("mcp-servers/coursetools/roles.allowlist.json")
    problems = []
    for name, role in policy.items():
        for op in COURSETOOLS_OPS:
            if ("coursetools", op) not in role["grants"]:
                problems.append(f"{name} / {op}: no coursetools row in the policy")
                continue
            declared = role["grants"][("coursetools", op)]
            enforced = name in allow.get(op, [])
            if declared != enforced:
                problems.append(f"{name} / {op}: policy says {'YES' if declared else 'NO'}, coursetools allow-list says {'granted' if enforced else 'denied'}")
    for op, roles in allow.items():
        if op not in COURSETOOLS_OPS and roles:
            problems.append(f"coursetools allow-list grants '{op}' to {roles}, but the policy grants that operation to no role")
        for r in roles:
            if r not in policy:
                problems.append(f"coursetools allow-list grants {op} to '{r}', which has no policy section")
    _fail_if(problems, "Coursetools policy and allow-list disagree:")


def test_agent_files_match_policy():
    policy = load_policy()
    problems = []
    named_files = set()
    for name, role in policy.items():
        if not role["agent_file"]:
            continue  # e.g. the orchestrator is defined in CLAUDE.md, not an agent file
        named_files.add(role["agent_file"])
        path = ROOT / "agents" / role["agent_file"]
        if not path.exists():
            problems.append(f"{name}: policy names agents/{role['agent_file']}, which does not exist")
            continue
        fm = load_frontmatter(path)
        if fm.get("name") != name:
            problems.append(f"{name}: agents/{role['agent_file']} has name '{fm.get('name')}'")
        if fm.get("version") != role["version"]:
            problems.append(f"{name}: policy version {role['version']}, agent file version {fm.get('version')}")
        tools = {t.strip() for t in fm.get("tools", "").split(",") if t.strip().startswith("mcp__")}
        wired = {tuple(t.split("__", 2)[1:]) for t in tools}  # (server, op)
        granted = {key for key, yes in role["grants"].items() if yes}
        for server, op in sorted(wired - granted):
            problems.append(f"{name}: agent file lists {server}.{op}, but the policy does not grant it")
        for server, op in sorted(granted - wired):
            problems.append(f"{name}: policy grants {server}.{op}, but the agent file's tools: line does not include it")
    for path in sorted((ROOT / "agents").glob("*.md")):
        if path.name not in named_files:
            problems.append(f"agents/{path.name} is not named by any policy role")
    _fail_if(problems, "Agent definitions and policy disagree:")


def test_every_skill_has_a_policy_row_for_every_role():
    policy = load_policy()
    skills = sorted(load_frontmatter(p).get("name") for p in (ROOT / "skills").glob("*/SKILL.md"))
    problems = []
    assert skills, "No skills found under skills/*/SKILL.md"
    for name, role in policy.items():
        for skill in skills:
            if skill not in role["skills"]:
                problems.append(f"{name}: no skill-activation row for '{skill}'")
        for skill in role["skills"]:
            if skill not in skills:
                problems.append(f"{name}: skill row '{skill}' matches no skill under skills/")
    _fail_if(problems, "Skill activation tables and the skills directory disagree:")


# --------------------------------------------------------------------------
# The evaluation harness's own copies of the grants
# --------------------------------------------------------------------------

def test_harness_grant_map_matches_policy():
    policy = load_policy()
    grant_map = _json("module3_doc/routing-and-tool-grant-map.json")
    orchestrator = _granted_ops(policy["orchestrator"]) if "orchestrator" in policy else set()
    expected = {name: _granted_ops(role) for name, role in policy.items()}
    for step in ORCHESTRATOR_REVIEW_STEPS:
        expected[step] = orchestrator
    expected[ORCHESTRATOR_TEST_STEP] = set()
    problems = []
    for key in sorted(set(expected) | set(grant_map)):
        if key not in grant_map:
            problems.append(f"harness grant map has no entry for '{key}'")
        elif key not in expected:
            problems.append(f"harness grant map has entry '{key}', which is not a policy role or an orchestrator step")
        elif set(grant_map[key]) != expected[key]:
            problems.append(f"{key}: policy grants {sorted(expected[key])}, harness map lists {sorted(grant_map[key])}")
    _fail_if(problems, "module3_doc/routing-and-tool-grant-map.json disagrees with the policy:")


def test_harness_forbidden_operations_match_policy():
    policy = load_policy()
    forbidden = load_forbidden_operations()
    orchestrator = _denied_storage_retrieval_ops(policy["orchestrator"]) if "orchestrator" in policy else set()
    expected = {name: _denied_storage_retrieval_ops(role) for name, role in policy.items()}
    for step in ORCHESTRATOR_REVIEW_STEPS:
        expected[step] = orchestrator
    expected[ORCHESTRATOR_TEST_STEP] = set(STORAGE_OPS + RETRIEVAL_OPS)
    problems = []
    for key in sorted(set(expected) | set(forbidden)):
        if key not in forbidden:
            problems.append(f"FORBIDDEN_OPERATIONS has no entry for '{key}'")
        elif key not in expected:
            problems.append(f"FORBIDDEN_OPERATIONS has entry '{key}', which is not a policy role or an orchestrator step")
        elif set(forbidden[key]) != expected[key]:
            problems.append(f"{key}: policy denies {sorted(expected[key])}, FORBIDDEN_OPERATIONS lists {sorted(forbidden[key])}")
    _fail_if(problems, "FORBIDDEN_OPERATIONS in eval/test_deterministic.py disagrees with the policy:")
