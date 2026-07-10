from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "validate.py"
SPEC = importlib.util.spec_from_file_location("validate", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate
SPEC.loader.exec_module(validate)


class MarkdownFilesTests(unittest.TestCase):
    def test_scratch_markdown_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "docs").mkdir()
            (root / ".scratch" / "task").mkdir(parents=True)
            (root / "README.md").write_text("project\n", encoding="utf-8")
            (root / "docs" / "guide.md").write_text("guide\n", encoding="utf-8")
            (root / ".scratch" / "task" / "STATE.md").write_text(
                "local context\n",
                encoding="utf-8",
            )

            discovered = {
                path.relative_to(root).as_posix()
                for path in validate.markdown_files(root)
            }

            self.assertEqual(discovered, {"README.md", "docs/guide.md"})


if __name__ == "__main__":
    unittest.main()
