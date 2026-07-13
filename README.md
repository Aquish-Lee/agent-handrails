# Agent Handrails

**Manual-first, automation-ready engineering handrails for AI coding agents.**

> Don't put your coding agent on rails. Give it handrails.

[![Release](https://img.shields.io/github/v/release/Aquish-Lee/agent-handrails?include_prereleases)](https://github.com/Aquish-Lee/agent-handrails/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status: community-ready alpha](https://img.shields.io/badge/status-community--ready%20alpha-orange)](#project-status)

Agent Handrails is seven explicit, independently useful engineering primitives.
It preserves professional discipline without forcing every task through a
brainstorm/spec/plan/test/review pipeline.

## Why

- Use the smallest safe path for the task and requested claim.
- Keep human selection, override, authorization, and rollback visible.
- Review the real current state, including dirty and multi-worktree changes.
- Separate development observations from evidence that supports a claim.
- Persist only when continuity is at risk; avoid accumulating phase documents.
- Automate composition only after the atomic skills earn trust through dogfood.

The active `usable-loop/v2` contract scales verification by claim width:

| Claim | Required path |
| --- | --- |
| `fact` | Direct fresh observation; no Boundary or Review Record |
| `scoped-task` | Deterministic Claim Boundary over all current candidates plus fresh checks |
| `high-assurance` | Exact current two-axis Review Record plus supporting claim evidence |

Any relevant outcome, boundary, code-state, or environment change stales the
evidence. v2 reruns the narrowest check instead of carrying evidence across a
change.

## The seven handrails

| Handrail | Atomic result |
| --- | --- |
| [`grill`](skills/grill/SKILL.md) | Resolve consequential uncertainty into an Alignment Snapshot |
| [`spec-lite`](skills/spec-lite/SKILL.md) | Capture converged intent as a lightweight Outcome Contract |
| [`plan-lite`](skills/plan-lite/SKILL.md) | Produce an implementation strategy and Review Boundary Seed |
| [`feedback-loop`](skills/feedback-loop/SKILL.md) | Produce development evidence for the next engineering move |
| [`two-axis-review`](skills/two-axis-review/SKILL.md) | Produce a deterministic Review Boundary and formal Review Record |
| [`verify-before-claim`](skills/verify-before-claim/SKILL.md) | Produce proportionate claim evidence and a Claim Record |
| [`branch-sandbox`](skills/branch-sandbox/SKILL.md) | Establish a reversible workspace/authorization boundary |

These are a toolbox, not a mandatory chain. Each Skill disables implicit Codex
invocation and may only suggest—not silently invoke—another handrail.

## Install as a Codex Plugin (recommended)

Install the immutable prerelease through this repository's marketplace:

```bash
codex plugin marketplace add Aquish-Lee/agent-handrails --ref v0.1.0-alpha.2
codex plugin add agent-handrails@agent-handrails
codex plugin list --json
```

Start a new Codex session after installation. Plugin Skills use the plugin
namespace:

```text
$agent-handrails:plan-lite Create a compact implementation plan for this request.
$agent-handrails:two-axis-review Review the actual current dirty task state.
$agent-handrails:verify-before-claim Verify only that this JSON file parses.
```

The alpha.2 package has been validated against Codex's real marketplace/add
flow; its cache contains only `.codex-plugin/plugin.json` and the seven Skills.

To move to a newer immutable tag, remove the installed plugin and pinned
marketplace, then add the new ref:

```bash
codex plugin remove agent-handrails@agent-handrails
codex plugin marketplace remove agent-handrails
codex plugin marketplace add Aquish-Lee/agent-handrails --ref <new-tag>
codex plugin add agent-handrails@agent-handrails
```

## Install standard Raw Skills

Raw Skills remain Agent Skills-compatible for manual installation and other
implementations:

```bash
git clone --branch v0.1.0-alpha.2 --depth 1 \
  https://github.com/Aquish-Lee/agent-handrails.git
cd agent-handrails

uvx --from skills-ref==0.1.1 agentskills validate skills/branch-sandbox
# Repeat validation for each directory under skills/.

python3 scripts/render_contract.py --check
python3 scripts/render_plugin.py --check
python3 scripts/sync_skills.py --apply --codex-link-root ~/.agents/skills
python3 scripts/sync_skills.py --check --codex-link-root ~/.agents/skills
```

New installations default to
`${XDG_DATA_HOME:-~/.local/share}/agent-handrails/skills`. An existing managed
`~/Workspace/Skills/.agent-handrails` layout stays there automatically. Override
the target with `--target PATH` or `AGENT_HANDRAILS_SKILLS_DIR`.

Managed updates stage and verify a complete content-addressed bundle, then
atomically switch one `current` pointer. Previous bundles remain available for
rollback. Unrelated skills/discovery entries are never managed.

### Safe uninstall and purge

The ownership manifest records every public/discovery link the project may
remove. A replaced or malformed path makes uninstall fail before any deletion.

```bash
# Remove only manifest-owned links; retain bundles for rollback.
python3 scripts/sync_skills.py --uninstall

# Explicitly delete verified retained bundles and managed metadata too.
python3 scripts/sync_skills.py --uninstall --purge
```

Re-running `--apply` after a normal uninstall restores the retained bundle and
links. `--purge` never removes unrelated content from the target directory.

### Roll back to alpha.1 and forward again

Alpha.1 is an immutable Raw-Skills-only historical baseline. Use detached
worktrees so the active checkout is untouched:

```bash
git worktree add --detach /tmp/agent-handrails-alpha1 v0.1.0-alpha.1
python3 /tmp/agent-handrails-alpha1/scripts/sync_skills.py \
  --apply --codex-link-root ~/.agents/skills

git worktree add --detach /tmp/agent-handrails-alpha2 v0.1.0-alpha.2
python3 /tmp/agent-handrails-alpha2/scripts/sync_skills.py \
  --apply --codex-link-root ~/.agents/skills
```

Remove the detached worktrees only after checking that their worktree state
contains no results you need.

## Deterministic boundaries

Skills that need exact Git state carry a standalone copy of
`handrails_state.py`. The interface is:

```text
inventory
confirm --kind claim|review --classifications <file|->
capture --boundary <confirmed-boundary.json>
```

The runtime assigns Candidate/Hunk IDs from mechanical fingerprints. Semantic
classifications reference only those IDs and include rationale plus
`authorized | needs-authorization | not-applicable`. It computes the canonical
SHA-256 digest itself and recaptures state. Missing units, overlaps, unmerged
conflicts, unauthorized included changes, drift, or tampering fail closed.

## Develop and validate

Requirements: Linux, Git, Python 3.10+, and `uv`.

```bash
uv sync --group dev
uv run python scripts/quality.py
```

The local gate runs tests, contract/plugin drift checks, official Agent Skills
validation, Ruff, Bandit, and packaging checks. Hosted GitHub Actions are
manual/advisory while billing is unavailable; they do not replace local or real
Codex acceptance.

See [CONTRIBUTING.md](CONTRIBUTING.md), [the v2 contract](docs/contracts/usable-loop-v2.md),
[domain context](CONTEXT.md), and [the practical playbook](playbooks/practical-development-loop.md).

## Compatibility

- Supported baseline: Linux, Git, Python 3.10+, Codex.
- Primary distribution: Codex Plugin; compatibility distribution: Raw Skills.
- Not yet verified release claims: Windows, macOS, Jujutsu, submodules, unborn
  `HEAD`, non-Codex agents, and network-filesystem/power-loss durability.
- No automatic orchestrator, persistent evidence service, telemetry, or bundle
  garbage collector is included.

## Project status

`v0.1.0-alpha.2` is a **community-ready alpha**: the repository, governance,
distribution, and local acceptance paths are independently maintainable, while
long-term product behavior is still being validated through real development
dogfood. It is not a stable `v0.1.0` release.

Use [Discussions](https://github.com/Aquish-Lee/agent-handrails/discussions) for
support, [Issues](https://github.com/Aquish-Lee/agent-handrails/issues) for
defects/proposals, and the private process in [SECURITY.md](SECURITY.md) for
vulnerabilities. Governance and maintainers are documented in
[GOVERNANCE.md](GOVERNANCE.md) and [MAINTAINERS.md](MAINTAINERS.md).

## License and provenance

Agent Handrails is MIT licensed. See [LICENSE](LICENSE),
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), and
[ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md).
