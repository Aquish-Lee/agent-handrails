from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSPECTOR = PROJECT_ROOT / "runtime" / "safe_diff.py"


def run(*command: str, cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout


class SafeDiffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary_directory.name)
        run("git", "init", "-q", cwd=self.repository)
        run("git", "config", "user.name", "Agent Handrails Test", cwd=self.repository)
        run("git", "config", "user.email", "handrails@example.invalid", cwd=self.repository)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def commit(self, path: str, content: str) -> str:
        destination = self.repository / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        run("git", "add", path, cwd=self.repository)
        run("git", "commit", "-qm", f"add {path}", cwd=self.repository)
        return run("git", "rev-parse", "HEAD", cwd=self.repository).strip()

    def inspect(self, base: str, path: str, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(INSPECTOR),
                "--repository",
                str(self.repository),
                "--base",
                base,
                "--path",
                path,
                *extra,
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_sensitive_environment_diff_never_emits_old_or_new_values(self) -> None:
        old_value = "synthetic-old-credential-value-123"
        new_value = "replace-with-your-service-access-key"
        base = self.commit(".env.example", f'SERVICE_ACCESS_KEY="{old_value}"\n')
        (self.repository / ".env.example").write_text(
            f'SERVICE_ACCESS_KEY="{new_value}"\n', encoding="utf-8"
        )

        completed = self.inspect(base, ".env.example")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        transcript = completed.stdout + completed.stderr
        self.assertNotIn(old_value, transcript)
        self.assertNotIn(new_value, transcript)
        self.assertIn("inspection: redacted", completed.stdout)
        self.assertIn("SERVICE_ACCESS_KEY", completed.stdout)
        self.assertIn("removed=configured-value", completed.stdout)
        self.assertIn("added=placeholder", completed.stdout)

    def test_credential_shaped_source_assignment_forces_redaction(self) -> None:
        old_value = "synthetic-token-before-12345"
        new_value = "sk-synthetic-token-after-67890"
        base = self.commit("settings.py", f'API_TOKEN = "{old_value}"\n')
        (self.repository / "settings.py").write_text(
            f'API_TOKEN = "{new_value}"\n', encoding="utf-8"
        )

        completed = self.inspect(base, "settings.py")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        transcript = completed.stdout + completed.stderr
        self.assertNotIn(old_value, transcript)
        self.assertNotIn(new_value, transcript)
        self.assertIn("inspection: redacted", completed.stdout)
        self.assertIn("reason: sensitive-assignment", completed.stdout)

    def test_non_sensitive_source_diff_remains_raw_and_useful(self) -> None:
        base = self.commit("calculator.py", "def add(left, right):\n    return left + right\n")
        (self.repository / "calculator.py").write_text(
            "def add(left, right):\n    return int(left) + int(right)\n", encoding="utf-8"
        )

        completed = self.inspect(base, "calculator.py")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("inspection: raw", completed.stdout)
        self.assertIn("return int(left) + int(right)", completed.stdout)

    def test_large_raw_diff_requires_bounded_hunk_selection(self) -> None:
        base = self.commit("large.py", "".join(f"VALUE_{index} = 0\n" for index in range(300)))
        (self.repository / "large.py").write_text(
            "".join(f"VALUE_{index} = 1\n" for index in range(300)), encoding="utf-8"
        )

        completed = self.inspect(base, "large.py")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("inspection: requires-hunk-selection", completed.stdout)
        self.assertNotIn("VALUE_299 = 1", completed.stdout)

        selected = self.inspect(base, "large.py", "--hunk", "1")
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertIn("inspection: hunk-too-large", selected.stdout)
        self.assertIn("chunks:", selected.stdout)

        chunk = self.inspect(base, "large.py", "--hunk", "1", "--chunk", "1")
        self.assertEqual(chunk.returncode, 0, chunk.stderr)
        self.assertIn("inspection: raw", chunk.stdout)
        self.assertNotIn("VALUE_299 = 1", chunk.stdout)

    def test_parent_symlink_escape_fails_without_reading_target_content(self) -> None:
        base = self.commit("tracked.py", "VALUE = 1\n")
        outside = self.repository.parent / f"{self.repository.name}-outside"
        outside.mkdir()
        self.addCleanup(shutil.rmtree, outside)
        protected_value = "synthetic-outside-value-that-must-not-appear"
        (outside / "value.txt").write_text(protected_value, encoding="utf-8")
        os.symlink(outside, self.repository / "escape")

        completed = self.inspect(base, "escape/value.txt")

        self.assertEqual(completed.returncode, 2)
        self.assertNotIn(protected_value, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
