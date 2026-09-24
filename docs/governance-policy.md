# Agent Governance Policy

Version: v1.0.0
Last updated: 2026-09-23
Reviewed by: Viji Ramu

## Policy basis

This policy is derived from:

- The routing-and-tool-grant map (docs/routing-and-tool-grant-map.md)
- Near-miss patterns observed in calibration (module3_doc/calibration-log.md)
- Least-privilege defaults applied to all roles

## Least-privilege default

Every role starts with no access. All grants below are explicit and justified.

Any access not explicitly granted to a role is denied by default.

To widen access, open a pull request with: the proposed grant, a concrete justification, and confirmation that the grant does not conflict with any near-miss pattern in the calibration log.

## Role: planner

**Version:** v2  
**Defined in:** `agents/planner.md`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason |
|---|---|---|---|
| write_entry | storage | NO | Planner produces a plan only; it never writes to project state. |
| read_entry | storage | NO | Not required for planner's job -- retrieve covers its context needs. |
| list_entries | storage | NO | Not required for planner's job. |
| update_entry | storage | NO | Planner must not change project state. |
| delete_entry | storage | NO | Planner must not remove project state. |
| audit_read | storage | NO | Audit inspection is owned by the orchestrator. |
| retrieve | retrieval | YES | Planner retrieves prior lessons before proposing an approach (CLAUDE.md, Orchestrator Instructions). |

### Skill activation scope

| Skill | Activation permitted | Reason if denied |
|---|---|---|
| summarize-session | YES | Planner may summarize its own planning work. |

### Data classification ceiling

**Maximum level:** internal  
**Reason:** Planner's own instructions require it to always pass `classification_ceiling="internal"` and never request higher (CLAUDE.md). This is self-declared by the caller, not server-enforced per role, until Layer 2 below.

### Autonomy level

**Level:** low  
**Conditions for human checkpoint:** None directly -- planner is read-only and advisory; its output is evaluated by the orchestrator before any handoff to implementer.  
**Reason:** Planner cannot take any action with real consequences on its own; the risk it carries is in the plan's content being wrong, not in anything it can directly do.  
**Container permissions:** workspace read-only, memory omitted

## Role: implementer

**Version:** v2  
**Defined in:** `agents/implementer.md`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason |
|---|---|---|---|
| write_entry | storage | YES | Implementer may record one new lesson learned when work surfaces something a future session couldn't reconstruct (CLAUDE.md). |
| read_entry | storage | NO | Implementer adds a new entry; it does not browse or edit existing history (module3_doc/role-access-table.md). |
| list_entries | storage | NO | Same reasoning as read_entry -- not part of implementer's defined job. |
| update_entry | storage | NO | Implementer adds, it does not edit existing entries. |
| delete_entry | storage | NO | Implementer must not remove project state. |
| audit_read | storage | NO | Audit inspection is owned by the orchestrator. |
| retrieve | retrieval | NO | Planner already supplies retrieved context during planning; implementer works from the approved plan, not a fresh retrieval (module3_doc/role-access-table.md). |

### Skill activation scope

| Skill | Activation permitted | Reason if denied |
|---|---|---|
| summarize-session | YES | Implementer may summarize its own implementation work. |

### Data classification ceiling

**Maximum level:** N/A (retrieve denied)  
**Reason:** Implementer has no retrieval access at all, so no ceiling applies.

### Autonomy level

**Level:** medium  
**Conditions for human checkpoint:** Before any implemented change is committed, present a run summary (plan, diff, test result) for approval -- unconditional, applies even when nothing went wrong (CLAUDE.md).  
**Reason:** Implementation is reversible within the container up to the commit point; the commit itself is the irreversible action requiring a human decision.  
**Container permissions:** workspace read-write, memory mounted

## Role: reviewer

**Version:** v1  
**Defined in:** `agents/reviewer.md`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason |
|---|---|---|---|
| write_entry | storage | NO | Reviewer must not change project state. |
| read_entry | storage | YES | Reviewer reads prior decisions relevant to what it's reviewing. |
| list_entries | storage | YES | Reviewer checks what exists before reviewing. |
| update_entry | storage | NO | Reviewer must not change project state. |
| delete_entry | storage | NO | Reviewer must not remove project state. |
| audit_read | storage | NO | Audit inspection is owned by the orchestrator. |
| retrieve | retrieval | YES | Reviewer retrieves relevant prior lessons/standards while forming a verdict. |

