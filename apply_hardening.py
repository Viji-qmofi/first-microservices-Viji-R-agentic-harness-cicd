#!/usr/bin/env python3
"""CI hardening: image-build retry with a mirror fallback, and integrity coverage for the governed gate.

Run from the repository root:   python3 apply_hardening.py

Safe to re-run: every step checks whether it has already been applied. It preserves each
file's existing line endings (LF or CRLF).
"""
import re
import sys
from pathlib import Path


def load(path):
    raw = Path(path).read_bytes().decode("utf-8")
    return raw.replace("\r\n", "\n"), ("\r\n" if "\r\n" in raw else "\n")


def save(path, text, eol):
    Path(path).write_bytes(text.replace("\n", eol).encode("utf-8"))


def fail(msg):
    print("STOPPED: " + msg)
    sys.exit(1)


def step(n, label, status):
    print(f"{n}. {label}: {status}")


MIRROR = "public.ecr.aws/docker/library/maven:3.9-eclipse-temurin-21"

# 1. Dockerfile: make the base image overridable, with the same default as before --------------
p = "Dockerfile"
t, eol = load(p)
OLD_FROM = "FROM maven:3.9-eclipse-temurin-21\n"
NEW_FROM = "ARG BASE_IMAGE=maven:3.9-eclipse-temurin-21\nFROM ${BASE_IMAGE}\n"
if t.startswith(NEW_FROM):
    step(1, "Dockerfile base image argument", "already applied")
elif t.startswith(OLD_FROM):
    save(p, NEW_FROM + t[len(OLD_FROM):], eol)
    step(1, "Dockerfile base image argument", "applied (default unchanged, so local builds behave as before)")
else:
    fail("Dockerfile does not start with the expected FROM line; check it by hand")

# 2. ci.yml: every image build retries, then falls back to the mirror --------------------------
p = ".github/workflows/ci.yml"
t, eol = load(p)
OLD_STEP = re.compile(
    r"(      - name: )Build course container\n((?:        if: [^\n]+\n)?)        run: docker build -t agentic_engineer_4 \.\n"
)
NEW_NAME = "Build course container (retry, then fall back to a mirror)"
def new_step(m):
    return (
        f"{m.group(1)}{NEW_NAME}\n{m.group(2)}"
        "        run: |\n"
        "          for attempt in 1 2 3; do\n"
        "            docker build -t agentic_engineer_4 . && exit 0\n"
        "            echo \"Build attempt $attempt failed.\"\n"
        "            if [ \"$attempt\" -lt 3 ]; then sleep 30; fi\n"
        "          done\n"
        "          echo \"Falling back to the AWS ECR Public mirror of the base image.\"\n"
        f"          docker build --build-arg BASE_IMAGE={MIRROR} -t agentic_engineer_4 .\n"
    )
found = len(OLD_STEP.findall(t))
done = t.count(NEW_NAME)
if found == 4 and done == 0:
    save(p, OLD_STEP.sub(new_step, t), eol)
    step(2, "ci.yml image-build steps", "applied (4 steps)")
elif found == 0 and done == 4:
    step(2, "ci.yml image-build steps", "already applied")
else:
    fail(f"ci.yml: expected 4 plain build steps (found {found}) or 4 already converted (found {done})")

# 3. Integrity checker: the governed gate is a required gate, so protect it too ----------------
p = "scripts/check-pipeline-integrity.py"
t, eol = load(p)
OLD_SET = 'GATING_JOBS = {"policy-gate", "eval-gate", "pipeline-integrity"}'
NEW_SET = 'GATING_JOBS = {"policy-gate", "eval-gate", "governed-file-gate", "pipeline-integrity"}'
if NEW_SET in t:
    step(3, "integrity checker gating set", "already applied")
elif OLD_SET in t:
    save(p, t.replace(OLD_SET, NEW_SET), eol)
    step(3, "integrity checker gating set", "applied (governed-file-gate added)")
else:
    fail("check-pipeline-integrity.py: GATING_JOBS line not found in either form")

# 4. docs/ci-step-design.md ---------------------------------------------------------------------
p = "docs/ci-step-design.md"
t, eol = load(p)
changed = []
OLD_DOES = "(1) none of `policy-gate`, `eval-gate`, or `pipeline-integrity` itself has `continue-on-error: true`"
NEW_DOES = "(1) none of `policy-gate`, `eval-gate`, `governed-file-gate`, or `pipeline-integrity` itself has `continue-on-error: true`"
if OLD_DOES in t:
    t = t.replace(OLD_DOES, NEW_DOES)
    changed.append("integrity coverage")
elif NEW_DOES not in t:
    fail("ci-step-design.md: integrity 'Does' text not found in either form")
ANCHOR = "A conditional gate that is not triggered still reports green, with every step skipped. Read a job's step list, not only its color.\n"
PARA = ("\nEvery job that needs the container image builds it with up to three attempts and then once more from an AWS ECR Public mirror of the base image, "
        "because Docker Hub rate-limits the shared IP addresses of GitHub's runners (it returned `429 Too Many Requests` on the pull request for the audit-log template update). "
        "The fallback still fails closed: if the mirror build fails, so does the job.\n")
if "Every job that needs the container image builds it" in t:
    pass
elif ANCHOR in t:
    t = t.replace(ANCHOR, ANCHOR + PARA)
    changed.append("build retry paragraph")
else:
    fail("ci-step-design.md: anchor paragraph not found")
if changed:
    save(p, t, eol)
step(4, "docs/ci-step-design.md", ", ".join(changed) if changed else "already applied")

print("\nDone. Next:  git diff --stat")
