---
name: plan-lite
description: "Explicit-invocation compact implementation planning for multi-step coding tasks. Invoke when a user or an explicit orchestrator requests a plan, task breakdown, tracer bullets, or implementation roadmap."
disable-model-invocation: true
argument-hint: "feature/spec/bugfix to plan"
---

# Plan Lite

Create enough plan to make implementation reliable, without Superpowers-style exhaustive ceremony or a full formal spec.

## Rules

- Do not let ambient model matching select this skill. Invocation must come from the user or an explicit orchestrator/harness decision.
- Do not plan operational micro-tasks unless the user asks; give commands directly and verify instead.
- Do not force rigid risk levels. Use task shape, uncertainty, blast radius, and acceptance criteria to choose planning depth.
- Let task granularity follow complexity. Use enough slices to make the work understandable, executable, and reviewable; do not force an arbitrary task count.
- Keep tasks vertical where possible: behavior + implementation + verification together.
- This is a strategy and execution map, not a mechanical TODO list. Each task must explain intent, boundary, and evidence, not just list chores.
- Include exact files when known; otherwise include an explicit discovery step.
- Include verification for each task and a final verification matrix.
- Include rollback/isolation notes when the change touches deployment, data, broad refactors, or production-like paths.
- Do not paste full implementation code unless API shape, algorithm, or test shape is the thing being decided.

## Relationship to specs

This skill consumes the best available outcome source and turns it into an implementation plan. It does not automatically create a formal spec.

Use `spec-lite` first when the missing piece is a stable outcome contract: behavior rules, interface/data contracts, acceptance criteria, domain invariants, or durable handoff. Otherwise, keep the live outcome source in the current conversation, an `grill` alignment snapshot, an issue/PRD, or this plan's acceptance criteria.

## Before writing the plan

If important gaps remain, do not fabricate. Either:

- ask one clarifying question,
- state assumptions explicitly,
- recommend `grill` first when the uncertainty is a design/product decision,
- or recommend `spec-lite` first when the uncertainty is an outcome contract that should be formalized.

Important gaps include unclear acceptance criteria, unknown target environment, unknown public seam, ambiguous data contract, or disagreement between local and deployment behavior.

## Plan format

```markdown
# <Task> Plan

Task shape:
Goal:
Acceptance criteria:
Non-goals:
Assumptions:
Open questions / known unknowns:
Blast radius:
Primary seams:
Isolation / rollback:

## Implementation strategy
<short explanation of chosen approach and why it is the smallest professional path>

## Tasks

### 1. <Tracer bullet / milestone slice>
Intent:
Scope:
Files:
Steps:
Verification:
Change boundary:

### 2. ...

## Verification matrix
| Layer | Command / check | Expected evidence |
| --- | --- | --- |
| Focused | ... | ... |
| Integration / smoke | ... | ... |
| Build / type / lint | ... | ... |
| Deployment / runtime, if relevant | ... | ... |

## Review gate
Use `two-axis-review` if this changes behavior across multiple files, touches production paths, or implements acceptance criteria that are easy to misunderstand.

## Suggested next skill
`spec-lite` if outcome contract is still unstable | `feedback-loop` | `branch-sandbox` | `two-axis-review` | `verify-before-claim` | none
```

## Plan fit review

Review the plan against this concrete task and project, not against generic planning aesthetics.

```markdown
## Plan fit review
- Acceptance fit: Does the plan directly satisfy the stated acceptance criteria?
- Project fit: Does it match current repo architecture, conventions, runtime, and constraints?
- Execution fit: Can an agent/developer act on the next slice without guessing?
- Verification fit: Are the proposed checks actually able to prove the claim in this project?
- Flexibility: Which parts are likely to change after spec/design/implementation feedback?
- Confidence: High | Medium | Low, with evidence from code/docs/tests/env inspected.
```

If confidence is low because important project facts were not inspected, say what must be inspected next instead of making the plan look complete.

## Plan persistence

Default to keeping plan context in the current conversation. Plans are often temporary and should not create stale project documentation by default.

Recommend saving a plan to a file only when one of these is true:

- Multiple sessions or agents must coordinate from it.
- The plan is a durable decision record or external handoff.
- The user explicitly asks to save it.
- The plan will survive beyond the current session and needs review later.

If saving, include status/currentness markers:

```markdown
Status: draft | active | superseded
Last updated:
Superseded by:
Stale when:
```

For Codex App workflows, prefer using the main planning conversation as the living plan context, then fork/derive child sessions for spec design or implementation. Feed child-session findings back into the main planning conversation instead of accumulating unmaintained plan files.

## Planning heuristics

- A task is good when it can be reviewed independently and verified with concrete evidence.
- Prefer tracer bullets or milestone slices over horizontal layers: do not create separate tasks for "all tests", then "all implementation", then "all cleanup" unless the repo forces that structure.
- Keep acceptance criteria visible. Tests passing is not enough if acceptance criteria are not met.
- Avoid speculative abstraction; note extension points only when required now.
- Let task count emerge from complexity. For goal-mode or refactor work, plan by milestone/slice rather than compressing everything into a fixed number of tasks.
- If multiple agents will execute the plan, include enough context per task that a fresh agent can work without reading the whole conversation.
- For deployment/migration plans, include exact commands, config readback, health checks, log checks, and rollback commands.
- Use `Change boundary` to describe the intended commit/review/rollback boundary. Suggest actual commit messages only when git history design matters.
