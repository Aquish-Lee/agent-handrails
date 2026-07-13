---
name: feedback-loop
description: Use tests, reproductions, smoke checks, and runtime observations to guide an explicitly requested bug fix, feature, refactor, or deployment path. Produces development evidence for the next engineering move, not completion claims.
---

# Feedback Loop

Build the shortest trustworthy loop between an engineering change and the
behavior that matters. This is evidence-guided development, not a ritual and not
a completion gate.

<!-- handrails-contract
contract: usable-loop/v2
role: development-evidence-builder
reference: references/usable-loop-v2.md
runtime: scripts/handrails_state.py
-->

The normal development-evidence path is self-contained. Load
[the local v2 contract](references/usable-loop-v2.md) only when the user asks for
the full schema, a Checkpoint trigger applies, or these instructions cannot
resolve a contract question. Do not inspect runtime source or `--help` unless
execution fails.

## Start from the outcome

Treat an unconflicted current user request as authoritative when the user owns
the scope. Preserve a supplied Outcome Reference. If none exists, create a
task-local reference; mark only agent-derived or conflicted interpretation
provisional.

Identify the nearest meaningful signal:

1. reproduce the bad behavior or record a baseline;
2. choose the smallest check that would distinguish progress from noise;
3. make one coherent change;
4. rerun the narrow check;
5. widen only when the narrow signal is useful.

Prefer observable module/system/business behavior over tests coupled only to
implementation details. A test that never failed against the bug is not a
regression test.

## Bind observations honestly

Before an important observation, capture state with:

```bash
python <this-skill-dir>/scripts/handrails_state.py inventory \
  --compact --repository . --base <task-base> \
  > <private-inventory.json>
```

Resolve `<this-skill-dir>` from this installed `SKILL.md`, not the project cwd.
In this source repository, use `runtime/handrails_state.py`.

Keep the machine inventory out of the response and tool transcript; read only
the digest, conflicts, counts, and paths needed for the observation. Use the
private path outside participating worktrees or in an ignored, undeclared
Handrails evidence location. Use the Inventory Digest as the development
observation's code-state binding. Declare ignored artifacts only when the task
explicitly makes their content a candidate. Do not declare `.scratch` merely
because private logs or Handrails evidence live there. Recapture after a
relevant change; do not claim that an older observation remains fresh.

Emit a Development Evidence Record with:

- evidence ID, Task ID, and Outcome Revision;
- Inventory Digest/code state and relevant environment;
- exact command or observation method;
- observed result and narrow scope;
- `observed | stale | blocked`, capture time, and stale conditions.

`observed` means useful for development; it cannot support a completion claim.
Verify Before Claim independently creates claim evidence when a claim is
requested. Do not require a verify-to-feedback backflow.

## Adapt the loop

- For a bug, reproduce first, then keep the smallest regression.
- For a feature, add a focused acceptance example before widening coverage.
- For a refactor, establish behavior or characterization checks before moving
  structure.
- For deployment work, use staged health/smoke signals and name the environment.
- When a check is flaky or expensive, report that limitation; do not repeatedly
  rerun until it happens to pass.

Stop when the signal is no longer informative, authority is ambiguous, state
has drifted, or the next action would exceed authorization.

## Direct result

Return the behavior observed, the exact check, the current development-evidence
status, its scope limit, and the next development move. Do not emit a completion
claim or full Checkpoint unless explicitly requested or continuity is at risk.
On resume, reconcile the designated Outcome Source/Revision first, read any
Capsule second, and recapture participating state third.
