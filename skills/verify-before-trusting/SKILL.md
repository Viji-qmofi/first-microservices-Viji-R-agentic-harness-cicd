---
name: verify-before-trusting
description: >
  Given a specific claim about project state (a commit status, a file's
  content, a test result, a role's permission, an audit-log entry), verify
  it directly against the real underlying artifact before accepting or
  acting on it. Use whenever a claim comes from a self-report, stale
  documentation, memory, or an assumption -- not from something you just
  directly observed yourself.
---

# Verify Before Trusting

This project's single most repeated lesson, formalized: a subagent's self-report, a memory record, or an assumption is a *claim*, not *evidence*. This skill is the procedure for closing that gap before a claim gets acted on.

## When to invoke this

- Before writing an ADR, policy document, or any other artifact that cites project state as fact.
- Before accepting a subagent's report that something "already exists," "was already committed," "already passed," or "is already granted."
- Before trusting a piece of existing documentation (a routing map, a classification doc, a README) as still accurate.
- Any time a claim's correctness, if wrong, would propagate into something else being built on top of it.

## Procedure

1. **Identify the claim's type.** Each type has a specific, direct verification method -- never substitute a different, weaker check for the one that type actually needs:
   - **Git/commit state** ("this was already committed," "this file hasn't changed") -> `git log --oneline -- <path>`, `git show <sha>:<path>`, or `git diff -w` for whitespace-only changes.
   - **File content** ("this doc says X") -> read the actual current file directly, not a cached summary or an earlier read from this session.
   - **Test/build result** ("tests passed") -> run the actual test command yourself; never accept a narrated pass/fail without the real output or a deterministic parse of it.
   - **Permission/access** ("this role can do X") -> call the actual enforcement mechanism directly (the real MCP tool, the real allow-list file), not what a policy document says should be true.
   - **Audit/log entry** ("this operation happened") -> grep or read the actual audit log for the real entry, not a transcript's reconstruction of it.
2. **Run the direct verification**, not an indirect proxy for it. A reconstruction, a prior read from earlier in the session, or another agent's description of having checked is not direct verification.
3. **Compare the verification result against the original claim explicitly.** State both: what was claimed, and what the direct evidence actually shows.
4. **Report match or mismatch plainly** -- do not soften a mismatch into the original claim's framing. If they match, say so and proceed. If they don't, correct the claim before anything else is built on it, and note what the real state actually is.

## Known failure mode this guards against

A claim can be wrong without anyone intending to deceive -- stale documentation, a reconstructed transcript, a subagent's honest-but-unverified belief, or an assumption that seemed safe. This project has hit this repeatedly: `decision-005.md`'s "not yet committed" line was wrong and independently rediscovered four separate times before being fixed; `docs/routing-and-tool-grant-map.md` was found to still be the sandbox's placeholder content, directly contradicting the real enforced system, only because it was checked directly rather than assumed accurate. In every case, the fix was the same: stop, check the real artifact, correct the claim, then proceed.

## What this skill does not do

It does not resolve ambiguity about what the *right* state should be -- only whether a specific claim matches the *actual* current state. A mismatch found this way may still need a human or further investigation to decide what to do about it; this skill's job ends at surfacing the mismatch honestly.
