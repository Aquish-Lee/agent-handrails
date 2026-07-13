from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = PROJECT_ROOT / "plugins" / "agent-handrails"


class CodexPluginTests(unittest.TestCase):
    def test_manifest_and_marketplace_are_versioned_and_coherent(self) -> None:
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        marketplace = json.loads(
            (PROJECT_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )
        entry = marketplace["plugins"][0]
        self.assertEqual(manifest["name"], "agent-handrails")
        self.assertEqual(manifest["version"], "0.1.0-alpha.2")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(marketplace["name"], "agent-handrails")
        self.assertEqual(entry["name"], manifest["name"])
        self.assertEqual(entry["source"]["path"], "./plugins/agent-handrails")

    def test_plugin_package_matches_raw_skills_without_dev_tree(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/render_plugin.py", "--check"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            {path.name for path in (PLUGIN_ROOT / "skills").iterdir() if path.is_dir()},
            {
                "branch-sandbox",
                "feedback-loop",
                "grill",
                "plan-lite",
                "spec-lite",
                "two-axis-review",
                "verify-before-claim",
            },
        )
        self.assertFalse((PLUGIN_ROOT / "tests").exists())
        self.assertFalse((PLUGIN_ROOT / "runtime").exists())


if __name__ == "__main__":
    unittest.main()
