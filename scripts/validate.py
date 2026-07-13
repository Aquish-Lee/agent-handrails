#!/usr/bin/env python3
"""Validate Agent Handrails repository structure and skill metadata."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED_SKILLS = {
    "branch-sandbox",
    "feedback-loop",
    "grill",
    "plan-lite",
    "spec-lite",
    "two-axis-review",
    "verify-before-claim",
}
REQUIRED_FILES = {
    ".github/workflows/validate.yml",
    "CHANGELOG.md",
    "README.md",
    "LICENSE",
    "docs/philosophy.md",
    "docs/workflow.md",
    "docs/harness-roadmap.md",
    "playbooks/README.md",
    "playbooks/practical-development-loop.md",
    "runtime/git_state.py",
    "scripts/sync_skills.py",
    "CONTEXT.md",
    "contracts/usable-loop-v1.json",
    "docs/adr/0001-versioned-usable-loop-contract.md",
    "docs/contracts/usable-loop-v1.md",
}
STALE_TERMS = (
    "Aquish",
    "aquish-",
    "Manual-only",
    "ABSOLUTELY MUST",
    "1% chance means invoke",
)
CONTRACT_ID = "usable-loop/v1"
CONTRACT_PATH = Path("contracts/usable-loop-v1.json")
CONTRACT_BLOCK_PATTERN = re.compile(
    r"<!-- handrails-contract\n(?P<body>.*?)\n-->",
    flags=re.DOTALL,
)
CONTRACT_BLOCK_FIELDS = {
    "contract",
    "role",
    "missing-outcome-reference",
    "authority-failure",
    "authority-failure-triggers",
    "outcome-record",
    "required-local-resources",
    "bootstrap-authority",
    "bootstrap-lifecycle",
    "bootstrap-currentness",
    "outcome-reference-output",
    "identity-revision-separation",
    "revision-digest-claim",
}
EXPECTED_CONTRACT_ROLES = {
    "branch-sandbox": "workspace-isolator",
    "feedback-loop": "evidence-builder",
    "grill": "outcome-aligner",
    "plan-lite": "execution-planner",
    "spec-lite": "outcome-contract-author",
    "two-axis-review": "boundary-reviewer",
    "verify-before-claim": "claim-gate",
}
OUTCOME_REFERENCE_LABELS = (
    "Contract: usable-loop/v1",
    "Task ID:",
    "Outcome Source kind:",
    "Outcome Source ID:",
    "Outcome Source locator:",
    "Outcome Revision:",
    "Revision basis:",
    "Outcome Authority:",
    "Authority basis:",
    "Outcome lifecycle:",
    "Outcome snapshot:",
    "Outcome currentness:",
    "Stale when:",
)
EXPECTED_SOURCE_KINDS = {
    "request",
    "conversation",
    "alignment-snapshot",
    "issue",
    "prd",
    "spec",
    "bug-repro",
    "deployment-objective",
    "other",
}
EXPECTED_AUTHORITY_FAILURE_TRIGGERS = {
    "authority-inaccessible",
    "authority-conflict",
    "authority-revision-mismatch",
}
EXPECTED_OUTCOME_REFERENCE_FIELDS = {
    "contract",
    "task_id",
    "source_kind",
    "source_id",
    "source_locator",
    "outcome_revision",
    "revision_basis",
    "authority",
    "authority_basis",
    "lifecycle",
    "snapshot",
    "currentness",
    "stale_when",
}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    detail: str


def issue(code: str, path: Path | str, detail: str) -> ValidationIssue:
    return ValidationIssue(code, Path(path).as_posix(), detail)


def contract_block(text: str) -> tuple[dict[str, str] | None, int]:
    matches = list(CONTRACT_BLOCK_PATTERN.finditer(text))
    if len(matches) != 1:
        return None, len(matches)
    values: dict[str, str] = {}
    for line in matches[0].group("body").splitlines():
        key, separator, value = line.partition(":")
        if not separator or not key.strip() or key.strip() in values:
            return None, 1
        values[key.strip()] = value.strip()
    return values, 1


def required_local_resources(value: str) -> tuple[str, ...]:
    if value == "none":
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def standalone_skill_errors(skill_dir: Path) -> list[ValidationIssue]:
    errors: list[ValidationIssue] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return [issue("missing-skill-file", skill_file, "SKILL.md is required")]
    try:
        text = skill_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [issue("unreadable-skill-file", skill_file, str(exc))]
    binding, count = contract_block(text)
    if binding is None:
        code = "missing-contract-marker" if count == 0 else "invalid-contract-marker"
        errors.append(
            issue(code, skill_file, "exactly one parseable handrails-contract block is required")
        )
        return errors

    if "role" not in binding or not binding["role"]:
        errors.append(issue("missing-contract-role", skill_file, "role is required"))
    if set(binding) != CONTRACT_BLOCK_FIELDS:
        errors.append(
            issue(
                "invalid-contract-fields",
                skill_file,
                f"expected fields {sorted(CONTRACT_BLOCK_FIELDS)}, got {sorted(binding)}",
            )
        )

    for label in OUTCOME_REFERENCE_LABELS:
        if label not in text:
            errors.append(
                issue(
                    "missing-outcome-reference-field",
                    skill_file,
                    f"missing self-contained field label: {label}",
                )
            )

    source_kind_line = re.search(r"(?m)^Outcome Source kind:\s*(.+)$", text)
    if source_kind_line is None or {
        value.strip() for value in source_kind_line.group(1).split("|")
    } != EXPECTED_SOURCE_KINDS:
        errors.append(
            issue(
                "invalid-source-kind-projection",
                skill_file,
                "Outcome Source kind must project the complete v1 enum",
            )
        )

    expected_binding_values = {
        "bootstrap-authority": "provisional",
        "bootstrap-lifecycle": "active",
        "bootstrap-currentness": "fresh",
        "outcome-reference-output": "complete",
        "identity-revision-separation": "required",
        "revision-digest-claim": "computed-only",
    }
    for key, expected in expected_binding_values.items():
        if binding.get(key) != expected:
            errors.append(
                issue(
                    "invalid-contract-policy",
                    skill_file,
                    f"{key} must be {expected}",
                )
            )
    local_triggers = {
        item.strip()
        for item in binding.get("authority-failure-triggers", "").split(",")
        if item.strip()
    }
    if local_triggers != EXPECTED_AUTHORITY_FAILURE_TRIGGERS:
        errors.append(
            issue(
                "invalid-contract-policy",
                skill_file,
                "authority-failure-triggers differ from usable-loop/v1",
            )
        )

    resource_value = binding.get("required-local-resources", "")
    for relative in required_local_resources(resource_value):
        resource = Path(relative)
        resolved = (skill_dir / resource).resolve(strict=False)
        skill_root = skill_dir.resolve(strict=False)
        if resource.is_absolute() or not resolved.is_relative_to(skill_root):
            errors.append(
                issue(
                    "external-required-resource",
                    skill_file,
                    f"required resource escapes the skill directory: {relative}",
                )
            )
            continue
        if not resolved.is_file():
            errors.append(
                issue(
                    "missing-required-resource",
                    skill_file,
                    f"required local resource does not exist: {relative}",
                )
            )
    return errors


def load_contract(root: Path) -> tuple[dict[str, object] | None, list[ValidationIssue]]:
    path = root / CONTRACT_PATH
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [issue("invalid-contract-json", path, str(exc))]
    if not isinstance(value, dict):
        return None, [issue("invalid-contract-shape", path, "top level must be an object")]
    return value, []


def contract_errors(root: Path = ROOT) -> list[ValidationIssue]:
    contract, errors = load_contract(root)
    if contract is None:
        return errors
    path = root / CONTRACT_PATH
    expected_top_level = {
        "contract",
        "schema_version",
        "status",
        "managed_skills",
        "enums",
        "policies",
        "records",
        "skills",
        "composition_paths",
    }
    if set(contract) != expected_top_level:
        errors.append(
            issue(
                "invalid-contract-top-level",
                path,
                f"expected {sorted(expected_top_level)}, got {sorted(contract)}",
            )
        )
    if contract.get("contract") != CONTRACT_ID:
        errors.append(issue("contract-id-mismatch", path, f"expected {CONTRACT_ID}"))
    if contract.get("schema_version") != 1:
        errors.append(issue("contract-version-mismatch", path, "expected schema version 1"))
    if contract.get("status") != "active":
        errors.append(issue("invalid-contract-status", path, "v1 status must be active"))

    enums = contract.get("enums")
    records = contract.get("records")
    skills = contract.get("skills")
    policies = contract.get("policies")
    if not isinstance(enums, dict):
        errors.append(issue("invalid-contract-enums", path, "enums must be an object"))
        enums = {}
    if not isinstance(records, dict):
        errors.append(issue("invalid-contract-records", path, "records must be an object"))
        records = {}
    if not isinstance(skills, dict):
        errors.append(issue("invalid-contract-skills", path, "skills must be an object"))
        skills = {}
    if not isinstance(policies, dict):
        errors.append(issue("invalid-contract-policies", path, "policies must be an object"))
        policies = {}

    for enum_name, values in enums.items():
        if (
            not isinstance(enum_name, str)
            or not isinstance(values, list)
            or not values
            or not all(isinstance(value, str) and value for value in values)
            or len(values) != len(set(values))
        ):
            errors.append(
                issue("invalid-contract-enum", path, f"invalid enum {enum_name!r}")
            )
    usable_enums = {
        enum_name: values
        for enum_name, values in enums.items()
        if isinstance(enum_name, str)
        and isinstance(values, list)
        and values
        and all(isinstance(value, str) and value for value in values)
        and len(values) == len(set(values))
    }

    managed = contract.get("managed_skills")
    if (
        not isinstance(managed, list)
        or not all(isinstance(name, str) for name in managed)
        or set(managed) != EXPECTED_SKILLS
    ):
        errors.append(
            issue("managed-skill-set-mismatch", path, "managed_skills must match repository skills")
        )
    if set(skills) != EXPECTED_SKILLS:
        errors.append(
            issue("contract-skill-set-mismatch", path, "skill declarations must match repository skills")
        )
    role_values = usable_enums.get("skill_role")
    if (
        not isinstance(role_values, list)
        or not all(isinstance(role, str) for role in role_values)
        or set(role_values) != set(EXPECTED_CONTRACT_ROLES.values())
    ):
        errors.append(issue("invalid-contract-enum", path, "skill_role"))
    if set(usable_enums.get("source_kind", [])) != EXPECTED_SOURCE_KINDS:
        errors.append(issue("invalid-contract-enum", path, "source_kind"))

    for record_name, declaration in records.items():
        if not isinstance(declaration, dict):
            errors.append(issue("invalid-contract-record", path, str(record_name)))
            continue
        required = declaration.get("required_fields")
        optional = declaration.get("optional_fields")
        availability = declaration.get("availability")
        raw_producers = declaration.get("producers")
        producers = (
            raw_producers
            if isinstance(raw_producers, list)
            and all(
                isinstance(producer, str) and producer in EXPECTED_SKILLS
                for producer in raw_producers
            )
            else []
        )
        if availability not in usable_enums.get("record_availability", []):
            errors.append(
                issue("invalid-contract-enum", path, f"{record_name}.availability")
            )
        if not isinstance(required, list) or not all(
            isinstance(field, str) and field for field in required
        ) or len(required) != len(set(required)):
            errors.append(issue("invalid-contract-record", path, f"{record_name}.required_fields"))
        if not isinstance(optional, list) or not all(
            isinstance(field, str) and field for field in optional
        ) or len(optional) != len(set(optional)):
            errors.append(issue("invalid-contract-record", path, f"{record_name}.optional_fields"))
        markdown_labels = declaration.get("markdown_labels")
        if availability == "active":
            if (
                not isinstance(markdown_labels, dict)
                or not isinstance(required, list)
                or set(markdown_labels) != set(required)
                or not all(
                    isinstance(label, str) and label
                    for label in markdown_labels.values()
                )
            ):
                errors.append(
                    issue(
                        "contract-record-fields-mismatch",
                        path,
                        f"{record_name} lacks labels for its active required fields",
                    )
                )
            else:
                for producer in producers:
                    producer_file = root / "skills" / producer / "SKILL.md"
                    try:
                        producer_text = producer_file.read_text(encoding="utf-8")
                    except (OSError, UnicodeError):
                        continue
                    for field, label in markdown_labels.items():
                        if label not in producer_text:
                            errors.append(
                                issue(
                                    "missing-contract-output-field",
                                    producer_file,
                                    f"{record_name}.{field} requires label {label}",
                                )
                            )
        if (
            record_name == "outcome-reference"
            and isinstance(required, list)
            and set(required) != EXPECTED_OUTCOME_REFERENCE_FIELDS
        ):
            errors.append(
                issue(
                    "contract-record-fields-mismatch",
                    path,
                    "outcome-reference required fields differ from the skill projection",
                )
            )
        for owner_key in ("producers", "primary_producers"):
            owners = declaration.get(owner_key, [])
            if not isinstance(owners, list) or not all(
                isinstance(owner, str) and owner in EXPECTED_SKILLS for owner in owners
            ):
                errors.append(
                    issue("unknown-contract-skill-reference", path, f"{record_name}.{owner_key}")
                )
        field_enums = declaration.get("field_enums", {})
        if not isinstance(field_enums, dict) or not all(
            isinstance(enum_name, str) and enum_name in usable_enums
            for enum_name in field_enums.values()
        ):
            errors.append(issue("invalid-contract-enum", path, f"{record_name}.field_enums"))

    for policy_name, declaration in policies.items():
        if not isinstance(declaration, dict):
            errors.append(issue("invalid-contract-policy", path, str(policy_name)))
            continue
        enum_name = declaration.get("enum")
        default = declaration.get("default")
        if not isinstance(enum_name, str) or enum_name not in usable_enums:
            errors.append(issue("invalid-contract-enum", path, f"policy {policy_name}"))
        elif default not in usable_enums[enum_name]:
            errors.append(issue("invalid-contract-enum", path, f"policy {policy_name} default"))
        produced = declaration.get("produces")
        if produced is not None and produced not in records:
            errors.append(issue("unknown-contract-record", path, f"policy {policy_name}"))
    authority_failure = policies.get("authority-failure")
    if isinstance(authority_failure, dict):
        triggers = authority_failure.get("triggers")
        if (
            not isinstance(triggers, list)
            or not all(isinstance(trigger, str) for trigger in triggers)
            or set(triggers) != EXPECTED_AUTHORITY_FAILURE_TRIGGERS
        ):
            errors.append(issue("invalid-contract-policy", path, "authority-failure.triggers"))
        effects = authority_failure.get("effects")
        if not isinstance(effects, dict):
            errors.append(issue("invalid-contract-policy", path, "authority-failure.effects"))
        else:
            if effects.get("outcome_authority") not in usable_enums.get(
                "outcome_authority",
                [],
            ):
                errors.append(issue("invalid-contract-enum", path, "outcome_authority"))
            if effects.get("outcome_currentness") not in usable_enums.get(
                "outcome_freshness",
                [],
            ):
                errors.append(issue("invalid-contract-enum", path, "outcome_currentness"))

    for skill_name, declaration in skills.items():
        if not isinstance(declaration, dict):
            errors.append(issue("invalid-contract-skill", path, str(skill_name)))
            continue
        for record_key, expected_availability in (
            ("consumes", "active"),
            ("produces", "active"),
            ("planned_consumes", None),
            ("planned_produces", "planned"),
        ):
            references = declaration.get(record_key)
            if not isinstance(references, list) or not all(
                isinstance(reference, str) and reference in records
                for reference in references
            ):
                errors.append(
                    issue("unknown-contract-record", path, f"{skill_name}.{record_key}")
                )
                continue
            for reference in references:
                record_declaration = records.get(reference)
                if (
                    expected_availability is not None
                    and isinstance(record_declaration, dict)
                    and record_declaration.get("availability") != expected_availability
                ):
                    errors.append(
                        issue(
                            "contract-record-availability-mismatch",
                            path,
                            f"{skill_name}.{record_key} references {reference}",
                        )
                    )
                if "produces" in record_key and isinstance(record_declaration, dict):
                    record_producers = record_declaration.get("producers")
                    if not isinstance(record_producers, list):
                        record_producers = []
                    if skill_name not in record_producers:
                        errors.append(
                            issue(
                                "contract-producer-mismatch",
                                path,
                                f"{skill_name}.{record_key} overclaims {reference}",
                            )
                        )
        expected_role = EXPECTED_CONTRACT_ROLES.get(skill_name)
        if declaration.get("role") != expected_role:
            errors.append(
                issue("contract-role-mismatch", path, f"{skill_name}.role")
            )
        missing_policy = declaration.get("missing_outcome_reference")
        authority_policy = declaration.get("authority_failure")
        if missing_policy not in usable_enums.get("missing_outcome_reference", []):
            errors.append(issue("invalid-contract-enum", path, f"{skill_name}.missing_outcome_reference"))
        if authority_policy not in usable_enums.get("authority_failure", []):
            errors.append(issue("invalid-contract-enum", path, f"{skill_name}.authority_failure"))

        skill_dir = root / "skills" / skill_name
        errors.extend(standalone_skill_errors(skill_dir))
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        local, _ = contract_block(skill_file.read_text(encoding="utf-8"))
        if local is None:
            continue
        if local.get("contract") != CONTRACT_ID:
            errors.append(issue("contract-id-mismatch", skill_file, CONTRACT_ID))
        if not local.get("role"):
            errors.append(issue("missing-contract-role", skill_file, "role is required"))
        elif local.get("role") != declaration.get("role"):
            errors.append(issue("contract-role-mismatch", skill_file, "role differs from catalog"))
        if local.get("missing-outcome-reference") not in usable_enums.get(
            "missing_outcome_reference",
            [],
        ):
            errors.append(issue("invalid-contract-enum", skill_file, "missing-outcome-reference"))
        if local.get("authority-failure") not in usable_enums.get("authority_failure", []):
            errors.append(issue("invalid-contract-enum", skill_file, "authority-failure"))
        if local.get("outcome-record") not in records:
            errors.append(issue("unknown-contract-record", skill_file, "outcome-record"))

    for record_name, declaration in records.items():
        if not isinstance(declaration, dict):
            continue
        raw_producers = declaration.get("producers")
        producers = (
            raw_producers
            if isinstance(raw_producers, list)
            and all(
                isinstance(producer, str) and producer in EXPECTED_SKILLS
                for producer in raw_producers
            )
            else []
        )
        for producer in producers:
            skill_declaration = skills.get(producer)
            producer_key = (
                "produces"
                if declaration.get("availability") == "active"
                else "planned_produces"
            )
            skill_records = (
                skill_declaration.get(producer_key)
                if isinstance(skill_declaration, dict)
                else None
            )
            if not isinstance(skill_records, list):
                skill_records = []
            if isinstance(skill_declaration, dict) and record_name not in skill_records:
                errors.append(
                    issue(
                        "contract-producer-mismatch",
                        path,
                        f"{producer} does not declare {producer_key} record {record_name}",
                    )
                )

    composition_paths = contract.get("composition_paths")
    if not isinstance(composition_paths, dict):
        errors.append(
            issue("invalid-composition-path", path, "composition_paths must be an object")
        )
    else:
        for path_name, declaration in composition_paths.items():
            if not isinstance(declaration, dict):
                errors.append(issue("invalid-composition-path", path, str(path_name)))
                continue
            if declaration.get("producer") not in EXPECTED_SKILLS:
                errors.append(issue("unknown-contract-skill-reference", path, str(path_name)))
            if declaration.get("consumer") not in EXPECTED_SKILLS:
                errors.append(issue("unknown-contract-skill-reference", path, str(path_name)))
            if declaration.get("record") not in records:
                errors.append(issue("unknown-contract-record", path, str(path_name)))
    return errors


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"')
    return result


def markdown_files(root: Path = ROOT) -> Iterator[Path]:
    for path in root.rglob("*.md"):
        if ".scratch" in path.relative_to(root).parts:
            continue
        yield path


def main() -> int:
    errors: list[str] = []

    actual_skills = {p.name for p in SKILLS.iterdir() if p.is_dir()}
    if actual_skills != EXPECTED_SKILLS:
        errors.append(
            f"skill directories differ: missing={sorted(EXPECTED_SKILLS - actual_skills)}, "
            f"unexpected={sorted(actual_skills - EXPECTED_SKILLS)}"
        )

    for relative in sorted(REQUIRED_FILES):
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    for contract_issue in contract_errors(ROOT):
        errors.append(
            f"{contract_issue.path}: [{contract_issue.code}] {contract_issue.detail}"
        )

    checked = 0
    for skill_name in sorted(EXPECTED_SKILLS):
        path = SKILLS / skill_name / "SKILL.md"
        if not path.is_file():
            errors.append(f"missing skill file: {path.relative_to(ROOT)}")
            continue

        checked += 1
        text = path.read_text(encoding="utf-8")
        meta = frontmatter(text)
        if not meta:
            errors.append(f"{path.relative_to(ROOT)}: invalid or missing frontmatter")
            continue

        # Use a real YAML parser when available. The validator remains stdlib-only,
        # but this catches edge cases such as an unquoted ": " inside a scalar.
        try:
            import yaml  # type: ignore[import-not-found]
        except ImportError:
            pass
        else:
            raw_frontmatter = text.split("---", 2)[1]
            try:
                parsed = yaml.safe_load(raw_frontmatter)
            except yaml.YAMLError as exc:
                errors.append(f"{path.relative_to(ROOT)}: invalid YAML frontmatter: {exc}")
            else:
                if not isinstance(parsed, dict):
                    errors.append(f"{path.relative_to(ROOT)}: YAML frontmatter is not a mapping")

        if meta.get("name") != skill_name:
            errors.append(
                f"{path.relative_to(ROOT)}: name={meta.get('name')!r}, expected {skill_name!r}"
            )
        if meta.get("disable-model-invocation") != "true":
            errors.append(
                f"{path.relative_to(ROOT)}: disable-model-invocation must be true"
            )
        if "explicit orchestrator/harness decision" not in text:
            errors.append(
                f"{path.relative_to(ROOT)}: explicit invocation contract missing"
            )

        openai_metadata = SKILLS / skill_name / "agents" / "openai.yaml"
        if not openai_metadata.is_file():
            errors.append(
                f"{openai_metadata.relative_to(ROOT)}: missing Codex metadata"
            )
        else:
            metadata_text = openai_metadata.read_text(encoding="utf-8")
            if not re.search(
                r"(?m)^\s*allow_implicit_invocation:\s*false\s*$",
                metadata_text,
            ):
                errors.append(
                    f"{openai_metadata.relative_to(ROOT)}: "
                    "allow_implicit_invocation must be false"
                )
        for term in STALE_TERMS:
            if term in text:
                errors.append(f"{path.relative_to(ROOT)}: stale/forbidden term {term!r}")

    checked_markdown = list(markdown_files())
    for path in checked_markdown:
        text = path.read_text(encoding="utf-8")
        for term in ("Aquish", "aquish-"):
            if term in text:
                errors.append(f"{path.relative_to(ROOT)}: stale private term {term!r}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for phrase in (
        "Manual-first, automation-ready",
        "autonomy should be earned, not assumed",
        "toolbox, not a mandatory chain",
    ):
        if phrase not in readme:
            errors.append(f"README.md: missing positioning phrase {phrase!r}")

    if errors:
        print("Agent Handrails validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Agent Handrails validation PASSED")
    print(f"- skills checked: {checked}")
    print(f"- markdown files checked for stale naming: {len(checked_markdown)}")
    print("- invocation model: ambient matching disabled; explicit harness selection allowed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
