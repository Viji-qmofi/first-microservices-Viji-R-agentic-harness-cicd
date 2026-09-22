---
classification: internal
project: proj-lessons
doc_type: lesson
---

# Claude Code Cannot Run Under --network none

What happened: following a course instruction to "keep network egress blocked unless explicitly told otherwise," a container was started with `--network none` for a routine agent task. Claude Code failed immediately with an API connection error before it could do anything at all -- even for a task that itself needed no external data.

What was learned: Claude Code is a client for the Anthropic API. It cannot run at all without reaching `api.anthropic.com`, regardless of what the underlying task needs -- this is a requirement of the agent tooling itself, not an exception scoped to one task. Network restriction has to apply to what the task can reach beyond that one necessary connection, not to Claude Code's own basic ability to function.

How to apply it: any container session that will invoke `claude` needs real network access, full stop. Restricting network is still valuable for other purposes (e.g. a plain shell doing pure file inspection with no agent involved), but it is never a lever available to a session that needs the agent itself to run.