### Skill activation scope

| Skill | Activation permitted | Reason if denied |
|---|---|---|
| summarize-session | YES | Reviewer may summarize its own review. |

### Data classification ceiling

**Maximum level:** internal  
**Reason:** Reviewer's job is evaluating internal engineering work; it does not require confidential material.

### Autonomy level

**Level:** low  
**Conditions for human checkpoint:** Reviewer output is advisory only; it may not apply any change. If a review disagrees with another reviewer on the same item (e.g. during a calibration exercise), the orchestrator escalates rather than either reviewer resolving it (CLAUDE.md, Reviewer Conflict Resolution).  
**Reason:** A review role that can change state can quietly alter the work it's supposed to independently inspect.  
**Container permissions:** workspace read-only, memory omitted

## Role: spring-boot-reviewer

**Version:** v2  
**Defined in:** `agents/spring-boot-reviewer.md`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason |
|---|---|---|---|
| write_entry | storage | NO | Advisory-only review agent; predates the MCP storage layer and does not use it. |
| read_entry | storage | NO | Not used -- reads the codebase directly via native tools (Read/Grep/Glob/Bash). |
| list_entries | storage | NO | Not used. |
| update_entry | storage | NO | Not used. |
| delete_entry | storage | NO | Must not remove project state. |
| audit_read | storage | NO | Audit inspection is owned by the orchestrator. |
| retrieve | retrieval | NO | Does not call the retrieval server; reviews Spring Boot-specific diff content directly. |

### Skill activation scope

| Skill | Activation permitted | Reason if denied |
|---|---|---|
| summarize-session | YES | May summarize its own review findings. |

### Data classification ceiling

**Maximum level:** N/A (retrieve denied)  
**Reason:** Does not call the retrieval server at all.

### Autonomy level

**Level:** low  
**Conditions for human checkpoint:** Advisory only -- findings (Critical/Warning/Suggestion) are reported to the human, never auto-applied.  
**Reason:** A domain-specific reviewer with any write access could silently "fix" what it's supposed to only flag.  
**Container permissions:** workspace read-only, memory omitted

## Role: orchestrator

**Version:** v1  
**Defined in:** `CLAUDE.md` (Orchestrator Instructions) -- the top-level session, not a separate agent definition file.

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason |
|---|---|---|---|
| write_entry | storage | NO | Writing to storage is implementer's job alone (CLAUDE.md, Storage and Retrieval Access). Previously **not enforced**: the audit log shows the orchestrator successfully called `update_entry` with no automated check able to catch it -- module3_doc/calibration-log.md, near-miss: orchestrator's undetectable forbidden storage write. |
| read_entry | storage | YES | Orchestrator reads state while evaluating results and investigating discrepancies. |
| list_entries | storage | YES | Same reasoning as read_entry. |
| update_entry | storage | NO | Same reasoning and same near-miss as write_entry above. |
| delete_entry | storage | NO | Orchestrator must not remove project state. |
| audit_read | storage | YES | Orchestrator is the role responsible for investigating authorization denials and audit history. |
| retrieve | retrieval | YES | Orchestrator retrieves relevant standards/prior lessons while evaluating implementer's result, standing in for a dedicated Reviewer-adjacent check (CLAUDE.md). |

### Skill activation scope

| Skill | Activation permitted | Reason if denied |
|---|---|---|
| summarize-session | YES | Orchestrator may summarize workflow state. |

### Data classification ceiling

**Maximum level:** confidential  
**Reason:** Orchestrator coordinates the full workflow and is the role accountable for classification decisions overall; it is the most trusted caller in the system.

### Autonomy level

