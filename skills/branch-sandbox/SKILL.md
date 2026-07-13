---
name: branch-sandbox
description: "Explicit-invocation branch/worktree isolation for risky coding-agent tasks. Invoke when a user or an explicit orchestrator requests an isolated branch, worktree, sandbox, risky refactor, migration, or autonomous agent run."
disable-model-invocation: true
argument-hint: "task or branch/worktree isolation goal"
---

# Branch Sandbox

Use branch/worktree isolation when the cost of a messy working tree, hard rollback, or agent interference is higher than the setup overhead.

This skill is about **process boundaries**: where the change is allowed to happen, how to diff it, how to abandon it safely, and how to bring it back when it is good.

## Contract binding

<!-- handrails-contract
contract: usable-loop/v1
role: workspace-isolator
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

Carry the Outcome Reference that names what the sandbox is for. If none exists, create a task-local provisional reference from the current request with a stable Task ID, truthful source identity/locator, revision basis, compact snapshot, active lifecycle, fresh currentness, and explicit stale conditions. Do not invent a durable source or authoritative status.

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

When bootstrapping, populate and emit every field in this template; do not replace the record with an ID-only shorthand. When consuming a reference, preserve its exact values in the Sandbox result.

Bootstrap state is always: authority `provisional`, lifecycle `active`, currentness `fresh`.

Keep Task ID and Outcome Source ID independent of Outcome Revision: do not put `r1`, a digest, or another revision suffix into either identity.

If the designated authority is inaccessible, conflicts with another designated source, or its revision mismatches, mark the reference provisional/stale and treat dependent evidence and claims as stale until reconciliation or reconfirmation. Never choose between authorities by recency or durability. A local Capsule is orientation only, never the Outcome Source.

Never describe an Outcome Revision as a hash or digest unless it was actually computed over identified canonical bytes; otherwise use an honest task-local opaque revision such as `r1`.

## Rules

- Do not let ambient model matching select this skill. Invocation must come from the user or an explicit orchestrator/harness decision.
- Do not create isolation for its own sake; use it only when it reduces working-tree risk, rollback cost, or agent interference.
- Do not treat branch/worktree creation as proof of safety; review and verification still happen separately.

## When isolation is worth it

Use a branch or worktree when one or more signals apply:

- Broad refactor, migration, generated assets, or cross-module behavior change.
- Long autonomous Codex/agent run where intermediate edits may be messy.
- Experiment likely to be discarded.
- Current workspace must stay usable while the agent works elsewhere.
- Multiple agents/sessions may run in parallel.
- You need a clean diff, easy rollback, or PR-ready boundary.
- The change touches production-like paths, data/config, deployment scripts, or public interfaces.

Do not force this for clear micro-tasks, one-file edits, read-only investigation, or commands where the working tree is not at risk.

## Branch vs worktree vs scratch clone

### Branch only

Use when:

- Current workspace is clean.
- You will work interactively in the current checkout.
- You do not need to keep another branch checked out at the same time.

Pros: lowest overhead.
Risk: the current working directory becomes the sandbox.

### Worktree

Use when:

- Main workspace should remain untouched.
- Running a long autonomous agent.
- Running multiple independent agents/experiments.
- You want separate build artifacts, dependency state, or editor context.

Pros: clean filesystem boundary and easy deletion.
Risk: parallel work can still conflict at merge time if scopes overlap.

### Scratch clone

Use only when:

- Worktree sharing is inconvenient,
- remote/CI behavior must be tested from a fresh clone,
- dependency or generated-file state should be fully isolated.

Pros: strongest isolation.
Risk: more setup and remote/auth overhead.

## Pre-flight

Run in the source repo:

```bash
git rev-parse --show-toplevel
git status --short
git branch --show-current
git rev-parse HEAD
git worktree list
```

Capture this state before creating or switching the sandbox. It is the task-start evidence, not merely setup output. Inventory the current workspace's staged, unstaged, and untracked paths; add ignored paths only when the task explicitly declares them. Record every worktree that will participate, including dependency, generation, verification, or integration worktrees.

When the repository bundle provides `runtime/git_state.py`, prefer its read-only capture for mechanical identities and fingerprints. A standalone copy of this skill remains usable with the Git commands above plus `git diff --cached --name-only`, `git diff --name-only`, and `git ls-files --others --exclude-standard`. Neither path decides task relevance.

If the current tree is dirty, decide explicitly:

- **Commit** if the dirty state is intentional and should be part of the base.
- **Stash** if it is unrelated temporary work.
- **Stop** if the dirty state is ambiguous.
- **Create worktree from clean base** if the dirty state should remain untouched and is not needed by the new task.

