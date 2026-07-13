---
name: branch-sandbox
description: Create a branch, worktree, or scratch clone when a user explicitly requests isolation or a risky or parallel coding task needs a reversible workspace boundary. Use for broad refactors, migrations, autonomous runs, and concurrent work; skip routine micro-tasks and read-only investigation.
---

# Branch Sandbox

Create only the isolation that materially reduces rollback, interference, or
working-tree risk. Isolation is a process boundary, not proof that a change is
correct or authorized.

<!-- handrails-contract
contract: usable-loop/v2
role: workspace-isolator
reference: references/usable-loop-v2.md
runtime: scripts/handrails_state.py
-->

Read [the local v2 contract](references/usable-loop-v2.md) when you need record
fields, authority rules, Checkpoint triggers, or runtime details.

## Decide whether to isolate

Use a worktree or branch for broad refactors, migrations, generated assets,
long autonomous work, experiments, concurrent tasks, production-like files, or
when the current checkout must remain usable. Prefer:

- no sandbox for a clear micro-task or read-only investigation;
- a branch when the checkout is clean and may be occupied by this task;
- a worktree when another branch/check-out must remain available;
- a scratch clone only for clean-clone, remote, or dependency isolation.

Do not silently pass control to another handrail. Return the sandbox result and
let the caller decide what happens next.

## Establish authority and state

Treat the current user request as authoritative when the user controls the task
and no permission or designated-source conflict exists. Otherwise mark derived
meaning provisional and expose the conflict.

Run the read-only preflight:

```bash
git rev-parse --show-toplevel
git status --short
git branch --show-current
git rev-parse HEAD
git worktree list
python <this-skill-dir>/scripts/handrails_state.py inventory --repository . --base HEAD
```

Resolve `<this-skill-dir>` from this installed `SKILL.md`, not from the project
working directory. Inside this source repository, `runtime/handrails_state.py`
is the canonical equivalent.

The runtime inventories staged, unstaged, committed-since-base, and untracked
state. Add ignored artifacts only with explicit `--declare-ignored` arguments.
Never infer or scan ignored caches, secrets, or local files.

If a Review Boundary Seed exists, consume it as a hypothesis. Record actual
task-start state and the delta from the seed; do not convert expected paths into
an allowlist. Without a seed, report `No seed supplied`.

For a dirty checkout:

- keep it untouched by creating a worktree from a clean base when it is unrelated;
- include it only when the user says it belongs to this task;
- stop when ownership is ambiguous;
- stash only after explicit authorization.

## Create the boundary

Use a repository-conforming branch name. Typical commands are:

```bash
git switch -c <type>/<topic>
git worktree add -b <type>/<topic> <path> <base>
git clone <source> <path>
```

After creation, recapture branch, HEAD, status, and participating worktrees.
Return a compact Work Boundary containing:

- Task ID and Outcome Revision;
- workspace identity and actual task-start state;
- Review Boundary Seed delta, if any;
- participating workspaces and authorization guardrails;
- explicitly declared ignored artifacts;
- base/recovery identity, sandbox location, rollback path, and stale conditions.

Paths and expected changes remain hypotheses. The later claim/review boundary
must inventory all current candidates again.

## Safety and cleanup

Never auto-run stash, reset, rebase, overwrite, force branch deletion, or remove
a worktree that contains results. Ask for explicit authorization for each such
operation. By default, report the cleanup command and its preconditions without
executing it.

Before proposing worktree removal, show status, branch, HEAD, and whether the
results are integrated or recoverable. Never use isolation as a reason to hide
or delete pre-existing work.

## Direct result

Keep the ordinary result compact: chosen isolation, exact location/base,
captured dirty-state limitation, rollback/cleanup command, and the necessary
next step. Expand a Checkpoint only for a trigger listed in the local contract.
