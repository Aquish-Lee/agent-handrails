# Review Boundary protocol

Use this protocol for `current-task-state` and `artifact-plus-local` reviews. It separates mechanical candidate discovery from semantic task classification.

## Contents

- Select the review target
- Establish participating workspaces
- Build the candidate inventory
- Classify logical change units
- Freeze the Boundary digest
- Reconcile state changes
- Apply blocking rules

## Select the review target

Choose exactly one:

- `published-artifact`: review only a fixed commit, patch, or PR artifact. Local changes are outside the target, but report when they prevent reproducing or verifying the artifact.
- `current-task-state`: review all current task work across participating workspaces, whether committed or not.
- `artifact-plus-local`: review a fixed artifact plus task-related local state that is not yet represented by it.

Do not silently fall back from current state to a commit diff because the worktree is dirty. A fixed-point diff is one discovery input, not a complete task boundary.

## Establish participating workspaces

Start from the Review Boundary Seed and Work Boundary, then reconcile against current facts:

1. Record the primary repository/worktree identity and exact revision.
2. List linked worktrees with `git worktree list --porcelain`.
3. Name every worktree used for implementation, dependency edits, generation, testing, integration, or recovery.
4. Record each participating worktree's base/exact revision, branch or recovery identity, conflict state, and dirty inventory.
5. Treat an expected but inaccessible worktree as unresolved. Do not approve around it.

Unrelated linked worktrees need not become participants merely because they exist. State why they are not participants when the relationship is ambiguous.

## Build the candidate inventory

For every participating worktree, inventory these layers independently:

1. `committed`: changes from the confirmed base/merge-base through the exact revision.
2. `staged`: index changes not represented by the exact revision.
3. `unstaged`: tracked worktree changes not represented by the index.
4. `untracked`: paths reported by Git. Inspect path/type/size metadata before content.
5. `declared-ignored`: only paths explicitly named by the user, Outcome Source, plan seed, Work Boundary, or current task record.

Do not run a blanket ignored-file scan. Do not infer caches, secrets, virtual environments, generated directories, or local config as declarations. If an ignored artifact may matter but is not declared, ask for or record an explicit declaration before reading it.

Use the bundled `runtime/git_state.py` when available to capture mechanical identities, inventories, and fingerprints. In a standalone copy, use read-only Git commands such as:

```bash
git rev-parse --show-toplevel
git rev-parse HEAD
git diff --name-status <base>...HEAD
git diff --cached --name-status
git diff --name-status
git ls-files --others --exclude-standard
git worktree list --porcelain
```

The helper and commands discover facts only. They do not determine task relevance.

### Preserve layers and mixed files

A path may appear in multiple layers. Preserve that distinction: staged and unstaged hunks in the same file can have different task meaning.

Classify logical change units, not whole filenames, when a file mixes task work with pre-existing or unrelated edits. Reference exact hunks, sections, generated relationships, or artifact fingerprints. If the units cannot be separated confidently, classify them `unresolved`; never exclude the whole file for convenience.

## Classify logical change units

Every candidate must be accounted for exactly once by one of these values:

- `include-required`: needed to satisfy the exact Outcome Reference or its acceptance criteria.
- `include-scope-creep`: created by this task but outside the accepted outcome/guardrails. It remains in review and normally requires removal or explicit authorization.
- `include-inherited-dependency`: pre-existing work that this task depends on, modifies, packages, or would ship with. Review its interaction and state the inheritance.
- `exclude-proven-unrelated`: proven independent of the task, its dependencies, generated outputs, verification, and integration path. Record concrete evidence; “pre-existing,” “uncommitted,” or “not in the plan” is insufficient.
- `unresolved`: relevance, ownership, layer, or dependency cannot yet be determined.

Unexpected work caused by the task is always `include-scope-creep`, never `exclude-proven-unrelated`. Known pre-existing work is an exclusion candidate, not an exclusion. Planned paths are hypotheses, not an allowlist.

For each unit record:

```text
Logical unit ID:
Workspace:
Layer: committed | staged | unstaged | untracked | declared-ignored
Paths / hunks / artifact fingerprints:
Classification:
Rationale and evidence:
Outcome or dependency relationship:
```

The inventory is complete only when every mechanical candidate maps to one or more logical units and every unit has one classification.

## Freeze the Boundary digest

Construct a canonical JSON object containing:

- contract ID, Task ID, Outcome Revision, and review target;
- participating workspace identities;
- base/exact revisions and recovery identities;
- every logical unit's stable ID, layer, path/hunk or artifact fingerprint, classification, and relationship;
- declared ignored paths and their content fingerprints;
- unresolved item IDs;
- relevant mechanical Code State Token fingerprints, excluding `review_boundary_digest` and `captured_at`.

Exclude `captured_at`, prose presentation, and command ordering. Serialize as UTF-8 JSON with keys sorted and separators `,` and `:` with no extra whitespace, then compute SHA-256 over those exact bytes. Record the algorithm and canonicalization. If the bytes were not actually canonicalized and hashed, call the value an opaque boundary revision, not a digest.

Avoid a digest cycle: first capture the mechanical token with `Review Boundary digest: unconfirmed`; compute the Boundary digest from its mechanical fields plus the semantic classifications while excluding the token's boundary field and timestamp; then capture/emit the final token with that digest. If the second mechanical capture differs, discard the digest and reconcile again.

The Boundary digest is semantic: changing a classification or logical-unit mapping changes it even if Git bytes do not. The Code State Token is mechanical: relevant byte/state changes alter its fingerprints even when classifications do not.

## Reconcile state changes

Capture the Code State Token when the boundary is frozen and re-capture it before recommendation or claim.

- Relevant code, artifact, conflict, workspace, or environment change: evidence and recommendation become stale; re-inventory and reverify.
- Outcome Revision change: the boundary, evidence, and recommendation become stale even when code bytes are unchanged.
- Proven unrelated edit: add/reconcile the candidate, recompute the Boundary digest, and retain only evidence whose original narrow scope and relevant mechanical state remain unchanged. The old Evidence Record keeps its original digest; the new Claim Record may cite it only with the explicit unrelated-change reconciliation.
- Child-worktree change: never transfer its evidence to an integrated state without capturing and verifying the integrated workspace.

Reconciliation cannot broaden an old claim.

## Apply blocking rules

Return `Not enough evidence` or `Request changes`; never approve when:

- any candidate is `unresolved`;
- the Boundary digest changed after review began and has not been rechecked;
- a participating worktree is inaccessible, omitted, or has an uncaptured relevant change;
- task-created scope creep remains unauthorized;
- evidence is bound to another Outcome Revision, Boundary digest, relevant Code State Token, or environment;
- only child-worktree evidence exists for an integration claim.
