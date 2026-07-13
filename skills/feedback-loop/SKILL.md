---
name: feedback-loop
description: "Explicit-invocation behavior/system feedback loop for bug fixes, features, refactors, and deployments. Invoke when a user or an explicit orchestrator requests test-first work, regression coverage, smoke checks, behavior verification, or evidence-driven development."
disable-model-invocation: true
argument-hint: "behavior, bug, feature, refactor, or deployment path to verify through feedback"
---

# Feedback Loop

Use tests and runtime checks as a professional feedback loop. The point is not ritual or proving a function works; the point is to keep development aligned with the real module, system, and business behavior.

## Contract binding

<!-- handrails-contract
contract: usable-loop/v1
role: evidence-builder
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

Carry the exact Outcome Reference that the evidence supports. If none exists, create a task-local provisional reference from the current request: record a stable Task ID, truthful source kind/ID/locator, revision basis, compact snapshot, active lifecycle, fresh currentness, and explicit stale conditions. Do not invent a durable source or authoritative status.

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

When bootstrapping, populate and emit every field in this template; do not replace the record with an ID-only shorthand. When consuming a reference, preserve its exact values in the feedback result.

Bootstrap state is always: authority `provisional`, lifecycle `active`, currentness `fresh`.

Keep Task ID and Outcome Source ID independent of Outcome Revision: do not put `r1`, a digest, or another revision suffix into either identity.

If the designated authority is inaccessible, conflicts with another designated source, or its revision mismatches, mark the reference provisional/stale; dependent evidence and claims stay stale until reconciliation or reconfirmation. Never choose between authorities by recency or durability. A local Capsule can restore orientation but cannot supply authority or evidence freshness.

Never describe an Outcome Revision as a hash or digest unless it was actually computed over identified canonical bytes; otherwise use an honest task-local opaque revision such as `r1`.

## Rules

- Do not let ambient model matching select this skill. Invocation must come from the user or an explicit orchestrator/harness decision.
- Test through public seams or real runtime boundaries, not private implementation.
- Choose evidence depth by task shape, business importance, and blast radius.
- One vertical slice at a time where practical: one behavior → one failing/reproducing signal → minimal professional change → passing evidence.
- For bugs, reproduce first. The repro may be an automated test, smoke script, log assertion, API call, UI flow, or deterministic command.
- For refactors, preserve behavior with characterization tests or smoke checks before restructuring.
- For deployment/operations, use health checks, logs, ports, config readback, and rollback checks; do not fake unit tests where runtime verification is the real seam.
- Exploratory spikes are allowed, but mark them as spikes and either delete, isolate, or convert the learning into durable tests/checks before productionizing.
- Do not blindly delete existing code because it was written before tests; add coverage around risky behavior before changing it.

## When this is worth it

Use this skill when at least one is true:

- Behavior is important, subtle, or likely to regress.
- A bug needs a reproducible failure before fixing.
- Refactor/migration needs behavior preservation.
- Public API, data contract, model/service integration, or user-visible flow changes.
- Deployment/runtime correctness matters more than isolated function correctness.
- You need confidence before delegating work to another agent/session.

It may be overkill for one-off commands, pure documentation, visual copy tweaks, generated boilerplate, or throwaway spikes. In those cases, use a small smoke/readback check instead.

## Discover the project feedback stack

Do not rely on generic language checklists unless the project gives no better signal. First inspect the repo/runtime to discover how this project proves correctness:

- existing test commands and test layout;
- build/type/lint commands;
- smoke scripts, health endpoints, CLI checks, or notebooks;
- API contracts, fixtures, golden examples, or integration harnesses;
- deployment/runtime verification commands;
- domain-specific acceptance criteria.

Examples like pytest, vitest, cargo test, go test, Playwright, health endpoints, or log checks are illustrative only. Choose the evidence that fits this project; do not let a short example list cap model reasoning.

## Evidence forms

Pick the smallest evidence that proves the relevant behavior:

- **Focused automated test**: unit/integration test at a public seam.
- **Regression test/repro**: fails or reproduces the bug, then passes after the fix.
- **Characterization test**: captures current behavior before refactor.
- **Smoke script/command**: exercises the real runtime path.
- **Contract test/check**: verifies API/data/service boundary.
- **System/business check**: proves the acceptance criterion at module/system/workflow level.

Function-level evidence is only enough when the acceptance criterion is truly function-level. Usually, prefer the lowest seam that still proves the business/system behavior.

## Workflow

1. **Choose the seam**
   ```text
   Candidate seams:
   Recommended seam:
   Observable behavior:
   Why this seam proves the business/system requirement:
   Evidence form:
   ```

   If multiple plausible seams exist, present them with trade-offs and ask the user to choose before writing tests/checks.

2. **Red / reproduce / characterize**
   - Write one focused failing test, repro command, or characterization check.
   - Run it.
   - Confirm the signal is meaningful: expected failure for new behavior/bug, or stable baseline for refactor.
   - If it fails due to setup noise, fix the setup before touching production code.

3. **Green / change**
   - Implement the smallest professional change that satisfies this behavior.
   - Avoid future-proofing, unrelated refactors, and test-only production APIs.

4. **Refactor after green**
   - Improve names, remove duplication, deepen modules if obvious.
   - Re-run the focused evidence after each meaningful refactor.

