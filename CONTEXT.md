# Agent Handrails Context

## Bounded context

Agent Handrails provides seven explicit, independently useful engineering
primitives for AI coding agents. They are a toolbox, not a mandatory workflow or
hidden orchestrator.

```text
Outcome → authorized state boundary → evidence → proportionate claim
```

## Domain invariants

- A person or visible orchestrator selects each handrail explicitly.
- Use the smallest professionally adequate path for the requested claim/task.
- A current user request is authoritative when the user controls the scope and
  no permission or designated-source conflict exists.
- Agent-derived or reinterpreted outcome meaning is provisional.
- Persistence never upgrades authority or evidence freshness.
- A Review Boundary Seed is a hypothesis, never an allowlist.
- Boundary IDs/digests are runtime-generated from canonical mechanical state.
- Development evidence guides work but cannot support a completion claim.
- Any relevant outcome, boundary, state, or environment change stales dependent
  evidence; v2 reruns the narrowest check instead of reusing it.
- Checkpoints are shared, optional continuity projections. A Local Capsule is a
  disposable orientation cache, never an Outcome Source.
- Every deployed skill remains usable when copied alone.

## Ubiquitous language

### Task ID

Stable task identity across skills, sessions, revisions, and workspaces. It is
not an Outcome Revision or branch name.

### Outcome Source and Revision

The source carries intended results: request, conversation, alignment snapshot,
issue, PRD, spec, bug repro, deployment objective, or another designated source.
Outcome Revision identifies one exact meaning. Use a native immutable revision
and digest when available; otherwise use an honest task-local opaque revision.

### Outcome Reference

The shared record binding Task ID to source identity/locator, Outcome Revision,
authority basis, snapshot, lifecycle, currentness, supersession, and stale
conditions. It identifies the outcome but is not the Outcome Source itself.

### Work Boundary and Review Boundary Seed

Work Boundary records actual task-start isolation and authorization state.
Review Boundary Seed records planning hypotheses, dependencies, guardrails,
known pre-existing work, and participating workspaces. Neither is a final review
allowlist.

### Candidate, Hunk, and Logical Unit

The runtime inventories current committed-since-base, staged, unstaged,
untracked, and explicitly declared ignored state. It creates a Candidate ID from
workspace, layer, path, and fingerprint. Tracked candidates are split into Hunk
IDs; untracked/declared-ignored artifacts are whole-content units. A semantic
classification applies to exactly one runtime ID.

### Claim Boundary and Review Boundary

A Claim Boundary scopes a `scoped-task` completion claim. A Review Boundary
scopes the two-axis review used for a `high-assurance` claim. Both use the same
canonical runtime but distinct classification schemas.

### Code State Token

A mechanical binding of Boundary Digest, Inventory Digest, repository/base,
participating workspaces, relevant environment, and capture time. It does not
decide semantic relevance.

### Development Evidence and Claim Evidence

Feedback Loop produces development evidence (`observed | stale | blocked`) to
guide the next change. Verify Before Claim produces claim evidence (`fresh |
stale | blocked`) that may support exact claim wording while its bindings match.

### Review Record

Two-Axis Review's formal output: Review ID, Outcome Revision, Boundary Digest,
Code State Token, Outcome Fit findings, Engineering Quality findings,
recommendation, missing evidence, time, and stale conditions.

### Claim Record

A claim classified as:

- `fact`: direct fresh claim evidence, no boundary/review;
- `scoped-task`: exact Claim Boundary plus fresh claim evidence;
- `high-assurance`: exact current Review Record plus supporting claim evidence.

### Checkpoint and Local Capsule

Any handrail may expand a Checkpoint on pause/block, handoff, context risk,
expensive evidence, or explicit request. A persisted Capsule rewrites the single
`.scratch/<task-id>/STATE.md` and is orientation only.

## Canonical specifications

- Active semantics: `docs/contracts/usable-loop-v2.md`
- Active machine contract: `contracts/usable-loop-v2.json`
- v2 decision: `docs/adr/0002-deterministic-claim-scaled-usable-loop-v2.md`
- Immutable predecessor: `usable-loop/v1` and ADR 0001
