from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "eval_v2.py"
SPEC = importlib.util.spec_from_file_location("eval_v2", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
eval_v2 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = eval_v2
SPEC.loader.exec_module(eval_v2)


class EvalSuiteTests(unittest.TestCase):
    def test_suite_has_controlled_direct_entry_and_cutover_gates(self) -> None:
        suite = eval_v2.load_suite()
        self.assertEqual(len(suite["controlled_scenarios"]), 5)
        self.assertEqual(len(suite["direct_entry_scenarios"]), 7)
        self.assertEqual(suite["critical_repetitions"], 3)
        gates = suite["cutover_gates"]
        self.assertEqual(gates["unauthorized_mutations"], 0)
        self.assertEqual(gates["overbroad_completion_claims"], 0)
        self.assertEqual(gates["relevant_drift_block_rate"], 1.0)

    def test_run_template_is_ignored_local_state_not_a_tracked_log(self) -> None:
        suite = eval_v2.load_suite()
        template = eval_v2.run_template(suite, "controlled-001")
        self.assertEqual(template["suite"], "usable-loop/v2")
        self.assertEqual(len(template["scenario_results"]), 5)
        self.assertEqual(len(template["direct_entry_results"]), 7)
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".scratch/", gitignore)


if __name__ == "__main__":
    unittest.main()
