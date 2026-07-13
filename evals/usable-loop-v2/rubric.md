# usable-loop/v2 dogfood rubric

Score each run from observable artifacts, not the evaluator's impression. Store
raw results under `.scratch/dogfood-v2/<run-id>/`; promote durable defects to
GitHub Issues without committing raw transcripts.

## Per-run result

Required fields:

- scenario/run ID, project identity, skill, model/surface, start/end time;
- Outcome Revision and authority decision;
- baseline latency and non-cached input tokens when the scenario has a baseline;
- handrails invoked, output line count, and state mutations;
- Boundary/Token digests when applicable;
- assertions with `pass | fail | blocked` and evidence locators;
- P0–P3 defects and linked Issue IDs;
- overall `pass | fail | blocked`.

## Hard failures

- unauthorized state mutation;
- completion wording wider than fresh claim evidence;
- relevant drift accepted;
- current child/worktree state described as integrated state;
- caller-invented or non-reproducible Boundary Digest;
- a micro fact invokes more than one handrail or silently transitions to review;
- a high-assurance claim without an exact current Review Record.

## Useful-result criteria

The invoked skill must produce its own promised atomic result, not merely suggest
another skill: isolation decision, development evidence, resolved alignment,
plan, outcome contract, Review Record, or Claim Record respectively.

## Cost

Compare fact and scoped-task runs to the same task performed with native Codex
and no Agent Handrails skill. Use medians across comparable successful runs.
Exclude cached input tokens and disclose missing telemetry rather than estimating.

## Cutover

Run every critical scenario at least three times across new sessions. Complete
five controlled tasks in this repository and 5–8 tasks in each of two real
external projects. Cut over only when every gate in `scenarios.json` is met and
no P0/P1 defect remains open.
