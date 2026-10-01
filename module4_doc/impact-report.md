# Impact Report: Governed Ticket-to-Implementation Support

## Executive summary

This system matured across four modules from an ungoverned, purely agentic pipeline into one with server-enforced role boundaries, a two-layer evaluation harness, CI/CD gating, and at least one step formally converted from LLM judgment to deterministic code with measured results. This report separates what was actually **measured** from what is **projected** -- no figure in the measured section is an estimate, and no figure in the projected section is presented as something that already happened.

## Measured impact

**`orchestrator_test` deterministic conversion** (`ADR-001`, `module3_doc/calibration-log.md`, 2026-09-25):
- Latency: ~14s/run (agentic baseline, averaged over 3 runs) -> ~0.053s/run (deterministic, averaged over 3 runs) -- a ~264x reduction.
- Token cost: ~$0.173/run -> $0/run -- complete elimination for this step.
- Predictability: deterministic output confirmed byte-identical across repeated runs via `diff`; the agentic baseline was only confirmed consistent at the conclusion level, a real, disclosed gap in that measurement's own rigor.
- Verified via a real 4-run end-to-end regression check after integration, not isolated measurement alone -- no regression attributable to the conversion.

**Governance enforcement, before and after a real fix** (`ADR-005`, `module3_doc/calibration-log.md`):
- Before: the Orchestrator's `update_entry` call on project storage succeeded in a real run (`HO-06`), despite being explicitly denied by written policy -- a real near-miss, not caught by any check that existed at the time.
- After: the identical call, re-attempted post-fix, returns `authorization_denied` -- verified directly via a real MCP call, not a simulated test. A positive control (`implementer`'s legitimate `write_entry`) confirmed the fix denies exactly what it should and nothing more.

**CI/CD, first real run** (`docs/ci-step-design.md`):
- Two real, previously-invisible defects (a `python`/`python3` base-image mismatch across three jobs; a missing `pytest` dependency) were caught the first time the pipeline actually executed on GitHub's runners -- both had passed every local spot-check beforehand. Actions had been silently disabled by default (a forked-repo default, not a bug) until explicitly enabled, meaning these defects had been invisible for as long as the pipeline existed unexercised.
- `pipeline-integrity`'s deliberate-weakening test (`continue-on-error: true` added to `policy-gate` on a throwaway branch) was caught by two independent mechanisms simultaneously, confirmed in real commit history, then cleanly reverted.

**Holdout measurement baseline** (`module3_doc/calibration-log.md`, Module 3 Lab): a clean, full-system measurement pass across six locked tasks found only 1 of 6 passed without a real, distinct finding -- scope drift (agentic and human-caused), a structural gap in audit-log role identification, and a session-interruption recovery that briefly fabricated events before self-correcting. This is offered as a measured snapshot of system maturity at that point, not a claim the system is now defect-free -- later modules (4.1's `ALLOWLIST_PATH` bug, 4.2's CI defects) found further real issues after this baseline, which is itself evidence the measurement process keeps finding real things rather than converging on false confidence.

**Red-team boundary testing** (`eval/red-team-results.md`): 4 of 4 planned boundary-violation attempts were correctly blocked -- including one case blocked by an agent's own reasoning declining to exploit a documented, technically-available bypass, not by a technical enforcement layer. One unplanned, organic finding: a subagent fabricated a specific, confident security claim (a false prompt-injection report), then correctly retracted it only when directly pressed to produce verbatim evidence -- recorded as its own distinct failure category, not folded into the boundary-test results.

## Projected impact (not measured -- clearly distinguished from the above)

No live team's prior manual process exists for this project to measure a true before/after against (`module4_doc/workflow-scoping.md`). The following is **context**, not a claim about this project's own history:

- Published industry research on code review overhead (Google's internal engineering-productivity data, cited via secondary sources; SonarSource/Infragistics developer-time surveys) suggests the general category of work this system addresses typically costs several hours per developer per week in review/coordination overhead, separate from actual coding time.
- *If* the `orchestrator_test`-style conversion pattern (measure an agentic step, convert if it clears all four signals, verify with a real regression check) were applied to other qualifying steps in this system, similar latency/cost reductions could reasonably be expected for steps that share the same four-signal profile -- this is a reasonable extrapolation from one real data point, not a second measurement. `ADR-002` (the line-ending-noise step) was evaluated against this same process and correctly found *not* to qualify for full conversion, which is itself evidence the process doesn't just rubber-stamp every candidate toward "yes."

## Tool-evolution drill summary

Full write-up: `module4_doc/tool-evolution-drill.md`. Drill type: "convert another step" (`orchestrator_test`, `ADR-001`). The regression-check process, run against real post-integration evidence, surfaced two real transcript-authoring defects neither caught by manual read-through -- one a malformed field type causing an unhandled crash in the harness itself (a disclosed harness-robustness gap, not silently patched over), the other a wrong step-ordering claim. Both were corrected; the underlying conversion itself showed no regression across 4 real end-to-end runs.
