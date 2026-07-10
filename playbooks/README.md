# Playbooks

Playbooks are advisory compositions of independent handrails. They are not mandatory chains, and a capable user or harness should skip steps that do not change the next decision, boundary, evidence, or review quality.

## Small bounded change

```text
implement -> verify-before-claim
```

Use direct execution when the desired change, scope, and verification seam are already clear.

## Bug fix

```text
optional grill -> feedback-loop -> implement -> verify-before-claim
```

Add `two-axis-review` when the diff is broad, risky, or merge-readiness is part of the claim. Use `grill` only when desired behavior or blast radius is ambiguous.

## Ambiguous feature

```text
grill -> optional spec-lite -> plan-lite -> feedback-loop
-> two-axis-review -> verify-before-claim
```

Skip `spec-lite` when the conversation or issue already provides a stable outcome contract. Keep the plan in live context unless durable coordination helps.

## Large refactor or migration

```text
branch-sandbox -> optional spec-lite -> plan-lite
-> feedback-loop -> two-axis-review -> verify-before-claim
```

Characterization checks or runtime smoke evidence may be more valuable than new unit tests. Isolation does not substitute for review or verification.

## Parallel agent work

```text
branch-sandbox -> plan-lite -> delegated implementation
-> two-axis-review -> verify-before-claim
```

Give each agent an explicit work boundary. Parallelism is useful only when scopes and reintegration paths are clear.

## Deployment/runtime change

```text
optional plan-lite -> execute -> verify-before-claim
```

Verification should target the real environment: process state, logs, ports, health checks, configuration readback, and rollback readiness as applicable.

## Harness interpretation

A future harness may use these as priors, not scripts. It should explain selections and skips, then stop adding process once the remaining uncertainty no longer changes implementation, evidence, rollback, or review.
