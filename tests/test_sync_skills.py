from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "sync_skills.py"
SPEC = importlib.util.spec_from_file_location("sync_skills", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
sync_skills = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sync_skills
SPEC.loader.exec_module(sync_skills)


def filesystem_snapshot(root: Path) -> tuple[tuple[str, ...], ...]:
    if not root.exists():
        return ()
    entries: list[tuple[str, ...]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            entries.append(("L", relative, os.readlink(path)))
        elif path.is_dir():
            entries.append(("D", relative))
        elif path.is_file():
            entries.append(("F", relative, sync_skills.file_digest(path)))
    return tuple(entries)


class BundleDeploymentTests(unittest.TestCase):
    def make_source(self, root: Path, label: str) -> Path:
        source = root / f"source-{label}"
        for name in sync_skills.SKILL_NAMES:
            skill = source / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"---\nname: {name}\n---\n\n# {name}\n\n{label}\n",
                encoding="utf-8",
            )
            (skill / "payload.txt").write_text(
                f"{label}:{name}\n",
                encoding="utf-8",
            )
        return source

    def make_legacy_install(
        self,
        source: Path,
        target: Path,
        codex_links: Path,
    ) -> dict[str, str]:
        target.mkdir()
        codex_links.mkdir()
        raw_links: dict[str, str] = {}
        for name in sync_skills.SKILL_NAMES:
            shutil.copytree(source / name, target / name)
            link = codex_links / name
            link.symlink_to(target / name, target_is_directory=True)
            raw_links[name] = os.readlink(link)
        (target / "unrelated-skill").mkdir()
        (target / "unrelated-skill" / "KEEP").write_text(
            "untouched\n",
            encoding="utf-8",
        )
        (codex_links / "unrelated-link").symlink_to(target / "unrelated-skill")
        return raw_links

    def assert_all_skills_resolve_to(self, target: Path, label: str) -> None:
        for name in sync_skills.SKILL_NAMES:
            self.assertEqual(
                (target / name / "payload.txt").read_text(encoding="utf-8"),
                f"{label}:{name}\n",
            )

    def leave_committed_journal(
        self,
        legacy: Path,
        source: Path,
        target: Path,
        codex_links: Path,
    ) -> sync_skills.ApplyResult:
        self.make_legacy_install(legacy, target, codex_links)
        transaction = sync_skills.transaction_root(target)
        real_rmtree = sync_skills.shutil.rmtree
        cleanup_failed = False

        def preserve_committed_transaction(
            path: Path,
            *args: object,
            **kwargs: object,
        ) -> None:
            nonlocal cleanup_failed
            if Path(path) == transaction and not cleanup_failed:
                cleanup_failed = True
                raise OSError("injected committed journal cleanup failure")
            real_rmtree(path, *args, **kwargs)

        with mock.patch.object(
            sync_skills.shutil,
            "rmtree",
            side_effect=preserve_committed_transaction,
        ):
            result = sync_skills.apply_bundle(source, target, codex_links)

        self.assertTrue(cleanup_failed)
        self.assertEqual(sync_skills.read_journal(target)["phase"], "committed")
        return result

    def test_default_target_uses_xdg_for_new_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            home = root / "home"
            xdg = root / "xdg"
            home.mkdir()

            selected = sync_skills.choose_default_target(
                environment={"XDG_DATA_HOME": str(xdg)},
                home=home,
            )

            self.assertEqual(selected, xdg / "agent-handrails" / "skills")

    def test_default_target_preserves_existing_legacy_managed_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            home = Path(temporary_directory)
            legacy = home / "Workspace" / "Skills"
            (legacy / ".agent-handrails").mkdir(parents=True)

            selected = sync_skills.choose_default_target(
                environment={"XDG_DATA_HOME": str(home / "xdg")},
                home=home,
            )

            self.assertEqual(selected, legacy)

    def test_uninstall_removes_only_owned_links_and_retains_bundles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v2")
            target = root / "target"
            codex_links = root / "codex"
            (target / "unrelated").mkdir(parents=True)
            (target / "unrelated" / "KEEP").write_text("keep\n", encoding="utf-8")
            sync_skills.apply_bundle(source, target, codex_links)
            active_id = sync_skills.current_bundle_id(target)

            result = sync_skills.uninstall_bundle(target)

            self.assertEqual(result.bundle_id, active_id)
            self.assertFalse(result.purged)
            for name in sync_skills.SKILL_NAMES:
                self.assertFalse(sync_skills.path_exists(target / name))
                self.assertFalse(sync_skills.path_exists(codex_links / name))
            self.assertTrue((target / ".agent-handrails" / "bundles" / active_id).is_dir())
            ownership = sync_skills.read_ownership(target)
            self.assertFalse(ownership["installed"])
            self.assertEqual(
                (target / "unrelated" / "KEEP").read_text(encoding="utf-8"),
                "keep\n",
            )

            reapplied = sync_skills.apply_bundle(source, target, codex_links)
            self.assertEqual(reapplied.mode, "reinstalled")
            self.assertEqual(
                sync_skills.check_installation(source, target, codex_links).exit_code, 0
            )

    def test_uninstall_refuses_replaced_link_before_any_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v2")
            target = root / "target"
            codex_links = root / "codex"
            sync_skills.apply_bundle(source, target, codex_links)
            replaced = codex_links / sync_skills.SKILL_NAMES[-1]
            replaced.unlink()
            replaced.write_text("external replacement\n", encoding="utf-8")
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)

            with self.assertRaisesRegex(RuntimeError, "ownership mismatch"):
                sync_skills.uninstall_bundle(target)

            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)

    def test_purge_requires_explicit_mode_and_keeps_unrelated_target_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v2")
            target = root / "target"
            codex_links = root / "codex"
            target.mkdir()
            (target / "KEEP").write_text("keep\n", encoding="utf-8")
            sync_skills.apply_bundle(source, target, codex_links)

            result = sync_skills.uninstall_bundle(target, purge=True)

            self.assertTrue(result.purged)
            self.assertFalse((target / ".agent-handrails").exists())
            self.assertEqual((target / "KEEP").read_text(encoding="utf-8"), "keep\n")
            self.assertTrue(target.is_dir())

    def test_first_install_uses_versioned_bundle_and_stable_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"

            result = sync_skills.apply_bundle(source, target, codex_links)

            managed = target / ".agent-handrails"
            current = managed / "current"
            self.assertTrue(current.is_symlink())
            self.assertEqual(
                os.readlink(current),
                f"bundles/{result.bundle_id}",
            )
            for name in sync_skills.SKILL_NAMES:
                self.assertEqual(
                    os.readlink(target / name),
                    f".agent-handrails/current/skills/{name}",
                )
                self.assertEqual(os.readlink(codex_links / name), str(target / name))
            self.assert_all_skills_resolve_to(target, "v1")
            self.assertEqual(
                sync_skills.check_installation(source, target, codex_links).exit_code,
                0,
            )

    def test_upgrade_switches_all_skills_together_and_retains_old_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_v1 = self.make_source(root, "v1")
            source_v2 = self.make_source(root, "v2")
            target = root / "target"
            codex_links = root / "codex"
            first = sync_skills.apply_bundle(source_v1, target, codex_links)
            entry_links = {name: os.readlink(target / name) for name in sync_skills.SKILL_NAMES}
            discovery_links = {
                name: os.readlink(codex_links / name) for name in sync_skills.SKILL_NAMES
            }

            second = sync_skills.apply_bundle(source_v2, target, codex_links)

            self.assertNotEqual(first.bundle_id, second.bundle_id)
            self.assertTrue((target / ".agent-handrails" / "bundles" / first.bundle_id).is_dir())
            self.assertTrue((target / ".agent-handrails" / "bundles" / second.bundle_id).is_dir())
            self.assertEqual(
                os.readlink(target / ".agent-handrails" / "current"),
                f"bundles/{second.bundle_id}",
            )
            self.assertEqual(
                entry_links,
                {name: os.readlink(target / name) for name in sync_skills.SKILL_NAMES},
            )
            self.assertEqual(
                discovery_links,
                {name: os.readlink(codex_links / name) for name in sync_skills.SKILL_NAMES},
            )
            self.assert_all_skills_resolve_to(target, "v2")

    def test_legacy_migration_preserves_old_bundle_and_discovery_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            legacy = self.make_source(root, "legacy")
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"
            original_links = self.make_legacy_install(legacy, target, codex_links)

            result = sync_skills.apply_bundle(source, target, codex_links)

            bundles = list((target / ".agent-handrails" / "bundles").iterdir())
            self.assertEqual(len(bundles), 2)
            self.assertIn(result.bundle_id, {path.name for path in bundles})
            for name in sync_skills.SKILL_NAMES:
                self.assertTrue((target / name).is_symlink())
                self.assertEqual(os.readlink(codex_links / name), original_links[name])
            self.assert_all_skills_resolve_to(target, "v1")
            self.assertEqual(
                (target / "unrelated-skill" / "KEEP").read_text(encoding="utf-8"),
                "untouched\n",
            )

    def test_preflight_rejects_late_discovery_conflict_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"
            target.mkdir()
            codex_links.mkdir()
            (target / "unrelated").write_text("keep\n", encoding="utf-8")
            conflicting = codex_links / sync_skills.SKILL_NAMES[-1]
            conflicting.write_text("do not replace\n", encoding="utf-8")
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)

            with self.assertRaisesRegex(RuntimeError, "discovery"):
                sync_skills.apply_bundle(source, target, codex_links)

            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)

    def test_failure_before_activation_preserves_exact_previous_installation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_v1 = self.make_source(root, "v1")
            source_v2 = self.make_source(root, "v2")
            target = root / "target"
            codex_links = root / "codex"
            sync_skills.apply_bundle(source_v1, target, codex_links)
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)

            def failpoint(name: str) -> None:
                if name == "activation.before-replace":
                    raise OSError("injected activation failure")

            with self.assertRaisesRegex(OSError, "injected activation failure"):
                sync_skills.apply_bundle(
                    source_v2,
                    target,
                    codex_links,
                    failpoint=failpoint,
                )

            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)
            self.assert_all_skills_resolve_to(target, "v1")

    def test_direct_bundle_discovery_link_is_not_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"
            result = sync_skills.apply_bundle(source, target, codex_links)
            link = codex_links / sync_skills.SKILL_NAMES[0]
            link.unlink()
            link.symlink_to(
                target
                / ".agent-handrails"
                / "bundles"
                / result.bundle_id
                / "skills"
                / sync_skills.SKILL_NAMES[0]
            )

            checked = sync_skills.check_installation(source, target, codex_links)

            self.assertEqual(checked.exit_code, 1)
            self.assertIn("different-target", "\n".join(checked.lines))

    def test_staging_failure_preserves_exact_previous_installation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_v1 = self.make_source(root, "v1")
            source_v2 = self.make_source(root, "v2")
            target = root / "target"
            codex_links = root / "codex"
            sync_skills.apply_bundle(source_v1, target, codex_links)
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)

            def failpoint(name: str) -> None:
                if name == "stage.after-copy":
                    raise OSError("injected staging failure")

            with self.assertRaisesRegex(OSError, "injected staging failure"):
                sync_skills.apply_bundle(
                    source_v2,
                    target,
                    codex_links,
                    failpoint=failpoint,
                )

            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)

    def test_legacy_migration_failure_restores_exact_legacy_layout(self) -> None:
        positions = (
            sync_skills.SKILL_NAMES[0],
            sync_skills.SKILL_NAMES[len(sync_skills.SKILL_NAMES) // 2],
            sync_skills.SKILL_NAMES[-1],
        )
        for failing_name in positions:
            with self.subTest(failing_name=failing_name):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    legacy = self.make_source(root, "legacy")
                    source = self.make_source(root, "v1")
                    target = root / "target"
                    codex_links = root / "codex"
                    self.make_legacy_install(legacy, target, codex_links)
                    before_target = filesystem_snapshot(target)
                    before_links = filesystem_snapshot(codex_links)

                    def failpoint(name: str) -> None:
                        if name == f"migration.after-entry:{failing_name}":
                            raise OSError("injected migration failure")

                    with self.assertRaisesRegex(
                        OSError,
                        "injected migration failure",
                    ):
                        sync_skills.apply_bundle(
                            source,
                            target,
                            codex_links,
                            failpoint=failpoint,
                        )

                    self.assertEqual(filesystem_snapshot(target), before_target)
                    self.assertEqual(filesystem_snapshot(codex_links), before_links)

    def test_first_install_link_failure_removes_new_installation(self) -> None:
        positions = (
            sync_skills.SKILL_NAMES[0],
            sync_skills.SKILL_NAMES[len(sync_skills.SKILL_NAMES) // 2],
            sync_skills.SKILL_NAMES[-1],
        )
        for failing_name in positions:
            with self.subTest(failing_name=failing_name):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    source = self.make_source(root, "v1")
                    target = root / "target"
                    codex_links = root / "codex"

                    def failpoint(name: str) -> None:
                        if name == f"links.after:{failing_name}":
                            raise OSError("injected discovery link failure")

                    with self.assertRaisesRegex(
                        OSError,
                        "injected discovery link failure",
                    ):
                        sync_skills.apply_bundle(
                            source,
                            target,
                            codex_links,
                            failpoint=failpoint,
                        )

                    self.assertFalse(target.exists())
                    self.assertFalse(codex_links.exists())

    def test_first_install_entrypoint_failure_removes_new_installation(self) -> None:
        positions = (
            sync_skills.SKILL_NAMES[0],
            sync_skills.SKILL_NAMES[len(sync_skills.SKILL_NAMES) // 2],
            sync_skills.SKILL_NAMES[-1],
        )
        for failing_name in positions:
            with self.subTest(failing_name=failing_name):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    source = self.make_source(root, "v1")
                    target = root / "target"
                    codex_links = root / "codex"

                    def failpoint(name: str) -> None:
                        if name == f"migration.after-entry:{failing_name}":
                            raise OSError("injected entrypoint failure")

                    with self.assertRaisesRegex(
                        OSError,
                        "injected entrypoint failure",
                    ):
                        sync_skills.apply_bundle(
                            source,
                            target,
                            codex_links,
                            failpoint=failpoint,
                        )

                    self.assertFalse(target.exists())
                    self.assertFalse(codex_links.exists())

    def test_failure_after_activation_rolls_back_to_previous_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_v1 = self.make_source(root, "v1")
            source_v2 = self.make_source(root, "v2")
            target = root / "target"
            codex_links = root / "codex"
            sync_skills.apply_bundle(source_v1, target, codex_links)
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)

            def failpoint(name: str) -> None:
                if name == "activation.after-replace":
                    raise OSError("injected post-activation failure")

            with self.assertRaisesRegex(
                OSError,
                "injected post-activation failure",
            ):
                sync_skills.apply_bundle(
                    source_v2,
                    target,
                    codex_links,
                    failpoint=failpoint,
                )

            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)
            self.assert_all_skills_resolve_to(target, "v1")

    def test_partial_legacy_layout_is_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"
            target.mkdir()
            codex_links.mkdir()
            first_name = sync_skills.SKILL_NAMES[0]
            shutil.copytree(source / first_name, target / first_name)
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)

            with self.assertRaisesRegex(RuntimeError, "layout conflict"):
                sync_skills.apply_bundle(source, target, codex_links)

            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)

    def test_reapply_same_bundle_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"
            first = sync_skills.apply_bundle(source, target, codex_links)
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)

            second = sync_skills.apply_bundle(source, target, codex_links)

            self.assertEqual(second.mode, "up-to-date")
            self.assertEqual(second.bundle_id, first.bundle_id)
            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)

    def test_apply_old_source_switches_to_retained_old_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_v1 = self.make_source(root, "v1")
            source_v2 = self.make_source(root, "v2")
            target = root / "target"
            codex_links = root / "codex"
            first = sync_skills.apply_bundle(source_v1, target, codex_links)
            second = sync_skills.apply_bundle(source_v2, target, codex_links)
            bundle_names = {
                path.name for path in (target / ".agent-handrails" / "bundles").iterdir()
            }

            rolled_back = sync_skills.apply_bundle(source_v1, target, codex_links)

            self.assertEqual(rolled_back.bundle_id, first.bundle_id)
            self.assertEqual(rolled_back.previous_bundle_id, second.bundle_id)
            self.assertEqual(
                {path.name for path in (target / ".agent-handrails" / "bundles").iterdir()},
                bundle_names,
            )
            self.assert_all_skills_resolve_to(target, "v1")

    def test_check_rejects_forged_manifest_with_unchanged_bundle_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"
            result = sync_skills.apply_bundle(source, target, codex_links)
            bundle = target / ".agent-handrails" / "bundles" / result.bundle_id
            name = sync_skills.SKILL_NAMES[0]
            skill = bundle / "skills" / name
            (skill / "payload.txt").write_text("forged\n", encoding="utf-8")
            manifest_path = bundle / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["skills"][name] = sync_skills.tree_digest(skill)
            manifest_path.write_text(
                sync_skills.canonical_json(manifest) + "\n",
                encoding="utf-8",
            )

            checked = sync_skills.check_installation(
                source,
                target,
                codex_links,
            )

            self.assertEqual(checked.exit_code, 2)
            self.assertTrue(any(line.startswith("ERROR:") for line in checked.lines))

    def test_check_rejects_unexpected_bundle_top_level_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"
            result = sync_skills.apply_bundle(source, target, codex_links)
            bundle = target / ".agent-handrails" / "bundles" / result.bundle_id
            (bundle / "EXTRA").write_text("unexpected\n", encoding="utf-8")

            checked = sync_skills.check_installation(
                source,
                target,
                codex_links,
            )

            self.assertEqual(checked.exit_code, 2)
            self.assertTrue(any(line.startswith("ERROR:") for line in checked.lines))

    def test_corrupt_retained_same_id_bundle_is_refused_without_overwrite(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_v1 = self.make_source(root, "v1")
            source_v2 = self.make_source(root, "v2")
            target = root / "target"
            codex_links = root / "codex"
            first = sync_skills.apply_bundle(source_v1, target, codex_links)
            second = sync_skills.apply_bundle(source_v2, target, codex_links)
            retained_payload = (
                target
                / ".agent-handrails"
                / "bundles"
                / first.bundle_id
                / "skills"
                / sync_skills.SKILL_NAMES[0]
                / "payload.txt"
            )
            retained_payload.write_text("corrupt\n", encoding="utf-8")
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)

            with self.assertRaises(RuntimeError):
                sync_skills.apply_bundle(source_v1, target, codex_links)

            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)
            self.assertEqual(retained_payload.read_text(encoding="utf-8"), "corrupt\n")
            self.assertEqual(
                os.readlink(target / ".agent-handrails" / "current"),
                f"bundles/{second.bundle_id}",
            )
            self.assert_all_skills_resolve_to(target, "v2")

    def test_atomic_write_json_replace_failure_removes_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "journal.json"
            destination.write_text("old\n", encoding="utf-8")

            with mock.patch.object(
                sync_skills.os,
                "replace",
                side_effect=OSError("injected JSON replace failure"),
            ):
                with self.assertRaisesRegex(OSError, "JSON replace failure"):
                    sync_skills.atomic_write_json(destination, {"phase": "new"})

            self.assertEqual(destination.read_text(encoding="utf-8"), "old\n")
            self.assertEqual(list(root.glob(".journal.json.tmp-*")), [])

    def test_current_replace_oserror_removes_temp_and_preserves_old_install(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_v1 = self.make_source(root, "v1")
            source_v2 = self.make_source(root, "v2")
            target = root / "target"
            codex_links = root / "codex"
            sync_skills.apply_bundle(source_v1, target, codex_links)
            current = target / ".agent-handrails" / "current"
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)
            real_replace = sync_skills.os.replace

            def fail_current_replace(source_path: Path, destination_path: Path) -> None:
                if Path(destination_path) == current:
                    raise OSError("injected current replace failure")
                real_replace(source_path, destination_path)

            with mock.patch.object(
                sync_skills.os,
                "replace",
                side_effect=fail_current_replace,
            ):
                with self.assertRaisesRegex(OSError, "current replace failure"):
                    sync_skills.apply_bundle(source_v2, target, codex_links)

            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)
            self.assertEqual(list(current.parent.glob(".current.tmp-*")), [])
            self.assert_all_skills_resolve_to(target, "v1")

    def test_check_missing_install_does_not_create_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"
            before = filesystem_snapshot(root)

            checked = sync_skills.check_installation(
                source,
                target,
                codex_links,
            )

            self.assertEqual(checked.exit_code, 1)
            self.assertFalse(sync_skills.path_exists(target))
            self.assertFalse(sync_skills.path_exists(codex_links))
            self.assertEqual(filesystem_snapshot(root), before)

    def test_check_committed_journal_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            legacy = self.make_source(root, "legacy")
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"
            self.leave_committed_journal(
                legacy,
                source,
                target,
                codex_links,
            )
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)

            checked = sync_skills.check_installation(
                source,
                target,
                codex_links,
            )

            self.assertEqual(checked.exit_code, 1)
            self.assertEqual(checked.lines, ("bundle/layout: recovery-required",))
            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)
            self.assertTrue(sync_skills.transaction_journal(target).is_file())

    def test_runtime_only_change_creates_and_activates_new_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v1")
            runtime = root / "runtime"
            runtime.mkdir()
            runtime_file = runtime / "helper.py"
            runtime_file.write_text("print('v1')\n", encoding="utf-8")
            runtime_file.chmod(0o755)
            target = root / "target"
            codex_links = root / "codex"

            first = sync_skills.apply_bundle(
                source,
                target,
                codex_links,
                runtime_root=runtime,
            )
            first_runtime = (
                target
                / ".agent-handrails"
                / "bundles"
                / first.bundle_id
                / "runtime"
                / runtime_file.name
            )
            runtime_file.write_text("print('v2')\n", encoding="utf-8")

            self.assertEqual(
                sync_skills.check_installation(
                    source,
                    target,
                    codex_links,
                    runtime_root=runtime,
                ).exit_code,
                1,
            )
            second = sync_skills.apply_bundle(
                source,
                target,
                codex_links,
                runtime_root=runtime,
            )

            second_bundle = target / ".agent-handrails" / "bundles" / second.bundle_id
            second_spec = sync_skills.spec_from_manifest(second_bundle / "manifest.json")
            self.assertNotEqual(first.bundle_id, second.bundle_id)
            self.assertEqual(second.previous_bundle_id, first.bundle_id)
            self.assertEqual(
                first_runtime.read_text(encoding="utf-8"),
                "print('v1')\n",
            )
            self.assertEqual(
                (second_bundle / "runtime" / runtime_file.name).read_text(encoding="utf-8"),
                "print('v2')\n",
            )
            self.assertEqual(
                second_spec.runtime_digest,
                sync_skills.tree_digest(runtime, ignore_generated_python=True),
            )
            self.assertEqual(
                sync_skills.check_installation(
                    source,
                    target,
                    codex_links,
                    runtime_root=runtime,
                ).exit_code,
                0,
            )

    def test_python_bytecode_is_not_hashed_or_deployed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v1")
            runtime = root / "runtime"
            runtime.mkdir()
            (runtime / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
            clean_spec = sync_skills.bundle_spec(
                sync_skills.source_skill_roots(source),
                runtime,
            )
            skill_cache = source / "grill" / "__pycache__"
            skill_cache.mkdir()
            (skill_cache / "helper.cpython-314.pyc").write_bytes(b"skill-bytecode")
            runtime_cache = runtime / "__pycache__"
            runtime_cache.mkdir()
            (runtime_cache / "helper.cpython-314.pyc").write_bytes(b"runtime-bytecode")
            (runtime / "orphan.pyc").write_bytes(b"orphan-bytecode")

            dirty_spec = sync_skills.bundle_spec(
                sync_skills.source_skill_roots(source),
                runtime,
            )
            target = root / "target"
            installed = sync_skills.apply_bundle(
                source,
                target,
                runtime_root=runtime,
            )
            bundle = target / ".agent-handrails" / "bundles" / installed.bundle_id

            self.assertEqual(dirty_spec, clean_spec)
            self.assertEqual(list(bundle.rglob("__pycache__")), [])
            self.assertEqual(list(bundle.rglob("*.pyc")), [])
            deployed_cache = bundle / "runtime" / "__pycache__"
            deployed_cache.mkdir()
            (deployed_cache / "injected.pyc").write_bytes(b"unexpected")
            self.assertEqual(
                sync_skills.check_installation(
                    source,
                    target,
                    runtime_root=runtime,
                ).exit_code,
                2,
            )

    def test_next_apply_cleans_committed_journal_without_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            legacy = self.make_source(root, "legacy")
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"
            installed = self.leave_committed_journal(
                legacy,
                source,
                target,
                codex_links,
            )
            transaction = sync_skills.transaction_root(target)
            self.assertTrue((transaction / "backups" / sync_skills.SKILL_NAMES[0]).is_dir())

            reapplied = sync_skills.apply_bundle(source, target, codex_links)

            self.assertEqual(reapplied.mode, "up-to-date")
            self.assertEqual(reapplied.bundle_id, installed.bundle_id)
            self.assertFalse(sync_skills.path_exists(transaction))
            self.assert_all_skills_resolve_to(target, "v1")

    def test_corrupt_journal_skill_set_is_rejected_without_losing_backup(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            legacy = self.make_source(root, "legacy")
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"
            self.make_legacy_install(legacy, target, codex_links)
            preflight = sync_skills.preflight_apply(source, target, codex_links)
            source_spec = sync_skills.bundle_spec(
                sync_skills.source_skill_roots(source),
            )
            sync_skills.prepare_bootstrap(
                source,
                target,
                codex_links,
                preflight,
                source_spec,
                None,
                sync_skills.SKILL_NAMES,
                sync_skills.no_failpoint,
            )
            first_name = sync_skills.SKILL_NAMES[0]
            backup = sync_skills.transaction_root(target) / "backups" / first_name
            os.replace(target / first_name, backup)
            sync_skills.install_symlink(
                target / first_name,
                sync_skills.expected_entrypoint_raw(first_name),
            )
            journal_path = sync_skills.transaction_journal(target)
            journal = sync_skills.read_journal(target)
            journal["phase"] = "migrating-entrypoints"
            journal["current_action"] = f"entrypoint:{first_name}"
            journal["skills"] = list(sync_skills.SKILL_NAMES[1:])
            journal_path.write_text(
                sync_skills.canonical_json(journal) + "\n",
                encoding="utf-8",
            )
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)

            with self.assertRaises(RuntimeError):
                sync_skills.apply_bundle(source, target, codex_links)

            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)
            self.assertTrue(backup.is_dir())

    def test_interrupted_legacy_journal_restores_prestate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            legacy = self.make_source(root, "legacy")
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"
            self.make_legacy_install(legacy, target, codex_links)
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)
            preflight = sync_skills.preflight_apply(
                source,
                target,
                codex_links,
            )
            source_spec = sync_skills.bundle_spec(
                sync_skills.source_skill_roots(source),
            )
            sync_skills.prepare_bootstrap(
                source,
                target,
                codex_links,
                preflight,
                source_spec,
                None,
                sync_skills.SKILL_NAMES,
                sync_skills.no_failpoint,
            )
            first_name = sync_skills.SKILL_NAMES[0]
            backup = sync_skills.transaction_root(target) / "backups" / first_name
            os.replace(target / first_name, backup)
            sync_skills.install_symlink(
                target / first_name,
                sync_skills.expected_entrypoint_raw(first_name),
            )

            sync_skills.recover_interrupted_migration(target)

            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)

    def test_source_change_after_staging_rolls_back_activation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_v1 = self.make_source(root, "v1")
            source_v2 = self.make_source(root, "v2")
            target = root / "target"
            codex_links = root / "codex"
            sync_skills.apply_bundle(source_v1, target, codex_links)
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)
            changed = False

            def failpoint(name: str) -> None:
                nonlocal changed
                if name == "activation.before-replace" and not changed:
                    changed = True
                    (source_v2 / sync_skills.SKILL_NAMES[0] / "payload.txt").write_text(
                        "changed during activation\n",
                        encoding="utf-8",
                    )

            with self.assertRaisesRegex(RuntimeError, "source changed"):
                sync_skills.apply_bundle(
                    source_v2,
                    target,
                    codex_links,
                    failpoint=failpoint,
                )

            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)
            self.assert_all_skills_resolve_to(target, "v1")

    def test_interrupted_migration_recovers_before_source_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            legacy = self.make_source(root, "legacy")
            source = self.make_source(root, "v1")
            target = root / "target"
            codex_links = root / "codex"
            self.make_legacy_install(legacy, target, codex_links)
            before_target = filesystem_snapshot(target)
            before_links = filesystem_snapshot(codex_links)
            preflight = sync_skills.preflight_apply(source, target, codex_links)
            source_spec = sync_skills.bundle_spec(
                sync_skills.source_skill_roots(source),
            )
            sync_skills.prepare_bootstrap(
                source,
                target,
                codex_links,
                preflight,
                source_spec,
                None,
                sync_skills.SKILL_NAMES,
                sync_skills.no_failpoint,
            )
            first_name = sync_skills.SKILL_NAMES[0]
            backup = sync_skills.transaction_root(target) / "backups" / first_name
            os.replace(target / first_name, backup)
            sync_skills.install_symlink(
                target / first_name,
                sync_skills.expected_entrypoint_raw(first_name),
            )
            shutil.rmtree(source / first_name)

            with self.assertRaisesRegex(RuntimeError, "canonical skill set"):
                sync_skills.apply_bundle(source, target, codex_links)

            self.assertEqual(filesystem_snapshot(target), before_target)
            self.assertEqual(filesystem_snapshot(codex_links), before_links)

    def test_overlapping_roots_are_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v1")
            before_source = filesystem_snapshot(source)

            with self.assertRaisesRegex(RuntimeError, "overlaps skill source"):
                sync_skills.apply_bundle(source, source, root / "codex")

            self.assertEqual(filesystem_snapshot(source), before_source)
            self.assertFalse((root / "codex").exists())

            target = root / "target"
            with self.assertRaisesRegex(RuntimeError, "must be disjoint"):
                sync_skills.apply_bundle(source, target, target / "codex")

            self.assertFalse(target.exists())

    def test_unrelated_bootstrap_prefix_directory_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_source(root, "v1")
            target = root / "target"
            target.mkdir()
            unrelated = target / ".agent-handrails.bootstrap-user-data"
            unrelated.mkdir()
            (unrelated / "KEEP").write_text("keep\n", encoding="utf-8")

            sync_skills.apply_bundle(source, target, root / "codex")

            self.assertEqual(
                (unrelated / "KEEP").read_text(encoding="utf-8"),
                "keep\n",
            )

    def test_install_symlink_refuses_path_that_appears_after_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            link = root / "managed-link"
            real_path_exists = sync_skills.path_exists
            raced = False

            def create_racing_file(path: Path) -> bool:
                nonlocal raced
                if path == link and not raced:
                    raced = True
                    link.write_text("external\n", encoding="utf-8")
                    return False
                return real_path_exists(path)

            with mock.patch.object(
                sync_skills,
                "path_exists",
                side_effect=create_racing_file,
            ):
                with self.assertRaisesRegex(RuntimeError, "refusing to replace"):
                    sync_skills.install_symlink(link, "some-target")

            self.assertFalse(link.is_symlink())
            self.assertEqual(link.read_text(encoding="utf-8"), "external\n")

    def test_link_rollback_does_not_delete_replacement_inode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "target"
            codex = root / "codex"
            target.mkdir()
            codex.mkdir()
            name = sync_skills.SKILL_NAMES[0]
            created = sync_skills.install_symlink(
                codex / name,
                str(target / name),
            )
            (codex / name).unlink()
            (codex / name).symlink_to(target / name)

            sync_skills.remove_created_links(
                [created],
                target,
                codex,
                False,
            )

            self.assertTrue((codex / name).is_symlink())


if __name__ == "__main__":
    unittest.main()
