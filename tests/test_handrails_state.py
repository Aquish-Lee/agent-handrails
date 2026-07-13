from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = PROJECT_ROOT / "runtime" / "handrails_state.py"


def load_runtime():
    spec = importlib.util.spec_from_file_location("handrails_state_runtime", RUNTIME_PATH)
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


class HandrailsStateFixture(unittest.TestCase):
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
        write(self.repository / "tracked.txt", "one\ntwo\nthree\nfour\nfive\n")
        git(self.repository, "add", ".gitignore", "tracked.txt")
        git(self.repository, "commit", "-m", "baseline")
        self.base = git(self.repository, "rev-parse", "HEAD")
        self.runtime = load_runtime()

    def inventory(self, **overrides):
        arguments = {
            "repository": self.repository,
            "base": self.base,
            "declared_ignored": (),
            "participating_worktrees": (self.repository,),
            "relevant_environment": {"platform": "linux", "python": "3.10"},
        }
        arguments.update(overrides)
        return self.runtime.inventory_git_state(**arguments)

    def complete_classifications(
        self,
        inventory: dict[str, object],
        *,
        kind: str = "claim",
    ) -> dict[str, object]:
        classifications = []
        for candidate in inventory["candidates"]:
            target_ids = [hunk["hunk_id"] for hunk in candidate.get("hunks", [])] or [
                candidate["candidate_id"]
            ]
            for target_id in target_ids:
                classifications.append(
                    {
                        "target_id": target_id,
                        "classification": (
                            "include-claim" if kind == "claim" else "include-required"
                        ),
                        "rationale": "Required by the current task.",
                        "authorization": "authorized",
                    }
                )
        return {
            "inventory_digest": inventory["inventory_digest"],
            "task_id": "task-runtime-v2",
            "outcome_revision": "r1",
            "logical_units": classifications,
        }


class InventoryTests(HandrailsStateFixture):
    def test_multi_worktree_inventory_and_review_boundary_bind_both_states(self) -> None:
        side = self.root / "side-worktree"
        git(self.repository, "worktree", "add", "-b", "side", str(side), self.base)
        write(self.repository / "tracked.txt", "PRIMARY\ntwo\nthree\nfour\nfive\n")
        write(side / "tracked.txt", "SIDE\ntwo\nthree\nfour\nfive\n")

        inventory = self.inventory(
            participating_worktrees=(self.repository, side),
        )
        classifications = self.complete_classifications(inventory, kind="review")
        boundary = self.runtime.confirm_boundary(
            kind="review",
            classifications=classifications,
            repository=self.repository,
            base=self.base,
            participating_worktrees=(self.repository, side),
            relevant_environment={"platform": "linux", "python": "3.10"},
        )

        self.assertEqual(len(inventory["workspaces"]), 2)
        self.assertEqual(
            {candidate["workspace"] for candidate in inventory["candidates"]},
            {str(self.repository), str(side)},
        )
        self.assertEqual(len(boundary["code_state_token"]["workspaces"]), 2)
        self.assertEqual(
            boundary["canonical_payload"]["inventory_digest"],
            inventory["inventory_digest"],
        )

    def test_inventory_emits_deterministic_candidate_and_hunk_ids(self) -> None:
        write(self.repository / "tracked.txt", "ONE\ntwo\nthree\nfour\nFIVE\n")
        write(self.repository / "untracked.txt", "new\n")

        first = self.inventory()
        second = self.inventory()

        self.assertEqual(first["contract"], "usable-loop/v2")
        self.assertEqual(first["record"], "boundary-inventory")
        self.assertEqual(first["inventory_digest"], second["inventory_digest"])
        self.assertEqual(first["candidates"], second["candidates"])
        tracked = next(
            candidate
            for candidate in first["candidates"]
            if candidate["layer"] == "unstaged" and candidate["path"] == "tracked.txt"
        )
        self.assertEqual(len(tracked["hunks"]), 2)
        self.assertTrue(tracked["candidate_id"].startswith("candidate:sha256:"))
        self.assertTrue(
            all(hunk["hunk_id"].startswith("hunk:sha256:") for hunk in tracked["hunks"])
        )
        untracked = next(
            candidate for candidate in first["candidates"] if candidate["layer"] == "untracked"
        )
        self.assertEqual(untracked["hunks"], [])
        self.assertEqual(untracked["kind"], "artifact")
        self.assertNotIn("captured_at", first["canonical_payload"])

    def test_declared_ignored_is_explicit_and_content_bound(self) -> None:
        write(self.repository / ".local" / "declared.txt", "declared\n")
        write(self.repository / ".local" / "secret.txt", "secret\n")

        inventory = self.inventory(declared_ignored=(self.repository / ".local" / "declared.txt",))
        serialized = json.dumps(inventory, sort_keys=True)

        self.assertIn(".local/declared.txt", serialized)
        self.assertNotIn("secret.txt", serialized)
        self.assertNotIn("secret\\n", serialized)


