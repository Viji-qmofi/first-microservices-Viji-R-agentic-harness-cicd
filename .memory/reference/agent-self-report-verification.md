---
classification: internal
project: proj-lessons
doc_type: lesson
---

# An Agent's Own Summary Is a Claim, Not Verification

What happened: multiple times across this project, an agent's closing summary of its own work was nearly accepted as sufficient evidence without checking the underlying artifact -- a build-check run once confidently reported "zero warnings" that turned out to be a detection-method miss on re-inspection, and a code-review agent's claim of having "included concrete code snippets" was almost scored as true before the actual output was read directly.

What was learned: a subagent's narrative description of what it did is a claim about its own output, not the same evidence as the output itself. This holds even when the agent is not being dishonest -- it can be confidently wrong about its own thoroughness, especially when using a narrower detection method than a previous, similarly-worded run.

How to apply it: before scoring or trusting any claimed behavior (a check that passed, output that was produced, a boundary that was respected), verify against the actual artifact -- the raw command output, the real diff, the literal file contents -- rather than the agent's own description of it. This applies to every agent in this project, not just one; it is now a standing rule in the project's rubric rather than a one-off catch.
