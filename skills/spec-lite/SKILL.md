---
name: spec-lite
description: Turn converged intent into a lightweight outcome contract when a user explicitly requests a spec or durable acceptance semantics are needed before consequential implementation. Skip routine tasks and unresolved discovery.
---

# Spec Lite

Record what must be true without prescribing unnecessary implementation detail.
This is an optional outcome contract, not a required document in every task.

<!-- handrails-contract
contract: usable-loop/v2
role: outcome-contract-author
reference: references/usable-loop-v2.md
runtime: none
-->

Read [the local v2 contract](references/usable-loop-v2.md) for exact record and
authority fields.

## When to write a spec

Use this skill for durable behavior/acceptance semantics, cross-session
coordination, public interfaces, migrations, or consequential tradeoffs. Return
to alignment when core intent remains unresolved. Skip a spec for a clear
micro-task or when a plan alone is enough.

An unconflicted current user request is authoritative when the user controls the
task. Preserve its exact meaning. Any agent-generated elaboration, inferred
constraint, or reinterpretation is provisional until confirmed.

## Write the outcome contract

Keep the document proportional and include:

- complete Outcome Reference;
- goal and non-goals;
- desired externally observable behavior;
- constraints, compatibility, risks, and authorization limits;
- testable acceptance criteria;
- verification signals;
- assumptions and open questions;
- implementation readiness: `ready | conditionally-ready | not-ready`.

Separate facts, user decisions, and assumptions. Avoid architecture or file-level
prescription unless the outcome depends on it. Use examples for semantic edge
cases when prose would remain ambiguous.

Do not make persistence confer authority. A repository spec can be provisional;
a conversational request can be authoritative. When the outcome changes, create
a new Outcome Revision and supersede the exact old revision rather than editing
history conceptually.

## Direct result

Lead with readiness and the agreed behavior, then acceptance criteria,
constraints, and unresolved blockers. Do not create a plan or invoke another
handrail automatically. Expand a Checkpoint only on a continuity trigger.
