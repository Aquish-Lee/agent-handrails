---
name: verify-before-claim
description: "Explicit-invocation completion gate requiring fresh evidence before claiming work is done, fixed, passing, deployed, or safe. Invoke when a user or an explicit orchestrator requests verification, validation, smoke testing, or a completion report."
disable-model-invocation: true
argument-hint: "claim or change to verify"
---

# Verify Before Claim

Evidence before claims. Use this before saying work is done, fixed, passing, deployed, safe, merged-ready, or production-ready.

This skill verifies the **claim being made**, not the agent's confidence. The final wording must be no broader than the evidence.

## Contract binding

<!-- handrails-contract
contract: usable-loop/v1
role: claim-gate
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

Bind the claim to an exact Outcome Reference. If direct entry has no reference, create a task-local provisional one from the current request with a stable Task ID, truthful source identity/locator, revision basis, compact snapshot, active lifecycle, fresh currentness, and explicit stale conditions. Do not invent a durable source or authoritative status.

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

When bootstrapping, populate and emit every field in this template; do not replace the record with an ID-only shorthand. When consuming a reference, preserve its exact values in the verification result.

Bootstrap state is always: authority `provisional`, lifecycle `active`, currentness `fresh`.

Keep Task ID and Outcome Source ID independent of Outcome Revision: do not put `r1`, a digest, or another revision suffix into either identity.

If the designated authority is inaccessible, conflicts with another designated source, or its revision mismatches, mark the reference provisional/stale and treat dependent evidence and claims as stale until reconciliation or reconfirmation. Never choose between authorities by recency or durability. A local Capsule may restore orientation but cannot restore authority or freshness.

Never describe an Outcome Revision as a hash or digest unless it was actually computed over identified canonical bytes; otherwise use an honest task-local opaque revision such as `r1`.

## Rules

- Do not let ambient model matching select this skill. Invocation must come from the user or an explicit orchestrator/harness decision.
- No success wording before fresh verification.
- Verify the narrowest claim that matters, then escalate only when task shape, blast radius, or acceptance criteria demand it.
- Read exit code and output. Do not rely on "looks fine" or a command merely starting.
- If verification is blocked, report the blocker and do not claim success.
- If verification fails, report the failure and the next useful diagnostic step; do not rephrase failure as partial success.
- Do not fabricate command output, timestamps, logs, or test results.
- Do not use old evidence unless it is explicitly still fresh and relevant; when in doubt, rerun or downgrade the claim.
- Do not use tests passing as proof of outcome unless the tests/checks encode the relevant acceptance criteria.

## State-bound claim gate

When a claim depends on repository state, require a confirmed Review Boundary and capture the Git Code State Token three times: immediately before verification, immediately after verification, and immediately before the final claim. Prefer the bundled read-only `runtime/git_state.py` when available; a standalone skill may capture the same fields with read-only Git commands. The helper never classifies task relevance.

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

Block a supported claim when any of these apply:

- the Outcome Revision differs from the reviewed or verified revision;
- the Review Boundary contains `unresolved` candidates;
- its digest changed or any participating worktree is missing;
- relevant Code State Token fields changed across the three captures;
- the verification environment differs in a claim-relevant way;
- evidence came from a child worktree but the claim concerns an integrated state.

A proven unrelated edit is not an automatic pass. Reconcile it into a new candidate inventory and Boundary digest; then retain only evidence whose original narrow scope is mechanically unchanged. Never use reconciliation to broaden the old claim.

For a non-repository operational claim, state `Code State Token: not applicable — claim does not depend on repository state` and bind the claim to the exact environment/readback evidence instead. Do not use this exception for code completion, review, integration, build, or deployment-artifact claims.

## Claim-shaped calibration, not rigid levels

Choose evidence by the shape of the claim. These are calibration aids, not gates.

### Operational claim

Examples: service is running, config loaded, port is open, model is available, job finished.

Useful evidence:
- status command or process check,
- config/readback command,
- port/health/log check,
- dry-run or no-op check if available.

### Bug-fix claim

Examples: the reported error is fixed, regression no longer happens, failing input now works.

Useful evidence:
- original repro now passes,
- focused regression test,
- relevant log no longer shows the error,
- no masking of the symptom by swallowing errors.

### Code-change claim

Examples: implementation completed, tests pass, behavior changed as intended.

Useful evidence:
- focused test or smoke path at the public seam,
- relevant suite/build/type/lint when blast radius requires it,
- acceptance criteria mapped to observed behavior.

