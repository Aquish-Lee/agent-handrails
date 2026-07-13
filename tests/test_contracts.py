from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "contracts" / "usable-loop-v2.json"
SKILL_NAMES = {
    "branch-sandbox",
    "feedback-loop",
    "grill",
    "plan-lite",
    "spec-lite",
    "two-axis-review",
    "verify-before-claim",
}
V1_HASHES = {
    "contracts/usable-loop-v1.json": "6a2455a83ba7a83bdc5b369cf1154d0462a2c8b5a2f8dc3b8edd3754545a5db8",
    "docs/contracts/usable-loop-v1.md": "3fb5cd6aa8aad84b36cef015a450aeb33e37da0ca836ffd53f1055d29db31753",
    "docs/adr/0001-versioned-usable-loop-contract.md": "bf10f3734293966fa377afc030d121a5f9b58aece65a0693a8a38ddaf88c31d4",
    "runtime/git_state.py": "1471ac833acdecc233d0110a312e8197677662a60baaebca83a4542a9154ba55",
}


def load_contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


class UsableLoopV2ContractTests(unittest.TestCase):
    def test_v1_files_are_immutable_history(self) -> None:
        for relative, expected in V1_HASHES.items():
            with self.subTest(path=relative):
                actual = hashlib.sha256((PROJECT_ROOT / relative).read_bytes()).hexdigest()
                self.assertEqual(actual, expected)

    def test_v2_is_active_and_manages_exactly_seven_skills(self) -> None:
        contract = load_contract()
        self.assertEqual(contract["contract"], "usable-loop/v2")
        self.assertEqual(contract["schema_version"], 2)
        self.assertEqual(contract["status"], "active")
        self.assertEqual(contract["predecessor"], "usable-loop/v1")
        self.assertEqual(set(contract["managed_skills"]), SKILL_NAMES)

    def test_direct_user_authority_and_fail_closed_evidence_are_canonical(self) -> None:
        policies = load_contract()["policies"]
        self.assertEqual(
            policies["authority-bootstrap"]["current_user_request"],
            "authoritative-unless-permission-or-source-conflict",
        )
        lifecycle = policies["evidence-lifecycle"]
        self.assertFalse(lifecycle["development_evidence_supports_claims"])
        self.assertEqual(lifecycle["proof-of-unrelated-change_reuse"], "unsupported-in-v2")
        self.assertEqual(lifecycle["recovery"], "rerun-narrowest-relevant-check")

    def test_claim_kinds_have_distinct_record_requirements(self) -> None:
        contract = load_contract()
        self.assertEqual(
            set(contract["enums"]["claim_kind"]),
            {"fact", "scoped-task", "high-assurance"},
        )
        conditions = contract["records"]["claim-record"]["conditional_fields"]
        self.assertEqual(
            conditions["fact"]["forbidden"],
            ["claim_boundary_digest", "review_id"],
        )
        self.assertEqual(conditions["scoped-task"]["required"], ["claim_boundary_digest"])
        self.assertEqual(conditions["high-assurance"]["required"], ["review_id"])

    def test_evidence_review_and_checkpoint_ownership_is_explicit(self) -> None:
        records = load_contract()["records"]
        self.assertEqual(records["development-evidence-record"]["producers"], ["feedback-loop"])
        self.assertEqual(records["claim-evidence-record"]["producers"], ["verify-before-claim"])
        self.assertEqual(records["review-record"]["producers"], ["two-axis-review"])
        self.assertEqual(set(records["checkpoint"]["producers"]), SKILL_NAMES)

    def test_boundary_runtime_policy_forbids_caller_digest_and_requires_recapture(self) -> None:
        policy = load_contract()["policies"]["boundary-runtime"]
        self.assertEqual(policy["caller_supplied_digest"], "forbidden")
        self.assertIn("second-identical-state-capture", policy["confirm_requires"])
        self.assertIn("state-drift", policy["fail_on"])
        runtime = (PROJECT_ROOT / "runtime" / "handrails_state.py").read_text(encoding="utf-8")
        self.assertNotIn("review_boundary_digest", runtime)

    def test_each_skill_has_standard_frontmatter_and_v2_binding(self) -> None:
        contract = load_contract()
        for name in sorted(SKILL_NAMES):
            with self.subTest(skill=name):
                skill_root = PROJECT_ROOT / "skills" / name
                text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
                frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
                self.assertIsNotNone(frontmatter)
                values = yaml.safe_load(frontmatter.group(1))
                self.assertEqual(set(values), {"name", "description"})
                self.assertEqual(values["name"], name)
                self.assertIn("contract: usable-loop/v2", text)
                self.assertIn(f"role: {contract['skills'][name]['role']}", text)
                reference = skill_root / "references" / "usable-loop-v2.md"
                self.assertTrue(reference.is_file())
                self.assertIn("Contract: usable-loop/v2", reference.read_text())

    def test_runtime_skills_are_standalone_and_generated(self) -> None:
        canonical = (PROJECT_ROOT / "runtime" / "handrails_state.py").read_bytes()
        for name in (
            "branch-sandbox",
            "feedback-loop",
            "two-axis-review",
            "verify-before-claim",
        ):
            with self.subTest(skill=name):
                local = PROJECT_ROOT / "skills" / name / "scripts" / "handrails_state.py"
                self.assertEqual(local.read_bytes(), canonical)
                completed = subprocess.run(
                    [sys.executable, str(local), "--help"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                self.assertIn("inventory", completed.stdout)

    def test_generated_contract_projections_are_current(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/render_contract.py", "--check"],
            cwd=PROJECT_ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_every_projection_preserves_authority_first_resume_order(self) -> None:
        for name in sorted(SKILL_NAMES):
            text = (PROJECT_ROOT / "skills" / name / "references" / "usable-loop-v2.md").read_text(
                encoding="utf-8"
            )
            outcome = text.index("first reconcile the designated Outcome Source/Revision")
            capsule = text.index("read the Capsule for orientation")
            state = text.index("recapture participating state")
            with self.subTest(skill=name):
                self.assertLess(outcome, capsule)
                self.assertLess(capsule, state)

    def test_openai_metadata_keeps_explicit_invocation_and_default_prompt(self) -> None:
        for name in sorted(SKILL_NAMES):
            with self.subTest(skill=name):
                metadata = yaml.safe_load(
                    (PROJECT_ROOT / "skills" / name / "agents" / "openai.yaml").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertFalse(metadata["policy"]["allow_implicit_invocation"])
                self.assertIn(f"${name}", metadata["interface"]["default_prompt"])
                self.assertLessEqual(len(metadata["interface"]["short_description"]), 64)

    def test_atomic_skill_promises_are_visible_in_main_instructions(self) -> None:
        required = {
            "branch-sandbox": ("explicit authorization", "report the cleanup command"),
            "feedback-loop": ("development evidence", "cannot support a completion claim"),
            "two-axis-review": ("Outcome Fit", "Review Record"),
            "verify-before-claim": ("`fact`", "`scoped-task`", "`high-assurance`"),
        }
        for name, terms in required.items():
            text = (PROJECT_ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            for term in terms:
                with self.subTest(skill=name, term=term):
                    self.assertIn(term, text)

    def test_fact_route_does_not_eagerly_load_full_contract(self) -> None:
        text = (PROJECT_ROOT / "skills" / "verify-before-claim" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("The `fact` and `scoped-task` routes below are self-contained", text)
        self.assertIn("claim_kind=fact", text)

    def test_scoped_route_uses_compact_runtime_without_source_inspection(self) -> None:
        text = (PROJECT_ROOT / "skills" / "verify-before-claim" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("The `fact` and `scoped-task` routes below are self-contained", text)
        self.assertIn("--compact --kind claim", text)
        self.assertIn("do **not** load the local reference, inspect runtime source", text)


if __name__ == "__main__":
    unittest.main()
