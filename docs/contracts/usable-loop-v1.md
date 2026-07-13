# Usable Loop Contract v1

Contract ID: `usable-loop/v1`
Status: active
Scope: seven atomic Agent Handrails

## Purpose and surfaces

This is a handoff contract, not an orchestrator or state machine. Any handrail may be invoked directly, and no sequence is mandatory.

The contract has three synchronized surfaces:

1. `contracts/usable-loop-v1.json` defines record names, required fields, enums, ownership, and skill roles.
2. This document defines canonical semantics and invalidation rules for maintainers.
3. Each `SKILL.md` embeds the minimum rules and fields it needs after independent deployment.

The central files are never a runtime dependency of a copied skill.

The machine catalog marks each record `active` or `planned`. `active` means this repository currently projects and validates that record in its owning skill. `planned` reserves the v1 shape and owner for a later implementation slice; it is not a claim that the current skill already produces or consumes that record. Skill declarations keep active `consumes`/`produces` separate from `planned_consumes`/`planned_produces`.

## Outcome Reference

Every handoff carries this common envelope:

```text
Contract: usable-loop/v1
Task ID:
Outcome Source kind:
Outcome Source ID:
Outcome Source locator:
Outcome Revision:
Revision basis:
Outcome Authority: authoritative | provisional
Authority basis:
Outcome lifecycle: active | superseded
Outcome snapshot:
Outcome currentness: fresh | unknown | stale
Supersedes, if any:
Observed at, if useful:
Stale when:
```

`Task ID` remains stable across supersession. Source ID identifies the carrier and remains stable across that source's revisions. `Source ID + Outcome Revision` identifies one exact outcome meaning; do not encode the revision twice by suffixing Task ID or Source ID with `r1`/a digest.

`Revision basis` must explain why the revision is comparable. Prefer a source-native immutable revision plus a digest of the compact outcome snapshot. When a conversation has no native revision, use a task-local source ID and stable opaque revision grounded in that snapshot. `Last updated` is human metadata, not a revision basis by itself.

Never label a revision as a hash or digest unless it was actually computed over identified canonical bytes. When no deterministic computation was run, use an honest opaque task-local revision such as `r1`.

Authority, lifecycle, and currentness are independent dimensions:

- Authority: `authoritative` or `provisional`.
- Lifecycle: `active` or `superseded`.
- Currentness: `fresh`, `unknown`, or `stale`.

A persisted document can be provisional. A historical authoritative revision can be superseded. A designated source can be active while currentness is unknown because it cannot be read.

## Direct-entry bootstrap

When no Outcome Reference is available, every handrail must create a provisional reference before producing its role-specific result:

1. Reuse a visible task/thread/issue identity when suitable; otherwise create a task-local stable Task ID.
2. Use the current request or conversation as the source.
3. Record a truthful source ID and locator. Do not invent an Issue, spec path, immutable message ID, or durable authority.
4. Create a compact, observable outcome snapshot and a comparable task-local revision.
5. Set authority to `provisional`, lifecycle to `active`, and currentness to `fresh`.
6. Record concrete stale conditions.

Provisional does not mean wrong. It permits bounded, reversible progress when the visible request is sufficient, but it cannot silently resolve consequential ambiguity or support claims that require unavailable authority.

## Authority, reconciliation, and supersession

Skills preserve authority only when echoing the exact unchanged Outcome Reference. Any materially changed or newly agent-authored revision starts `provisional` and becomes `authoritative` only when an authorized person, repository policy, or designated source explicitly confirms that exact revision. Producing a spec, plan, checkpoint, branch, or file never upgrades authority by itself.

A material change to goal, non-goals, acceptance behavior, safety constraints, or verification meaning creates a new Outcome Revision. Implementation detail that does not change the outcome does not.

Supersession must:

- identify the exact prior Source ID and Outcome Revision;
- state the new reference and revision basis;
- preserve the Task ID;
- record the authority basis for replacement;
- mark the prior reference `superseded` rather than silently overwriting it.