**Level:** medium  
**Conditions for human checkpoint:** Before any implemented change is committed (unconditional); before proceeding past a plan that changes externally-visible behavior; before proceeding past an unresolved reviewer conflict, which must escalate rather than self-resolve (CLAUDE.md).  
**Reason:** Orchestration coordinates other roles and is largely reversible within the container, but the commit point, externally-visible behavior changes, and unresolved conflicts are exactly the moments this system has had real near-misses around -- human accountability belongs there specifically.  
**Container permissions:** workspace read-write, memory mounted

## Role: decision-auditor

**Version:** v1
**Defined in:** `agents/decision-auditor.md`

### MCP server and operation access

| Operation | Server | Granted | Justification / Denial reason |
|---|---|---|---|
| write_entry | storage | NO | Creating a new lesson/decision entry is implementer's job. Granting this role write_entry too would blur two roles into doing the same thing through two different paths. |
| read_entry | storage | YES | Must read an existing record before it can check or correct it. |
| list_entries | storage | YES | Must be able to survey what records exist for a project before auditing them. |
| update_entry | storage | YES | This role's entire purpose. First role ever granted this operation -- previously denied to every role (see Known Gap below). |
| delete_entry | storage | NO | No established need; correcting a stale record is not the same as removing it. |
| audit_read | storage | NO | Audit inspection is owned by the orchestrator. |
| retrieve | retrieval | NO | This role's job is checking a record against real git/build state, not researching prior lessons. Granting retrieve risks it "correcting" a record based on a plausible-sounding prior lesson instead of verified current reality -- the exact failure mode this role exists to prevent, not commit itself. |

**Known gap this role closes:** `update_entry` was granted to *no* role at all until now -- confirmed directly during red-team Prompt 4 (`eval/red-team-results.md`), where the Orchestrator found no mechanical way to correct an existing entry existed for anyone. `decision-auditor` is the first role given this operation, scoped narrowly to exactly the case it's needed for.

**Evidence motivating this role:** `decision-005.md`'s "Not yet done: change has not been committed" line was independently rediscovered as stale four separate times (holdout tasks HO-01, HO-03, HO-05, and again during the Module 4 activation exercise) by four different agents, none of whom had the job of noticing or fixing it -- each just stumbled onto it mid-unrelated-task. `decision-001.md`'s placeholder review date is a live, still-uncorrected instance of the same pattern. This is the single most evidence-grounded gap in the project's memory system.

### Skill activation scope

| Skill | Activation permitted | Reason if denied |
|---|---|---|
| summarize-session | YES | May summarize its own audit findings. |

### Data classification ceiling

**Maximum level:** N/A (retrieve denied)
**Reason:** Does not call the retrieval server at all -- see denial reasoning above.

### Autonomy level

**Level:** low
**Conditions for human checkpoint:** Any correction to an existing entry should be flagged in the run summary for human awareness, same as any other change to project memory -- this role does not get a lighter review standard just because its job is "fixing," not "creating."
**Reason:** Silently correcting records, even accurately, removes the human's ability to notice a pattern of staleness (as this role's own motivating evidence shows -- four *separate* people/sessions missed the same thing before anyone acted on it).
**Container permissions:** workspace read-only except `.memory/project/`, writable only through coursetools' role-scoped path exception (`file_write` permits `.memory/project/` for `role="decision-auditor"` only; `.memory/storage/`, `.memory/reference/`, and `.memory/knowledge/` stay blocked for `file_write` regardless of role). Memory otherwise omitted. Storage-server entries are still corrected only through `update_entry`, never by editing files.

**Note -- original read-only design was incomplete:** v1 of this role assumed every correction would go through `update_entry`, so it was granted no `file_write` and a fully read-only workspace. That assumption didn't hold. Git-tracked project files -- `MEMORY_INDEX.md` and `decisions/decision-*.md` -- are plain files, not storage entries, so `update_entry` can't reach them. The first real run of this role showed the gap directly: asked to fix `decision-001`'s review-date placeholder in `MEMORY_INDEX.md`, the auditor found no storage entry to update and no file write path, and could only report the problem, which left the exact staleness this role was created to fix still uncorrected. `file_write` on `.memory/project/` closes that gap. Like every coursetools role check, it enforces the allow-list against a *self-declared* `role` value, not verified caller identity.
