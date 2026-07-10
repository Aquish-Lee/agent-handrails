# Domain documentation

This repository uses a single-context domain documentation layout.

## Before exploring

- Read `CONTEXT.md` at the repository root when it exists.
- Read relevant architectural decision records under `docs/adr/` when that directory exists.
- If either source does not exist, proceed without treating its absence as a blocker.

## Use the domain glossary

When naming concepts in issues, plans, tests, refactors, or documentation, use the vocabulary defined in `CONTEXT.md`. Avoid introducing synonyms for terms the glossary defines.

If a needed concept is missing, first check whether existing project language already covers it. Otherwise, record the vocabulary gap for later clarification.

## Respect architectural decisions

Surface any conflict with an existing ADR explicitly instead of silently overriding the recorded decision.

The expected layout is:

```text
/
├── CONTEXT.md
├── docs/
│   └── adr/
└── skills/
```
