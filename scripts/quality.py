#!/usr/bin/env python3
"""Run the complete versioned local quality and packaging gate."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = (
    "branch-sandbox",
    "feedback-loop",
    "grill",
    "plan-lite",
    "spec-lite",
    "two-axis-review",
    "verify-before-claim",
)


def run(command: list[str]) -> None:
    print(f"+ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-official-skills",
        action="store_true",
        help="skip pinned agentskills validation (only for Python 3.10/advisory CI)",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    python = sys.executable
    commands = [
        [python, "-m", "unittest", "discover", "-s", "tests", "-v"],
        [python, "scripts/validate.py"],
        [python, "scripts/render_contract.py", "--check"],
        [python, "scripts/render_plugin.py", "--check"],
        [python, "scripts/eval_v2.py", "--check"],
        [python, "-m", "ruff", "check", "."],
        [python, "-m", "ruff", "format", "--check", "."],
        [
            python,
            "-m",
            "bandit",
            "-q",
            "-c",
            "pyproject.toml",
            "-r",
            "runtime/handrails_state.py",
            "runtime/safe_diff.py",
            "scripts",
        ],
    ]
    try:
        for command in commands:
            run(command)
        if not arguments.skip_official_skills:
            uvx = shutil.which("uvx")
            if uvx is None:
                raise RuntimeError("uvx is required for pinned official Skill validation")
            for skill in SKILLS:
                run(
                    [
                        uvx,
                        "--from",
                        "skills-ref==0.1.1",
                        "agentskills",
                        "validate",
                        f"skills/{skill}",
                    ]
                )
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"quality gate failed: {error}", file=sys.stderr)
        return 1
    print("Agent Handrails local quality gate PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
