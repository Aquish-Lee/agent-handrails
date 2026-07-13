#!/usr/bin/env python3
"""Render/check the minimal Codex plugin package from canonical Raw Skills."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills"
PLUGIN_ROOT = ROOT / "plugins" / "agent-handrails"
DESTINATION = PLUGIN_ROOT / "skills"
MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
SKILL_NAMES = {
    "branch-sandbox",
    "feedback-loop",
    "grill",
    "plan-lite",
    "spec-lite",
    "two-axis-review",
    "verify-before-claim",
}


def _ignored(path: Path) -> bool:
    return "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if _ignored(path.relative_to(root)):
            continue
        relative = path.relative_to(root).as_posix().encode()
        if path.is_symlink():
            kind = b"L"
            content = os.readlink(path).encode()
        elif path.is_dir():
            kind = b"D"
            content = b""
        else:
            kind = b"F"
            content = path.read_bytes()
        for part in (kind, relative, str(path.lstat().st_mode & 0o111).encode(), content):
            digest.update(len(part).to_bytes(8, "big"))
            digest.update(part)
    return digest.hexdigest()


def validate_roots() -> None:
    if not MANIFEST.is_file():
        raise RuntimeError(f"plugin manifest is missing: {MANIFEST}")
    actual = {path.name for path in SOURCE.iterdir() if path.is_dir()}
    if actual != SKILL_NAMES:
        raise RuntimeError(f"canonical skill set differs: {sorted(actual)}")


def apply() -> None:
    validate_roots()
    if DESTINATION.is_symlink():
        raise RuntimeError(f"refusing to replace symlinked plugin skills: {DESTINATION}")
    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)
    DESTINATION.mkdir()
    for name in sorted(SKILL_NAMES):
        shutil.copytree(
            SOURCE / name,
            DESTINATION / name,
            symlinks=True,
            ignore=lambda _directory, names: {
                name
                for name in names
                if name == "__pycache__" or Path(name).suffix in {".pyc", ".pyo"}
            },
        )


def drift() -> list[str]:
    validate_roots()
    if DESTINATION.is_symlink() or not DESTINATION.is_dir():
        return ["skills directory missing or invalid"]
    actual = {path.name for path in DESTINATION.iterdir() if path.is_dir()}
    problems = []
    if actual != SKILL_NAMES:
        problems.append(
            f"skill set differs: missing={sorted(SKILL_NAMES - actual)}, "
            f"unexpected={sorted(actual - SKILL_NAMES)}"
        )
    for name in sorted(SKILL_NAMES & actual):
        if tree_digest(SOURCE / name) != tree_digest(DESTINATION / name):
            problems.append(f"skill differs: {name}")
    return problems


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        if arguments.apply:
            apply()
        problems = drift()
    except (OSError, RuntimeError) as error:
        print(f"plugin render failed: {error}", file=sys.stderr)
        return 2
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    print("Codex plugin package matches canonical Raw Skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
