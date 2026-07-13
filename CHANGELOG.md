# Changelog

All notable changes to Agent Handrails are recorded here.

## [0.1.0-alpha.2] - 2026-07-13

### Added

- `usable-loop/v2` with `fact`, `scoped-task`, and `high-assurance` claim routes.
- Deterministic `inventory → confirm → capture` Boundary runtime with stable
  Candidate/Hunk IDs, canonical SHA-256, authorization checks, conflict/drift
  blocking, and no caller-supplied digest.
- Separate Development Evidence, Claim Evidence, formal Review Record, and
  shared optional Checkpoint ownership.
- Generated self-contained v2 contract/runtime projections for standalone Skills.
- Tracked dogfood scenarios/rubric with ignored local result storage.
- Codex marketplace/plugin package and standard Raw Skills distribution.
- XDG default Raw installation, legacy managed-layout retention, ownership-
  proven uninstall, explicit purge, and reinstall from retained bundles.
- Governance, support, security, conduct, contribution, Issue/PR templates,
  dependency locking, Ruff/Bandit, Dependabot, and pinned advisory Actions.

### Changed

- All seven Skills now use standard Agent Skills frontmatter and provide complete
  Codex interface metadata with implicit invocation disabled.
- A current user request defaults to authoritative when scope/permission/source
  do not conflict; agent-derived interpretation remains provisional.
- Direct results are compact by default; full Checkpoints appear only for a
  continuity trigger or explicit request.
- Hosted CI is manual/advisory and does not block alpha publication.

### Removed

- Hidden review dependency for narrow verification.
- Feedback-to-verify evidence ownership ambiguity and verify-to-feedback backflow.
- Evidence reuse after a boundary/state/environment change in v2.
- Non-standard `disable-model-invocation` and `argument-hint` Skill frontmatter.

### Known limitations

- Linux, Git, Python 3.10+, and Codex are the supported baseline.
- Jujutsu, Windows, macOS, other agents, submodules, and unborn `HEAD` remain unverified.
- Real-project dogfood continues after publication; this is not stable `v0.1.0`.

## [0.1.0-alpha.1] - 2026-07-13

Historical pre-merge preview and rollback baseline for `usable-loop/v1`.
Superseded by alpha.2 for normal installation; its tag and v1 semantics remain
immutable.

[0.1.0-alpha.2]: https://github.com/Aquish-Lee/agent-handrails/compare/v0.1.0-alpha.1...v0.1.0-alpha.2
[0.1.0-alpha.1]: https://github.com/Aquish-Lee/agent-handrails/releases/tag/v0.1.0-alpha.1
