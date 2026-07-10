---
name: grill
description: "Explicit-invocation design grilling for clarifying intent, constraints, risks, and decision branches before non-trivial work. Invoke when a user or an explicit orchestrator requests grilling, stress-testing, clarification, or interrogation of a plan/design."
disable-model-invocation: true
argument-hint: "plan, feature, architecture, or uncertainty to grill"
---

# Grill

Use this as a lightweight alternative to Superpowers brainstorming: clarify enough to work professionally, without forcing a full spec ceremony.

## Contract binding

<!-- handrails-contract
contract: usable-loop/v1
role: outcome-aligner
missing-outcome-reference: bootstrap-provisional
authority-failure: stale-until-reconfirmed
authority-failure-triggers: authority-inaccessible,authority-conflict,authority-revision-mismatch
outcome-record: outcome-reference
required-local-resources: none
bootstrap-authority: provisional
bootstrap-lifecycle: active
bootstrap-currentness: fresh
outcome-reference-output: complete
identity-revision-separation: required
revision-digest-claim: computed-only
-->

Carry an existing Outcome Reference forward. If none is available, create one from the current request: keep a task-local stable Task ID, use the visible request/conversation as the source without inventing a durable locator, set authority to `provisional`, and record a compact outcome snapshot plus concrete stale conditions.

```text
Contract: usable-loop/v1
Task ID:
Outcome Source kind: request | conversation | alignment-snapshot | issue | prd | spec | bug-repro | deployment-objective | other
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
Stale when:
```

When bootstrapping, populate and emit every field in this template; do not replace the record with an ID-only shorthand. When consuming a reference, preserve its exact values unless this skill explicitly creates a superseding revision.

Bootstrap state is always: authority `provisional`, lifecycle `active`, currentness `fresh`.

Keep Task ID and Outcome Source ID independent of Outcome Revision: do not put `r1`, a digest, or another revision suffix into either identity.

Do not raise authority merely because a spec, plan, or file was created. If the designated authority is inaccessible, conflicts with another designated source, or its revision does not match, mark the reference provisional/stale and treat dependent evidence and claims as stale until the outcome is reconciled or reconfirmed. Never choose between authorities by recency or durability. A local Capsule may restore orientation but never becomes the Outcome Source.

Never describe an Outcome Revision as a hash or digest unless it was actually computed over identified canonical bytes; otherwise use an honest task-local opaque revision such as `r1`.

## Rules

- Do not let ambient model matching select this skill. Invocation must come from the user or an explicit orchestrator/harness decision.
- Ask one question at a time.
- If code/docs can answer a question, inspect them instead of asking.
- Do not reduce open engineering decisions to forced A/B/C choices. Offer multiple valuable approaches when useful, but preserve open-ended reasoning.
- For every meaningful question, include your current recommendation and why; the user should get judgment, not just interrogation.
- Stop when the remaining uncertainty no longer changes implementation strategy, verification strategy, or risk handling.
- Do not block simple operational or small coding tasks unless the user asks to grill them.
- Do not produce a formal spec by default. If the converged outcome needs durable coordination or handoff, recommend `spec-lite`.

## Task-shape calibration, not classification

Software work is open-ended. Do not force tasks into rigid risk levels. Instead, use the likely task shape only to choose how deep the grilling should go.

Common task shapes:

- **Operational micro-task**: run service, inspect state, produce executable commands.
- **Bug fix**: diagnose an error, reproduce/fix/verify a failure.
- **Feature work**: implement a behavior, usually as a small set of todos.
- **Goal-mode development**: complete a phase with acceptance criteria and an approximate direction.
- **Large refactor**: execute a planned code restructuring with broad blast radius.
- **Deployment / migration**: move locally verified work to a server or different runtime environment.
- **Unknown / hybrid**: any task that does not fit cleanly; treat the shape as uncertain.

Begin with a lightweight read such as:

```text
I read this as <task shape>, so I will grill mainly on <decision areas>. If that framing is wrong, correct me.
```

This read is a calibration aid, not a gate.

## Process

1. **Frame the work**
   - Desired outcome: what should be true after this?
   - Non-goals: what should not change?
   - Constraints: time, environment, repo conventions, deployment/runtime, safety.
   - Blast radius: files, services, data, users, runtime.

2. **Find decision branches**
   - Architecture / interface choices.
   - Data model and state transitions.
   - Failure modes, rollback, observability.
   - Test seams and verification signals.
   - Human/product decisions that cannot be inferred from code.

3. **Question one branch at a time**
   Ask in this shape:
   ```text
   Question: ...
   Why it matters: ...
   My current recommendation: ...
   Alternative approaches worth considering: ...
   What I need from you: ...
   ```

   Alternatives may be two options, five options, a continuum, a trade-off matrix, or an open design space. Choose the form that best preserves reasoning quality.

4. **Converge**
   When enough is clear, produce an alignment snapshot. If convergence materially changes the outcome meaning, issue a new Outcome Revision and point `Supersedes` to the prior exact reference. Mark it `authoritative` only when the designated authority explicitly confirms it.

   When emitting that superseding revision, also mark the prior reference lifecycle `superseded`; only the new reference remains `active`.

   ```markdown
   ## Alignment Snapshot
   ### Outcome Reference
   - Contract: usable-loop/v1
   - Task ID:
   - Outcome Source kind: echo the input; use `alignment-snapshot` only for an explicit superseding reference
   - Outcome Source ID:
   - Outcome Source locator:
   - Outcome Revision:
   - Revision basis:
   - Outcome Authority: authoritative | provisional
   - Authority basis:
   - Outcome lifecycle: active | superseded
   - Outcome snapshot:
   - Outcome currentness: fresh | unknown | stale
   - Supersedes, if any:
   - Stale when:

   - Task shape / framing:
   - Goal:
   - Non-goals:
   - Chosen direction:
   - Key constraints:
   - Decisions resolved:
   - Open risks or unknowns:
   - Verification signals:
   - Suggested next skill: spec-lite | plan-lite | feedback-loop | two-axis-review | verify-before-claim | branch-sandbox | none
   ```

   Do not produce a spec by default. If the discussion has converged and a formal spec would help the agent or future sessions, recommend `spec-lite` before planning.

   If the Alignment Snapshot only restates the current outcome, embed the exact input Outcome Reference unchanged. Creating a role artifact does not by itself create a new Outcome Source.

## Professional bar

Good grilling reduces rework and increases design quality. Bad grilling is performative questioning or premature narrowing. Prefer questions that change design, testing, rollout, rollback, or risk handling.
