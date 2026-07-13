# Agent Handrails Workflow

Agent Handrails exposes seven explicit primitives without imposing a universal
pipeline. Select one only when it changes the next decision, boundary, evidence,
or claim.

## Selection rule

- Execute and directly observe a clear micro-task.
- Use `grill` only for consequential unresolved intent.
- Use `spec-lite` only when durable outcome semantics help.
- Use `plan-lite` when ordered slices, risk controls, or a boundary seed help.
- Use `branch-sandbox` when isolation materially improves rollback/interference.
- Use `feedback-loop` when iterative behavioral evidence improves development.
- Use `two-axis-review` for explicit review and high-assurance readiness.
- Use `verify-before-claim` for the exact claim being made.

A skill may suggest another, but must return control. There is no hidden
transition or mandatory chain.

## Outcome continuity

All active skills use `usable-loop/v2`. An unconflicted current request is
authoritative when the user controls the scope. Agent-derived interpretation is
provisional. Outcome changes create a new revision; dependent evidence becomes
stale.

Every skill is a direct entry point and can create the minimal Outcome Reference
it needs. A saved spec, plan, or Capsule does not become authority by existing.

## Claim-scaled paths

```text
narrow fact
  direct observation → fresh claim evidence → fact Claim Record

small completed task
  inventory → Claim Boundary → narrow checks → scoped-task Claim Record

merge/deploy/production/no-regressions claim
  inventory → Review Boundary → two-axis Review Record
  → exact recapture/checks → high-assurance Claim Record
```

Micro facts never require review. Broad claims never downgrade to a small-task
boundary merely to avoid review.

## Real current state

`runtime/handrails_state.py` inventories committed-since-base, staged,
unstaged, untracked, explicitly declared ignored artifacts, and participating
worktrees. It emits deterministic Candidate/Hunk IDs. Semantic classification
references those IDs; the runtime validates complete non-overlapping coverage,
authorization, canonicalizes the payload, computes SHA-256 itself, and
recaptures state. Compact confirmation can atomically persist the full boundary
to an explicit path; later validation captures that exact artifact.

The runtime never accepts a caller's naked Boundary Digest. Undeclared ignored
content is not scanned. Missing units, unauthorized included changes, state
drift, or digest mismatch fail closed. Classification rationale is digest-bound
semantic content, so callers reuse a persisted boundary rather than reconfirming
it with newly worded rationale.

Compact inventory keeps Candidate/Hunk routing IDs, paths, layers, ordinals,
headers, and conflicts while omitting redundant fingerprint strings. Store the
machine projection privately, query it incrementally, and let a risk map control
inspection depth without reducing complete boundary coverage.

Private machine evidence inside a participating worktree must be ignored and
must remain outside declared ignored candidates. Do not declare the `.scratch`
root merely because logs or Capsules exist there: declaring it makes its bytes
part of the boundary, so a later log write would stale the record.

## Evidence ownership

Feedback Loop's `observed` development evidence guides the next engineering
move. It cannot support a completion claim. Verify Before Claim reruns the
required checks and owns `fresh` claim evidence. There is no reverse backflow
requirement.

Any relevant Outcome Revision, Boundary Digest, code-state, or environment
change stales dependent evidence. v2 does not retain old evidence after an
unrelatedness argument; run the narrowest relevant check again.

## Conversation-first continuity

Ordinary calls return conclusion, evidence, scope limits, and the necessary next
step. Any handrail may expand a Checkpoint only for pause/block, cross-session or
agent handoff, context risk, expensive/non-repeatable evidence, or explicit
handoff request. Persist at most one rewritten `.scratch/<task-id>/STATE.md`.

Resume in this order:

1. reconcile the designated Outcome Source and Revision;
2. read the Capsule for orientation;
3. recapture all participating state;
4. treat prior evidence as stale when any binding changed.

Promote durable knowledge to an Issue, PR, spec, or ADR and delete the Capsule
after integration/handoff when it contains no unique information.

## Isolation safety

Stash, force branch deletion, deletion of worktrees containing results, reset,
rebase, and overwrite require explicit authorization. Default to reporting
cleanup commands with preconditions, not executing them.

## Distribution and release evidence

Canonical source lives in this repository. `scripts/render_contract.py --check`
guards generated skill-local contract/runtime copies. The bundle installer
deploys all seven skills together. Local tests, repository validation, official
Skill validation, temporary install/check, real Codex calls, and clean-clone
acceptance are release evidence. Hosted CI remains advisory while billing is
unavailable.
