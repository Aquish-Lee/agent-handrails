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
| [`plan-lite`](skills/plan-lite/SKILL.md) | Turn an outcome source into a strategy and execution map. |
| [`feedback-loop`](skills/feedback-loop/SKILL.md) | Use tests, repros, smoke checks, and runtime evidence to stay aligned with real behavior. |
| [`two-axis-review`](skills/two-axis-review/SKILL.md) | Review outcome fit and engineering quality separately, with evidence reported explicitly. |
| [`verify-before-claim`](skills/verify-before-claim/SKILL.md) | Keep completion claims no broader than fresh evidence. |
| [`branch-sandbox`](skills/branch-sandbox/SKILL.md) | Isolate risky or parallel work with explicit boundaries and rollback paths. |

These are a toolbox, not a mandatory chain.

## Manual-first does not mean manual-only

Each skill currently carries:

```yaml
disable-model-invocation: true
```

That disables ambient model matching: a platform should not silently inject a skill merely because it might be relevant. It does **not** forbid automation.

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

## Use from a source checkout

Keep this repository as the source of truth, then register or link only the handrails you want in your agent environment.

A generic symlink example:

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/verify-before-claim" ~/.agents/skills/verify-before-claim
```

Agent-specific installation instructions will be added as the project is validated across Codex, Claude Code, Cursor, Copilot, Gemini CLI, and other `SKILL.md`-compatible environments. Do not assume every platform interprets frontmatter identically.

## Validate the repository

```bash
python3 scripts/validate.py
```

## Project status

Early and intentionally small. The current goal is to validate each handrail through real engineering work before adding an orchestrator that automates their composition.

## License

MIT. See [`LICENSE`](LICENSE).
