---
name: verify-before-claim
description: Verify a requested fact, scoped task completion, or high-assurance readiness claim against fresh evidence. Routes narrow facts without review, builds deterministic Claim Boundaries for small tasks, and requires an exact Review Record for broad claims.
---

# Verify Before Claim

Choose the least expensive path that is still safe for the width of the claim.
Never broaden the claim beyond fresh evidence.

<!-- handrails-contract
contract: usable-loop/v2
role: claim-gate
reference: references/usable-loop-v2.md
runtime: scripts/handrails_state.py
-->

The `fact` route below is self-contained. For a fact, do **not** load the local
reference or state runtime unless the user explicitly requests a full record
schema. For `scoped-task` or `high-assurance`, read
[the local v2 contract](references/usable-loop-v2.md) for full Claim Evidence,
Boundary, Review, and Claim Record fields.

## Route by claim width

Classify the requested wording before running checks:

### `fact`

A narrow observable statement: a command exited successfully, a file exists, a
configuration reads back to a value, or one named check passed. Run the smallest
direct observation. Produce fresh Claim Evidence and a Claim Record. Do not
require a Claim Boundary or Review Record.

For the compact fact result, state claim wording, `claim_kind=fact`, exact check
and result, scope limit, and stale condition. An Evidence ID is optional in the
displayed result unless another consumer needs it.

### `scoped-task`

Completion of a bounded small code task. Inventory every current candidate,
classify all Candidate/Hunk IDs as `include-claim` or
`exclude-proven-unrelated`, include rationale and authorization, and confirm a
Claim Boundary:

```bash
python <this-skill-dir>/scripts/handrails_state.py inventory \
  --repository . --base <task-base> [...]
python <this-skill-dir>/scripts/handrails_state.py confirm \
  --kind claim --classifications <file|-> \
  --repository . --base <task-base> [...same capture arguments...]
```

Resolve `<this-skill-dir>` from this installed `SKILL.md`, not the project cwd.
In this source repository, use `runtime/handrails_state.py`.

Run the narrow checks against that exact state. The Claim Record carries
`claim_boundary_digest` and no Review ID.

### `high-assurance`

Merge-ready, integrated, production/deployment safe, no regressions, or an
equivalently broad claim. Require a formal Review Record. Validate its canonical
boundary and recapture current state:

```bash
python <this-skill-dir>/scripts/handrails_state.py capture \
  --boundary <review-boundary.json>
```

Outcome Revision, Boundary Digest, and Code State Token must match exactly and
the recommendation/evidence must support the requested wording. The Claim
Record carries `review_id` and no Claim Boundary Digest.

If wording is ambiguous, route to the wider safe class or narrow the proposed
claim explicitly. A micro fact must not trigger a hidden review transition.

## Produce claim evidence

Only this skill produces Claim Evidence with `fresh | stale | blocked`. Record:

- Evidence ID, Task ID, Outcome Revision;
- exact code state, boundary/review link when applicable, and environment;
- command/observation, observed result, and narrow scope;
- status, capture time, and stale conditions.

Development evidence from Feedback Loop is orientation only. Rerun the needed
check; do not relabel `observed` evidence as `fresh`. Any relevant outcome,
boundary, code-state, or environment change makes claim evidence stale. v2 does
not preserve it after proving a change unrelated.

## Produce the Claim Record

State exact claim wording, `fact | scoped-task | high-assurance`, Evidence IDs,
`supported | limited | unsupported | blocked | stale`, scope limitations, and
invalidation conditions. Never say done, safe, integrated, or regression-free
when the evidence only supports a narrower fact.

## Direct result

For a fact, use at most 12 lines. For a scoped task, use at most 30 lines.
Default to conclusion, evidence, scope limit, and necessary next step. Expand
full records only on explicit request or a Checkpoint trigger. Do not feed the
result back into Feedback Loop as a mandatory step.
