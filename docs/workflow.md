# Agent Handrails Workflow

This document describes how the atomic handrails fit together without turning them into a mandatory workflow.

## Design thesis

Handrails should serve the engineer's development rhythm, not take it over. The repository exposes professional discipline as small explicit primitives that work manually and remain ready for visible, inspectable orchestration.

## Non-goals

- No always-on gateway skill.
- No "1% chance means invoke" rule.
- No mandatory brainstorming/spec/TDD/review chain for every task.
- No auto-triggered replacement for professional judgment.
- No assumption that manual-first means automation is forbidden.

## Invocation contract

Use the smallest professional path that protects quality. The listed skills are a toolbox, not a chain.

- Start from the user's actual request, not from a workflow template.
- Invoke a skill only when it changes the next decision, evidence, isolation, review quality, or handoff quality.
- Prefer one next useful skill over running the whole set.
- Stop adding process when remaining uncertainty no longer changes implementation, verification, rollback, or review.
- If a task is clear and low-risk, execute and verify directly.
- If a skill recommends another skill, treat it as advice, not an automatic transition.

## Automation contract

Manual-first does not mean manual-only. A user, playbook, or coding engineering harness may explicitly select a handrail.

- Ambient model matching is disabled; a skill should not appear merely because it might be relevant.
- An orchestrator selection is explicit invocation, not ambient matching.
- The orchestrator should record why the handrail was selected, what output/evidence it should produce, and when control returns.
- Automation must preserve inspectability, override, bounded execution, and rollback.
- A harness should use the same smallest-professional-path rule as a human user.
- Autonomy should increase only after the primitive, transition, model capability, and project feedback stack have earned trust.

The current repository validates handrails first. Playbooks and a future harness compose them later; each handrail must remain independently useful.

## Spec lifecycle

There is no mandatory spec artifact for every task.

- For small tasks and many bug fixes, the "spec" may simply be the current conversation: goal, non-goals, acceptance criteria, bug repro, or an alignment snapshot.
- `grill` can produce an **Alignment Snapshot** when uncertainty is resolved, but it does not create a formal spec by default.
- `spec-lite` can turn a converged alignment snapshot, issue, PRD, bug repro, or behavior description into a lightweight outcome contract when formalization is useful.
- `plan-lite` turns the exact Outcome Reference into an execution map: acceptance criteria, assumptions, seams, tasks, and verification. It is a plan, not automatically a formal spec.
- Create a saved formal spec only when it materially helps: multi-session coordination, durable handoff, complex domain behavior, high-risk acceptance criteria, or explicit user request.
- If a saved spec is created, mark currentness/status so it does not become stale authority.
- Review should use the current exact **Outcome Reference** designated by the task authority. If none exists, create an explicit provisional reference from the current request; do not choose a supposedly "best" authority or invent a spec.

## Outcome continuity

All seven handrails use `usable-loop/v1`. A stable Task ID and exact Outcome Reference carry source identity, revision, authority basis, compact snapshot, lifecycle, currentness, supersession, and stale conditions across optional skill transitions.

- A plan echoes its input Outcome Reference; it does not become authority merely by restating acceptance criteria.
- A saved spec is durable but remains provisional unless the designated authority confirms it.
- A material outcome change creates a new revision and explicit supersession.
- An inaccessible or mismatched authority makes dependent boundary seeds, evidence, and claims stale until reconciliation.
- Every skill can bootstrap a provisional reference when directly invoked, so no gateway or mandatory first step is required.

See `CONTEXT.md` for domain vocabulary and `docs/contracts/usable-loop-v1.md` for canonical semantics.

## Review the real current task state

A fixed commit range is useful but incomplete when task work is staged, unstaged, untracked, explicitly ignored, or spread across worktrees.

- `plan-lite` produces a Review Boundary Seed: expectations and guardrails, not an allowlist.
- `branch-sandbox` captures the task-start Work Boundary and participating workspaces.
- `runtime/git_state.py` can capture read-only mechanical Git inventories and fingerprints; it never classifies task relevance.
- `two-axis-review` reconciles every candidate into a confirmed Review Boundary and computes its digest.
- `feedback-loop` and `verify-before-claim` bind evidence and claims to that digest, the exact Outcome Revision, relevant environment, and Code State Token.

For current-state review, account for committed, staged, unstaged, untracked, explicitly declared ignored artifacts, and all participating worktrees. Do not scan undeclared ignored files. Treat task-created unexpected changes as scope creep, and block approval while any candidate is unresolved or the boundary/state changed after evidence capture.

## Conversation-first continuity

Every `feedback-loop` result is Checkpoint-compatible, but persistence remains proportional:

1. Keep clear single-session work in conversation only.
2. Compactly rewrite one `.scratch/<task-id>/STATE.md` when a session/agent handoff, context loss, pause/block, relevant uncommitted state that must survive a handoff, or expensive evidence makes reconstruction risky.
3. Promote durable project knowledge to an Issue, PR, spec, or ADR; do not accumulate phase logs.

The Local Capsule stores the current Outcome locator/revision/authority/snapshot, boundary and state bindings, next/blocker, evidence/claim status, scope limits, and invalidation/cleanup rules. It never becomes authority. Resume by reading the Outcome Source first, then the Capsule, then recapturing repository/workspace/environment state before reusing evidence.

