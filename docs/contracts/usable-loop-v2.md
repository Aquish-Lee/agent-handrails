# usable-loop/v2 semantic contract

`usable-loop/v2` is the active contract for Agent Handrails. Its machine source
of truth is `contracts/usable-loop-v2.json`; generated skill-local references
are self-contained projections, not independent specifications.

## Design spine

```text
Outcome → authorized state boundary → evidence → proportionate claim
```

Handrails remain explicit, independently useful tools. No skill may silently
invoke another or turn the seven tools into a mandatory workflow.

## Authority

A current user request is `authoritative` when the user controls the requested
scope and no permission or designated-source conflict exists. Agent-derived,
reinterpreted, inaccessible, or conflicting meaning is `provisional`. Saving a
record never upgrades authority.

## Claim-scaled verification

- `fact`: a narrow observable fact. Produce claim evidence and a Claim Record;
  do not require a boundary or review.
- `scoped-task`: completion of a bounded small code task. Confirm a Claim
  Boundary over every current candidate, run the narrow checks, then issue the
  Claim Record.
- `high-assurance`: merge-ready, integrated, production/deployment safe,
  no-regressions, or an equivalently broad assertion. Consume a Review Record
  whose Outcome Revision, Boundary Digest, and Code State Token match exactly.

## Deterministic boundaries

`runtime/handrails_state.py` exposes `inventory`, `confirm`, and `capture`.
Inventory assigns IDs from mechanical fingerprints. Humans or agents classify
only those IDs and provide rationale plus authorization state. Confirm requires
complete, non-overlapping coverage, computes the canonical digest itself, and
recaptures state. `confirm --boundary-out <path>` atomically persists the full
confirmed boundary while compact stdout remains a summary. Capture rejects a
modified payload or any later drift.

Rationale is canonical semantic content, not presentation prose. Changing the
rationale creates a different semantic boundary. A caller therefore persists
one confirmed boundary and later captures that exact artifact instead of
reconfirming merely to reconstruct a discarded payload.

An explicit boundary output path may be outside participating worktrees. Inside
a participating worktree it must be ignored and must not fall within any
declared ignored candidate. This prevents publishing machine evidence from
changing the state it just confirmed. Ignored logs or `.scratch` content are not
declared merely because they exist; declaration means their content belongs in
the task boundary.

Tracked files are classified by hunk. Untracked and explicitly declared ignored
artifacts are classified by complete content. Ignored content is never scanned
without an explicit declaration.

Compact inventory is a classification-routing projection, not another source
of mechanical truth. Candidate/Hunk IDs remain bound to full fingerprints in
the runtime, while redundant fingerprint strings and canonical payloads stay out
of ordinary agent context. The projection identifies its contract/schema/base,
provides counts, workspaces, and candidates, and remains self-describing without
runtime-source inspection. Machine inventories and full boundaries should be
redirected to private files and queried incrementally.

## Evidence and review ownership

Feedback Loop produces development evidence with `observed | stale | blocked`.
Observed evidence guides development but cannot support a completion claim.
Verify Before Claim produces claim evidence with `fresh | stale | blocked`.
Two-Axis Review produces both a confirmed Review Boundary and a Review Record
containing Outcome Fit findings, Engineering Quality findings, recommendation,
missing evidence, time, and invalidation rules.

Any Outcome Revision, Boundary Digest, relevant code state, or relevant
environment change stales the dependent record. v2 does not reuse old evidence
after proving a change unrelated; rerun the narrowest relevant check.

## Continuity and output

Ordinary direct calls return only conclusion, evidence, scope limits, and the
necessary next step. A full Checkpoint is optional for every handrail and is
expanded only on pause/block, cross-session or agent handoff, context risk,
expensive/non-repeatable evidence, or explicit request. When persisted, rewrite
the single `.scratch/<task-id>/STATE.md` Capsule. It is orientation only.

High-assurance review starts with a risk map and inspects every candidate/hunk;
risk changes inspection depth, never boundary coverage. Full contracts, record
templates, broad diffs, and smell references load only when a specific question
requires them. Source inspection is bounded to one changed source, at most 20
context lines, and at most 240 output lines per command, with a private coverage
ledger preventing accidental rereads.

Changed-file content first passes through the bundled safe-diff preflight. It
privately checks review-base and current content as well as the bounded diff.
Sensitive paths, credential-bearing assignments, and credential-shaped tokens
produce structural redaction only; historical, current, and replacement values
must not enter the transcript. A redacted result cannot be bypassed through
direct file, diff, history, search, or fixture output. Non-sensitive raw output
remains bounded, and lock/generated content stays summary-only.

## Safety

Stash, force branch deletion, deletion of a worktree containing results, reset,
rebase, and overwrite operations require explicit authorization. The default is
to report a cleanup command without executing it.
