---
name: summarize-session
description: >
  Produces a structured summary of the current session's decisions, rule
  changes, and outstanding work. Use at a natural workflow breakpoint before
  the context window fills, or when the user asks for a session summary.
---

# Skill: Summarize Session

When this skill is invoked, produce a structured session summary using
exactly the format below. Do not paraphrase acceptance criteria or rules
-- copy them verbatim from the conversation. Do not omit any modified
files or decisions. The summary will be used as the sole context for
the next phase of work, so it must be complete and accurate.

---

## SESSION SUMMARY

### Original Task and Acceptance Criteria
(Copy the original task description and all rules/criteria verbatim.
Do not paraphrase or shorten.)

### Decisions Made So Far
(Numbered list. Each item states what was decided and the brief reason
why, if one was given.)

1.
2.
3.

### Rule Changes
(If any rules were updated, modified, or removed during the session,
list them here explicitly. State the original rule and what it changed
to. If no rules changed, write "None.")

### Current State of All Modified Artifacts
(For each file or document section that has been edited, provide the
filename or section name and a one-sentence description of its current
state. If the full current text is short enough to include, include it.)

### Outstanding Work Remaining
(Numbered list of the work that has not yet been done, in the order
it should be completed.)

1.
2.
3.

### Known Open Questions or Blockers
(Anything unresolved that the next phase needs to be aware of. If none,
write "None.")

---

After producing the summary, ask the user to review it for accuracy before proceeding. Do not continue with any task until the user confirms the summary is correct or provides corrections.
