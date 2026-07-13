---
name: plan-lite
description: "Explicit-invocation compact implementation planning for multi-step coding tasks. Invoke when a user or an explicit orchestrator requests a plan, task breakdown, tracer bullets, or implementation roadmap."
disable-model-invocation: true
argument-hint: "feature/spec/bugfix to plan"
---

# Plan Lite

Create enough plan to make implementation reliable, without Superpowers-style exhaustive ceremony or a full formal spec.

## Contract binding

<!-- handrails-contract
contract: usable-loop/v1
role: execution-planner
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

Echo the exact input Outcome Reference; a plan is not automatically a new Outcome Source. If no reference exists, bootstrap one from the current request with a task-local stable Task ID, a truthful request/conversation locator, `provisional` authority, a compact snapshot, and explicit stale conditions.

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

When bootstrapping, populate and emit every field in this template; do not replace the record with an ID-only shorthand. When consuming a reference, echo its exact values rather than minting a plan-owned revision.

Bootstrap state is always: authority `provisional`, lifecycle `active`, currentness `fresh`.

Keep Task ID and Outcome Source ID independent of Outcome Revision: do not put `r1`, a digest, or another revision suffix into either identity.

If planning exposes a material outcome change, reconcile or reconfirm a new Outcome Revision before presenting the plan as current. If authority is inaccessible, conflicts with another designated source, or the revision mismatches, mark the reference provisional/stale and stale dependent boundary seeds, evidence, and claims. Never choose between authorities by recency or durability. A local Capsule is orientation only, never the Outcome Source.

Never describe an Outcome Revision as a hash or digest unless you actually computed it over identified canonical bytes; otherwise use an honest task-local opaque revision such as `r1`.

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
- Treat planned files and paths as discovery hypotheses, never as a closed allowlist or the final Review Boundary.

## Relationship to specs

This skill consumes the currently designated Outcome Reference and turns it into an implementation plan. When none has been designated, it uses an explicit provisional reference rather than choosing an authority on the user's behalf. It does not automatically create a formal spec.

Use `spec-lite` first when the missing piece is a stable outcome contract: behavior rules, interface/data contracts, acceptance criteria, domain invariants, or durable handoff. Otherwise, let the Outcome Reference point to the current conversation, a `grill` alignment snapshot, an issue/PRD, or the current request; do not promote this plan's restatement into authority.

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

## Outcome Reference
- Contract: usable-loop/v1
- Task ID:
- Outcome Source kind:
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

Task shape:
Goal:
Acceptance criteria:
Non-goals:
Assumptions:
Open questions / known unknowns:
Blast radius:
Primary seams:
Isolation / rollback:

## Review Boundary Seed
- Outcome binding: Task ID + Outcome Source ID + Outcome Revision
- Expected logical changes:
- Dependent or generated changes:
- Authorization guardrails:
- Known pre-existing changes:
- Participating workspaces:
- Base and recovery hints:
- Declared ignored artifacts, if any:
- Open boundary questions:
- Path semantics: hypotheses-not-allowlist

The seed is a planning hypothesis, not an allowlist or final Review Boundary. Omitted paths are not proven unrelated. Known pre-existing changes are exclusion candidates, not exclusions. Unexpected task-created changes remain reviewable as scope creep. Only review-time inventory and classification may produce the final boundary.

List ignored artifacts only when the user, Outcome Source, or task record explicitly declares them. Do not infer common cache, secret, virtual-environment, or generated paths as declarations.

Under `Base and recovery hints`, name the intended task-start revision and ask `branch-sandbox` or the implementer to capture the actual dirty candidates before editing. Under `Participating workspaces`, include every known implementation, dependency, generation, verification, and integration worktree; mark unknown future participants as an open boundary question rather than silently omitting them.

## Implementation strategy
<short explanation of chosen approach and why it is the smallest professional path>

## Tasks

### 1. <Tracer bullet / milestone slice>
Intent:
Scope:
Files:
Steps:
Verification:
Logical Change Unit / integration boundary:

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

When a continuity trigger requires a Local Capsule, let the Capsule point to this plan/Outcome Reference and preserve only the current next action, blocker, boundary/state binding, and evidence delta. Do not copy the whole plan into phase logs. On resume, reconcile the Outcome Source and repository state before treating the plan as current.

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

These lifecycle timestamps do not replace the Outcome Revision in the plan's Outcome Reference.

For Codex App workflows, prefer using the main planning conversation as the living plan context, then fork/derive child sessions for spec design or implementation. Feed child-session findings back into the main planning conversation instead of accumulating unmaintained plan files.

## Planning heuristics

- A task is good when it can be reviewed independently and verified with concrete evidence.
- Prefer tracer bullets or milestone slices over horizontal layers: do not create separate tasks for "all tests", then "all implementation", then "all cleanup" unless the repo forces that structure.
- Keep acceptance criteria visible. Tests passing is not enough if acceptance criteria are not met.
- Avoid speculative abstraction; note extension points only when required now.
- Let task count emerge from complexity. For goal-mode or refactor work, plan by milestone/slice rather than compressing everything into a fixed number of tasks.
- If multiple agents will execute the plan, include enough context per task that a fresh agent can work without reading the whole conversation.
- For deployment/migration plans, include exact commands, config readback, health checks, log checks, and rollback commands.
- Use `Logical Change Unit / integration boundary` to describe the intended commit, review, and rollback slice. It is not the task's final Review Boundary. Suggest actual commit messages only when git history design matters.
