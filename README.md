# Agent Handrails

**Manual-first, automation-ready engineering handrails for AI coding agents.**

> Don't put your coding agent on rails. Give it handrails.

Not vibe coding. Not workflow capture. Agent Handrails is a small set of explicit, composable engineering primitives that you can invoke by hand today and orchestrate through a coding engineering harness tomorrow.

**Core thesis:** autonomy should be earned, not assumed.

## Why

AI coding agents benefit from professional engineering discipline, but a useful discipline does not need to become a mandatory ceremony for every task.

Agent Handrails takes a different path:

- use the smallest professional path that protects quality;
- keep each handrail useful on its own;
- formalize specs only when durable outcome alignment helps;
- test and verify the real behavior or claim, not a ritual proxy;
- preserve human visibility, override, and rollback;
- automate only after the primitives and their selection logic have earned trust.

## The handrails

| Handrail | Purpose |
|---|---|
| [`grill`](skills/grill/SKILL.md) | Clarify consequential uncertainty without forcing a design ceremony. |
| [`spec-lite`](skills/spec-lite/SKILL.md) | Create a compact outcome contract only when conversation context is insufficient. |
| [`plan-lite`](skills/plan-lite/SKILL.md) | Turn an exact Outcome Reference into a strategy and execution map. |
| [`feedback-loop`](skills/feedback-loop/SKILL.md) | Use tests, repros, smoke checks, and runtime evidence to stay aligned with real behavior. |
| [`two-axis-review`](skills/two-axis-review/SKILL.md) | Review outcome fit and engineering quality separately, with evidence reported explicitly. |
| [`verify-before-claim`](skills/verify-before-claim/SKILL.md) | Keep completion claims no broader than fresh evidence. |
| [`branch-sandbox`](skills/branch-sandbox/SKILL.md) | Isolate risky or parallel work with explicit boundaries and rollback paths. |

These are a toolbox, not a mandatory chain.

All seven handrails share the versioned `usable-loop/v1` handoff contract. A stable Task ID and exact Outcome Reference preserve outcome identity, authority, currentness, and invalidation across optional transitions, while every skill remains a valid direct entry point. See [domain context](CONTEXT.md) and the [contract semantics](docs/contracts/usable-loop-v1.md).

## Manual-first does not mean manual-only

Each skill currently carries cross-platform frontmatter:

```yaml
disable-model-invocation: true
```

For Codex, each skill also carries:

```yaml
policy:
  allow_implicit_invocation: false
```

These disable ambient model matching on platforms that support the respective metadata: a platform should not silently inject a skill merely because it might be relevant. They do **not** forbid explicit automation.

A user, playbook, or coding engineering harness may explicitly select a handrail. The selection should remain inspectable:

- Why this handrail?
- Why now?
- What evidence or decision should it produce?
- What was intentionally skipped?
- When should control return to the human?

See [Philosophy](docs/philosophy.md) and [Harness Roadmap](docs/harness-roadmap.md).

## Progressive autonomy

Agent Handrails is designed to support a progression rather than a binary manual/automatic choice:

1. **Direct mode** — a person invokes one handrail.
2. **Suggested mode** — an agent recommends the next useful handrail and waits.
3. **Orchestrated mode** — a harness explicitly selects handrails and records why.
4. **Autonomous mode** — a capable agent executes within bounded workspaces and returns an evidence bundle.

The repository currently focuses on the validated primitives. It does not yet claim to provide a production-ready autonomous harness.

## Example compositions

```text
Small, clear change
  implement -> verify-before-claim

Ambiguous feature
  grill -> optional spec-lite -> plan-lite -> feedback-loop
  -> two-axis-review -> verify-before-claim

Large or parallel refactor
  branch-sandbox -> plan-lite -> feedback-loop
  -> two-axis-review -> verify-before-claim
```

These are examples, not required workflows. Direct implementation plus verification is valid when the task is already clear and bounded.

More examples live in [`playbooks/`](playbooks/README.md).

## Project source and managed deployment

Keep the Git repository in an engineering workspace and treat `skills/` and any shared `runtime/` support as canonical source. The deployment root exposes stable skill entrypoints backed by complete, content-addressed bundles:

```text
~/Workspace/Projects/agent-handrails/
  skills/                                  # develop and review here
  runtime/                                 # optional shared runtime support
                  ↓ explicit sync
~/Workspace/Skills/
  .agent-handrails/
    bundles/<content-id>/                  # retained complete bundles
    current -> bundles/<content-id>        # single activation pointer
  <skill> -> .agent-handrails/current/skills/<skill>
                  ↑ Codex follows stable discovery symlinks
~/.agents/skills/<skill> -> ~/Workspace/Skills/<skill>
```

Check the managed deployment without writing:

```bash
python3 scripts/sync_skills.py --check \
  --codex-link-root ~/.agents/skills
```

Install, migrate, or update all seven managed handrails:

```bash
python3 scripts/sync_skills.py --apply \
  --codex-link-root ~/.agents/skills
```

The default deployment root is `~/Workspace/Skills`. Override it with `--target PATH` or `AGENT_HANDRAILS_SKILLS_DIR`; an explicit `--target` takes precedence. `--codex-link-root` is optional. When supplied, missing discovery symlinks are created, correct existing links are preserved, and conflicting paths cause the apply to stop without replacing them. Unrelated skills and discovery entries are never managed.

The first bundle-aware check of a complete legacy seven-directory installation reports `bundle/layout: migration-required` and exits with status `1`, even when every deployed skill matches the source. Running `--apply` preserves the legacy content as a retained bundle, replaces the seven public entries with stable symlinks, and leaves correct Codex discovery links unchanged. Partial, mixed, or conflicting legacy layouts are refused before mutation.

Managed upgrades stage and verify the entire bundle before atomically replacing the single `current` pointer, so all seven skills change together. First installation and legacy migration modify multiple paths and are not atomic as a whole; caught failures are rolled back. A later apply recovers an intact migration journal when path ownership can be proven; ambiguous crash state is left untouched and reported instead of being guessed away. The deployer does not fsync every file and directory involved and therefore makes no persistence guarantee for sudden power loss.

`--check` exits `0` when the requested deployment and discovery links are current, `1` for a recognized but non-current state such as a missing deployment, required migration, source drift, link drift, or pending recovery, and `2` when the source or managed layout cannot be safely interpreted. `--apply` exits `0` after successful verification and `2` when preflight refuses the layout or deployment fails. Human-readable status lines may evolve; scripts should use the exit status.

Verified bundles are retained by default; this release performs no automatic pruning. To roll back, use a known-good revision that already contains the bundle-aware deployer, then run `--apply` and `--check` again. Do not use a pre-migration version of `sync_skills.py` against a managed bundle layout or edit the `current` link manually.

Managed entrypoints and bundle contents are deployment artifacts, not a second development source. Edit the project files, review and commit them, then sync again. The v0.1 deployment helper supports Linux with Python 3.10 or newer. Each handrail includes `agents/openai.yaml` with `policy.allow_implicit_invocation: false`, so Codex can expose it for explicit invocation without ambient matching. Other agents may interpret metadata or symlink discovery differently.

## Validate the repository

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
```

## Project status

Early and intentionally small. The current goal is to validate each handrail through real engineering work before adding an orchestrator that automates their composition.

## License

MIT. See [`LICENSE`](LICENSE).
