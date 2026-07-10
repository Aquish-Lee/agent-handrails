# Coding Engineering Harness Roadmap

**Status:** Directional design, not an implemented harness.

Agent Handrails begins with explicit engineering primitives. A future coding engineering harness may compose them when the handrails, model capability, and project feedback stack have earned that level of trust.

## Layer 0 — Atomic handrails

Current focus:

```text
grill
spec-lite
plan-lite
feedback-loop
two-axis-review
verify-before-claim
branch-sandbox
```

Each primitive must remain useful independently of any orchestrator.

## Layer 1 — Advisory playbooks

Capture common compositions without making them mandatory:

- small bounded change;
- bug fix;
- ambiguous feature;
- broad refactor or migration;
- parallel agent work;
- deployment/runtime change.

A playbook is a recommendation with stop/skip conditions, not a state machine that must always run to completion.

## Layer 2 — Suggestion harness

The harness reads the task and project state, then recommends the next useful handrail.

Expected behavior:

- identify the task shape without rigid classification;
- state which uncertainty, boundary, or evidence motivates the recommendation;
- allow the user to accept, reject, or redirect;
- preserve the current conversation as the live source of truth unless a durable artifact helps.

## Layer 3 — Explicit orchestration harness

The harness may select and execute handrails without asking at every transition, but every selection is recorded.

Minimum state model:

- **Task context** — goal, constraints, non-goals, current task shape;
- **Outcome source** — conversation, issue, PRD, spec, bug repro, deployment objective;
- **Work boundary** — repository, branch/worktree, allowed scope, rollback path;
- **Decision trace** — selected/skipped handrails and reasons;
- **Evidence ledger** — commands, outputs, reviews, runtime observations;
- **Claim ledger** — claims currently supported, unsupported, or blocked;
- **Escalation state** — decisions that require a person.

## Layer 4 — Autonomous coding engineering harness

A capable agent can plan, delegate, implement, review, verify, and prepare integration within explicit boundaries.

Autonomy does not remove gates. It changes who operates them.

A run should still return an inspectable evidence bundle:

```text
Outcome source
Selected and skipped handrails
Work boundary
Changes made
Verification evidence
Review findings
Supported completion claim
Remaining risks
Rollback/reintegration path
```

## Selection contract

A harness should select a handrail only when it changes at least one of:

- the next engineering decision;
- outcome clarity;
- implementation or isolation strategy;
- evidence quality;
- review quality;
- rollback/recovery quality;
- durable coordination or handoff quality.

It should stop adding process when remaining uncertainty no longer changes those things.

## Escalation triggers

A future harness should return control to a human when, for example:

- outcome sources conflict;
- multiple irreversible approaches remain materially different;
- required credentials, production access, or destructive actions are involved;
- available evidence cannot support the requested claim;
- changes exceed the agreed work boundary;
- rollback is unclear;
- review finds a product/design decision rather than an implementation defect.

These are examples, not a complete fixed taxonomy.

## What must be validated before implementation

Before building a real harness, collect real-work evidence about:

1. which handrails repeatedly improve outcomes;
2. which trigger conditions cause unnecessary ceremony;
3. which outputs are reliable enough for another agent to consume;
4. which transitions can safely be automated;
5. what project signals are needed to calibrate autonomy;
6. how evidence and claims should be serialized across agents/sessions;
7. where humans consistently want control back.

The harness is a later composition layer, not the justification for the handrails themselves.