Do not hide or overwrite dirty state just to proceed.

## Work Boundary / sandbox card

Before launching work, emit this compact `usable-loop/v1` Work Boundary:

```markdown
## Work Boundary
- Task ID:
- Outcome Revision:
- Workspace identity:
- Task-start revision:
- Task-start candidates:
- Participating workspaces:
- Expected logical changes:
- Authorization guardrails:
- Declared ignored artifacts:
- Base revision:
- Recovery identity, if available:
- Sandbox type: branch | worktree | scratch clone
- Branch name:
- Worktree path, if any:
- Verification expected:
- Rollback path:
- Stale when:
```

This is not a path allowlist or implementation plan. Expected paths are hypotheses. Preserve all task-start candidates for later classification: pre-existing does not mean unrelated, and unexpected task-created work remains reviewable scope creep.

Use `None declared` when no ignored artifact was explicitly named. Never infer caches, secrets, virtual environments, build directories, or common local files. Do not scan ignored content merely to complete the card.

## Branch flow

```bash
git switch -c <type>/<short-topic>
```

Recommended branch prefixes:

- `feat/<topic>` for feature work.
- `fix/<topic>` for bug fixes.
- `refactor/<topic>` for behavior-preserving structure changes.
- `spike/<topic>` for disposable experiments.
- `agent/<topic>` for autonomous agent runs.

After switching:

```bash
git status --short
git branch --show-current
```

Record the base commit so review can later use:

```bash
git diff <base>...HEAD --stat
git diff <base>...HEAD
```

## Worktree flow

Choose a path outside the main checkout, preferably under a predictable parent such as `/tmp`, `~/Workspace/Worktrees`, or the project team's chosen worktree directory.

```bash
git worktree add -b <type>/<short-topic> <path> <base>
```

Then enter the worktree and verify boundary:

```bash
cd <path>
git status --short
git branch --show-current
git rev-parse HEAD
```

Use one worktree per autonomous agent or independent experiment.

## Parallel agent discipline

Parallel agents are allowed only when their scopes are explicit.

Before launching agents, define for each:

- worktree path,
- branch name,
- goal,
- files/modules allowed,
- files/modules forbidden,
- whether committing is allowed,
- verification expected before reporting.

Avoid two agents editing the same files unless the merge/conflict plan is explicit. If overlap becomes necessary, stop and re-coordinate rather than letting agents race.

For Codex-style runs, the prompt should include the sandbox boundary, e.g.:

```text
You are working in <worktree path> on branch <branch> from base <base>.
Goal: ...
Allowed scope: ...
Out of scope: ...
Do not edit outside this scope. Report commands run and verification evidence.
Do not claim completion without verification.
```

## Completion / reintegration

Before saying the sandbox is ready to merge or keep:

```bash
git status --short
git diff <base>...HEAD --stat
git diff <base>...HEAD
git log --oneline <base>..HEAD
```

Re-list participating worktrees and compare them with the Work Boundary. A missing or newly participating worktree must be reconciled before review; evidence from a child worktree cannot prove the integrated state until that state is captured and verified.

Then:

- Use `two-axis-review` for broad diffs, behavior changes, refactors, migrations, or agent-generated work.
- Use `verify-before-claim` for the exact completion claim.
- If the work is experimental, decide: keep, extract partial patch, or discard.
- If using a worktree, do not remove it until useful changes are merged, copied, committed elsewhere, or explicitly abandoned.

## Rollback / abandon

For an unmerged branch that should be discarded:

```bash
git switch <safe-base-branch>
git branch -D <type>/<short-topic>
```

For a worktree that should be discarded:

```bash
git -C <path> status --short
git worktree remove <path>
git branch -D <type>/<short-topic>  # only if branch is truly abandoned
```

If the worktree has uncommitted useful changes, do not remove it. Commit, patch-export, or ask the user before deletion.

Avoid `git reset --hard` unless you are inside the isolated sandbox, the target commit is explicit, and the destructive scope is understood.

## Output shape

When this skill is used, end with:

```markdown
## Sandbox result
- Sandbox type:
- Branch:
- Path:
- Base:
- Scope:
- Commands run:
- Current status:
- Diff/review command to use:
- Rollback/cleanup command:
- Recommended next skill: plan-lite | feedback-loop | two-axis-review | verify-before-claim | none
```

## Anti-patterns

- Launching a long agent run in a dirty main workspace.
- Creating worktrees without recording base commit or branch.
- Running parallel agents with overlapping scopes and no merge plan.
- Deleting a worktree before checking for useful uncommitted changes.
- Treating branch creation as rollback; rollback only exists if abandon/revert path is known.
- Using sandboxing as a substitute for review and verification.
