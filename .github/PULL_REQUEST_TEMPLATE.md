## Outcome

<!-- What user/project result changes? Link the Issue/ADR. -->

## Scope and design

<!-- Summarize the chosen approach, non-goals, and any generated projections. -->

## Evidence

<!-- Paste concise local gate results and relevant dogfood evidence; do not attach raw private transcripts. -->

- [ ] Tests cover the behavior and important failure paths.
- [ ] `python scripts/render_contract.py --check` passes.
- [ ] `python scripts/render_plugin.py --check` passes.
- [ ] `python scripts/quality.py` passes.
- [ ] Official Agent Skills validation passes for all seven Skills.

## Safety and compatibility

- [ ] No v1 immutable file or historical tag was changed.
- [ ] No unauthorized/destructive state mutation is introduced.
- [ ] Plugin and Raw Skills remain coherent, or the PR explains why not applicable.
- [ ] Documentation, changelog, migration, and rollback guidance are updated.
- [ ] No secrets, caches, `.scratch/` content, or unrelated local changes are included.

## Review limits

<!-- State unverified platforms, environments, claims, or follow-up Issues. -->
