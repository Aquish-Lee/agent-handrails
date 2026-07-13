# Changelog

All notable changes to Agent Handrails are recorded here.

## [0.1.0] - Unreleased

### Added

- Seven explicit, independently deployable engineering handrails with ambient invocation disabled.
- The versioned `usable-loop/v1` contract: Outcome Reference, Work/Review Boundary, Code State Token, Evidence Record, Claim Record, and conversation-first Checkpoint.
- Task-scoped Git review across committed, staged, unstaged, untracked, explicitly declared ignored artifacts, and participating worktrees.
- A pure-standard-library, read-only Git state helper with deterministic content fingerprints and no semantic relevance classification.
- One optional, ignored Local Capsule for cross-session continuity, compactly rewritten instead of accumulating phase documents.
- Content-addressed complete bundles with a single atomic `current` activation pointer, retained rollback bundles, guarded legacy migration, and Codex discovery links.
- Python 3.10 and 3.14 validation CI, contract tests, Git/worktree fixtures, failure-injected deployment tests, and clean temporary installation checks.

### Known limitations

- Git is the only implemented VCS provider. Jujutsu integration is deferred.
- Linux is the verified deployment target; Windows and macOS are not yet verified release claims.
- Codex is the target agent surface. Other agents may interpret frontmatter and symlink discovery differently.
- Submodules, unborn `HEAD`, multi-repository tasks, network filesystems, and sudden-power-loss durability are not supported release claims.
- Boundary digests are reproducibility fingerprints, not security attestations.
- No orchestrator, automatic handrail selection, persistent evidence service, telemetry, or automatic bundle garbage collection is included.
- Real Codex installation, five-scenario dogfood, an external-project loop, and GitHub release publication remain gates before the stable tag.
