# Contributing to Agent Handrails

Thanks for helping improve Agent Handrails. The project is an alpha: changes
should preserve the seven handrails as explicit, independently useful tools and
must not introduce a hidden mandatory workflow.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md). Questions and usage
help belong in GitHub Discussions; confirmed bugs and design proposals belong in
Issues.

## Development setup

Requirements: Linux, Git, Python 3.10+, and `uv` for the locked development
environment. Codex is needed only for plugin/direct-invocation acceptance.

```bash
git clone git@github.com:Aquish-Lee/agent-handrails.git
cd agent-handrails
uv sync --group dev
```

`uv.lock` is the dependency lock. Do not update it incidentally. PyYAML, Ruff,
and Bandit support Python 3.10; the official `skills-ref` validator requires
Python 3.11+ and is invoked through a pinned `uvx` environment.

## Source of truth and generated files

- `contracts/usable-loop-v2.json` is the active machine contract.
- `skills/` contains canonical standard Raw Skills.
- `runtime/handrails_state.py` is the canonical v2 boundary runtime.
- `runtime/safe_diff.py` is the canonical sensitive-review preflight runtime.
- skill-local v2 references/runtime copies are generated.
- `plugins/agent-handrails/skills/` is the generated minimal Codex plugin payload.
- v1 contract/runtime files are immutable history.

After changing v2 contract, runtime, or canonical skills:

```bash
uv run python scripts/render_contract.py --apply
uv run python scripts/render_plugin.py --apply
```

Never edit generated projections as an independent source.

## Validation

Run the complete local gate:

```bash
uv run python scripts/quality.py
```

The gate runs unit/integration tests, repository validation, projection/plugin
drift checks, eval-schema validation, Ruff, Bandit, and the pinned official
Agent Skills validator. Hosted GitHub Actions are advisory/manual while project
billing is unavailable; local output is required release evidence.

For a narrow iteration, run the relevant unit module first, then the full gate
before opening a PR.

## Contract and design changes

Changes to record ownership, authority, evidence lifecycle, claim routing,
boundary canonicalization, distribution safety, or the seven-skill product
surface need a Design Proposal Issue and, when accepted, an ADR in `docs/adr/`.
Preserve `usable-loop/v1` exactly; new behavior belongs in a new v2 revision or a
future contract version.

Dogfood transcripts stay in `.scratch/dogfood-v2/`. Promote durable defects to
Issues; do not commit raw model/session logs.

## Commits and pull requests

- Keep commits focused and explain behavior, not file activity.
- Add or update tests for behavior and failure paths.
- Regenerate projections in the same commit as their source change.
- Do not include unrelated local work, secrets, caches, or `.scratch/` content.
- Open a draft PR while evidence is incomplete; mark ready only after the local
  gate passes and the PR template is complete.
- Link the Issue/ADR for durable project-level work.

Maintainers may ask for dogfood evidence when a change affects agent behavior,
claim safety, output cost, installation, or rollback.
