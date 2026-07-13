# Governance

Agent Handrails currently uses a maintainer-led model suitable for an early
alpha and a small contributor community.

## Decision making

Maintainers seek evidence-backed consensus in Issues and PRs. Routine fixes may
be accepted through review. Changes to core philosophy, contract semantics,
record ownership, public distribution, compatibility, or security require a
Design Proposal Issue and normally an ADR.

When consensus cannot be reached, the lead maintainer makes the final decision
and records the rationale. Decisions may be revisited when dogfood or community
evidence changes.

## Roles

- Contributors propose Issues/PRs and participate under the Code of Conduct.
- Maintainers triage, review, protect release integrity, moderate the community,
  and decide releases.
- The lead maintainer is the final escalation point for product and governance decisions.

Maintainer changes are recorded in [MAINTAINERS.md](MAINTAINERS.md). Additional
maintainers are appointed based on sustained, trustworthy contributions,
technical judgment, community conduct, and willingness to share operational
responsibility.

## Releases

Maintainers publish immutable tags from accepted default-branch commits after
the versioned local acceptance gate. Alpha releases may use advisory hosted CI.
Security fixes may use an expedited private advisory flow.
