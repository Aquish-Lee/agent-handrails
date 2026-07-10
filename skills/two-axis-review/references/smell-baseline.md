# Smell Baseline for Engineering Quality Review

Use these as heuristics, not hard rules. Repo-specific conventions override this baseline. Skip issues already enforced by tooling unless the tooling result is missing from the review evidence.

## Naming and clarity

- **Mysterious Name**: a function, variable, type, file, or concept whose name does not reveal what it does or holds. Rename it; if no honest name exists, the design may be unclear.
- **Inconsistent Domain Language**: code uses synonyms or generic names where the project has established domain terms. Align names with the repo's domain language.

## Duplication and abstraction

- **Duplicated Code**: repeated logic shape across hunks/files. Extract only when the shared concept is real, not speculative.
- **Speculative Generality**: abstractions, parameters, hooks, config, or framework layers added for needs not required now. Remove or defer.
- **Middle Man**: a wrapper that mostly delegates without owning policy, validation, or simplification. Inline or give it real responsibility.

## Module boundaries

- **Shotgun Surgery**: one logical change requires scattered edits across many files. Consider moving related responsibilities together.
- **Divergent Change**: one module is edited for unrelated reasons. Split responsibilities or isolate the change.
- **Shallow Module**: interface is broad while implementation adds little value. Prefer deep modules: simple interface, meaningful behavior behind it.
- **Feature Envy**: code reaches deeply into another module's data/logic. Move behavior closer to the data or expose a better seam.
- **Message Chains**: callers navigate long object/service chains. Hide traversal behind a clearer interface.

## Data and contracts

- **Primitive Obsession**: strings/numbers/dicts stand in for meaningful domain concepts. Introduce small types only when they clarify real behavior.
- **Data Clumps**: the same fields travel together repeatedly. Consider bundling into a named concept.
- **Unclear Contract**: API/data/service boundary lacks validation, error semantics, or version assumptions.

## Testing and verification

- **Implementation-Coupled Test**: test breaks on refactor even when behavior is unchanged.
- **Over-Mocked Test**: mocks the system under test or verifies mocks instead of behavior.
- **Weak Evidence**: tests pass but do not encode acceptance criteria or important runtime behavior.
- **Flaky Verification**: relies on retries, sleeps, timing luck, or partial logs without deterministic signal.

## Operations and safety

- **Missing Observability**: change can fail without logs, metrics, status, or readback needed to diagnose it.
- **Missing Rollback**: deployment/data/config change lacks a credible rollback path.
- **Unsafe Default**: default behavior widens permissions, writes production data, skips checks, or hides failure.
