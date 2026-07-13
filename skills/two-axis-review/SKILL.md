---
name: two-axis-review
description: Review an explicitly requested current task or integration candidate on Outcome Fit and Engineering Quality, including dirty and multi-worktree state. Produces a deterministic Review Boundary and formal Review Record for high-assurance claims.
---

# Two-Axis Review

Review the actual current state on two separate axes: whether it solves the
intended problem and whether it is engineered safely and maintainably.

<!-- handrails-contract
contract: usable-loop/v2
role: boundary-reviewer
reference: references/usable-loop-v2.md
runtime: scripts/handrails_state.py
-->

Read [the local v2 contract](references/usable-loop-v2.md) for exact Review
Record fields and boundary rules. Use
[the smell baseline](references/smell-baseline.md) as prompts, not a checklist
that replaces judgment.

## Establish the review target

Preserve the exact Outcome Reference. Treat a current, unconflicted user request
as authoritative when the user owns the task; keep derived interpretation
provisional. Identify the task base, all participating worktrees, relevant
environment, explicitly declared ignored artifacts, and any Seed/Work Boundary.

Do not equate the review target with commits. Inventory current committed,
staged, unstaged, untracked, and explicitly declared ignored candidates:

```bash
python <this-skill-dir>/scripts/handrails_state.py inventory \
  --repository . --base <task-base> \
  [--participating-worktree <path>] \
  [--declare-ignored <path>] \
  [--environment KEY=VALUE]
```

Resolve `<this-skill-dir>` from this installed `SKILL.md`, not the project cwd.
In this source repository, use `runtime/handrails_state.py`.

Classify every runtime Candidate/Hunk ID exactly once:

- `include-required`;
- `include-scope-creep`;
- `include-inherited-dependency`;
- `exclude-proven-unrelated`.

Each logical unit needs a concrete rationale and `authorized |
needs-authorization | not-applicable`. Excluded units require evidence of
unrelatedness. Included task/scope-creep units require authorization. Mixed
files are classified hunk by hunk.

Rationale is digest-bound semantic content. Choose a private boundary path
outside participating worktrees; use an already-declared ignored Capsule
location only when a continuity trigger requires persistence. Confirm once with
the same capture parameters:

```bash
python <this-skill-dir>/scripts/handrails_state.py confirm \
  --compact --kind review --classifications <file|-> \
  --boundary-out <private-review-boundary.json> \
  --repository . --base <task-base> [...same capture arguments...]
```

Never invent a Boundary Digest. Missing candidates, overlap, authorization
conflict, state drift, or digest mismatch blocks review.

## Axis 1: Outcome Fit

Check the actual behavior against goals, non-goals, acceptance criteria,
compatibility, failure cases, and user-visible consequences. Distinguish direct
evidence from inference. Development evidence may guide inspection but cannot
support a completion claim.

## Axis 2: Engineering Quality

Inspect correctness, failure handling, security, maintainability, interfaces,
tests, observability, performance, and operational/recovery behavior in
proportion to risk. Report findings by severity with exact locations and impact.
Avoid style-only churn unless it affects maintainability or repository policy.

After the review checks, validate the exact confirmed artifact:

```bash
python <this-skill-dir>/scripts/handrails_state.py capture --compact \
  --boundary <private-review-boundary.json>
```

Do not reconfirm merely to reconstruct a discarded payload. Boundary,
Inventory, and Code State Token mismatch or drift blocks the Review Record.

## Produce the Review Record

After the confirmed Review Boundary remains current, emit:

- Review ID, Task ID, Outcome Revision;
- Boundary Digest and Code State Token;
- Outcome Fit findings and Engineering Quality findings;
- `approve | approve-with-limits | changes-required | blocked`;
- missing evidence, review time, and stale conditions.

Any relevant outcome, boundary, state, or environment change stales the record.
Do not silently repair code during a review-only request.

## Direct result

Lead with blocking/high-severity findings, then recommendation, evidence gaps,
and exact scope. Keep full Boundary/Review records in the response only when the
user requests them or a Checkpoint trigger applies.
