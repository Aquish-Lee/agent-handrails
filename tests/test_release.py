from __future__ import annotations

import unittest
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ReleasePackagingTests(unittest.TestCase):
    def test_ci_uses_current_official_actions_and_supported_python_matrix(self) -> None:
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "validate.yml"
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        job = workflow["jobs"]["validate"]
        self.assertEqual(job["strategy"]["matrix"]["python-version"], ["3.10", "3.14"])
        uses = [step.get("uses") for step in job["steps"] if "uses" in step]
        self.assertIn("actions/checkout@v7", uses)
        self.assertIn("actions/setup-python@v6", uses)

    def test_ci_runs_full_repository_and_bundle_acceptance(self) -> None:
        text = (
            PROJECT_ROOT / ".github" / "workflows" / "validate.yml"
        ).read_text(encoding="utf-8")
        for required in (
            "pip install PyYAML",
            "python -m unittest discover -s tests -v",
            "python scripts/validate.py",
            "python scripts/sync_skills.py --apply",
            "python scripts/sync_skills.py --check",
            "python runtime/git_state.py --help",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_readme_documents_explicit_codex_invocation_and_release_limits(self) -> None:
        text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("`$plan-lite`", text)
        self.assertIn("`/skills`", text)
        self.assertIn("Python 3.10+", text)
        self.assertIn("python3 -m pip install PyYAML==6.0.3", text)
        self.assertIn("Linux", text)
        self.assertIn("not yet verified", text)
        self.assertIn("3eee4ac41bd6d295ef3253a40109fd0dd72654f7", text)
        self.assertIn("git worktree add --detach", text)

    def test_changelog_records_v010_capabilities_and_limits(self) -> None:
        text = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## [0.1.0] - Unreleased", text)
        self.assertIn("usable-loop/v1", text)
        self.assertIn("Code State Token", text)
        self.assertIn("Local Capsule", text)
        self.assertIn("Jujutsu", text)
        self.assertIn("Windows", text)


if __name__ == "__main__":
    unittest.main()
