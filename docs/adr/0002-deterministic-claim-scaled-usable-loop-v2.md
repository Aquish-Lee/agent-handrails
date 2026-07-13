# ADR 0002: Deterministic, claim-scaled usable-loop/v2

- Status: Accepted
- Date: 2026-07-13
- Supersedes for new work: ADR 0001 / `usable-loop/v1`

## Context

`usable-loop/v1` established explicit handrails and exact-state evidence, but its
record graph accidentally made Review Boundary creation a hidden prerequisite
for ordinary verification. The boundary digest was also accepted from the
caller, Checkpoint ownership was concentrated in one skill, and development
evidence could be mistaken for claim evidence. These properties made narrow
facts too expensive and broad claims less reliable than intended.

## Decision

New work uses `usable-loop/v2`; v1 remains immutable history and a rollback
baseline.

1. Verification routes by claim width: `fact`, `scoped-task`, or
   `high-assurance`.
2. Facts need fresh claim evidence but no boundary. Scoped tasks need a
   deterministic Claim Boundary. High-assurance claims need a current Review
   Record produced by two-axis review.
3. A local runtime inventories Git candidates, assigns stable Candidate/Hunk
   IDs, validates complete semantic classifications, creates the canonical
   payload, computes its SHA-256 digest, and recaptures state. Callers cannot
   supply a naked digest. Compact confirmation may atomically persist that full
   boundary through an explicit output path so later checks capture the exact
   artifact instead of reconstructing it.
4. Development evidence is `observed`, never claim-supporting. Only
   verify-before-claim produces claim evidence with `fresh | stale | blocked`.
5. Any relevant outcome, boundary, code-state, or environment change stales
   dependent evidence. v2 deliberately provides no unrelated-change reuse
   proof; rerun the narrowest relevant check.
6. Every handrail may emit the shared Checkpoint projection, but expands it only
   for pause, handoff, context risk, expensive evidence, or explicit request.
7. A current user request is authoritative when the user controls the task and
   no permission/source conflict exists. Agent-derived or reinterpreted meaning
   remains provisional.
8. Classification rationale is canonical semantic content. Editing it creates a
   new boundary even when mechanical state and classification categories are
   unchanged.

## Consequences

- Micro facts and small tasks no longer traverse a hidden review workflow.
- Review retains semantic judgment while boundary mechanics become repeatable
  and fail closed on missing classification, authorization, drift, or tampering.
- Output and context cost fall because full records live in generated references
  and appear only when continuity requires them.
- Evidence cannot survive state changes in v2, even if a later reviewer believes
  the change was unrelated. This is intentionally conservative for the alpha.
- Standalone skills that need Git state carry the generated runtime locally.

## Compatibility

The v1 contract, semantic document, ADR, runtime, and alpha.1 tag are not edited.
There is no mixed v1/v2 record composition path.
