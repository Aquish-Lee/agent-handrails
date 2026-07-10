---
name: feedback-loop
description: "Explicit-invocation behavior/system feedback loop for bug fixes, features, refactors, and deployments. Invoke when a user or an explicit orchestrator requests test-first work, regression coverage, smoke checks, behavior verification, or evidence-driven development."
disable-model-invocation: true
argument-hint: "behavior, bug, feature, refactor, or deployment path to verify through feedback"
---

# Feedback Loop

Use tests and runtime checks as a professional feedback loop. The point is not ritual or proving a function works; the point is to keep development aligned with the real module, system, and business behavior.

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
