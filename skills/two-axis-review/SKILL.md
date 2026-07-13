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

The normal review path is self-contained. Do not load the full local contract,
runtime source, runtime `--help`, or the complete
[smell baseline](references/smell-baseline.md) by default. Open the contract only
for a user-requested full schema or unresolved contract question; open targeted
smell sections when the risk map points to them. Once Codex injects this Skill,
do not reread this `SKILL.md` from disk.

## Establish the review target

Preserve the exact Outcome Reference. Treat a current, unconflicted user request
as authoritative when the user owns the task; keep derived interpretation
provisional. Identify the task base, all participating worktrees, relevant
environment, explicitly declared ignored artifacts, and any Seed/Work Boundary.

Do not equate the review target with commits. Inventory current committed,
staged, unstaged, untracked, and explicitly declared ignored candidates:

```bash
python <this-skill-dir>/scripts/handrails_state.py inventory \
  --compact --repository . --base <task-base> \
  [--participating-worktree <path>] \
  [--declare-ignored <path>] \
  [--environment KEY=VALUE] \
  > <private-inventory.json>
```

Resolve `<this-skill-dir>` from this installed `SKILL.md`, not the project cwd.
In this source repository, use `runtime/handrails_state.py`.

Never print the complete inventory, canonical payload, full boundary, or an
unbounded repository diff. Query the private inventory for its digest, counts,
path/layer summary, conflicts, and one target set at a time.
Never serialize `candidates` or loop over all Candidate/Hunk records to stdout,
even from compact inventory. A command may expose a bounded path/layer/count
summary or at most one target set per command. Transform IDs privately: scripts
may read every record to build the ledger or classifications, but must write the
classification file without echoing its logical units; print only aggregate
counts or digests. Printing each record in one loop is a full inventory dump and
fails the review-context gate.
Its top-level compact fields are `contract`, `record`, `schema_version`,
`base_revision`, `inventory_digest`, `counts`, `workspaces`, and `candidates`;
do not probe for fields from the full inventory.
Do not declare `.scratch` merely because logs or Handrails artifacts live there.
Declare an ignored artifact only when the task explicitly makes its content a
candidate. A private machine-evidence path inside a worktree must be ignored but
remain undeclared, otherwise writing evidence would stale the boundary.

## Inspect progressively without losing coverage

Build a risk map from the Outcome, repository guidance, worktree/status facts,
diff/numstat and commit summaries, changed interfaces or data paths, and
available tests. Use it to choose inspection depth, not to omit candidates.

Inspect every classified candidate at least once on both Outcome Fit and
Engineering Quality. For a tracked candidate, inspect every hunk; start with a
targeted diff and adjacent tests, then widen into callers, shared invariants,
generated artifacts, migrations, or operations when risk or evidence warrants
it. Never print a raw content diff for a lockfile or generated artifact. Inspect
its generator/source separately, run the authoritative drift or lock check, and
emit only a mechanically derived package/metadata/hash summary of at most 40
lines. Treat supplied test evidence as orientation and rerun only the checks
needed to establish fresh review evidence.

For source/diff inspection, use one changed source file per command.
Use at most 20 context lines and at most 240 output lines. Split the command before
execution when it could exceed that bound. Maintain a private target ledger
recording which Candidate/Hunk IDs were inspected on each axis; never print the
ledger or re-expand an inspected hunk unless a new concrete question requires
it.

Classify every runtime Candidate/Hunk ID exactly once:

- `include-required`;
- `include-scope-creep`;
- `include-inherited-dependency`;
- `exclude-proven-unrelated`.

Each logical unit needs a concrete rationale and `authorized |
needs-authorization | not-applicable`. Excluded units require evidence of
unrelatedness. Included task/scope-creep units require authorization. Mixed
files are classified hunk by hunk. When compact inventory says
`classification_target=hunks`, classify every `hunk_id`, never its parent
Candidate ID; use the Candidate ID only for
`classification_target=candidate`.

Write the private classifications with exactly this top-level shape; no contract
or runtime-source lookup is needed:

```json
{
  "task_id": "stable task ID",
  "outcome_revision": "r1",
  "inventory_digest": "runtime inventory digest",
  "logical_units": [
    {
      "target_id": "runtime candidate or hunk ID",
      "classification": "include-required | include-scope-creep | include-inherited-dependency | exclude-proven-unrelated",
      "rationale": "task-specific semantic reason",
      "authorization": "authorized | needs-authorization | not-applicable"
    }
  ]
}
```

Add `boundary_seed_digest` only when consuming an actual Seed.

Rationale is digest-bound semantic content. Choose a private boundary path
outside participating worktrees, or an ignored Handrails evidence path that
remains undeclared. Never write inside a declared ignored candidate. Confirm
once with the same capture parameters:

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