### Refactor / migration claim

Examples: behavior preserved, interface migrated, data/config transition safe.

Useful evidence:
- characterization tests or before/after smoke checks,
- compatibility checks,
- migration/readback/rollback check,
- affected integration path still works.

### Deployment / runtime claim

Examples: deployed, reachable, healthy, safe to roll forward.

Useful evidence:
- command exit code from deploy/start/reload,
- service status,
- health endpoint or functional smoke,
- logs after the change,
- config/version/readback,
- rollback path identified or tested when risk demands it.

### Review / merge-readiness claim

Examples: ready to merge, no blocking issues, acceptable risk.

Useful evidence:
- `two-axis-review` result or equivalent diff review,
- verification matrix coverage,
- known remaining risks stated explicitly,
- CI/local checks relevant to the changed area.

## Process

1. **Name the exact claim**

   Good:
   - "The API smoke path returns 200 locally."
   - "The original repro no longer fails."
   - "Focused tests for `<module>` pass."

   Too broad unless proven:
   - "The feature works."
   - "The bug is fixed everywhere."
   - "The deployment is safe."
   - "No regressions."

2. **Map claim to evidence**

   For each claim, state:
   - What would prove it?
   - What command/check/log/readback will be used?
   - What output or exit code is expected?
   - What would remain unproven even if the check passes?

3. **Run or inspect evidence**

   Prefer the smallest convincing command first. Escalate if:
   - the command only proves a function-level detail while the claim is system-level,
   - the change touches multiple files/modules,
   - acceptance criteria involve runtime behavior,
   - deployment/data/security/safety risk exists,
   - prior checks are stale or from a different environment.

4. **Interpret evidence honestly**

   - Passing command with irrelevant scope = not enough evidence.
   - Command starts but process later crashes = not verified.
   - Log contains warnings relevant to the claim = partially verified or not verified.
   - One happy-path smoke does not prove edge cases unless the claim is limited to the happy path.

5. **State result with scoped language**

   Use:
   - `Verified by <command/check>: <specific claim>.`
   - `Partially verified: <what passed>; missing <what remains>.`
   - `Not verified: <blocker/failure>.`
   - `Verification failed: <evidence>; next diagnostic step is <step>.`

## Gate format

````markdown
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

## Claim to verify
- Claim:
- Exact Outcome Reference / acceptance criteria:
- Environment:
- Freshness requirement:

## State binding
- Review Boundary digest:
- Code State Token before verification:
- Code State Token after verification:
- Code State Token before claim:
- Participating workspaces reconciled:

## Evidence plan
| Claim part | Check / command | Expected evidence | Scope limit |
| --- | --- | --- | --- |
| ... | ... | ... | ... |

## Commands / checks run
```bash
<command 1>
<command 2>
```

## Evidence observed
- Exit codes:
- Key output / logs / readback:
- Failures / warnings:
- What this proves:
- What this does not prove:

## Result
Verified | Partially verified | Not verified | Verification failed

## Claim Record
- Claim ID:
- Task ID:
- Outcome Revision:
- Review Boundary digest:
- Code State Token:
- Claim:
- Evidence IDs:
- Status: supported | unsupported | blocked | stale
- Scope limit:
- Stale when:

## Remaining risk / next step
- ...
````

## Language discipline

Allowed only after evidence:

- "Verified by `<command>`: ..."
- "Focused tests passed for `<scope>`: ..."
- "Smoke check passed for `<path>` in `<environment>`: ..."
- "Partially verified: ..."
- "Not verified because ..."
- "Verification failed because ..."

Avoid before evidence or when evidence is too narrow:

- "done"
- "fixed"
- "works"
- "safe"
- "ready"
- "no regressions"
- "should work"
- "looks good"
- "probably"

## When to call another skill

- Use `feedback-loop` when no good verification seam exists yet.
- Use `two-axis-review` when the claim is merge-readiness or implementation quality, not just runtime/test evidence.
- Use `spec-lite` or `grill` when the claim cannot be verified because the desired outcome is still ambiguous.

## Anti-patterns

- Running a broad command and claiming success without reading output.
- Treating typecheck/build success as proof of product behavior.
- Treating a mocked unit test as proof of integration behavior.
- Saying "fixed" when only one symptom was suppressed.
- Claiming deployment success from a successful upload without service health/readback.
- Ignoring warnings because exit code was zero.
- Expanding the claim after seeing narrow evidence.
