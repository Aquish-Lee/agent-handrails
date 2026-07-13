# Philosophy

## Manual-first, automation-ready

Agent Handrails rejects neither automation nor autonomous coding. It rejects
automation that has not earned trust through understandable primitives, real
evidence, bounded execution, and recoverable decisions.

> Autonomy should be earned, not assumed.

## Handrails, not rails

A rail determines the route. A handrail supports the person or system choosing
the route. Therefore:

- the user retains control of development rhythm;
- no handrail is mandatory merely because it might be relevant;
- each handrail stays useful alone;
- visible orchestration may compose them without hidden ceremony;
- the shortest professionally adequate path beats the most elaborate process.

## Evidence gates, not workflow gates

The useful questions are not whether brainstorming, a spec, or a test phase ran.
They are whether the desired behavior is clear, isolation is needed, the actual
current state is authorized, and fresh evidence supports the exact claim.

`usable-loop/v2` makes that proportional: narrow facts take a direct path,
small-task completion gets a lightweight deterministic boundary, and broad
readiness/safety claims require formal two-axis review.

## Mechanical facts and semantic judgment

The state runtime owns inventories, fingerprints, Candidate/Hunk IDs,
canonicalization, SHA-256, and drift detection. People/agents own task relevance,
rationale, authorization, outcome fit, and engineering judgment. Neither side
pretends to do the other's job.

## Explicit invocation

Codex metadata sets `policy.allow_implicit_invocation: false`. A person invokes a
skill directly, or a future harness makes a visible selection decision with a
reason, expected output, stop condition, and return-of-control point.

The main Agent Skills frontmatter remains standard (`name` and `description`
only); platform-specific invocation policy lives in `agents/openai.yaml`.

## Conversation first, durable knowledge where it belongs

Routine work should not leave a trail of phase documents. A compact Checkpoint
is expanded only when continuity is genuinely at risk, and its one local Capsule
is rewritten rather than accumulated. Durable project decisions and defects
belong in Issues, PRs, specs, or ADRs.

## Capability-aware autonomy

Autonomy depends on model/tool capability, outcome authority, repository
feedback quality, blast radius, reversibility, observability, cost of false
success, and the user's desired control points. A workflow having run is never by
itself evidence that autonomy was safe.

## Non-goals

Agent Handrails is not an always-on gateway, universal phase diagram, giant
marketplace, substitute for repository/domain knowledge, or promise of safety
from workflow completion.