5. **Escalate verification**
   - Focused evidence first.
   - Then related tests/build/typecheck/smoke when the change crosses module, service, UI, data, or deployment boundaries.
   - Verify acceptance criteria, not just test pass/fail.

## Bind evidence to current state

For repository-dependent evidence, capture a Code State Token immediately before the check and again immediately after it. Prefer the bundled read-only `runtime/git_state.py` when available; otherwise capture the equivalent Git facts with `rev-parse`, staged/unstaged diffs, `ls-files --others --exclude-standard`, explicit ignored paths, and `worktree list`. The helper inventories and fingerprints; it never decides which candidates belong to the task.

Use the confirmed Review Boundary digest. If only a Review Boundary Seed exists—or direct entry has no boundary record—use `unconfirmed` and mark the evidence `unknown`; such evidence can guide development but cannot support approval or a completion claim until `two-axis-review` confirms the inventory.

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

Do not scan ignored files. Fingerprint an ignored artifact only through an explicit task declaration. Include task-related untracked content explicitly; a filename-only inventory does not bind its bytes.

After each meaningful check, emit an Evidence Record:

```text
## Evidence Record
Evidence ID:
Task ID:
Outcome Revision:
Review Boundary digest:
Code State Token:
Environment:
Check:
Observed result:
Scope:
Freshness: fresh | unknown | stale
Captured at:
```

Evidence is `fresh` only when the before/after token's relevant fields match, the Outcome Revision is unchanged, the Review Boundary digest is confirmed and unchanged, and the relevant environment matches. A relevant mismatch makes it `stale`; do not silently rerun a different check or widen its scope. A proven unrelated edit may preserve only the original narrow evidence after the candidate inventory is reconciled and re-digested.

Evidence captured in a child worktree supports only that worktree state. It does not support an integration claim until the integrated workspace receives its own capture and verification.

## Return a Checkpoint-compatible Feedback result

End every invocation with this compact Feedback result, even when no file is written:

```text
## Feedback result / Checkpoint
Task ID:
Outcome Reference: complete usable-loop/v1 record, including locator, revision, authority, snapshot, and stale conditions
Boundary state: seed | confirmed digest | unresolved, with participating workspaces
Code State Token: exact token or unconfirmed/not-applicable with reason
Repro or baseline:
Change delta:
Done:
Next:
Blockers:
Decision delta:
Evidence delta: Evidence IDs, freshness, and scope
Supported claims:
Still unverified:
Stale when:
Delete when: optional; only for a materialized Local Capsule
```

Keep this result in the conversation only by default. A clear, single-session task must not create a checkpoint file merely because this skill ran.

Materialize a Local Capsule only when continuity would otherwise be costly or unsafe:

- work crosses a session or agent handoff;
- context compaction/loss is imminent or has occurred;
- work pauses or is blocked before a clean handoff;
- relevant uncommitted state must be recovered later; or
- evidence is expensive, environment-specific, or non-repeatable.

When a trigger applies and local project writes are allowed, compactly rewrite exactly one living `.scratch/<task-id>/STATE.md`. Do not append phase logs and do not create sibling checkpoint/spec files. Use a stable filesystem-safe task slug contained under `.scratch/`; never interpolate path separators or `..` from an untrusted Task ID.

The Capsule must preserve the complete Checkpoint above, including unsupported claims and scope limits. It is an orientation cache, not an Outcome Source, authority, revision, or freshness proof. If writing is unavailable, return the same complete record in conversation and state `Capsule: not persisted`.

Keep only compact observations, Evidence IDs, locators, digests, and reproducible commands. Never copy credentials, tokens, private keys, secret values, or large/raw logs into the Capsule; Git ignore is not secure storage.

On resume:

1. Read the designated Outcome Source first when accessible and compare its exact revision.
2. Read the one Capsule to restore orientation, next action, blockers, and prior evidence IDs.
3. Recapture every participating repository/workspace and relevant environment before trusting evidence.
4. Mark mismatched evidence stale and run only the focused revalidation needed for the next claim.
5. If authority is unavailable, conflicting, or revision-mismatched, resume provisional/stale and request reconciliation before reusing outcome-dependent claims.

Delete the Capsule only after integration or a clean durable handoff, and only after every unique decision, defect, evidence recipe, or follow-up has been promoted to an Issue/PR/spec/ADR or made reproducible elsewhere. Never delete it merely because one check passed.

## Good evidence checklist

- Names behavior in domain language.
- Uses a public seam or real runtime boundary.
- Expected value comes from the requirement/example/observed bug/business rule, not from reimplementing the code.
- Would survive internal refactor.
- Fails or reproduces before the fix when it should.
- Passes after the fix/change.
- Proves the relevant module/system/business behavior, not just an isolated function unless that is the real requirement.
- Does not over-mock the thing being tested.
- Does not add production hooks solely for tests unless they are real design seams.

## Anti-patterns

- Testing private functions when public behavior is available.
- Treating "function works" as proof that the module/system works.
- Snapshotting large output without asserting meaning.
- Mocking the system under test so the test only verifies the mock.
- Writing all tests first for imagined behavior, then forcing implementation to match the fantasy.
- Keeping a flaky test and treating retries as verification.
- Declaring success from tests alone when acceptance criteria require runtime/deployment/business evidence.
