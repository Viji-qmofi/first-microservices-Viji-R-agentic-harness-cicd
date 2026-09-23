# Enforcement Verification

## Layer 1: Container Permissions

**Role:** reviewer

**Workspace check**

**Command:** `touch /workspace/should-fail.txt`

**Output:**
```
touch: cannot touch '/workspace/should-fail.txt': Read-only file system
```

**Result:** blocked as expected.

---

**Role:** implementer

**Workspace check**

**Command:** `touch /workspace/ok-to-write.txt && rm /workspace/ok-to-write.txt`

**Output:** (no output -- silent success)

**Result:** succeeded as expected.

**Memory (.memory/knowledge) check, even under a read-write role**

**Command:** `touch /workspace/.memory/knowledge/should-fail.txt`

**Output:**
```
touch: cannot touch '/workspace/.memory/knowledge/should-fail.txt': Read-only file system
```

**Result:** blocked as expected -- confirms the dedicated `.memory/knowledge` `:ro` mount overrides the role's general read-write workspace access, not merely coinciding with it. See docs/governance-policy.md for why this project uses a single workspace read/write dimension rather than a separate memory-volume dimension: `.memory/` lives inside `/workspace`, and knowledge specifically is protected by its own always-`:ro` sub-mount regardless of the role's overall mode.

---

**Role:** planner

**Workspace check**

**Command:** `touch /workspace/should-fail.txt`

**Output:**
```
touch: cannot touch '/workspace/should-fail.txt': Read-only file system
```

**Result:** blocked as expected.

---

**Role:** spring-boot-reviewer

**Workspace check**

**Command:** `touch /workspace/should-fail.txt`

**Output:**
```
touch: cannot touch '/workspace/should-fail.txt': Read-only file system
```

**Result:** blocked as expected.

---

**Role:** orchestrator

**Workspace check**

**Command:** `touch /workspace/ok-to-write.txt && rm /workspace/ok-to-write.txt`

**Output:** (no output -- silent success)

**Result:** succeeded as expected.

All five roles' container-level permissions confirmed to match their `docs/governance-policy.md` entries: `implementer` and `orchestrator` read-write; `planner`, `reviewer`, and `spring-boot-reviewer` read-only. `.memory/knowledge` confirmed read-only regardless of role.
