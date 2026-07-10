#!/usr/bin/env python3
"""Deploy Agent Handrails skills from the project checkout to a local skills root."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "skills"
DEFAULT_TARGET = Path(
    os.environ.get("AGENT_HANDRAILS_SKILLS_DIR", "~/Workspace/Skills")
).expanduser()
DEFAULT_CODEX_LINK_ROOT = Path("~/.agents/skills").expanduser()
SKILL_NAMES = (
    "branch-sandbox",
    "feedback-loop",
    "grill",
    "plan-lite",
    "spec-lite",
    "two-axis-review",
    "verify-before-claim",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check or deploy the repository's canonical handrails, with optional "
            "Codex discovery symlinks."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help="compare deployed copies with the project source; do not write",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="atomically replace managed skill copies that differ",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help=f"deployment root (default: {DEFAULT_TARGET})",
    )
    parser.add_argument(
        "--codex-link-root",
        type=Path,
        help=(
            "also check/create Codex discovery symlinks, normally "
            f"{DEFAULT_CODEX_LINK_ROOT}"
        ),
    )
    return parser.parse_args()


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            digest.update(b"L\0")
            digest.update(relative.encode())
            digest.update(b"\0")
            digest.update(os.readlink(path).encode())
        elif path.is_file():
            digest.update(b"F\0")
            digest.update(relative.encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def validate_source() -> None:
    actual = {path.name for path in SOURCE_ROOT.iterdir() if path.is_dir()}
    expected = set(SKILL_NAMES)
    if actual != expected:
        raise RuntimeError(
            "canonical skill set differs from deployment manifest: "
            f"missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )

    for name in SKILL_NAMES:
        skill_file = SOURCE_ROOT / name / "SKILL.md"
        if not skill_file.is_file():
            raise RuntimeError(f"missing canonical skill file: {skill_file}")
        match = re.search(r"(?m)^name:\s*([^\n]+)$", skill_file.read_text())
        declared = match.group(1).strip().strip('"') if match else None
        if declared != name:
            raise RuntimeError(
                f"{skill_file}: declares name={declared!r}, expected {name!r}"
            )


def path_exists(path: Path) -> bool:
    return os.path.lexists(path)


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def compare(source: Path, target: Path) -> str:
    if not path_exists(target):
        return "missing"
    if target.is_symlink() or not target.is_dir():
        return "unmanaged-path-type"
    return "up-to-date" if tree_digest(source) == tree_digest(target) else "different"


def link_state(link: Path, deployed_target: Path) -> str:
    if not path_exists(link):
        return "missing"
    if not link.is_symlink():
        return "unmanaged-path-type"
    return (
        "up-to-date"
        if link.resolve(strict=False) == deployed_target.resolve(strict=False)
        else "different-target"
    )


def ensure_link(link: Path, deployed_target: Path) -> str:
    state = link_state(link, deployed_target)
    if state == "up-to-date":
        return state
    if state != "missing":
        raise RuntimeError(
            f"refusing to replace existing Codex discovery path: {link} ({state})"
        )
    link.symlink_to(deployed_target, target_is_directory=True)
    if link_state(link, deployed_target) != "up-to-date":
        link.unlink(missing_ok=True)
        raise RuntimeError(f"Codex discovery link verification failed: {link}")
    return "linked"


def deploy_one(source: Path, target: Path, target_root: Path) -> str:
    state = compare(source, target)
    if state == "up-to-date":
        return "up-to-date"
    if state == "unmanaged-path-type":
        raise RuntimeError(
            f"refusing to replace non-directory or symlink target: {target}"
        )

    container = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.staging-", dir=target_root)
    )
    staged = container / target.name
    backup: Path | None = None
    target_replaced = False
    try:
        shutil.copytree(source, staged, symlinks=True)
        if tree_digest(source) != tree_digest(staged):
            raise RuntimeError(f"staged copy verification failed for {target.name}")

        if path_exists(target):
            backup_path = target_root / f".{target.name}.backup-{uuid.uuid4().hex}"
            os.replace(target, backup_path)
            backup = backup_path
        os.replace(staged, target)
        target_replaced = True

        if tree_digest(source) != tree_digest(target):
            raise RuntimeError(f"deployed copy verification failed for {target.name}")
    except Exception:
        if target_replaced and path_exists(target):
            remove_path(target)
        if backup is not None and path_exists(backup):
            os.replace(backup, target)
        raise
    finally:
        if container.exists():
            shutil.rmtree(container)

    if backup is not None:
        shutil.rmtree(backup)
    return "installed" if state == "missing" else "updated"


def main() -> int:
    args = parse_args()
    target_root = args.target.expanduser().resolve()
    codex_link_root = (
        args.codex_link_root.expanduser().resolve()
        if args.codex_link_root is not None
        else None
    )

    try:
        validate_source()
    except (OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.check:
        all_current = True
        for name in SKILL_NAMES:
            state = compare(SOURCE_ROOT / name, target_root / name)
            print(f"{name}: {state}")
            all_current = all_current and state == "up-to-date"
        if codex_link_root is not None:
            for name in SKILL_NAMES:
                state = link_state(codex_link_root / name, target_root / name)
                print(f"codex-link/{name}: {state}")
                all_current = all_current and state == "up-to-date"
        return 0 if all_current else 1

    target_root.mkdir(parents=True, exist_ok=True)
    try:
        for name in SKILL_NAMES:
            state = deploy_one(SOURCE_ROOT / name, target_root / name, target_root)
            print(f"{name}: {state}")
    except (OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if codex_link_root is not None:
        codex_link_root.mkdir(parents=True, exist_ok=True)
        try:
            for name in SKILL_NAMES:
                state = ensure_link(codex_link_root / name, target_root / name)
                print(f"codex-link/{name}: {state}")
        except (OSError, RuntimeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    remaining = [
        name
        for name in SKILL_NAMES
        if compare(SOURCE_ROOT / name, target_root / name) != "up-to-date"
    ]
    if remaining:
        print(f"ERROR: deployment verification failed: {remaining}", file=sys.stderr)
        return 2

    if codex_link_root is not None:
        bad_links = [
            name
            for name in SKILL_NAMES
            if link_state(codex_link_root / name, target_root / name)
            != "up-to-date"
        ]
        if bad_links:
            print(
                f"ERROR: Codex link verification failed: {bad_links}",
                file=sys.stderr,
            )
            return 2

    print(f"Deployment verified: {target_root}")
    if codex_link_root is not None:
        print(f"Codex discovery links verified: {codex_link_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
