#!/usr/bin/env python3
"""Validate the v2 dogfood suite and initialize ignored local run records."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITE_PATH = ROOT / "evals" / "usable-loop-v2" / "scenarios.json"
RESULT_ROOT = ROOT / ".scratch" / "dogfood-v2"
SKILLS = {
    "branch-sandbox",
    "feedback-loop",
    "grill",
    "plan-lite",
    "spec-lite",
    "two-axis-review",
    "verify-before-claim",
}


def load_suite() -> dict[str, object]:
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    if suite.get("suite") != "usable-loop/v2":
        raise ValueError("suite must be usable-loop/v2")
    controlled = suite.get("controlled_scenarios")
    direct = suite.get("direct_entry_scenarios")
    if not isinstance(controlled, list) or len(controlled) != 5:
        raise ValueError("exactly five controlled scenarios are required")
    ids = [scenario.get("id") for scenario in controlled]
    if len(set(ids)) != len(ids) or not all(isinstance(value, str) for value in ids):
        raise ValueError("controlled scenario IDs must be unique strings")
    if not isinstance(direct, list) or {item.get("skill") for item in direct} != SKILLS:
        raise ValueError("direct-entry scenarios must cover all seven skills")
    if suite.get("critical_repetitions") != 3:
        raise ValueError("critical scenarios require three repetitions")
    return suite


def run_template(suite: dict[str, object], run_id: str) -> dict[str, object]:
    scenario_ids = [item["id"] for item in suite["controlled_scenarios"]]
    return {
        "suite": suite["suite"],
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "project": None,
        "model_surface": None,
        "scenario_results": {
            scenario_id: {
                "status": "blocked",
                "evidence": [],
                "defects": [],
                "notes": "not run",
            }
            for scenario_id in scenario_ids
        },
        "direct_entry_results": {
            skill: [] for skill in sorted(SKILLS)
        },
        "gate_summary": {},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--list", action="store_true")
    mode.add_argument("--init-run", metavar="RUN_ID")
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        suite = load_suite()
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(f"invalid v2 eval suite: {error}", file=sys.stderr)
        return 1
    if arguments.check:
        print("usable-loop/v2 eval suite is valid")
        return 0
    if arguments.list:
        for scenario in suite["controlled_scenarios"]:
            print(f"{scenario['id']}: ${scenario['target_skill']}")
        return 0
    run_id = arguments.init_run
    if not run_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in run_id):
        print("RUN_ID may contain only letters, digits, hyphen, and underscore", file=sys.stderr)
        return 2
    destination = RESULT_ROOT / run_id / "result.json"
    if destination.exists():
        print(f"run already exists: {destination}", file=sys.stderr)
        return 2
    destination.parent.mkdir(parents=True, exist_ok=False)
    destination.write_text(
        json.dumps(run_template(suite, run_id), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
