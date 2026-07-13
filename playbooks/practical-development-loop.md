# Practical Development Loop

This is a selection guide, not a pipeline. Start with the smallest path that
protects the current task and stop adding handrails when they no longer change a
decision, boundary, evidence, or claim.

## Fast paths

### Narrow fact or operational check

```text
observe directly → verify-before-claim (fact)
```

No plan, spec, Review Boundary, or Capsule is needed.

### Clear bounded change

```text
implement → focused development check
→ verify-before-claim (scoped-task)
```

Verify inventories every current candidate and confirms the lightweight Claim
Boundary. A review is optional unless the requested wording is high-assurance.

### Ambiguous or consequential work

```text
optional grill → optional spec-lite → optional plan-lite
→ implementation / feedback-loop → two-axis-review
→ verify-before-claim (high-assurance when requested)
```

Skip every step that does not change the work. Use `branch-sandbox` only when
isolation reduces actual risk.

## 1. Bind the outcome

Carry one `usable-loop/v2` Outcome Reference. Treat the user's current request
as authoritative when they own the scope and no permission/source conflict
exists. Keep agent-derived interpretations provisional.

## 2. Seed without closing the boundary

When planning helps, record expected logical changes, dependencies/generated
outputs, authorization guardrails, known pre-existing changes, participating
workspaces, and explicitly declared ignored artifacts. Omitted paths are not
proven unrelated.

## 3. Develop with observations

Feedback Loop records development evidence as `observed | stale | blocked`.
Capture the Inventory Digest around meaningful observations. Use it to choose the
next change, not to justify a completion claim.

## 4. Confirm current state when the claim needs it

```bash
python3 runtime/handrails_state.py inventory \
  --repository . --base <task-base> \
  --participating-worktree . \
  --environment platform=linux
```

Classify every runtime ID. For a small-task claim use `claim` classifications;
for review use the four review classifications. Include rationale and
authorization, then run `confirm` with identical capture arguments.

Never type or reuse a Boundary Digest manually. Reinventory after drift.

## 5. Verify exact wording

- `fact`: rerun the direct observation; no boundary or review.
- `scoped-task`: verify against the exact Claim Boundary.
- `high-assurance`: require an exact, current two-axis Review Record and recapture
  its Review Boundary before running any final checks.

If only part is supported, narrow the claim and state the limitation. Relevant
change means stale evidence and a new narrow check.

## 6. Pause only with proportional continuity

Keep ordinary single-session state in conversation. On pause, handoff, context
risk, expensive evidence, or explicit request, rewrite exactly one
`.scratch/<task-id>/STATE.md`. On resume, read and reconcile the designated
Outcome Source, then the Capsule, then recapture all participating state.

The Capsule is disposable. Promote durable decisions or defects to Issues/ADRs
and remove it after the unique handoff value is gone.

## 7. Clean up safely

Do not stash, reset, rebase, overwrite, force-delete branches, or delete a
worktree containing results without explicit authorization. Report cleanup
commands and recovery identity by default.
