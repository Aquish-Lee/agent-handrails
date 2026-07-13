from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0-alpha.2"


class ReleasePackagingTests(unittest.TestCase):
    def test_advisory_workflow_is_manual_and_actions_are_sha_pinned(self) -> None:
        path = PROJECT_ROOT / ".github" / "workflows" / "validate.yml"
        text = path.read_text(encoding="utf-8")
        workflow = yaml.safe_load(text)
        job = workflow["jobs"]["validate"]
        self.assertEqual(job["strategy"]["matrix"]["python-version"], ["3.10", "3.14"])
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("\n  push:", text)
        uses = re.findall(r"uses:\s*([^\s#]+)", text)
        self.assertEqual(
            uses,
            [
                "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0",
                "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
            ],
        )

    def test_workflow_exercises_quality_and_raw_install_lifecycle(self) -> None:
        text = (PROJECT_ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        for required in (
            "python scripts/quality.py --skip-official-skills",
            "agentskills validate",
            "scripts/sync_skills.py --apply",
            "scripts/sync_skills.py --check",
            "scripts/sync_skills.py --uninstall --target",
            "scripts/sync_skills.py --uninstall --purge",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_plugin_marketplace_and_manifest_point_to_same_alpha(self) -> None:
        manifest = json.loads(
            (
                PROJECT_ROOT / "plugins" / "agent-handrails" / ".codex-plugin" / "plugin.json"
            ).read_text(encoding="utf-8")
        )
        marketplace = json.loads(
            (PROJECT_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["version"], VERSION)
        self.assertEqual(manifest["name"], "agent-handrails")
        self.assertEqual(marketplace["name"], "agent-handrails")
        self.assertEqual(
            marketplace["plugins"][0]["source"]["path"],
            "./plugins/agent-handrails",
        )

    def test_readme_documents_complete_plugin_and_raw_paths(self) -> None:
        text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        for required in (
            "codex plugin marketplace add Aquish-Lee/agent-handrails --ref v0.1.0-alpha.2",
            "codex plugin add agent-handrails@agent-handrails",
            "$agent-handrails:verify-before-claim",
            "git clone --branch v0.1.0-alpha.2",
            "scripts/sync_skills.py --uninstall",
            "scripts/sync_skills.py --uninstall --purge",
            "${XDG_DATA_HOME:-~/.local/share}/agent-handrails/skills",
            "v0.1.0-alpha.1",
            "community-ready alpha",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_community_health_files_and_templates_exist(self) -> None:
        required = (
            "CODE_OF_CONDUCT.md",
            "CONTRIBUTING.md",
            "GOVERNANCE.md",
            "MAINTAINERS.md",
            "SECURITY.md",
            "SUPPORT.md",
            "THIRD_PARTY_NOTICES.md",
            ".github/ISSUE_TEMPLATE/bug.yml",
            ".github/ISSUE_TEMPLATE/feature.yml",
            ".github/ISSUE_TEMPLATE/design.yml",
            ".github/PULL_REQUEST_TEMPLATE.md",
            ".github/dependabot.yml",
        )
        for relative in required:
            with self.subTest(path=relative):
                self.assertTrue((PROJECT_ROOT / relative).is_file())
        for name in ("bug.yml", "feature.yml", "design.yml"):
            form = yaml.safe_load(
                (PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE" / name).read_text(encoding="utf-8")
            )
            self.assertIn("needs-triage", form["labels"])

    def test_dependency_and_quality_configuration_is_locked(self) -> None:
        pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        requirements = (PROJECT_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        lock = (PROJECT_ROOT / "uv.lock").read_text(encoding="utf-8")
        for dependency in ("bandit==1.9.4", "PyYAML==6.0.3", "ruff==0.15.21"):
            self.assertIn(dependency.lower(), requirements.lower())
        self.assertIn("[tool.ruff]", pyproject)
        self.assertIn("[tool.bandit]", pyproject)
        self.assertIn('name = "agent-handrails"', lock)

    def test_changelog_marks_alpha1_superseded_and_alpha2_current(self) -> None:
        text = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## [0.1.0-alpha.2] - 2026-07-13", text)
        self.assertIn("## [0.1.0-alpha.1] - 2026-07-13", text)
        self.assertIn("Superseded by alpha.2", text)
        self.assertNotIn("## [0.1.0]", text)


if __name__ == "__main__":
    unittest.main()
