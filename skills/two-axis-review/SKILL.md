---
name: two-axis-review
description: "Explicit-invocation review of a diff along two independent axes: outcome fit and engineering quality, with verification evidence reported separately. Invoke when a user or an explicit orchestrator requests review of a branch, PR, diff, implementation, or work since a fixed point."
disable-model-invocation: true
argument-hint: "fixed point, PR, branch, or diff to review"
---

# Two-Axis Review

Review changes without mixing two questions: did we build the right outcome, and did we build it well? Verification evidence is reported separately so "looks right" does not become a success claim.

## Inputs

- Fixed point: commit, branch, tag, PR base, worktree base, or `HEAD~N`.
- Outcome source: issue, PRD, `spec-lite` output, plan, conversation alignment snapshot, goal acceptance criteria, bug repro, deployment objective, or explicit "no outcome source".
- Standards source: repo docs, existing patterns, linters, type system, architecture decisions, and smell baseline. Use `references/smell-baseline.md` when deeper smell vocabulary is needed.
- Evidence source: commands already run, test output, build output, smoke checks, logs, health/readback results.

If the fixed point is missing, ask for it. If there is no formal spec, review against the best available outcome source instead of pretending Spec is not assessable.

## Optional parallel review

For large diffs, high-risk changes, or work where review quality matters more than minimal overhead, split the review into independent passes:

- **Outcome reviewer**: checks only Outcome Fit against the outcome source and acceptance criteria.
- **Quality reviewer**: checks only Engineering Quality against repo standards, architecture, and smell baseline.
- **Evidence reviewer** (optional): checks only verification evidence and missing proof.

Run these in parallel agents/sessions when available, then aggregate without merging the axes. This improves focus and can reduce wall-clock time. Do not force parallel review for small diffs.

## Process

1. **Confirm review boundary**
   ```bash
   git rev-parse <fixed-point>
   git diff <fixed-point>...HEAD --stat
   git diff <fixed-point>...HEAD
   ```
   If the diff is empty or the fixed point is wrong, stop and report that.

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

5. **Report separately**
   ```markdown
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
- Prefer actionable findings with file/path/hunk references where possible.
- This skill reviews concrete code artifacts/diffs. Use or create a separate review skill for designs, plans, standalone patch files, or pre-implementation proposals.