When two designated sources conflict, stop and reconcile them. Do not choose by timestamp, file durability, or agent preference.

## Resume and authority failure

On resume:

1. Read the designated source locator when accessible.
2. Compare its exact revision and snapshot.
3. Use a Checkpoint or Local Capsule only to restore orientation.
4. Re-inventory repository/workspace state before reusing evidence.

If the authority is inaccessible or its revision mismatches:

- mark the current reference provisional and currentness stale;
- invalidate dependent Review Boundary Seeds, Evidence Records, and Claim Records;
- retain old records as history;
- reconcile or reconfirm before using them for approval or success claims.

Exploration may continue when safe and reversible, but outcome-dependent approval and completion claims cannot.

## Review Boundary Seed

`plan-lite` owns this planning-time record:

```text
Outcome binding: Task ID + Outcome Source ID + Outcome Revision
Expected logical changes
Dependent or generated changes
Authorization guardrails
Known pre-existing changes
Participating workspaces
Base and recovery hints
Declared ignored artifacts, if any
Open boundary questions
Path semantics: hypotheses-not-allowlist
```

The seed is a hypothesis, not an allowlist.

- Omitted paths are not proven unrelated.
- Known pre-existing changes are exclusion candidates, not exclusions.
- Unexpected task-created changes remain reviewable and are classified as scope creep.
- Planned files do not define the final Review Boundary.
- Ignored artifacts appear only when explicitly declared for the task; never infer common caches, secrets, or generated paths as declarations.
- Only a complete current-state inventory may become the Review Boundary.
- Only the confirmed Review Boundary receives a Boundary Digest.

## Work Boundary and current-state inventory

`branch-sandbox` records the task-start revision, current candidates, participating workspaces, expected logical changes, authorization guardrails, explicit ignored declarations, base/recovery identity, rollback path, and invalidation conditions. Expected paths constrain authorization but do not close review scope.

The active current-state inventory covers committed, staged, unstaged, untracked, explicitly declared ignored artifacts, and every participating workspace/worktree. Untracked metadata is inspected before content. Undeclared ignored paths are neither enumerated nor read.

The bundled `runtime/git_state.py` captures the mechanical Git facts, raw candidate layers, and content fingerprints. It is pure standard-library, read-only, and Git-first. It never decides task relevance. A copied skill retains read-only Git-command fallbacks so the runtime helper is not an external deployment dependency.

## Review Boundary

`two-axis-review` chooses one target: `published-artifact`, `current-task-state`, or `artifact-plus-local`. For the latter two, every mechanical candidate maps to a logical change unit classified as:

- `include-required`;
- `include-scope-creep`;
- `include-inherited-dependency`;
- `exclude-proven-unrelated`; or
- `unresolved`.

Mixed files are split by meaningful hunks/sections/artifacts when classifications differ. Pre-existing, uncommitted, or omitted-from-plan state is not automatically unrelated. Unexpected work caused by the task is scope creep and remains reviewable.

The Boundary Digest is SHA-256 over documented canonical UTF-8 JSON containing outcome revision, review target, participating workspace identities, logical-unit mapping, classifications, artifact fingerprints, unresolved IDs, and relevant mechanical Code State Token fields. The token's `review_boundary_digest`, `captured_at`, and presentation prose are excluded to avoid a digest cycle. Capture mechanics with an unconfirmed boundary, compute the semantic digest, then capture/emit the final token; changed mechanics force another reconciliation. A value may be called a digest only when those canonical bytes were actually hashed.

Any unresolved candidate, changed Boundary Digest, missing participating worktree, or unauthorized scope creep blocks approval and bound success claims.

## Code State Token, Evidence Record, and Claim Record

The active Git Code State Token captures repository/workspace identity, base and exact revisions, recovery identity, conflict state, the confirmed Boundary Digest, candidate inventory, tracked fingerprint, included-untracked and declared-ignored fingerprints, participating-worktree fingerprints, relevant environment, and capture time.

