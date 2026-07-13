---
name: spec-lite
description: "Explicit-invocation lightweight specification skill for turning converged intent into an outcome contract. Invoke when a user or an explicit orchestrator requests a spec, outcome contract, acceptance spec, or durable handoff."
disable-model-invocation: true
argument-hint: "goal, alignment snapshot, issue, PRD, bug repro, or behavior to specify"
---

# Spec Lite

Create a compact outcome contract when conversation-only context is no longer enough. This preserves the useful part of Superpowers-style specs without making every task pass through a spec ceremony.

## Contract binding

<!-- handrails-contract
contract: usable-loop/v1
role: outcome-contract-author
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

Consume an existing Outcome Reference when present. If none exists, bootstrap one from the current request with a task-local stable Task ID, a truthful request/conversation locator, `provisional` authority, a compact snapshot, and explicit stale conditions.

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

Creating or saving a spec does not itself increase authority. A materially changed spec creates a new Outcome Revision, points `Supersedes` at the exact prior reference, and inherits provisional authority until the designated authority explicitly confirms it. If authority is inaccessible, conflicts with another designated source, or the revision mismatches, mark the reference provisional/stale and stale any dependent evidence or claims. Never choose between authorities by recency or durability. A local Capsule is orientation only, never the Outcome Source.

When a new spec revision supersedes an earlier reference, mark the prior reference lifecycle `superseded`; only the new reference remains `active`.

If a Local Capsule points to this spec, keep the spec's source locator and exact Outcome Revision in the Capsule. On resume, read this spec first and compare revisions; never reconstruct or overwrite spec authority from the Capsule snapshot. Promote durable outcome decisions here only when a spec is already warranted—do not create a spec merely to empty a Capsule.

Never describe an Outcome Revision as a hash or digest unless it was actually computed over identified canonical bytes; otherwise use an honest task-local opaque revision such as `r1`.

## When to use

Use this only when a formalized outcome contract materially helps:

- Multiple sessions, agents, or humans need a designated Outcome Source.
- The task has complex domain behavior, state transitions, data contracts, permissions, or rollback requirements.
- Acceptance criteria are high-risk, easy to misunderstand, or likely to be reviewed later.
- A plan needs stable outcome boundaries before implementation.
- the user explicitly asks for a spec, acceptance contract, handoff note, or durable alignment doc.

Do not use this for clear operational micro-tasks, tiny bug fixes, or situations where an `grill` alignment snapshot or `plan-lite` acceptance criteria are enough.

## Rules

- Do not let ambient model matching select this skill. Invocation must come from the user or an explicit orchestrator/harness decision.
- Do not invent product decisions, domain rules, API contracts, or acceptance criteria. If missing information changes implementation or verification, ask one focused question or mark it as an open question.
- Keep the spec outcome-focused. Do not turn it into an implementation plan, task list, or code skeleton.
- Prefer concise, reviewable contracts over comprehensive documents.
- Preserve currentness. A stale spec is worse than no spec.
- Treat `Last updated` as human metadata, never as the Outcome Revision.
- Echo an unchanged input reference with its authority intact. Any materially changed or newly authored revision starts `provisional` and becomes `authoritative` only when the designated authority explicitly confirms that exact revision.
- If code/docs can answer a factual question, inspect them instead of asking.
- Explicitly separate decided behavior from assumptions and open questions.

## Relationship to other skills

- `grill` resolves uncertainty and can produce an Alignment Snapshot.
- `spec-lite` freezes enough of that intent into an outcome contract when needed.
- `plan-lite` turns the outcome contract into execution strategy and tasks.
- `two-axis-review` later checks implementation against the exact Outcome Reference; this spec may be its designated source.

Typical flow:

```text
grill -> optional spec-lite -> plan-lite -> implementation -> two-axis-review -> verify-before-claim
```

## Process

1. **Collect source context**
   - User request, issue, PRD, bug repro, deployment objective, or alignment snapshot.
   - Relevant repo docs, existing behavior, APIs, tests, domain language, and runtime constraints when available.
   - Explicit constraints: non-goals, safety, compatibility, performance, data, rollout, rollback.

2. **Decide spec depth**
   Choose the smallest useful contract:
   - Acceptance spec: goal + criteria + non-goals + verification.
   - Behavior spec: user/system behavior, states, edge cases, failure modes.
   - Interface spec: API/data/event/schema contract and compatibility rules.
   - Handoff spec: decisions, assumptions, open questions, owners, currentness.

3. **Write the spec**

   ```markdown
   # <Feature / Behavior / Change> Spec

   Contract: usable-loop/v1
   Task ID:
   Outcome Source kind: echo the input; use `spec` only when this spec is explicitly designated as a superseding source
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

   Status: draft | active | superseded
   Last updated:
   Implementation readiness: ready | blocked

   ## Source context
   - Origin:
   - Related issue / PRD / conversation / bug repro:
   - Existing behavior inspected:

   ## Goal
   <what should be true after this>

   ## Non-goals
   <what must not change or is intentionally out of scope>

   ## Users / actors / systems
   <who or what interacts with this behavior>

   ## Desired behavior
   - <observable behavior>
   - <state transition or domain rule>
   - <edge case / boundary condition>

   ## Contracts
   - API / CLI / UI / data / event contract:
   - Backward compatibility:
   - Error semantics:

   ## Constraints and risks
   - Runtime / environment:
   - Security / privacy / safety:
   - Performance / scale:
   - Rollout / rollback:
   - Observability:

   ## Acceptance criteria
   - [ ] <criterion that can be verified>
   - [ ] <criterion that can be verified>

   ## Verification signals
   - Focused:
   - Integration / smoke:
   - Build / type / lint:
   - Runtime / deployment, if relevant:

   ## Assumptions
   - <assumption and why it is acceptable>

   ## Open questions
   - <question, why it matters, who can answer>
   ```

4. **Review the spec before handoff**
   - Is every acceptance criterion observable?
   - Are non-goals explicit enough to prevent scope creep?
   - Are assumptions separated from decisions?
   - Does verification prove outcome-level behavior rather than only function-level behavior?
   - Is the spec small enough that an implementation agent will actually follow it?

5. **Choose persistence**
   - Keep in conversation if it is only needed for the current session.
   - Save to a file only when it is durable coordination/handoff material or the user asks.
   - If saved, include currentness markers and link it from the plan/review prompt.
   - Saving changes the artifact locator. Create a superseding Outcome Reference only when the saved spec is explicitly designated as the new source; otherwise preserve the input reference and treat the saved spec as a derived contract.

## Output shape

End with:

```markdown
## Spec handoff
- Exact Outcome Reference to use in planning/review:
- Recommended next skill: plan-lite | feedback-loop | two-axis-review | none
- Must resolve before implementation:
- Safe to implement now: yes | no, because ...
```

## Anti-patterns

- Writing a spec before the core uncertainty is understood.
- Treating a plan as a spec or a spec as a plan.
- Burying open questions inside acceptance criteria.
- Specifying implementation internals that should remain design choices.
- Producing a long document no agent will reread.
- Letting an old spec override newer conversation decisions without explicitly updating status.
