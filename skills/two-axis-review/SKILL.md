---
name: two-axis-review
description: "Explicit-invocation review of a diff along two independent axes: outcome fit and engineering quality, with verification evidence reported separately. Invoke when a user or an explicit orchestrator requests review of a branch, PR, diff, implementation, or work since a fixed point."
disable-model-invocation: true
argument-hint: "fixed point, PR, branch, or diff to review"
---

# Two-Axis Review

Review changes without mixing two questions: did we build the right outcome, and did we build it well? Verification evidence is reported separately so "looks right" does not become a success claim.

## Contract binding

<!-- handrails-contract
contract: usable-loop/v1
role: boundary-reviewer
missing-outcome-reference: bootstrap-provisional
authority-failure: stale-until-reconfirmed
authority-failure-triggers: authority-inaccessible,authority-conflict,authority-revision-mismatch
outcome-record: outcome-reference
required-local-resources: references/review-boundary.md,references/smell-baseline.md
bootstrap-authority: provisional
bootstrap-lifecycle: active
bootstrap-currentness: fresh
outcome-reference-output: complete
identity-revision-separation: required
revision-digest-claim: computed-only
-->

Review against the exact Outcome Reference when one exists. If direct entry has no reference, create a task-local provisional reference from the current request with a stable Task ID, truthful source identity/locator, revision basis, compact snapshot, active lifecycle, fresh currentness, and explicit stale conditions. Do not invent a spec or authoritative locator.

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

When bootstrapping, populate and emit every field in this template; do not replace the record with an ID-only shorthand. When consuming a reference, preserve its exact values in the review result.

Bootstrap state is always: authority `provisional`, lifecycle `active`, currentness `fresh`.

Keep Task ID and Outcome Source ID independent of Outcome Revision: do not put `r1`, a digest, or another revision suffix into either identity.

If the designated authority is inaccessible, conflicts with another designated source, or its revision mismatches, mark the reference provisional/stale and do not let prior evidence or claims support approval until reconciliation or reconfirmation. Never choose between authorities by recency or durability. A local Capsule is orientation only, never the Outcome Source.

Never describe an Outcome Revision as a hash or digest unless it was actually computed over identified canonical bytes; otherwise use an honest task-local opaque revision such as `r1`.

## Inputs

- Outcome Reference: the exact `usable-loop/v1` record. Its locator may designate an issue, PRD, spec, conversation alignment snapshot, goal acceptance criteria, bug repro, or deployment objective.
- Review target: `published-artifact`, `current-task-state`, or `artifact-plus-local`. Default to `current-task-state` when the user asks to review the work for the current task rather than naming a fixed published artifact.
- Base revision: commit, branch, tag, PR base, worktree base, or `HEAD~N` used as one candidate-discovery anchor; it is not the complete Review Boundary.
- Review Boundary Seed / Work Boundary: expected logical changes, task-start candidates, guardrails, declared ignored artifacts, and participating workspaces. Treat these as hypotheses to reconcile, not as an allowlist.
- Standards source: repo docs, existing patterns, linters, type system, architecture decisions, and smell baseline. Use `references/smell-baseline.md` when deeper smell vocabulary is needed.
- Evidence source: commands already run, test output, build output, smoke checks, logs, health/readback results.

If the Outcome Reference is missing, bootstrap the complete provisional record above. A plan, spec, or latest file becomes the designated source only through that reference; do not select one as authority by preference. A formal spec is not required.

## Optional parallel review

For large diffs, high-risk changes, or work where review quality matters more than minimal overhead, split the review into independent passes:

- **Outcome reviewer**: checks only Outcome Fit against the outcome source and acceptance criteria.
- **Quality reviewer**: checks only Engineering Quality against repo standards, architecture, and smell baseline.
- **Evidence reviewer** (optional): checks only verification evidence and missing proof.

Run these in parallel agents/sessions when available, then aggregate without merging the axes. This improves focus and can reduce wall-clock time. Do not force parallel review for small diffs.

## Process

