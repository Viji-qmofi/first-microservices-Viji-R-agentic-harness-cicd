# Reflection Log

Each entry records a real change to an agent, skill, memory rule or orchestration rule that followed from observed evidence. Every entry names the trigger, the change, the before and after, and what confirmed it held. Entries are sourced from the files cited, and the limits are stated.

## 1. `spring-boot-reviewer` v1 to v2: fixes must include code (2026-07-31)

- **Trigger:** Runs 001 and 002 scored Fix Example Quality 3 both times. The agent described fixes but did not show code (`module2_doc/iteration-log.md`).
- **Change:** `agents/spring-boot-reviewer.md` v2 requires a code snippet for every suggested fix. Commits `dce1883` (v1) and `a740bd7` (v2), as recorded in the Module 2 iteration log.
- **Before and after:** Fix Example Quality 3, 3, then 4 in Run 003. Issue Detection and Severity Classification stayed at 4, and cost stayed flat.
- **Rerun that confirmed it:** Run 003 is the rerun, scored against the actual snippets.
- **Limits:** one rerun. It has not been re-checked since.

## 2. Verify agent output against raw artifacts (2026-07-31)

- **Trigger:** a review claim about its own output could not be taken at face value. Scores had to be assigned from the raw snippets, not from the agent's summary.
- **Change:** a standing verification requirement in `module2_doc/rubric.md`, and later the `verify-before-trusting` skill (`skills/verify-before-trusting`).
- **Before and after:** Run 003's Fix Example Quality of 4 was assigned only after reading the snippets. In October 2026 the same rule caught a report that said "Warnings/errors: None" when the logs held warnings (`docs/iteration-log.md`, Runs 005 and 006).
- **Rerun that confirmed it:** the Module 1 re-runs, scored against a ground-truth answer key.
- **Limits:** the rule is applied by the reviewer, not enforced by code.

## 3. Sensitive data in memory: a classification scheme and a hard stop (2026-08-26)

- **Trigger:** Exercise 2.4. A fake key was written to memory only after a deliberate override. The rule existed but there was no classification scheme behind it (`module2_doc/iteration-log.md`, Run 007).
- **Change:** a Data Classification section in `module2_doc/memory-architecture.md`, a classification-first rule in `CLAUDE.md`, the offending entry corrected (commit `a079da2`), and a versioned pre-commit hook (`scripts/hooks/pre-commit`).
- **Before and after:** before, protection depended on the model's own judgment. After, a commit containing `password=test123` under `.memory/project/` was blocked with exit code 1 and HEAD did not move.
- **Rerun that confirmed it:** the blocked commit, verified directly in Run 007.
- **Limits:** substring matching has a known false positive on the word "Task-Resumption", and the hook covers `.memory/` only.

## 4. Reviewer conflicts go to a human (2026-09-21)

- **Trigger:** two temporary reviewers disagreed on two sections and the Orchestrator had no rule for what to do next (`module3_doc/calibration-log.md`, Entry 1).
- **Change:** a "Reviewer Conflict Resolution" section in `CLAUDE.md`. A contradiction must not be silently resolved: it needs an `orchestrator_conflict_resolution` step, `escalated_to_human: true` and a human decision.
- **Before and after:** `CAL-01-before` scored 8/13 on the deterministic checks. `CAL-01-after` scored 13/13 deterministic and 4/4 on the rubric (correctness 3, task adherence 4, groundedness 3, clarity 3).
- **Rerun that confirmed it:** `.eval-artifacts/runs/CAL-01-after.json`, with the same reviewers and instructions.
- **Limits:** the entry itself records that the after-fix cost figure ($1.39) is a session-cumulative upper bound, not an isolated measurement.

## 5. `planner` v3: stop when retrieval is missing (2026-10-07)

- **Trigger:** with the retrieval tool unavailable, the planner substituted `codebase_search` and produced a full plan. Only the Orchestrator caught it (`module3_doc/calibration-log.md`, findings 7 and 8).
- **Change:** `agents/planner.md` v3 (commit `9eaf370`): stop and report if `retrieve` is unavailable, and never substitute another search tool. The Orchestrator guard was tightened in commit `0a06f01`.
- **Before and after:** before, the planner substituted. After, the planner stopped on its own and said the decision belonged to the Orchestrator. The Orchestrator guard also held on a second retest.
- **Rerun that confirmed it:** the planner v3 retest and the guard retest, both on 2026-10-07.
- **Limits:** one run before and one after, so it shows the change can hold, not that it always will. The model differed between runs and was not controlled.

## 6. `decision-auditor` v1 to v2: scope widened with evidence (2026-10)

- **Trigger:** building the role exposed a stale default in `coursetools` that had silently disabled earlier governance work, and a v1 grant (`update_entry`) that could not reach the git-tracked files it needed to fix (`module4_doc/decision-auditor-case-study.md`).
- **Change:** the allow-list path default was corrected, and v2 gained a narrow read and write exception limited to `.memory/project/`.
- **Before and after:** before, the long-standing stale status in `decision-005.md` was rediscovered four separate times by four agents. After, the role corrected `decision-001`'s placeholder review date and `decision-004`'s build status in `MEMORY_INDEX.md`.
- **Rerun that confirmed it:** the real correction run, and a red-team prompt that invited it to infer a value from memory, which it declined.
- **Limits:** its scope exception rests on the self-declared role, although the path limit itself is a real server-side check.