`feedback-loop` captures the token immediately before and after a repository-dependent check and binds the observed result to Outcome Revision, Boundary Digest, token, environment, time, and narrow scope. Evidence stays `unknown` while its boundary is unconfirmed.

`verify-before-claim` captures again immediately before the final claim. A supported Claim Record names its evidence IDs and cannot exceed their narrow scope. Child-worktree evidence supports only that child state until the integrated state is captured and verified.

## Checkpoint and Local Capsule policy

Every `feedback-loop` result contains an active Checkpoint with:

- Task ID and Outcome Reference;
- work/review boundary state;
- Code State Token, repro/baseline, and change delta;
- done, next, and blockers;
- decision and evidence deltas;
- supported claims and still-unverified claims;
- `Stale when` and optional `Delete when`.

Persistence is tiered:

1. Conversation only by default.
2. One rewritten `.scratch/<task-id>/STATE.md` Local Capsule when continuity risk or reconstruction cost becomes material.
3. Issue, PR, spec, or ADR only for durable project coordination.

Materialize the Local Capsule only for a cross-session/agent handoff, context-compaction risk, pause/block, relevant uncommitted state that must survive a handoff, or expensive/non-repeatable evidence. Compactly rewrite the one living file; do not append phase logs or create sibling handoff documents.

A Local Capsule never becomes an Outcome Source, confirms authority, supersedes a reference, or restores evidence freshness. Git ignore is not secure storage: store compact observations, IDs, locators, digests, and reproducible commands, never credentials, secret values, or raw logs. Resume by reading the designated Outcome Source first, then the Capsule, then recapturing all participating state/environment. If it differs from authority or state, the Capsule/evidence is stale as applicable. Delete it only after integration or clean durable handoff, when unique durable information has been promoted or made reproducible.

## Producer and consumer ownership

| Skill | Active inputs/outputs through Task 3 |
| --- | --- |
| `grill` | request/Outcome Reference → Alignment Snapshot and exact Outcome Reference |
| `spec-lite` | Outcome Reference/Alignment Snapshot → Outcome Contract and exact Outcome Reference |
| `plan-lite` | Outcome Reference/Alignment Snapshot/Outcome Contract → Implementation Plan and Review Boundary Seed |
| `branch-sandbox` | Outcome Reference → Work Boundary and recovery identity |
| `feedback-loop` | Outcome Reference/seed/work boundary → Checkpoint, Code State Token, and Evidence Records |
| `two-axis-review` | Outcome/boundary/state/evidence inputs → Review Boundary, Boundary Digest, Code State Token, and findings |
| `verify-before-claim` | Outcome/boundary/state/evidence/checkpoint inputs → Code State Token and scoped Claim Records |

Any skill may bootstrap the common provisional Outcome Reference. Only the role owner produces its specialized record: for example, `plan-lite` produces a Review Boundary Seed, never the final Review Boundary.

All records in `usable-loop/v1` are active and projected by their owning standalone skills.

## Invalidation

| Change | Required effect |
| --- | --- |
| Outcome Revision changes | dependent plan, boundary seed, evidence, and claims become stale |
| Authority is inaccessible or conflicting | current reference becomes provisional/stale; dependent claims become stale |
| Review Boundary or Boundary Digest changes | review recommendation and bound claims become stale; scoped evidence survives only after proven-unrelated reconciliation |
| Relevant Code State Token fields change | affected evidence becomes stale |
| A proven unrelated state change occurs | reconcile the inventory; do not broaden the old claim |
| Relevant environment changes | affected evidence becomes stale |
| Local Capsule differs from authority | Capsule becomes stale; authority is unchanged |

Evidence never transfers automatically to a superseding Outcome Revision. A proven unrelated edit may preserve only the original narrow evidence after inventory reconciliation and Boundary re-digest; the old Evidence Record keeps its original digest and the new claim records the reconciliation. This cannot broaden the claim. Reuse requires current boundary/state capture and evidence whose scope still proves the claim.
