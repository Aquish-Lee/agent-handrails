#!/usr/bin/env python3
"""Validate Agent Handrails repository structure and skill metadata."""

from __future__ import annotations

import re
import sys
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
    "README.md",
    "LICENSE",
    "docs/philosophy.md",
    "docs/workflow.md",
    "docs/harness-roadmap.md",
    "playbooks/README.md",
}
STALE_TERMS = (
    "Aquish",
    "aquish-",
    "Manual-only",
    "ABSOLUTELY MUST",
    "1% chance means invoke",
)


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
        for term in STALE_TERMS:
            if term in text:
                errors.append(f"{path.relative_to(ROOT)}: stale/forbidden term {term!r}")

    for path in ROOT.rglob("*.md"):
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

    markdown_count = sum(1 for _ in ROOT.rglob("*.md"))
    print("Agent Handrails validation PASSED")
    print(f"- skills checked: {checked}")
    print(f"- markdown files checked for stale naming: {markdown_count}")
    print("- invocation model: ambient matching disabled; explicit harness selection allowed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
