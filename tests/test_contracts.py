from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate.py"
SPEC = importlib.util.spec_from_file_location("contract_validator", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)

CONTRACT_PATH = PROJECT_ROOT / "contracts" / "usable-loop-v1.json"
SKILL_NAMES = {
    "branch-sandbox",
    "feedback-loop",
    "grill",
    "plan-lite",
    "spec-lite",
    "two-axis-review",
    "verify-before-claim",
}
OUTCOME_FIELDS = {
    "contract",
    "task_id",
    "source_kind",
    "source_id",
    "source_locator",
    "outcome_revision",
    "revision_basis",
    "authority",
    "authority_basis",
    "lifecycle",
    "snapshot",
    "currentness",
    "stale_when",
}


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def contract_block(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"<!-- handrails-contract\n(?P<body>.*?)\n-->",
        text,
        flags=re.DOTALL,
    )
    if match is None:
        return {}
    result: dict[str, str] = {}
    for line in match.group("body").splitlines():
        key, separator, value = line.partition(":")
        if separator:
            result[key.strip()] = value.strip()
    return result


class UsableLoopContractTests(unittest.TestCase):
    def test_optional_spec_paths_share_one_outcome_reference_shape(self) -> None:
        contract = load_contract()
        records = contract["records"]
        paths = contract["composition_paths"]
        self.assertIsInstance(records, dict)
        self.assertIsInstance(paths, dict)
        outcome = records["outcome-reference"]
        self.assertTrue(OUTCOME_FIELDS.issubset(outcome["required_fields"]))
        self.assertEqual(
            {paths[name]["record"] for name in ("no-spec", "with-spec")},
            {"outcome-reference"},
        )
        self.assertEqual(paths["no-spec"]["consumer"], "plan-lite")
        self.assertEqual(paths["with-spec"]["consumer"], "plan-lite")

    def test_task1_activates_only_records_projected_by_current_skills(self) -> None:
        records = load_contract()["records"]
        active = {
            name
            for name, declaration in records.items()
            if declaration["availability"] == "active"
        }
        self.assertEqual(
            active,
            {
                "outcome-reference",
                "alignment-snapshot",
                "outcome-contract",
                "implementation-plan",
                "review-boundary-seed",
            },
        )

    def test_every_handrail_can_bootstrap_a_provisional_reference(self) -> None:
        contract = load_contract()
        self.assertEqual(set(contract["skills"]), SKILL_NAMES)
        for name, declaration in contract["skills"].items():
            with self.subTest(skill=name):
                self.assertEqual(
                    declaration["missing_outcome_reference"],
                    "bootstrap-provisional",
                )
                self.assertEqual(
                    declaration["authority_failure"],
                    "stale-until-reconfirmed",
                )
                self.assertIn("outcome-reference", declaration["produces"])
                local = contract_block(PROJECT_ROOT / "skills" / name / "SKILL.md")
                self.assertEqual(local.get("contract"), "usable-loop/v1")
                self.assertEqual(local.get("role"), declaration["role"])
                self.assertEqual(
                    local.get("missing-outcome-reference"),
                    declaration["missing_outcome_reference"],
                )
                self.assertEqual(
                    local.get("authority-failure"),
                    declaration["authority_failure"],
                )
                self.assertEqual(local.get("outcome-record"), "outcome-reference")

    def test_authority_failure_stales_evidence_and_claims(self) -> None:
        contract = load_contract()
        policy = contract["policies"]["authority-failure"]
        self.assertEqual(
            set(policy["triggers"]),
            {
                "authority-inaccessible",
                "authority-conflict",
                "authority-revision-mismatch",
            },
        )
        self.assertEqual(policy["effects"]["dependent_evidence"], "stale")
        self.assertEqual(policy["effects"]["dependent_claims"], "stale")
        self.assertIn(
            policy["effects"]["outcome_currentness"],
            contract["enums"]["outcome_freshness"],
        )
        self.assertEqual(policy["recovery"], "reconcile-or-reconfirm")

    def test_revision_and_ignored_artifact_policies_are_fail_honest(self) -> None:
        policies = load_contract()["policies"]
        self.assertEqual(
            policies["revision-integrity"],
            {
                "enum": "revision_digest_claim",
                "default": "computed-only",
                "fallback": "task-local-opaque-revision",
            },
        )
        self.assertEqual(
            policies["ignored-artifact-declaration"]["default"],
            "explicit-only",
        )

    def test_repository_contract_metadata_is_consistent(self) -> None:
        self.assertEqual(validator.contract_errors(PROJECT_ROOT), [])

    def test_validator_rejects_invalid_skill_contract_metadata(self) -> None:
        mutations = {
            "missing-contract-marker": lambda text: re.sub(
                r"\n<!-- handrails-contract\n.*?\n-->\n",
                "\n",
                text,
                count=1,
                flags=re.DOTALL,
            ),
            "missing-contract-role": lambda text: text.replace(
                "role: outcome-aligner\n",
                "",
                1,
            ),
            "contract-role-mismatch": lambda text: text.replace(
                "role: outcome-aligner",
                "role: execution-planner",
                1,
            ),
            "invalid-contract-enum": lambda text: text.replace(
                "authority-failure: stale-until-reconfirmed",
                "authority-failure: keep-current",
                1,
            ),
            "unknown-contract-record": lambda text: text.replace(
                "outcome-record: outcome-reference",
                "outcome-record: imaginary-record",
                1,
            ),
        }
        for expected_code, mutate in mutations.items():
            with self.subTest(expected_code=expected_code):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    shutil.copytree(PROJECT_ROOT / "contracts", root / "contracts")
                    shutil.copytree(PROJECT_ROOT / "skills", root / "skills")
                    skill_file = root / "skills" / "grill" / "SKILL.md"
                    skill_file.write_text(
                        mutate(skill_file.read_text(encoding="utf-8")),
                        encoding="utf-8",
                    )
                    codes = {issue.code for issue in validator.contract_errors(root)}
                    self.assertIn(expected_code, codes)

    def test_validator_rejects_catalog_projection_and_ownership_drift(self) -> None:
        mutations = {
            "contract-record-fields-mismatch": lambda contract: contract["records"][
                "outcome-reference"
            ]["required_fields"].append("new_required_field"),
            "contract-record-availability-mismatch": lambda contract: contract[
                "skills"
            ]["grill"]["produces"].append("checkpoint"),
        }
        for expected_code, mutate in mutations.items():
            with self.subTest(expected_code=expected_code):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    shutil.copytree(PROJECT_ROOT / "contracts", root / "contracts")
                    shutil.copytree(PROJECT_ROOT / "skills", root / "skills")
                    path = root / "contracts" / "usable-loop-v1.json"
                    contract = json.loads(path.read_text(encoding="utf-8"))
                    mutate(contract)
                    path.write_text(
                        json.dumps(contract, indent=2) + "\n",
                        encoding="utf-8",
                    )

                    codes = {issue.code for issue in validator.contract_errors(root)}

                    self.assertIn(expected_code, codes)

    def test_validator_reports_malformed_nested_types_without_crashing(self) -> None:
        mutations = {
            "invalid-contract-enum": lambda contract: contract["enums"].__setitem__(
                "record_availability",
                7,
            ),
            "unknown-contract-skill-reference": lambda contract: contract["records"][
                "alignment-snapshot"
            ].__setitem__("producers", 7),
            "unknown-contract-record": lambda contract: contract["skills"][
                "grill"
            ].__setitem__("produces", 7),
        }
        for expected_code, mutate in mutations.items():
            with self.subTest(expected_code=expected_code):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    shutil.copytree(PROJECT_ROOT / "contracts", root / "contracts")
                    shutil.copytree(PROJECT_ROOT / "skills", root / "skills")
                    path = root / "contracts" / "usable-loop-v1.json"
                    contract = json.loads(path.read_text(encoding="utf-8"))
                    mutate(contract)
                    path.write_text(json.dumps(contract) + "\n", encoding="utf-8")

                    codes = {issue.code for issue in validator.contract_errors(root)}

                    self.assertIn(expected_code, codes)

    def test_each_skill_is_self_contained_when_copied_alone(self) -> None:
        for name in sorted(SKILL_NAMES):
            with self.subTest(skill=name):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    copy = Path(temporary_directory) / name
                    shutil.copytree(PROJECT_ROOT / "skills" / name, copy)
                    self.assertEqual(validator.standalone_skill_errors(copy), [])

    def test_standalone_skill_rejects_external_required_resource(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            copy = root / "grill"
            shutil.copytree(PROJECT_ROOT / "skills" / "grill", copy)
            (root / "shared-contract.md").write_text("external\n", encoding="utf-8")
            skill_file = copy / "SKILL.md"
            skill_file.write_text(
                skill_file.read_text(encoding="utf-8").replace(
                    "required-local-resources: none",
                    "required-local-resources: ../shared-contract.md",
                    1,
                ),
                encoding="utf-8",
            )

            codes = {
                issue.code for issue in validator.standalone_skill_errors(copy)
            }

            self.assertIn("external-required-resource", codes)

    def test_first_three_skills_expose_outcome_reference_fields(self) -> None:
        labels = {
            "Task ID:",
            "Outcome Source kind:",
            "Outcome Source ID:",
            "Outcome Source locator:",
            "Outcome Revision:",
            "Revision basis:",
            "Outcome Authority:",
            "Authority basis:",
            "Outcome lifecycle:",
            "Outcome snapshot:",
            "Outcome currentness:",
            "Stale when:",
        }
        for name in ("grill", "spec-lite", "plan-lite"):
            with self.subTest(skill=name):
                text = (PROJECT_ROOT / "skills" / name / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                missing = sorted(label for label in labels if label not in text)
                self.assertEqual(missing, [])

    def test_plan_emits_review_boundary_seed_fields(self) -> None:
        text = (PROJECT_ROOT / "skills" / "plan-lite" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        for label in (
            "Expected logical changes:",
            "Dependent or generated changes:",
            "Authorization guardrails:",
            "Known pre-existing changes:",
            "Participating workspaces:",
            "Base and recovery hints:",
            "Open boundary questions:",
        ):
            self.assertIn(label, text)


if __name__ == "__main__":
    unittest.main()
