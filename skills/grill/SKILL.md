---
name: grill
description: Interrogate consequential uncertainty when a user explicitly asks for rigorous clarification or a non-trivial task has unresolved goals, constraints, tradeoffs, or acceptance signals. Skip settled work and low-cost micro-decisions.
---

# Grill

Resolve only the uncertainty that could materially change the outcome,
architecture, authorization, or verification strategy.

<!-- handrails-contract
contract: usable-loop/v2
role: outcome-aligner
reference: references/usable-loop-v2.md
runtime: none
-->

Read [the local v2 contract](references/usable-loop-v2.md) for the full Alignment
Snapshot and Outcome Reference shapes.

## Calibrate the questioning

Do not question for ceremony. Skip or stop when the task is already
decision-complete. Focus on uncertainties with high consequence and low
reversibility:

- what result must be true for the user;
- who or what has authority to define that result;
- constraints, non-goals, compatibility, and safety boundaries;
- the tradeoff between plausible approaches;
- observable acceptance and failure signals.

Ask one compact cluster at a time. Explain why an answer changes the design when
that is not obvious. Use repository evidence for discoverable facts instead of
asking the user to repeat them.

## Authority handling

A current request is authoritative when the user owns its scope and no source
or permission conflict exists. Agent-created options and interpretations remain
provisional until selected. Do not let a saved spec, plan, Capsule, or previous
answer silently override the current designated authority.

## Converge

When the consequential questions are settled, return a compact Alignment
Snapshot:

- Outcome Reference;
- task shape and goal;
- non-goals;
- chosen direction and rejected consequential alternatives;
- key constraints and decisions;
- open risks or unknowns;
- verification signals;
- an optional suggested next handrail.

A suggestion is not an invocation. Do not create a spec or plan unless the user
asked for one. For a micro-task, a short conversational alignment is enough.

## Direct result

Lead with the resolved decision, then remaining material uncertainty and its
impact. Expand a full Checkpoint only for a continuity trigger.
