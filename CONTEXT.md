# Agent Handrails Context

## Bounded context

Agent Handrails provides seven explicit, independently useful engineering primitives for AI coding agents. They are a toolbox rather than a mandatory workflow or hidden orchestrator.

The shared domain spine is:

```text
Outcome → Decision and Boundary → Evidence → Claim
```

## Domain invariants

- Invocation is explicit: a person or visible orchestrator selects a handrail.
- Use the smallest professionally adequate path for the task.
- Persistence does not confer authority.
- An agent-generated spec, plan, or checkpoint cannot silently upgrade its input authority.
- Evidence is valid only for its bound outcome revision, code state, boundary, environment, and claim scope.
- A Review Boundary Seed is a hypothesis, never an allowlist.
- A Local Capsule is a disposable cache, never an Outcome Source.
- Every deployed skill must retain the minimum contract needed to work when copied alone.

## Ubiquitous language

### Task ID

The stable identity of one engineering task across skills, sessions, Outcome Source revisions, and workspaces. It is not a branch name, Issue ID, or Outcome Revision, though one of those may help derive it.

### Outcome Source

The original carrier of intended results: a request, conversation, alignment snapshot, issue, PRD, spec, bug repro, deployment objective, or other explicitly designated source. Saving a source does not automatically make it authoritative.

### Outcome Revision

An exact, comparable version of the outcome meaning. Use a source-native immutable revision plus a compact outcome digest when available; otherwise use a task-local opaque revision grounded in the snapshot. A timestamp or `Last updated` field alone is not an Outcome Revision.

### Outcome Reference

The handoff record that binds a Task ID to an exact Outcome Source ID, locator, Outcome Revision, authority basis, compact snapshot, lifecycle, currentness, supersession, and stale conditions. It identifies the outcome; it is not the Outcome Source itself.

### Outcome Authority

Whether the current reference has been reconciled with the person, repository policy, or explicitly authorized source that may define the outcome. `authoritative` and `provisional` describe this relationship, not confidence or document durability.

### Supersession

An explicit relationship in which a new Outcome Reference replaces one exact prior revision and records the authority basis. Newer timestamps or more durable files do not supersede automatically.

### Staleness

A state in which a record can no longer be shown to match its dependencies. Stale records remain useful history but cannot support a current approval or completion claim until reconciled and, where needed, reverified.

### Work Boundary

The authorization and isolation boundary: repository/workspace, permitted scope, forbidden scope, guardrails, and rollback path. It does not decide which current changes must be reviewed.

### Logical Change Unit

A plan's intended commit, review, integration, or rollback slice. It organizes execution but is not the final Review Boundary.

### Review Boundary Seed

Planning hypotheses about expected logical changes, dependent/generated changes, authorization guardrails, known pre-existing changes, and participating workspaces. Omitted paths are not proven unrelated.

### Review Boundary

The actual review scope produced only after inventorying the current participating workspaces and classifying every candidate change. A commit range or planned file list cannot substitute for it.

### Boundary Digest

A reproducible digest of the confirmed inventory, classifications, and workspace identities. It fingerprints an already-made semantic boundary decision; it does not decide task relevance.

### Checkpoint

A compact structured view of current task state: outcome reference, boundary state, done/next/blockers, decisions, evidence, claims, and invalidation rules. It lives in conversation by default.

### Local Capsule

The optional, single, rewritten `.scratch/<task-id>/STATE.md` representation of a Checkpoint. It restores orientation after continuity risk but never supplies authority, Outcome Revision, or evidence freshness.

### Code State Token

A mechanical capture of exact repository, workspace, VCS, boundary, and relevant environment state. It does not determine which changes are task-related.

### Evidence Record

An observed check/result bound to an Outcome Revision, Boundary Digest, Code State Token, environment, time, and narrow scope. Evidence is not itself a completion claim.

### Claim Record

A result statement whose wording and scope do not exceed its fresh Evidence Records. It records unsupported portions and stale conditions explicitly.

## Relationship summary

```text
Outcome Source + Outcome Revision
  → Outcome Reference
  → Plan + Review Boundary Seed
  → Review Boundary + Boundary Digest + Code State Token
  → Evidence Record
  → Claim Record
```

Work Boundary constrains authorization throughout. Checkpoints may summarize every stage; a Local Capsule only caches that summary.

## Canonical specifications

- Contract semantics: `docs/contracts/usable-loop-v1.md`
- Machine catalog: `contracts/usable-loop-v1.json`
- Architecture decision: `docs/adr/0001-versioned-usable-loop-contract.md`
