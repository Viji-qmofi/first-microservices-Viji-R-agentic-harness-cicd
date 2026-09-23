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
