# Routing and Tool Grant Map

| Role | Route condition | coursetools (file_read / file_write / codebase_search) | Storage operations | Retrieval | Notes |
|---|---|---|---|---|---|
| planner | Deciding how to make a change, not just making it | file_read, codebase_search | None | retrieve, ceiling internal | Read-only, advisory. Retrieves prior lessons before proposing an approach. |
| implementer | Writing code per an approved plan | file_read, file_write, codebase_search | write_entry only | None | No read/list/update/delete on storage -- adds new lessons, never browses or edits existing ones. No retrieve -- planner already supplies retrieved context during planning. |
| reviewer | Independent diff review, general | file_read, codebase_search | read_entry, list_entries | retrieve, ceiling internal | Advisory only, no write access anywhere. |
| spring-boot-reviewer | Spring Boot convention review | None (native tools only: Read/Grep/Glob/Bash) | None | None | Predates the MCP storage/retrieval layer; reviews the codebase directly, not via MCP. |
| decision-auditor | Checking/correcting project memory records against git reality | file_read, file_write -- scoped to `.memory/project/` only, role-gated | read_entry, list_entries, update_entry | None | First and only role ever granted `update_entry` (v2, Module 4.1) -- closes the gap where no role could correct an existing entry. Denied `retrieve` deliberately: every correction must trace to verified current state, never a remembered or researched prior lesson. |
| orchestrator | Parent workflow coordination, evaluation, human checkpoint | None directly (coordinates subagents; runs shell commands like `./mvnw test` natively) | read_entry, list_entries, audit_read -- **write_entry/update_entry/delete_entry explicitly denied** | retrieve, ceiling confidential | The denial is load-bearing, not incidental: module3_doc/calibration-log.md's HO-06 finding recorded the Orchestrator successfully calling `update_entry` before this was enforced -- a real near-miss, not a hypothetical one. `_authorize()` (Module 4.1) now denies this for real; verified directly with a live MCP call. |

## Converted steps

- `orchestrator_test` (Maven test-result interpretation): converted to deterministic code, no MCP access required (ADR-001).
- Line-ending-noise detection during diff review: readiness package only, not implemented -- see ADR-002. Recommended design (if ever built) uses no MCP access; it's a local `git diff` operation.

## Known limitation, documented not hidden

Every grant in this table is enforced against a *self-declared* `calling_role` (or, for coursetools, `role`) parameter -- not a verified, process-level caller identity. A caller that states a role it isn't will have that claim accepted by `_authorize()`'s allow-list check. This is a real, confirmed-by-direct-test limitation (CLAUDE.md, Storage and Retrieval Access), not a gap this table pretends doesn't exist. It applies uniformly to every row above.
