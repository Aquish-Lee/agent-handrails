---
name: spec-lite
description: "Explicit-invocation lightweight specification skill for turning converged intent into an outcome contract. Invoke when a user or an explicit orchestrator requests a spec, outcome contract, acceptance spec, or durable handoff."
disable-model-invocation: true
argument-hint: "goal, alignment snapshot, issue, PRD, bug repro, or behavior to specify"
---

# Spec Lite

Create a compact outcome contract when conversation-only context is no longer enough. This preserves the useful part of Superpowers-style specs without making every task pass through a spec ceremony.

## When to use

Use this only when a formalized outcome contract materially helps:

- Multiple sessions, agents, or humans need a shared source of truth.
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
- If code/docs can answer a factual question, inspect them instead of asking.
- Explicitly separate decided behavior from assumptions and open questions.

## Relationship to other skills

- `grill` resolves uncertainty and can produce an Alignment Snapshot.
- `spec-lite` freezes enough of that intent into an outcome contract when needed.
- `plan-lite` turns the outcome contract into execution strategy and tasks.
- `two-axis-review` later checks the diff against this spec as one possible Outcome source.

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

   Status: draft | active | superseded
   Last updated:
   Superseded by:
   Stale when:

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

## Output shape

End with:

```markdown
## Spec handoff
- Outcome source to use in planning/review:
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