Delete the Capsule only after integration or a clean durable handoff and after all unique information is promoted or reproducible. A passing test alone is not a cleanup signal.

## Release acceptance

Treat a clean GitHub Actions checkout as the release packaging boundary. On Python 3.10 and the current stable matrix version, install PyYAML, run the full tests and repository validator, smoke the Git state helper, then apply/check a complete temporary bundle with discovery links. The release candidate must leave tracked source clean.

Before a stable tag, repeat those checks from a fresh clone, exercise rollback with the exact bundle-aware baseline, and run the real Codex/dogfood gates. Local green tests do not substitute for unpublished CI, real installation, or external-project evidence.

## Task shapes, not rigid levels

Software engineering work is open-ended. These shapes are a shared vocabulary for choosing how much process is useful, not a classifier that restricts the agent.

### Operational micro-task

Examples: run a service, inspect state, produce executable commands, fix a local environment issue.

Useful discipline:
- Identify target and blast radius.
- Execute narrowly.
- Verify with command output or readback.

Typical skills:
- `verify-before-claim`.

### Bug fix

Examples: reported error, failing test, runtime exception, performance regression.

Useful discipline:
- Reproduce or minimize the symptom.
- Explain the causal hypothesis before fixing.
- Add regression coverage or a deterministic smoke check when practical.
- Verify before claiming fixed.

Typical skills:
- `grill` only if the desired behavior or blast radius is ambiguous.
- `feedback-loop` for regression/repro loop.
- `verify-before-claim`.

### Feature work

Examples: implement a behavior, endpoint, UI workflow, adapter, or model-service integration.

Useful discipline:
- Clarify product/engineering choices that affect implementation.
- Create a compact tracer-bullet plan when multiple files or states are involved.
- Test important public seams.
- Review both outcome fit and engineering quality.

Typical skills:
- `grill`
- optional `spec-lite` when behavior or acceptance needs a durable outcome contract
- `plan-lite`
- `feedback-loop`
- `two-axis-review`
- `verify-before-claim`

### Goal-mode development

Examples: complete a phase with acceptance criteria and an approximate implementation direction.

Useful discipline:
- Preserve the goal and acceptance criteria as the north star.
- Split into milestones or tracer bullets.
- Keep context fresh through handoffs, notes, or subagents when needed.
- Verify against acceptance criteria, not just tests.

Typical skills:
- `grill`
- optional `spec-lite`
- `plan-lite`
- optional branch/worktree isolation
- `two-axis-review`
- `verify-before-claim`

### Large refactor

Examples: execute a refactor plan, untangle modules, migrate interfaces, change architecture.

Useful discipline:
- Isolate work when blast radius is high.
- Preserve behavior with characterization tests or smoke checks.
- Move in reversible increments.
- Review design quality separately from behavior preservation.

Typical skills:
- `branch-sandbox`
- optional `spec-lite` before planning if behavior preservation or interface contracts need formalization
- `plan-lite`
- `feedback-loop` or characterization tests
- `two-axis-review`
- `verify-before-claim`

### Deployment / migration

Examples: move locally verified work to server, deploy service, adapt environment/runtime.

Useful discipline:
- Separate local correctness from target-environment correctness.
- Write exact commands and rollback steps.
- Verify service state, logs, ports, health checks, and config readback.

Typical skills:
- `plan-lite` if multiple commands or environments are involved.
- `verify-before-claim`.
- `branch-sandbox` only if code/config changes are risky.

### Unknown / hybrid

If the task does not fit cleanly, say so. Use the task shape as a conversation aid, not a restriction. The agent should adapt the process to the actual uncertainty and blast radius.

## Atomic handrails

1. `grill` — clarify intent and design decisions without forcing a spec ceremony.
2. `spec-lite` — create a lightweight outcome contract when conversation-only context is not enough.
3. `plan-lite` — produce a compact tracer-bullet implementation plan.
4. `feedback-loop` — use seam-based tests, repros, smoke checks, and runtime evidence where feedback improves confidence.
5. `two-axis-review` — review changes separately for outcome fit and engineering quality.
6. `verify-before-claim` — require fresh evidence before success claims.
7. `branch-sandbox` — isolate risky work in a branch/worktree with rollback clarity.

## Installation model

Separate engineering source from agent runtime copies:

- Develop, review, validate, and version the canonical handrails in this Git repository.
- Deploy complete versioned bundles behind stable agent-facing entrypoints and create Codex discovery pointers with `python3 scripts/sync_skills.py --apply --codex-link-root ~/.agents/skills`.
- Detect runtime or discovery-link drift with `python3 scripts/sync_skills.py --check --codex-link-root ~/.agents/skills`.
- Never treat a deployed copy as a second source of truth; edit the project and sync again.
- The deployment manifest contains only the seven Agent Handrails skills, so unrelated skills in the target root are not managed.

Every current skill sets `disable-model-invocation: true` for compatible platforms and `agents/openai.yaml` sets `policy.allow_implicit_invocation: false` for Codex. These disable ambient model selection, but they do not prevent a user or explicit harness from invoking the skill deliberately. Platform behavior varies, so verify how each agent interprets metadata before claiming compatibility.
