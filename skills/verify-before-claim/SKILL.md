---
name: verify-before-claim
description: Verify a requested fact, scoped task completion, or high-assurance readiness claim against fresh evidence. Routes narrow facts without review, builds deterministic Claim Boundaries for small tasks, and requires an exact Review Record for broad claims.
---

# Verify Before Claim

Choose the least expensive safe path for the claim width. Never broaden the
claim beyond fresh evidence.

<!-- handrails-contract
contract: usable-loop/v2
role: claim-gate
reference: references/usable-loop-v2.md
runtime: scripts/handrails_state.py
-->

The `fact` and `scoped-task` routes are self-contained. Do **not** reread this
SKILL.md, load the local reference, inspect runtime source, or call runtime
`--help` unless execution fails or the user requests a full schema.

## Route by claim width

### `fact`

A narrow observable statement such as a command result, file existence, config
readback, or one named check. Run the smallest observation. Produce fresh Claim
Evidence and a Claim Record without a boundary or review. Return claim wording,
`claim_kind=fact`, check/result, scope limit, and stale condition.

### `scoped-task`

Completion of a bounded small code task. Resolve `<this-skill-dir>` from this
installed Skill; in this source repository use `runtime/handrails_state.py`.
Inventory all current candidates:

```bash
python <this-skill-dir>/scripts/handrails_state.py inventory \
  --compact --repository . --base <task-base> [...] \
  > <private-inventory.json>
```

Keep the machine inventory out of the response and tool transcript. Query its
digest, counts, paths, and one target set at a time. For
`classification_target=hunks`, classify every runtime `hunk_id` and never the
parent Candidate ID; for `classification_target=candidate`, classify its
`candidate_id` once. The private inventory path must be outside participating
worktrees or ignored and undeclared. Pass exactly this shape through stdin:

```json
{
  "task_id": "stable task ID",
  "outcome_revision": "r1",
  "inventory_digest": "runtime inventory digest",
  "logical_units": [
    {
      "target_id": "runtime candidate or hunk ID",
      "classification": "include-claim | exclude-proven-unrelated",
      "rationale": "task-specific reason",
      "authorization": "authorized | not-applicable"
    }
  ]
}
```

Use each runtime target ID exactly once. `include-claim` requires `authorized`;
`exclude-proven-unrelated` requires `not-applicable`. Never invent an ID or
digest. Rationale is digest-bound semantic content. Choose a private boundary
path outside participating worktrees, or an ignored Handrails evidence path
that is **not** passed through `--declare-ignored`. Never write machine evidence
inside a declared ignored candidate; that would immediately stale the state.
Confirm once with the same capture arguments:

```bash
python <this-skill-dir>/scripts/handrails_state.py confirm \
  --compact --kind claim --classifications - \
  --boundary-out <private-claim-boundary.json> \
  --repository . --base <task-base> [...]
```

Run narrow checks. Then validate the exact confirmed artifact:

```bash
python <this-skill-dir>/scripts/handrails_state.py capture --compact \
  --boundary <private-claim-boundary.json>
```

Require its Boundary, Inventory, and Code State Token digests to match the
confirmation. Drift blocks the claim. Do not reconfirm merely to reconstruct a
discarded payload. The Claim Record carries `claim_boundary_digest`, not Review
ID.

### `high-assurance`

Merge-ready, integrated, production/deployment safe, no-regressions, or similar.
Read [the local v2 contract](references/usable-loop-v2.md). Require a formal
Review Record, validate its boundary, and recapture current state:

```bash
python <this-skill-dir>/scripts/handrails_state.py capture \
  --compact --boundary <review-boundary.json>
```

Outcome Revision, Boundary Digest, and Code State Token must match exactly. The
Claim Record carries `review_id`, not Claim Boundary Digest. If wording is
ambiguous, widen the route or explicitly narrow the claim. Never hide a review
transition inside a micro fact.

## Produce claim evidence

Only this skill produces Claim Evidence with `fresh | stale | blocked`.
Development evidence is orientation only. Record Evidence ID, task/outcome,
exact state and environment, boundary/review link, check/result, narrow scope,
capture time, and stale conditions. Outcome, boundary, relevant code state, or
environment changes stale it; rerun the narrow check.

The Claim Record states exact wording, claim kind, Evidence IDs, `supported |
limited | unsupported | blocked | stale`, scope limits, and invalidation. Never
say done, safe, integrated, or regression-free beyond the evidence.

## Direct result

For a fact, use at most 12 lines. For a scoped task, use at most 30 lines.
Return conclusion, evidence, scope limit, and necessary next step. Expand only
on explicit request or a Checkpoint trigger. No mandatory Feedback Loop backflow.