class BoundaryConfirmationTests(HandrailsStateFixture):
    def test_unmerged_conflict_is_inventoried_and_blocks_confirmation(self) -> None:
        git(self.repository, "switch", "-c", "other")
        write(self.repository / "tracked.txt", "other\ntwo\nthree\nfour\nfive\n")
        git(self.repository, "add", "tracked.txt")
        git(self.repository, "commit", "-m", "other")
        git(self.repository, "switch", "main")
        write(self.repository / "tracked.txt", "main\ntwo\nthree\nfour\nfive\n")
        git(self.repository, "add", "tracked.txt")
        git(self.repository, "commit", "-m", "main")
        completed = subprocess.run(
            ["git", "-C", str(self.repository), "merge", "other"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        inventory = self.inventory()
        self.assertEqual(inventory["workspaces"][0]["conflict_paths"], ["tracked.txt"])

        with self.assertRaisesRegex(self.runtime.BoundaryError, "unmerged conflict"):
            self.runtime.confirm_boundary(
                kind="claim",
                classifications=self.complete_classifications(inventory),
                repository=self.repository,
                base=self.base,
                participating_worktrees=(self.repository,),
                relevant_environment={"platform": "linux", "python": "3.10"},
            )

    def test_same_state_and_classifications_have_same_boundary_digest(self) -> None:
        write(self.repository / "tracked.txt", "ONE\ntwo\nthree\nfour\nFIVE\n")
        inventory = self.inventory()
        classifications = self.complete_classifications(inventory, kind="review")

        first = self.runtime.confirm_boundary(
            kind="review",
            classifications=classifications,
            repository=self.repository,
            base=self.base,
            participating_worktrees=(self.repository,),
            relevant_environment={"python": "3.10", "platform": "linux"},
        )
        second = self.runtime.confirm_boundary(
            kind="review",
            classifications=classifications,
            repository=self.repository,
            base=self.base,
            participating_worktrees=(self.repository,),
            relevant_environment={"platform": "linux", "python": "3.10"},
        )

        self.assertEqual(first["record"], "review-boundary")
        self.assertEqual(first["boundary_digest"], second["boundary_digest"])
        self.assertEqual(
            first["code_state_token"]["token_digest"],
            second["code_state_token"]["token_digest"],
        )
        self.assertNotIn("captured_at", first["canonical_payload"])

    def test_mixed_file_requires_every_hunk_exactly_once(self) -> None:
        write(self.repository / "tracked.txt", "ONE\ntwo\nthree\nfour\nFIVE\n")
        inventory = self.inventory()
        classifications = self.complete_classifications(inventory)
        classifications["logical_units"].pop()

        with self.assertRaisesRegex(self.runtime.BoundaryError, "unclassified"):
            self.runtime.confirm_boundary(
                kind="claim",
                classifications=classifications,
                repository=self.repository,
                base=self.base,
                participating_worktrees=(self.repository,),
                relevant_environment={"platform": "linux", "python": "3.10"},
            )

    def test_overlapping_and_unknown_targets_are_rejected(self) -> None:
        write(self.repository / "tracked.txt", "ONE\ntwo\nthree\nfour\nfive\n")
        inventory = self.inventory()
        classifications = self.complete_classifications(inventory)
        classifications["logical_units"].append(dict(classifications["logical_units"][0]))

        with self.assertRaisesRegex(self.runtime.BoundaryError, "more than once"):
            self.runtime.confirm_boundary(
                kind="claim",
                classifications=classifications,
                repository=self.repository,
                base=self.base,
                participating_worktrees=(self.repository,),
                relevant_environment={"platform": "linux", "python": "3.10"},
            )

        classifications["logical_units"][-1]["target_id"] = "hunk:sha256:unknown"
        with self.assertRaisesRegex(self.runtime.BoundaryError, "unknown target"):
            self.runtime.confirm_boundary(
                kind="claim",
                classifications=classifications,
                repository=self.repository,
                base=self.base,
                participating_worktrees=(self.repository,),
                relevant_environment={"platform": "linux", "python": "3.10"},
            )

    def test_unapproved_scope_creep_is_rejected(self) -> None:
        write(self.repository / "tracked.txt", "ONE\ntwo\nthree\nfour\nfive\n")
        inventory = self.inventory()
        classifications = self.complete_classifications(inventory, kind="review")
        classifications["logical_units"][0].update(
            classification="include-scope-creep",
            authorization="needs-authorization",
        )

        with self.assertRaisesRegex(self.runtime.BoundaryError, "authorization"):
            self.runtime.confirm_boundary(
                kind="review",
                classifications=classifications,
                repository=self.repository,
                base=self.base,
                participating_worktrees=(self.repository,),
                relevant_environment={"platform": "linux", "python": "3.10"},
            )

    def test_stale_inventory_is_rejected(self) -> None:
        write(self.repository / "tracked.txt", "ONE\ntwo\nthree\nfour\nfive\n")
        inventory = self.inventory()
        classifications = self.complete_classifications(inventory)
        write(self.repository / "tracked.txt", "CHANGED AGAIN\ntwo\nthree\nfour\nfive\n")

        with self.assertRaisesRegex(self.runtime.BoundaryError, "inventory digest"):
            self.runtime.confirm_boundary(
                kind="claim",
                classifications=classifications,
                repository=self.repository,
                base=self.base,
                participating_worktrees=(self.repository,),
                relevant_environment={"platform": "linux", "python": "3.10"},
            )

    def test_capture_rejects_state_drift_and_boundary_tampering(self) -> None:
        write(self.repository / "tracked.txt", "ONE\ntwo\nthree\nfour\nfive\n")
        inventory = self.inventory()
        boundary = self.runtime.confirm_boundary(
            kind="claim",
            classifications=self.complete_classifications(inventory),
            repository=self.repository,
            base=self.base,
            participating_worktrees=(self.repository,),
            relevant_environment={"platform": "linux", "python": "3.10"},
        )
        fresh = self.runtime.capture_boundary(boundary)
        self.assertEqual(fresh["boundary_digest"], boundary["boundary_digest"])

        tampered = json.loads(json.dumps(boundary))
        tampered["canonical_payload"]["outcome_revision"] = "r2"
        with self.assertRaisesRegex(self.runtime.BoundaryError, "digest mismatch"):
            self.runtime.capture_boundary(tampered)

        write(self.repository / "tracked.txt", "DRIFT\ntwo\nthree\nfour\nfive\n")
        with self.assertRaisesRegex(self.runtime.BoundaryError, "state drift"):
            self.runtime.capture_boundary(boundary)


class BoundaryCliTests(HandrailsStateFixture):
    def test_cli_has_only_inventory_confirm_and_capture_subcommands(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RUNTIME_PATH), "--help"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertIn("inventory", completed.stdout)
        self.assertIn("confirm", completed.stdout)
        self.assertIn("capture", completed.stdout)
        self.assertNotIn("review-boundary-digest", completed.stdout)

    def test_compact_cli_projection_keeps_ids_and_digests_without_canonical_payload(self) -> None:
        write(self.repository / "tracked.txt", "ONE\ntwo\nthree\nfour\nfive\n")
        write(self.repository / "note.tmp", "local\n")
        inventory_completed = subprocess.run(
            [
                sys.executable,
                str(RUNTIME_PATH),
                "inventory",
                "--compact",
                "--repository",
                str(self.repository),
                "--base",
                "HEAD",
            ],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        inventory = json.loads(inventory_completed.stdout)
        self.assertNotIn("canonical_payload", inventory)
        self.assertNotIn("capture_spec", inventory)
        self.assertEqual(len(inventory["logical_units"]), 2)
        self.assertTrue(all(unit["target_id"] for unit in inventory["logical_units"]))

        inventory_git_state = self.runtime.inventory_git_state(
            repository=self.repository,
            base="HEAD",
        )
        classifications = self.complete_classifications(inventory_git_state)
        confirm_completed = subprocess.run(
            [
                sys.executable,
                str(RUNTIME_PATH),
                "confirm",
                "--compact",
                "--kind",
                "claim",
                "--classifications",
                "-",
                "--repository",
                str(self.repository),
                "--base",
                "HEAD",
            ],
            input=json.dumps(classifications),
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        boundary = json.loads(confirm_completed.stdout)
        self.assertNotIn("canonical_payload", boundary)
        self.assertEqual(boundary["inventory_digest"], inventory_git_state["inventory_digest"])
        self.assertTrue(boundary["boundary_digest"].startswith("sha256:"))
        self.assertTrue(boundary["code_state_token"].startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
