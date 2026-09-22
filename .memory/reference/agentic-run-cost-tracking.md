---
classification: confidential
project: proj-lessons
doc_type: internal-notes
---

# Per-Run Agent Cost Patterns (Internal)

What happened: across the agent definition and context-management exercises, per-run costs were tracked via `/status` immediately before and after each invocation, isolated from any other command run in the same session.

What was learned: a single `spring-boot-reviewer` invocation on this codebase has typically run in the roughly $0.30-$1.10 range depending on session state -- cleanly isolated single-command sessions landed at the low end (around $0.33-$0.58), while sessions that combined a code-fix command and a review command in the same terminal session (uncleanly isolated) measured over $1.00 for the combined total, not attributable to either command alone. Cost did not meaningfully increase when the agent definition was changed to require concrete code snippets in its output rather than prose descriptions -- richer output was close to free in this case.

How to apply it: when estimating budget for a round of agent-based code review or orchestrated multi-role work on this project, isolate each invocation's `/status` check immediately before and after the command, in an otherwise-empty session, to get an attributable figure rather than a session-wide total that mixes multiple commands together.
