# Practical Development Loop

Use this as a selection guide, not a required pipeline. Start with the smallest path that protects the current task and stop adding handrails when they no longer change a decision, boundary, evidence, or claim.

## Fast paths

### Clear single-session change

```text
implement → focused check → verify-before-claim
```

Bootstrap a provisional Outcome Reference if needed. Keep the Checkpoint in conversation only. Create no plan, spec, Capsule, or review document unless the task discovers real complexity.

### Ambiguous or multi-step work

```text
optional grill → optional spec-lite → optional plan-lite
→ implementation/feedback-loop → two-axis-review → verify-before-claim
```

Skip `spec-lite` when the request, Issue, or conversation already defines the outcome. Skip `plan-lite` when the next safe vertical slice is obvious. Use `branch-sandbox` only when isolation reduces real risk.

## 1. Bind the outcome

Carry one complete `usable-loop/v1` Outcome Reference. Keep Task ID and source identity stable across revisions. Treat any agent-authored revision as provisional until the designated authority confirms that exact revision.

If authority is unavailable, conflicting, or revision-mismatched, continue only with safe reversible exploration; stale dependent evidence cannot support approval or completion.

## 2. Seed, do not close, the boundary

When planning helps, record expected logical changes, dependencies/generated outputs, guardrails, task-start hints, known pre-existing candidates, participating workspaces, and explicitly declared ignored artifacts.

This Review Boundary Seed is a hypothesis:

- omitted paths are not proven unrelated;
- pre-existing work is an exclusion candidate, not an exclusion;
- unexpected task-created work is reviewable scope creep;
- undeclared ignored files are never scanned.

## 3. Capture state around evidence

For Git-backed evidence, prefer the bundled helper:

```bash
python3 runtime/git_state.py \
  --repository . \
  --base <task-base> \
  --review-boundary-digest <digest-or-unconfirmed> \
  --participating-worktree . \
  --include-untracked <explicit-task-artifact> \
  --declare-ignored <explicit-ignored-artifact> \
  --environment platform=linux
```

Repeat `--participating-worktree`, `--include-untracked`, `--declare-ignored`, and `--environment` as needed. The helper is read-only and mechanical; it does not decide relevance.

Capture before and after each meaningful check. Bind the Evidence Record to Outcome Revision, Boundary digest, Code State Token, environment, observed result, and narrow scope.

## 4. Review the real current task state

Choose `published-artifact`, `current-task-state`, or `artifact-plus-local`. For current state, inventory committed, staged, unstaged, untracked, explicitly declared ignored artifacts, and every participating worktree.

Classify every logical unit as `include-required`, `include-scope-creep`, `include-inherited-dependency`, `exclude-proven-unrelated`, or `unresolved`. Split mixed files by hunk/section/artifact when necessary.

Block approval when any candidate is unresolved, the Boundary digest changed without re-review, a participating worktree is missing, or task-created scope creep remains unauthorized.

## 5. Verify the exact claim

Capture state before verification, after verification, and before the final claim. Require the same Outcome Revision, confirmed Boundary digest, relevant code state, worktree set, and environment.

Relevant drift stales evidence. Proven unrelated drift requires boundary reconciliation and may preserve only the original narrow evidence; it never broadens a claim. Child-worktree evidence cannot prove an integrated state.

## 6. Return a Checkpoint

Every `feedback-loop` result returns the current Outcome Reference, boundary/state, repro or baseline, change/evidence deltas, done/next/blockers, supported claims, missing proof, and stale conditions.

Keep it in conversation only unless one of these continuity triggers applies:

- another session or agent must continue;
- context compaction/loss is likely;
- work pauses or blocks;
- relevant uncommitted state must survive;
- evidence is expensive or non-repeatable.

Then compactly rewrite exactly one `.scratch/<task-id>/STATE.md`. Do not append phase logs. The Capsule is an orientation cache, never an Outcome Source or freshness proof.

Store IDs, locators, digests, compact observations, and reproducible commands—not credentials, secret values, or raw logs. Git ignore is not secure storage.

## 7. Resume and clean up

On resume:

1. Read and reconcile the designated Outcome Source.
2. Read the Capsule for next action, blockers, and evidence IDs.
3. Recapture all participating state and relevant environment.
4. Mark mismatches stale and revalidate the narrow affected claims.

Delete the Capsule only after integration or clean durable handoff, when every unique decision, defect, evidence recipe, or follow-up has been promoted or made reproducible.

## Stop conditions

- Stop adding process when the next action, boundary, evidence, and rollback are already clear.
- Stop implementation for consequential outcome ambiguity or unauthorized scope expansion.
- Stop approval for unresolved candidates or stale boundary/state evidence.
- Stop success language when the evidence is narrower than the claim.
