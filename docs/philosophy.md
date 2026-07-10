# Philosophy

## The thesis

Agent Handrails is **manual-first, not manual-only**.

It rejects neither automation nor autonomous coding. It rejects automation that has not earned trust through understandable primitives, real evidence, bounded execution, and recoverable decisions.

> Autonomy should be earned, not assumed.

## Handrails, not rails

A rail determines the route. A handrail supports the person or system moving through it.

That distinction shapes this project:

- the user retains control of development rhythm;
- no handrail is mandatory merely because it might be relevant;
- each handrail remains independently useful;
- an orchestrator may compose handrails without turning their composition into hidden ceremony;
- the shortest professionally adequate path is preferable to the most elaborate process.

## Engineering primitives before orchestration

The repository develops in this order:

1. Define a small engineering primitive.
2. Use it manually in real work.
3. Observe when it helps, when it wastes time, and where it fails.
4. Refine its input, output, evidence, and stop conditions.
5. Capture useful compositions as advisory playbooks.
6. Only then let a harness select or execute it automatically.

This reverses the common framework-first approach. The harness should be built on validated primitives rather than using orchestration to hide weak primitives.

## Explicit invocation

Every current handrail sets cross-platform frontmatter:

```yaml
disable-model-invocation: true
```

Its Codex metadata also sets:

```yaml
policy:
  allow_implicit_invocation: false
```

On platforms that support the respective metadata, ambient semantic matching should not silently select the skill. Invocation must be explicit through one of two paths:

- a person requests the handrail;
- an orchestrator/harness makes a visible, inspectable selection decision.

An explicit orchestrator decision should record at least:

- the task and current Outcome Reference;
- why this handrail changes the next decision or evidence;
- the expected output or stop condition;
- what will happen if the handrail cannot produce useful evidence;
- whether human review is required before continuing.

## Evidence gates over workflow gates

Rigid workflow gates ask whether a phase has been completed:

```text
Did we brainstorm? Did we write a spec? Did we write tests?
```

Engineering evidence gates ask what the next claim or decision requires:

```text
Is the desired behavior still ambiguous?
What behavior must be preserved?
What evidence would justify this completion claim?
Does this work need an isolation boundary?
```

The second form adapts better to task shape, project maturity, and model capability.

## Capability-aware autonomy

The same task should not receive the same autonomy under every condition. A harness should consider:

- model/tool capability;
- clarity, authority, and currentness of the Outcome Reference;
- repository feedback quality;
- blast radius and reversibility;
- isolation and rollback options;
- observability of the target environment;
- cost of a false success claim;
- whether the user wants direct control, approval points, or autonomous execution.

A stronger model can receive more freedom only when the surrounding evidence and recovery mechanisms are also strong enough.

## Human override and legibility

Automation is acceptable only while a human can understand and interrupt it.

A future harness should make these visible:

- selected handrails and reasons;
- skipped handrails and reasons;
- worktree/branch/sandbox boundary;
- current Outcome Reference;
- evidence collected so far;
- claims supported and unsupported;
- unresolved risks and escalation points.

## Non-goals

Agent Handrails is not intended to become:

- an always-on gateway that captures every task;
- a universal phase diagram for all software engineering;
- a giant skill marketplace;
- a substitute for repository-specific standards or domain knowledge;
- a promise that automation is safe merely because a workflow ran;
- a framework that forces strong engineers to surrender judgment.
