# Harness Baseline Run Report (3.3 Exercise 1, Step 6)

## DEV-01 -- dry run, harness self-validation

Purpose: produce the first real transcript and confirm the harness's own scripts execute against real data before trusting them on anything that matters. Task: fix the keyword-search fallback in `mcp/retrieval/server.py` to stop matching on filler words (a documented gap from `retrieval-quality-report.md`'s Q5 finding) -- deliberately chosen as harness-infrastructure work, not one of the six locked holdout tasks.

**First deterministic run: 10/13.** Two categories of failure, both real:
- `role_order` failed because the Orchestrator legitimately reviews twice in one run (evaluating the plan before handoff, evaluating the diff before testing), which the check's "each role runs once" assumption didn't anticipate. Not a bug in the run -- a gap in the check and the transcript-recording convention. Fixed by splitting the single `orchestrator_review` role into two distinct, single-occurrence roles: `orchestrator_plan_review` and `orchestrator_diff_review`.
- `latency`/`cost` failed because `duration_seconds`/`cost_usd` were never actually measured -- the original `CLAUDE.md` instructions showed a placeholder value but never required real measurement. Fixed by adding an explicit rule: bracket the run with `date` and `/status`, and record honestly if a run wasn't measured rather than fabricating a plausible number.

**Corrected DEV-01: 11/13.** `role_order` now passes. `latency`/`cost` still fail, correctly -- DEV-01 had already finished before the measurement rule existed, so there was no real number to retroactively supply. Recorded as `null` with an honest note, not backfilled. This is the checks working as designed: refusing to treat a missing measurement as a passing one.

## DEV-02 (constructor injection) -- the baseline run

Task: convert `OrderServiceImpl` and `OrderController` from field `@Autowired` injection to constructor injection, per `coding-standards.md`'s dependency injection standard -- flagged as a Suggestion by `spring-boot-reviewer` across Runs 001-004, never previously fixed. Chosen specifically as an ordinary, unrelated task (not more harness self-improvement), to validate the pipeline on a genuine "test subject."

Measurement: bracketed with `date` from before the task through the commit. Cost measurement was not checked before the task started (only after), so the recorded `cost_usd` ($1.19) is an honest session-cumulative upper bound, not an isolated figure -- documented explicitly as such in the transcript rather than presented as precise. Duration (188s) excludes the human-approval wait window, using the last available pre-approval timestamp as a documented, slightly-undercounting estimate.

### First deterministic run: 12/13

`retrieval_citations` failed -- 2 of the transcript's recorded retrieval results were missing `source_document`/`chunk_index`. Investigating *why*, rather than just patching the missing fields, surfaced that the failure was in the transcript's own accuracy, not in what the retrieval server actually returned: the Orchestrator's reconstruction had collapsed two real `retrieve` calls into one, used a placeholder query string instead of the verbatim text `CLAUDE.md` requires, dropped one of four real results, and omitted `retrieval_method` entirely. Recovering the real data from `planner`'s own subagent transcript showed two genuine, verbatim queries ("constructor injection vs field @Autowired dependency injection style"; "coding standard dependency injection constructor"), both correctly filtered to `proj-lessons`/`internal`, both returning results exclusively via the keyword fallback -- including two documents entirely unrelated to dependency injection (`git-worktree-windows-paths.md`, `chmod-root-bypass.md`).

Two corrections followed:
1. The transcript entry was replaced with the two real `retrieve` events, verbatim query text, all four real results, real `retrieval_method` for each.
2. A new finding was documented in `retrieval-quality-report.md`, distinct from Q5: the stopword fix only removes filler words, not the deeper precision problem that the keyword fallback's OR-join lets a single shared content word match an entirely unrelated document. Recorded as a known gap, not fixed in this exercise.

### Second deterministic run: 13/13, clean.

### Rubric suite: first successful execution (previously gated out by deterministic failures both times)

| Dimension | Score | Judge's stated reasoning (condensed) |
|---|---|---|
| correctness | 4/4 | Both classes correctly converted, no `@Autowired` remains, all 26 tests pass. |
| task_adherence | 4/4 | Only the two specified classes changed; unrelated line-ending noise was restored before commit. |
| groundedness | 3/4 | Planner's own retrieved-source claims were accurate, but the Orchestrator's plan review quoted `coding-standards.md` wording the planner reportedly could not read -- flagged by the judge as a minor stretch. |
| clarity | 3/4 | Well organized overall; dense measurement notes and post-hoc corrections were the stated rough edges. |

