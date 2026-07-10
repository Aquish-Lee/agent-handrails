# ADR 0001: Version the usable-loop contract and keep continuity artifacts non-authoritative

Status: Accepted
Date: 2026-07-10

## Context

The seven Agent Handrails are intentionally atomic and independently invokable. Their existing prose described useful compositions, but cross-skill handoffs did not preserve an exact task/outcome identity or expose when a downstream plan, review, evidence record, or claim had become stale.

Keeping all continuity only in conversation is lightweight but vulnerable to context compression, new sessions, parallel agents, and expensive evidence reconstruction. Requiring a tracked spec or phase document after every handrail would preserve context at the cost of long-lived document debris and stale competing authorities.

The review model also relied on fixed commit ranges, which cannot describe staged, unstaged, untracked, ignored-declared, or multi-worktree task state. Binding the public contract directly to Git commits would make that weakness harder to correct and would obstruct a future Jujutsu provider.

## Decision

1. Adopt the versioned `usable-loop/v1` handoff contract.
2. Maintain three contract surfaces:
   - a machine catalog at `contracts/usable-loop-v1.json`;
   - canonical maintainer semantics at `docs/contracts/usable-loop-v1.md`;
   - a minimal self-contained projection in every deployed `SKILL.md`.
3. Preserve outcome continuity with a stable Task ID and an exact Outcome Reference containing source identity/revision, authority basis, snapshot, lifecycle, currentness, supersession, and stale rules.
4. Allow every handrail to be a direct entry point. When no reference exists, it bootstraps a truthful provisional reference from the current request.
5. Keep persistence conversation-first. Materialize at most one rewritten, ignored `.scratch/<task-id>/STATE.md` Local Capsule only when continuity risk warrants it.
6. Treat the Local Capsule as a cache/index. It never becomes the Outcome Source, grants authority, supersedes a reference, or restores evidence freshness.
7. Let planning produce a Review Boundary Seed only. The final Review Boundary is decided later from complete current-state inventory and semantic classification.
8. Keep public names VCS-neutral. The first implementation supports Git; Jujutsu may become an optional provider after the v0.1 loop is proven.
9. Do not add an eighth gateway/state/checkpoint skill, a mandatory workflow, or an orchestrator in this release.
10. Require independently deployed skills to remain useful without reading repository-level contract or documentation files.

## Consequences

### Positive

- Downstream work can name the exact outcome revision it supports.
- Stale plans, reviews, evidence, and claims become explicit instead of being inferred from conversational recency.
- Cross-session continuity is available without creating tracked phase-document piles.
- Review can evolve from commit-range assumptions to dirty/multi-worktree inventory without changing upper-layer vocabulary.
- VCS-neutral records leave room for Jujutsu Change ID, Commit ID, and Operation ID mappings later.

### Costs and limitations

- Skill outputs carry a small common envelope.
- Maintainers must keep the machine catalog, semantic document, and skill-local projections consistent.
- A provisional or stale reference can limit approval/claim language until authority is restored.
- A Local Capsule does not solve cross-machine durable coordination; project knowledge still belongs in Issues, PRs, specs, or ADRs.
- Static checks prove structural consistency, not that a model will follow the instructions in real work; dogfood remains required.

## Rejected alternatives

### Conversation only, with no checkpoint representation

Rejected because long or resumed tasks can lose the evidence/decision chain and require costly reconstruction.

### Automatically write a spec or phase document after every handrail

Rejected because most small tasks do not need durable artifacts and accumulated documents become stale noise.

### Treat the Local Capsule as source of truth

Rejected because a local cache can be stale, unavailable elsewhere, or conflict with a user/Issue/spec authority.

### Treat a fixed Git range as the complete Review Boundary

Rejected because it omits current dirty, untracked, explicitly declared ignored, and participating-worktree state.

### Treat planned paths as an allowlist

Rejected because implementation discovers dependencies and scope creep; omitted paths are not evidence of irrelevance.

### Expose a Git-specific public contract

Rejected because task/outcome/evidence semantics do not inherently depend on Git and should admit future providers such as Jujutsu.

### Add a gateway or orchestrator skill now

Rejected because selection automation has not yet been earned through real-use evidence, and each current handrail must remain independently valuable.
