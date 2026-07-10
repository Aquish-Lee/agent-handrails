from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "sync_skills.py"
SPEC = importlib.util.spec_from_file_location("sync_skills", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
sync_skills = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_skills)


class DeployOneTests(unittest.TestCase):
    def make_source_and_target(
        self,
        root: Path,
        *,
        with_existing_target: bool = True,
    ) -> tuple[Path, Path, Path]:
        source = root / "source" / "example-skill"
        target_root = root / "deployed"
        target = target_root / source.name
        source.mkdir(parents=True)
        target_root.mkdir(parents=True)
        (source / "SKILL.md").write_text("new source\n", encoding="utf-8")
        if with_existing_target:
            target.mkdir()
            (target / "SKILL.md").write_text(
                "existing deployment\n",
                encoding="utf-8",
            )
        return source, target_root, target

    def test_existing_target_survives_staging_copy_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source, target_root, target = self.make_source_and_target(root)
            existing = target / "SKILL.md"

            with mock.patch.object(
                sync_skills.shutil,
                "copytree",
                side_effect=OSError("injected staging copy failure"),
            ):
                with self.assertRaisesRegex(OSError, "injected staging copy failure"):
                    sync_skills.deploy_one(source, target, target_root)

            self.assertTrue(target.is_dir())
            self.assertEqual(
                existing.read_text(encoding="utf-8"),
                "existing deployment\n",
            )

    def test_existing_target_survives_backup_move_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source, target_root, target = self.make_source_and_target(root)
            real_replace = sync_skills.os.replace

            def fail_when_moving_existing_target(
                source_path: Path,
                destination_path: Path,
            ) -> None:
                if Path(source_path) == target:
                    raise OSError("injected backup move failure")
                real_replace(source_path, destination_path)

            with mock.patch.object(
                sync_skills.os,
                "replace",
                side_effect=fail_when_moving_existing_target,
            ):
                with self.assertRaisesRegex(OSError, "injected backup move failure"):
                    sync_skills.deploy_one(source, target, target_root)

            self.assertEqual(
                (target / "SKILL.md").read_text(encoding="utf-8"),
                "existing deployment\n",
            )

    def test_existing_target_is_restored_after_deployed_copy_verification_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source, target_root, target = self.make_source_and_target(root)

            with mock.patch.object(
                sync_skills,
                "tree_digest",
                side_effect=(
                    "source",
                    "existing",
                    "source",
                    "source",
                    "source",
                    "corrupt",
                ),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "deployed copy verification failed",
                ):
                    sync_skills.deploy_one(source, target, target_root)

            self.assertEqual(
                (target / "SKILL.md").read_text(encoding="utf-8"),
                "existing deployment\n",
            )

    def test_failed_first_install_removes_unverified_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source, target_root, target = self.make_source_and_target(
                root,
                with_existing_target=False,
            )

            with mock.patch.object(
                sync_skills,
                "tree_digest",
                side_effect=("source", "source", "source", "corrupt"),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "deployed copy verification failed",
                ):
                    sync_skills.deploy_one(source, target, target_root)

            self.assertFalse(target.exists())

    def test_successful_update_replaces_target_and_cleans_temporary_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source, target_root, target = self.make_source_and_target(root)

            result = sync_skills.deploy_one(source, target, target_root)

            self.assertEqual(result, "updated")
            self.assertEqual(
                (target / "SKILL.md").read_text(encoding="utf-8"),
                "new source\n",
            )
            self.assertEqual(
                [path.name for path in target_root.iterdir()],
                ["example-skill"],
            )


if __name__ == "__main__":
    unittest.main()
