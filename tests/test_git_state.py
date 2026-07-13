from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GIT_STATE_PATH = PROJECT_ROOT / "runtime" / "git_state.py"


def load_git_state_module():
    spec = importlib.util.spec_from_file_location("git_state_runtime", GIT_STATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class GitStateFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.repository = self.root / "repository"
        self.repository.mkdir()
        git(self.repository, "init", "-b", "main")
        git(self.repository, "config", "user.name", "Agent Handrails Test")
        git(self.repository, "config", "user.email", "tests@example.invalid")
        write(self.repository / ".gitignore", ".local/\n")
        write(self.repository / "tracked.txt", "baseline\n")
        git(self.repository, "add", ".gitignore", "tracked.txt")
        git(self.repository, "commit", "-m", "baseline")
        self.base = git(self.repository, "rev-parse", "HEAD")
        self.module = load_git_state_module()

    def capture(self, **overrides):
        arguments = {
            "repository": self.repository,
            "base": self.base,
            "review_boundary_digest": "sha256:boundary",
            "included_untracked": (),
            "declared_ignored": (),
            "participating_worktrees": (self.repository,),
            "relevant_environment": {"python": "3.10+", "platform": "linux"},
        }
        arguments.update(overrides)
        return self.module.capture_git_state(**arguments)


class GitStateCaptureTests(GitStateFixture):
    def test_inventory_covers_dirty_layers_without_scanning_ignored_files(self) -> None:
        write(self.repository / "tracked.txt", "unstaged\n")
        write(self.repository / "staged.txt", "staged\n")
        git(self.repository, "add", "staged.txt")
        write(self.repository / "untracked.txt", "untracked\n")
        write(self.repository / ".local" / "declared.txt", "declared\n")
        write(self.repository / ".local" / "secret.txt", "do-not-read\n")

        token = self.capture(
            included_untracked=(self.repository / "untracked.txt",),
            declared_ignored=(self.repository / ".local" / "declared.txt",),
        )

        inventory = token["candidate_inventory"]
        self.assertIn("staged.txt", inventory["staged"])
        self.assertIn("tracked.txt", inventory["unstaged"])
        self.assertIn("untracked.txt", inventory["untracked"])
        self.assertEqual(inventory["declared_ignored"], [".local/declared.txt"])
        serialized = json.dumps(token, sort_keys=True)
        self.assertNotIn("secret.txt", serialized)
        self.assertNotIn("do-not-read", serialized)
        self.assertEqual(
            token["included_untracked_fingerprints"][0]["path"],
            "untracked.txt",
        )
        self.assertEqual(
            token["declared_ignored_fingerprints"][0]["path"],
            ".local/declared.txt",
        )

    def test_committed_changes_since_base_are_inventory_candidates(self) -> None:
        write(self.repository / "committed.txt", "committed\n")
        git(self.repository, "add", "committed.txt")
        git(self.repository, "commit", "-m", "task change")

        token = self.capture()

        self.assertEqual(
            token["candidate_inventory"]["committed"],
            [{"path": "committed.txt", "status": "A"}],
        )
        self.assertEqual(token["base_revision"], self.base)
        self.assertEqual(token["exact_revision"], git(self.repository, "rev-parse", "HEAD"))

    def test_relevant_edits_change_the_mechanical_fingerprints(self) -> None:
        write(self.repository / "untracked.txt", "one\n")
        write(self.repository / ".local" / "declared.txt", "one\n")
        before = self.capture(
            included_untracked=(self.repository / "untracked.txt",),
            declared_ignored=(self.repository / ".local" / "declared.txt",),
        )

        write(self.repository / "tracked.txt", "changed\n")
        write(self.repository / "untracked.txt", "two\n")
        write(self.repository / ".local" / "declared.txt", "two\n")
        after = self.capture(
            included_untracked=(self.repository / "untracked.txt",),
            declared_ignored=(self.repository / ".local" / "declared.txt",),
        )

        self.assertNotEqual(
            before["tracked_state_fingerprint"],
            after["tracked_state_fingerprint"],
        )
        self.assertNotEqual(
            before["included_untracked_fingerprints"],
            after["included_untracked_fingerprints"],
        )
        self.assertNotEqual(
            before["declared_ignored_fingerprints"],
            after["declared_ignored_fingerprints"],
        )

    def test_boundary_assignment_does_not_change_mechanical_fingerprints(self) -> None:
        write(self.repository / "untracked.txt", "content\n")
        first = self.capture(
            review_boundary_digest="unconfirmed",
            included_untracked=(self.repository / "untracked.txt",),
        )
        second = self.capture(
            review_boundary_digest="sha256:confirmed",
            included_untracked=(self.repository / "untracked.txt",),
        )

        for field in (
            "base_revision",
            "exact_revision",
            "conflict_state",
            "candidate_inventory",
            "tracked_state_fingerprint",
            "included_untracked_fingerprints",
            "declared_ignored_fingerprints",
            "participating_worktree_fingerprints",
        ):
            with self.subTest(field=field):
                self.assertEqual(first[field], second[field])

    def test_participating_worktree_state_is_bound_into_the_token(self) -> None:
        worktree = self.root / "side-worktree"
        git(self.repository, "worktree", "add", "-b", "side", str(worktree), self.base)
        before = self.capture(participating_worktrees=(self.repository, worktree))

        write(worktree / "tracked.txt", "side change\n")
        after = self.capture(participating_worktrees=(self.repository, worktree))

        self.assertEqual(len(after["participating_worktrees"]), 2)
        self.assertEqual(len(after["candidate_inventory"]["by_workspace"]), 2)
        self.assertNotEqual(
            before["participating_worktree_fingerprints"],
            after["participating_worktree_fingerprints"],
        )

    def test_capture_is_read_only_for_repository_state(self) -> None:
        write(self.repository / "tracked.txt", "dirty\n")
        before = git(self.repository, "status", "--porcelain=v1", "--untracked-files=all")
        head_before = git(self.repository, "rev-parse", "HEAD")
        index = self.repository / ".git" / "index"
        index_bytes_before = index.read_bytes()
        index_mtime_before = index.stat().st_mtime_ns

        self.capture()

        self.assertEqual(index.read_bytes(), index_bytes_before)
        self.assertEqual(index.stat().st_mtime_ns, index_mtime_before)
        self.assertEqual(
            git(self.repository, "status", "--porcelain=v1", "--untracked-files=all"),
            before,
        )
        self.assertEqual(git(self.repository, "rev-parse", "HEAD"), head_before)
        self.assertFalse((self.repository / ".git" / "index.lock").exists())

    def test_conflicts_are_reported_and_bound_into_state(self) -> None:
        git(self.repository, "switch", "-c", "other")
        write(self.repository / "tracked.txt", "other\n")
        git(self.repository, "add", "tracked.txt")
        git(self.repository, "commit", "-m", "other change")
        git(self.repository, "switch", "main")
        write(self.repository / "tracked.txt", "main\n")
        git(self.repository, "add", "tracked.txt")
        git(self.repository, "commit", "-m", "main change")
        merge = subprocess.run(
            ["git", "-C", str(self.repository), "merge", "other"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertNotEqual(merge.returncode, 0)

        token = self.capture()

        self.assertTrue(token["conflict_state"]["present"])
        self.assertTrue(
            any(path.endswith("::tracked.txt") for path in token["conflict_state"]["paths"])
        )

    def test_ignored_artifact_requires_explicit_declared_channel(self) -> None:
        ignored = self.repository / ".local" / "secret.txt"
        write(ignored, "secret\n")

        with self.assertRaisesRegex(self.module.GitStateError, "ignored artifact"):
            self.capture(included_untracked=(ignored,))

    def test_cli_emits_stable_contract_shape(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(GIT_STATE_PATH),
                "--repository",
                str(self.repository),
                "--base",
                self.base,
                "--review-boundary-digest",
                "sha256:boundary",
                "--environment",
                "platform=linux",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "TZ": "UTC"},
        )
        token = json.loads(completed.stdout)

        self.assertEqual(token["contract"], "usable-loop/v1")
        self.assertEqual(token["record"], "code-state-token")
        self.assertEqual(token["provider"], "git")
        self.assertEqual(token["review_boundary_digest"], "sha256:boundary")
        self.assertEqual(token["relevant_environment"], {"platform": "linux"})
        contract = json.loads(
            (PROJECT_ROOT / "contracts" / "usable-loop-v1.json").read_text(encoding="utf-8")
        )
        self.assertTrue(
            set(contract["records"]["code-state-token"]["required_fields"]).issubset(token)
        )


if __name__ == "__main__":
    unittest.main()
