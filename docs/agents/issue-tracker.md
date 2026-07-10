# Issue tracker: local scratch and GitHub

This repository uses two complementary places to track work:

- `.scratch/` holds temporary, local development items, drafts, and short-lived implementation notes.
- GitHub Issues holds durable, project-level work such as features, bugs, proposals, and backlog items.

Do not promote every scratch item to GitHub. Promote an item when it should remain visible, discussable, or actionable beyond the current local development session.
The `.scratch/` directory is gitignored and must remain local to this checkout.

## Local scratch conventions

- One feature or investigation per directory: `.scratch/<feature-slug>/`.
- A local PRD is `.scratch/<feature-slug>/PRD.md`.
- Local implementation items are `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`.
- Triage state is recorded as a `Status:` line near the top of an item.
- Append discussion history under a `## Comments` heading when history is useful.

When a user explicitly asks for a local, temporary, draft, or scratch item, write it under `.scratch/`.

## GitHub Issues conventions

Use GitHub Issues for project-level records after the repository has a GitHub remote. Use the `gh` CLI for operations:

- Create: `gh issue create --title "..." --body "..."`.
- Read: `gh issue view <number> --comments`.
- List: `gh issue list --state open` with appropriate JSON fields, labels, and state filters.
- Comment: `gh issue comment <number> --body "..."`.
- Apply or remove labels: `gh issue edit <number> --add-label "..."` or `--remove-label "..."`.
- Close: `gh issue close <number> --comment "..."`.

Infer the GitHub repository from the configured Git remote. If no GitHub remote exists yet, do not attempt a GitHub write; keep the proposed issue content ready and report the missing remote.

When a user asks to publish, create an issue, add to the backlog, or record project-level work, use GitHub Issues.

## Resolving ambiguity

- Prefer `.scratch/` for work that is disposable or useful only during current implementation.
- Prefer GitHub Issues for work that should survive, be prioritized, or be discussed by collaborators.
- If the requested destination materially changes visibility or permanence and intent is unclear, confirm with the user.
