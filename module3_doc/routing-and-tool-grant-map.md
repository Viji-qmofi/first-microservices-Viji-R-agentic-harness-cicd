# Routing and Tool Grant Map

Project: `first-microservices-Viji-R`

This map is the design decision of record. Agent definitions in `.claude/agents/` implement this table. When a definition and this map disagree, update the definition to match the map.

All tool operations are on the `coursetools` MCP server and are named `mcp__coursetools__<tool_name>` in agent definitions, per `mcp/README.md`. Every call also requires a `role` argument, checked against `mcp/roles.allowlist.json`.

## Tool grants

| Role | Tools granted | Tools denied (reason) |
| :--- | :--- | :--- |
| `planner` | `mcp__coursetools__file_read`, `mcp__coursetools__codebase_search` | `file_write` -- a plan is a document, not a code change; the Planner never touches source. `test_runner`, `task_tracker`, `shell` -- outside its single responsibility (producing a plan). |
| `implementer` | `mcp__coursetools__file_read`, `mcp__coursetools__file_write`, `mcp__coursetools__codebase_search` | `test_runner` -- verification is the Orchestrator's job this round, not the Implementer's; a role that can both write code and self-report test results has no independent check on its own work. `task_tracker`, `shell` -- outside scope. |
| `reviewer` (designed, not implemented this round) | `mcp__coursetools__file_read`, `mcp__coursetools__codebase_search` | `file_write` -- the Reviewer's whole value is that it cannot change what it's reviewing. `test_runner`, `task_tracker`, `shell` -- outside scope. |
| `tester` (designed, not implemented this round) | `mcp__coursetools__test_runner`, `mcp__coursetools__file_read` | `file_write` -- reports results, does not fix failures. `task_tracker`, `shell`, `codebase_search` -- outside scope; works from the file list it's given, not an open-ended search. |

Cross-role check:

- `file_read` is granted to every implemented/designed role -- read access alone carries little risk and every role needs to see the code it's working on.
- `file_write` is granted to exactly one role, `implementer` -- the only role whose job is to change code. No other role can write.
- `test_runner` is granted to `tester` only (and stands in for the Orchestrator's own direct `./mvnw test` call this round, since Tester isn't implemented yet).
- `task_tracker` and `shell` are granted to no role in this workflow -- this project doesn't have a real ticket tracker to wire up, and `shell` is deliberately withheld from everyone per the server's own default allow-list (empty list for `shell`), since unscoped shell access defeats the purpose of per-tool scoping entirely.
- `web_search` is granted to no role -- no role in this workflow needs external research; it exists on the server for other course scenarios, not this one.

Alternative considered: granting `implementer` `test_runner` directly, so it could self-verify before returning. Ruled out because it would let the same role that wrote the change also be the sole judge of whether it's correct -- the entire point of separating Implementer from verification is an independent check, even a lightweight one (the Orchestrator's own test run, standing in for Tester this round).

Alternative considered: granting `planner` `codebase_search` only, without `file_read`, on the theory that search alone is enough to produce a plan. Ruled out because the Planner needs to read the actual current `catch` block in full to reason about how to split it, not just see which lines a keyword search happens to match.