1. **Confirm the Review Boundary**

   For `published-artifact`, resolve the exact commit/patch/PR object and inventory its changes; report local drift when it prevents reproduction or verification, but do not silently add local work to that target. Read `references/review-boundary.md` for `current-task-state` or `artifact-plus-local`: inventory every participating worktree and every candidate layer—committed, staged, unstaged, untracked, and explicitly declared ignored artifacts. Inspect untracked metadata before content; never scan undeclared ignored files.

   Classify every logical change unit as exactly one of: `include-required`, `include-scope-creep`, `include-inherited-dependency`, `exclude-proven-unrelated`, or `unresolved`. Split mixed files by hunks/sections/artifacts when their meanings differ. Task-created unexpected work is scope creep, never an exclusion. Pre-existing and omitted-from-plan are not proof of unrelatedness.

   Emit and actually compute the confirmed boundary:

   ```text
   ## Review Boundary
   Task ID:
   Outcome Revision:
   Review target: published-artifact | current-task-state | artifact-plus-local
   Participating workspaces:
   Candidate inventory:
   Classifications:
   Boundary digest:
   Unresolved items:
   Captured at:
   ```

   Prefer bundled `runtime/git_state.py` for read-only mechanical capture when available; retain the Git-command fallback in the reference for standalone use. The helper does not classify relevance. Block review approval if an item is unresolved or a participating worktree is missing.

   Capture the matching token:

   ```text
   ## Code State Token
   Provider: git
   Repository identity:
   Workspace identity:
   Base revision:
   Exact revision:
   Recovery identity, if available:
   Conflict state:
   Review Boundary digest:
   Candidate inventory:
   Tracked-state fingerprint:
   Included-untracked fingerprints:
   Declared-ignored fingerprints:
   Participating-worktree fingerprints:
   Relevant environment:
   Captured at:
   ```

2. **Review Outcome Fit**
   Ask: does this change satisfy the real task?

   Check:
   - Acceptance criteria satisfied, missing, or only partially satisfied.
   - Bug repro fixed without hiding the symptom.
   - User-facing/API/data/model-service behavior matches intent.
   - Deployment/runtime objective met if this is operational work.
   - No unrequested behavior or scope creep that changes product/system meaning.
   - Constraints, non-goals, safety boundaries, and rollback expectations respected.

3. **Review Engineering Quality**
   Ask: is this a good way to build it in this project?

   Check:
   - Fits current repo architecture, conventions, and domain language.
   - Clear names, low duplication, sensible module boundaries.
   - Public seams are preserved or improved.
   - Error handling, observability, rollback, and failure modes are addressed.
   - Security/safety/performance risks are not introduced.
   - Tests/checks are meaningful and not over-mocked or implementation-coupled.
   - No speculative abstractions beyond current need.

4. **Review Verification Evidence**
   Ask: what was actually proven?

   Check:
   - Which focused tests/repros/smoke checks/builds were run.
   - Whether evidence proves outcome-level behavior, not only function-level behavior.
   - What remains unverified and why.
   - Whether `verify-before-claim` should be run next.

   Reject evidence bound to a different Outcome Revision, Boundary digest, relevant Code State Token, participating worktree set, or environment. Child-worktree evidence proves only that child state, not integration.

5. **Recheck state and report separately**

   Re-capture the Code State Token before recommending approval. If the Boundary digest or relevant state changed, reconcile the inventory and repeat affected review/evidence checks. A proven unrelated edit may preserve only the original narrow evidence after reconciliation; it cannot broaden a claim.

   ```markdown
   ## Outcome Reference
   <complete usable-loop/v1 record>

   ## Review Boundary
   <complete record and digest>

   ## Outcome Fit
   - Critical/Important/Minor findings

   ## Engineering Quality
   - Critical/Important/Minor findings

   ## Verification Evidence
   - Verified:
   - Missing evidence:
   - Recommended commands/checks:

   ## Recommendation
   Approve | Approve with follow-ups | Request changes | Not enough evidence
   ```

## Severity

- Critical: wrong outcome, broken acceptance criterion, data loss, security/safety issue, broken build/test, impossible rollback.
- Important: likely bug, maintainability problem, missing important check, unclear contract, weak observability, risky deployment gap.
- Minor: naming, small duplication, docs, polish, local consistency.

## Rules

- Do not let ambient model matching select this skill. Invocation must come from the user or an explicit orchestrator/harness decision.
- Keep Outcome Fit and Engineering Quality separate. A change can be well-engineered but wrong, or correct but poorly engineered.
- Do not require a formal spec file. The outcome source may live in the current conversation.
- Do not use tests passing as a proxy for outcome fit unless the tests encode the acceptance criteria.
- Do not approve if verification evidence is absent for the main claim; use "Not enough evidence" instead.
- Do not approve with unresolved candidates, a changed Boundary digest, a missing participating worktree, unauthorized task-created scope creep, or stale state-bound evidence.
- Prefer actionable findings with file/path/hunk references where possible.
- This skill reviews concrete code artifacts/diffs. Use or create a separate review skill for designs, plans, standalone patch files, or pre-implementation proposals.
