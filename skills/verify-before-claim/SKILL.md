---
name: verify-before-claim
description: "Explicit-invocation completion gate requiring fresh evidence before claiming work is done, fixed, passing, deployed, or safe. Invoke when a user or an explicit orchestrator requests verification, validation, smoke testing, or a completion report."
disable-model-invocation: true
argument-hint: "claim or change to verify"
---

# Verify Before Claim

Evidence before claims. Use this before saying work is done, fixed, passing, deployed, safe, merged-ready, or production-ready.

This skill verifies the **claim being made**, not the agent's confidence. The final wording must be no broader than the evidence.

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
## Claim to verify
- Claim:
- Outcome source / acceptance criteria:
- Environment:
- Freshness requirement:

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
