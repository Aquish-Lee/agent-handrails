---
name: plan-lite
description: Create a compact implementation strategy when a user explicitly requests a plan or a non-trivial task needs ordered, verifiable work slices, risk controls, and a review-boundary seed. Skip obvious single-step edits.
---

# Plan Lite

Turn a sufficiently clear outcome into the smallest plan that makes execution,
verification, review, and rollback legible.

<!-- handrails-contract
contract: usable-loop/v2
role: execution-planner
reference: references/usable-loop-v2.md
runtime: none
-->

Read [the local v2 contract](references/usable-loop-v2.md) for complete record
fields and authority/invalidation rules.

## Preconditions

Use the current request, Alignment Snapshot, or Outcome Contract as the outcome
source. An unconflicted current user request is authoritative when the user owns
the task. Agent-derived interpretation is provisional. If a missing decision
would materially change the plan, expose it instead of burying it as a task.

Do not require a spec. Do not plan a clear one-step edit. Do not execute the plan
or silently invoke another handrail.

## Build the implementation map

State:

1. goal, acceptance criteria, and non-goals;
2. chosen implementation strategy and major tradeoffs;
3. ordered vertical slices with observable completion;
4. verification at the narrow, integration, and risk-specific levels;
5. isolation/rollback needs and explicit authorization gates;
6. known dependencies, unknowns, and stopping conditions.

Prefer independently verifiable slices over file-by-file activity lists. Name
likely files only when they clarify navigation; planned paths are hypotheses.

## Review Boundary Seed

Produce a compact seed containing:

- exact Outcome Reference binding;
- expected logical changes;
- dependent/generated changes;
- authorization guardrails;
- known pre-existing changes;
- participating workspaces;
- base/recovery hints;
- open boundary questions;
- `Path semantics: hypotheses-not-allowlist`.

The seed does not approve omitted paths and does not classify future changes.
Branch Sandbox may record actual task-start delta from it. Two-Axis Review or
Verify Before Claim must inventory and classify current candidates mechanically.

## Direct result

Return the strategy, ordered slices, verification matrix, main risk/rollback,
and Review Boundary Seed. Keep it conversational unless the user asks for a
durable artifact. Bind Task ID, Outcome Revision, and Authority in one line by
default; do not expand the full Outcome Reference or record schema unless the
user explicitly asks for it or continuity requires it. Use a Checkpoint only on
a continuity trigger.
