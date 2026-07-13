#!/usr/bin/env python3
"""Validate Agent Handrails structure, v2 contract, and generated projections."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
CONTRACT_PATH = Path("contracts/usable-loop-v2.json")
CONTRACT_ID = "usable-loop/v2"
SKILL_NAMES = {
    "branch-sandbox",
    "feedback-loop",
    "grill",
    "plan-lite",
    "spec-lite",
    "two-axis-review",
    "verify-before-claim",
}
RUNTIME_SKILLS = {
    "branch-sandbox",
    "feedback-loop",
    "two-axis-review",
    "verify-before-claim",
}
REQUIRED_FILES = {
    ".agents/plugins/marketplace.json",
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/design.yml",
    ".github/ISSUE_TEMPLATE/feature.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/dependabot.yml",
    ".github/workflows/validate.yml",
    "AGENTS.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CONTEXT.md",
    "GOVERNANCE.md",
    "LICENSE",
    "MAINTAINERS.md",
    "README.md",
    "SECURITY.md",
    "SUPPORT.md",
    "THIRD_PARTY_NOTICES.md",
    "contracts/usable-loop-v1.json",
    "contracts/usable-loop-v2.json",
    "docs/adr/0001-versioned-usable-loop-contract.md",
    "docs/adr/0002-deterministic-claim-scaled-usable-loop-v2.md",
    "docs/contracts/usable-loop-v1.md",
    "docs/contracts/usable-loop-v2.md",
    "docs/philosophy.md",
    "docs/workflow.md",
    "evals/usable-loop-v2/rubric.md",
    "evals/usable-loop-v2/scenarios.json",
    "playbooks/practical-development-loop.md",
    "plugins/agent-handrails/.codex-plugin/plugin.json",
    "pyproject.toml",
    "requirements-dev.txt",
    "runtime/git_state.py",
    "runtime/handrails_state.py",
    "scripts/eval_v2.py",
    "scripts/quality.py",
    "scripts/render_contract.py",
    "scripts/render_plugin.py",
    "scripts/sync_skills.py",
    "uv.lock",
}
V1_IMMUTABLE_HASHES = {
    "contracts/usable-loop-v1.json": "6a2455a83ba7a83bdc5b369cf1154d0462a2c8b5a2f8dc3b8edd3754545a5db8",
    "docs/contracts/usable-loop-v1.md": "3fb5cd6aa8aad84b36cef015a450aeb33e37da0ca836ffd53f1055d29db31753",
    "docs/adr/0001-versioned-usable-loop-contract.md": "bf10f3734293966fa377afc030d121a5f9b58aece65a0693a8a38ddaf88c31d4",
    "runtime/git_state.py": "1471ac833acdecc233d0110a312e8197677662a60baaebca83a4542a9154ba55",
}
STALE_TERMS = (
    "ABSOLUTELY MUST",
    "1% chance means invoke",
    "Manual-only",
)
CONTRACT_BLOCK_PATTERN = re.compile(r"<!-- handrails-contract\n(?P<body>.*?)\n-->", re.DOTALL)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    detail: str


def issue(code: str, path: Path | str, detail: str) -> ValidationIssue:
    return ValidationIssue(code, Path(path).as_posix(), detail)


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in root.rglob("*.md")
            if ".git" not in path.parts and ".scratch" not in path.parts
        ),
        key=lambda path: path.as_posix(),
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("top level must be an object")
    return value


def _frontmatter(text: str) -> dict[str, object]:
    match = re.match(r"\A---\n(?P<body>.*?)\n---\n", text, re.DOTALL)
    if match is None:
        raise ValueError("missing YAML frontmatter")
    value = yaml.safe_load(match.group("body"))
    if not isinstance(value, dict):
        raise ValueError("frontmatter must be an object")
    return value


def _contract_block(text: str) -> dict[str, str]:
    matches = list(CONTRACT_BLOCK_PATTERN.finditer(text))
    if len(matches) != 1:
        raise ValueError("exactly one handrails-contract block is required")
    result: dict[str, str] = {}
    for line in matches[0].group("body").splitlines():
        key, separator, value = line.partition(":")
        key = key.strip()
        if not separator or not key or key in result:
            raise ValueError("invalid handrails-contract line")
        result[key] = value.strip()
    return result


def _inside(root: Path, relative: str) -> Path | None:
    candidate = Path(relative)
    if candidate.is_absolute():
        return None
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve(strict=False)
    return resolved if resolved.is_relative_to(resolved_root) else None


def contract_errors(root: Path = ROOT) -> list[ValidationIssue]:
    errors: list[ValidationIssue] = []
    path = root / CONTRACT_PATH
    try:
        contract = _load_json(path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        return [issue("invalid-contract", path, str(error))]
    if contract.get("contract") != CONTRACT_ID:
        errors.append(issue("contract-id", path, f"expected {CONTRACT_ID}"))
    if contract.get("schema_version") != 2 or contract.get("status") != "active":
        errors.append(issue("contract-state", path, "v2 must be schema 2 and active"))
    if set(contract.get("managed_skills", [])) != SKILL_NAMES:
        errors.append(issue("managed-skills", path, "managed skill set differs"))

    enums = contract.get("enums", {})
    expected_enums = {
        "claim_kind": {"fact", "scoped-task", "high-assurance"},
        "development_evidence_status": {"observed", "stale", "blocked"},
        "claim_evidence_status": {"fresh", "stale", "blocked"},
        "authorization_state": {
            "authorized",
            "needs-authorization",
            "not-applicable",
        },
    }
    for name, expected in expected_enums.items():
        if set(enums.get(name, [])) != expected:
            errors.append(issue("contract-enum", path, f"invalid {name}"))

    policies = contract.get("policies", {})
    authority = policies.get("authority-bootstrap", {})
    if authority.get("current_user_request") != (
        "authoritative-unless-permission-or-source-conflict"
    ):
        errors.append(issue("authority-policy", path, "user request default drifted"))
    lifecycle = policies.get("evidence-lifecycle", {})
    if lifecycle.get("proof-of-unrelated-change_reuse") != "unsupported-in-v2":
        errors.append(issue("evidence-policy", path, "v2 evidence reuse must be disabled"))
    boundary = policies.get("boundary-runtime", {})
    if boundary.get("caller_supplied_digest") != "forbidden":
        errors.append(issue("boundary-policy", path, "naked digest must be forbidden"))

    records = contract.get("records", {})
    skills = contract.get("skills", {})
    if not isinstance(records, dict) or not isinstance(skills, dict):
        return errors + [issue("contract-shape", path, "records/skills must be objects")]
    checkpoint = records.get("checkpoint", {})
    if set(checkpoint.get("producers", [])) != SKILL_NAMES:
        errors.append(issue("checkpoint-ownership", path, "checkpoint must be shared"))

    for skill_name in SKILL_NAMES:
        declaration = skills.get(skill_name)
        if not isinstance(declaration, dict):
            errors.append(issue("missing-skill-contract", path, skill_name))
            continue
        produced = set(declaration.get("produces", []))
        optional = set(declaration.get("optional_produces", []))
        if optional != {"checkpoint"}:
            errors.append(issue("checkpoint-projection", path, skill_name))
        if bool(declaration.get("runtime_required")) != (skill_name in RUNTIME_SKILLS):
            errors.append(issue("runtime-ownership", path, skill_name))
        for record_name in produced | optional:
            record = records.get(record_name, {})
            if skill_name not in record.get("producers", []):
                errors.append(
                    issue(
                        "record-producer-drift",
                        path,
                        f"{skill_name} -> {record_name}",
                    )
                )
    return errors


def skill_errors(root: Path = ROOT) -> list[ValidationIssue]:
    errors: list[ValidationIssue] = []
    contract = _load_json(root / CONTRACT_PATH)
    actual = {path.name for path in (root / "skills").iterdir() if path.is_dir()}
    if actual != SKILL_NAMES:
        errors.append(issue("skill-set", root / "skills", "unexpected skill directories"))
    runtime_bytes = (root / "runtime" / "handrails_state.py").read_bytes()
    for name in sorted(SKILL_NAMES):
        skill_root = root / "skills" / name
        skill_path = skill_root / "SKILL.md"
        try:
            text = skill_path.read_text(encoding="utf-8")
            frontmatter = _frontmatter(text)
            binding = _contract_block(text)
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
            errors.append(issue("invalid-skill", skill_path, str(error)))
            continue
        if set(frontmatter) != {"name", "description"}:
            errors.append(
                issue("frontmatter-fields", skill_path, "only name and description allowed")
            )
        if frontmatter.get("name") != name:
            errors.append(issue("skill-name", skill_path, f"expected {name}"))
        description = frontmatter.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(issue("skill-description", skill_path, "description required"))
        expected_binding = {
            "contract": CONTRACT_ID,
            "role": contract["skills"][name]["role"],
            "reference": "references/usable-loop-v2.md",
            "runtime": ("scripts/handrails_state.py" if name in RUNTIME_SKILLS else "none"),
        }
        if binding != expected_binding:
            errors.append(issue("contract-binding", skill_path, str(binding)))
        reference = _inside(skill_root, binding.get("reference", ""))
        if reference is None or not reference.is_file():
            errors.append(issue("local-reference", skill_path, "missing local v2 reference"))
        if name in RUNTIME_SKILLS:
            runtime = _inside(skill_root, binding.get("runtime", ""))
            if runtime is None or not runtime.is_file():
                errors.append(issue("local-runtime", skill_path, "missing local runtime"))
            elif runtime.read_bytes() != runtime_bytes:
                errors.append(issue("local-runtime-drift", runtime, "runtime copy differs"))
        metadata_path = skill_root / "agents" / "openai.yaml"
        try:
            metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
            interface = metadata["interface"]
            policy = metadata["policy"]
        except (OSError, UnicodeError, yaml.YAMLError, KeyError, TypeError) as error:
            errors.append(issue("invalid-openai-metadata", metadata_path, str(error)))
            continue
        short = interface.get("short_description", "")
        prompt = interface.get("default_prompt", "")
        if not 25 <= len(short) <= 64:
            errors.append(issue("short-description", metadata_path, "must be 25-64 chars"))
        if f"${name}" not in prompt:
            errors.append(issue("default-prompt", metadata_path, f"must mention ${name}"))
        if policy.get("allow_implicit_invocation") is not False:
            errors.append(issue("implicit-invocation", metadata_path, "must be false"))
    return errors


def generated_projection_errors(root: Path = ROOT) -> list[ValidationIssue]:
    script = root / "scripts" / "render_contract.py"
    spec = importlib.util.spec_from_file_location("render_contract_validator", script)
    if spec is None or spec.loader is None:
        return [issue("projection-loader", script, "cannot load generator")]
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    contract = module.load_contract()
    errors = [
        issue("generated-projection-drift", path, "run render_contract.py --apply")
        for path in module.check(module.generated_files(contract))
    ]
    plugin_script = root / "scripts" / "render_plugin.py"
    plugin_spec = importlib.util.spec_from_file_location("render_plugin_validator", plugin_script)
    if plugin_spec is None or plugin_spec.loader is None:
        return errors + [issue("plugin-loader", plugin_script, "cannot load generator")]
    plugin_module = importlib.util.module_from_spec(plugin_spec)
    plugin_spec.loader.exec_module(plugin_module)
    for detail in plugin_module.drift():
        errors.append(
            issue(
                "generated-plugin-drift",
                root / "plugins" / "agent-handrails",
                detail,
            )
        )
    return errors


def repository_errors(root: Path = ROOT) -> list[ValidationIssue]:
    errors: list[ValidationIssue] = []
    for relative in sorted(REQUIRED_FILES):
        if not (root / relative).is_file():
            errors.append(issue("missing-file", root / relative, "required file"))
    for relative, expected in V1_IMMUTABLE_HASHES.items():
        path = root / relative
        if path.is_file() and _sha256(path) != expected:
            errors.append(issue("v1-mutated", path, "v1 history must remain immutable"))
    for path in markdown_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(issue("invalid-markdown", path, str(error)))
            continue
        for term in STALE_TERMS:
            if term in text:
                errors.append(issue("stale-term", path, term))
    return errors


def validate(root: Path = ROOT) -> list[ValidationIssue]:
    return (
        repository_errors(root)
        + contract_errors(root)
        + skill_errors(root)
        + generated_projection_errors(root)
    )


def main() -> int:
    errors = validate(ROOT)
    if errors:
        print("Agent Handrails validation FAILED", file=sys.stderr)
        for error in errors:
            print(
                f"- [{error.code}] {error.path}: {error.detail}",
                file=sys.stderr,
            )
        return 1
    print("Agent Handrails validation PASSED")
    print(f"- skills checked: {len(SKILL_NAMES)}")
    print("- active contract: usable-loop/v2")
    print("- usable-loop/v1 immutable baseline: verified")
    print("- generated skill-local projections: current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