**All four passed the per-dimension floor.** This is the correct, final recorded state for DEV-02 -- not re-run after the regression fix below, since the gap the judge flagged was a true historical fact about this specific run (planner genuinely never called `file_read` at the time), not an error in the transcript.

## Regression found via the rubric judge's own reasoning, not a scripted test

The `groundedness` judge's justification -- *"the orchestrator's plan review... quotes coding-standards.md wording, which the planner could not read"* -- was investigated rather than accepted as a minor stretch. Sequence:

1. Confirmed `planner` made no `file_read` call at all during DEV-02 -- it had attempted `codebase_search` on `.memory/knowledge/`, been correctly refused (by design, from the 3.2 fix), and stopped there rather than trying `file_read` next, despite its own agent definition explicitly directing it to use `file_read` for exactly this.
2. Tested whether `file_read` would have worked if attempted: it did not. Direct call, `role="planner"`, path `.memory/knowledge/coding-standards.md`, returned the same `PermissionError` used for `.memory/storage/`, `.memory/reference/`, and `.memory/project/`.
3. **Root cause: a genuine regression from the 3.2 Step 6 fix.** That fix correctly closed a real bypass for `.memory/storage/` (raw SQLite access) and `.memory/reference/` (classification-ceiling bypass), but its blanket `.memory/` path check also caught `.memory/knowledge/` -- which was never meant to be blocked. Direct `file_read` access to `.memory/knowledge/` is the *intended*, designed path (documented since Exercise 2.3); its protection comes from the `:ro` Docker mount preventing writes, not from being unreadable.
4. **Fix, narrowed rather than reverted:** the `.memory/` block in `file_read` specifically (not `file_write`, not `codebase_search`) now excludes `.memory/knowledge/`. `.memory/storage/`, `.memory/reference/`, and `.memory/project/` remain blocked exactly as before -- the last of these deliberately, since project-memory writes now have a disciplined, audited path via the storage server (`decision-004`, `decision-005`), and routing reads through the same boundary keeps one consistent access model.

### Reverification, four separate checks

1. `file_read` on `.memory/knowledge/coding-standards.md`, `role="planner"` -- now succeeds.
2. `file_read` on `.memory/storage/storage.db`, `.memory/reference/agentic-run-cost-tracking.md`, `.memory/project/MEMORY_INDEX.md` -- all three still correctly refused.
3. `planner` invoked fresh on a new, related task ("confirm whether OrderServiceImpl and OrderController currently comply with our documented DI standard") -- this time it correctly called `file_read` on `coding-standards.md`, quoted the "Dependency injection style" section, and that quote was verified against the real file. Concluded (correctly, independently confirmed via `grep`) that both classes already complied and no further change was needed.
4. Honest residual limitation, not hidden: `planner`'s claim of having called `file_read` is self-reported -- nothing independently logs coursetools read calls the way `storage-audit.log` does for storage writes. This is the same gap already documented in `check_tool_grants`' own docstring (coursetools calls aren't yet reliably captured as transcript `tool_call` events); this run is a concrete, motivating instance of that gap, not a new discovery.

Commits: keyword-fallback stopword fix (DEV-01), the transcript-recording corrections (`orchestrator_plan_review`/`orchestrator_diff_review` split, required real measurement, `similarity_score` field-name fix), `9ebb640` (constructor injection), the `retrieval_citations` transcript correction and new Q5-adjacent finding in `retrieval-quality-report.md`, and the narrowed `.memory/knowledge/` regression fix in `mcp/coursetools_server.py`.

## Summary

The harness is validated end-to-end: both layers execute correctly, gate appropriately (rubric never runs on a failing deterministic result), and -- most importantly -- the rubric layer caught a real, previously-undetected system regression through ordinary judgment-based scoring, not a check anyone wrote specifically to catch it. That regression traced back three levels deep (an agent behavior gap, which traced to a tool permission failure, which traced to an overly broad fix from a prior exercise) before reaching its actual root cause, and the fix was scoped narrowly enough to preserve every protection the original fix was built for.
