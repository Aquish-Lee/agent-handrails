#!/usr/bin/env python3
"""Capture read-only mechanical Git state for usable-loop/v1.

This helper inventories facts and fingerprints bytes. It deliberately does not
decide whether a path is task-related or whether evidence remains sufficient.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence


CONTRACT_ID = "usable-loop/v1"
RECORD_NAME = "code-state-token"


class GitStateError(RuntimeError):
    """Raised when an exact, fail-honest capture cannot be produced."""


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def digest_json(value: object) -> str:
    return digest_bytes(canonical_json(value))


def _git(
    repository: Path,
    *arguments: str,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    completed = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repository), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise GitStateError(
            f"git {' '.join(arguments)} failed in {repository}: {detail or completed.returncode}"
        )
    return completed


def _git_text(repository: Path, *arguments: str, check: bool = True) -> str:
    return _git(repository, *arguments, check=check).stdout.decode(
        "utf-8",
        errors="strict",
    ).strip()


def _nul_paths(output: bytes) -> list[str]:
    return sorted(
        item.decode("utf-8", errors="surrogateescape")
        for item in output.split(b"\0")
        if item
    )


def _repository_root(path: Path) -> Path:
    candidate = Path(os.path.abspath(os.fspath(path)))
    root = _git_text(candidate, "rev-parse", "--show-toplevel")
    return Path(root)


def _resolve_commit(repository: Path, revision: str) -> str:
    completed = _git(
        repository,
        "rev-parse",
        "--verify",
        f"{revision}^{{commit}}",
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise GitStateError(f"cannot resolve commit {revision!r}: {detail}")
    return completed.stdout.decode("ascii").strip()


def _worktree_roots(repository: Path) -> set[Path]:
    output = _git_text(repository, "worktree", "list", "--porcelain")
    roots: set[Path] = set()
    for line in output.splitlines():
        if line.startswith("worktree "):
            roots.add(Path(line.removeprefix("worktree ")))
    return roots


def _committed_inventory(repository: Path, base_revision: str) -> list[dict[str, str]]:
    exact_revision = _resolve_commit(repository, "HEAD")
    output = _git(
        repository,
        "diff",
        "--name-status",
        "-z",
        "--find-renames",
        f"{base_revision}...{exact_revision}",
        "--",
    ).stdout
    items = [item for item in output.split(b"\0") if item]
    result: list[dict[str, str]] = []
    index = 0
    while index < len(items):
        status_text = items[index].decode("ascii", errors="strict")
        index += 1
        if index >= len(items):
            raise GitStateError("malformed git diff --name-status output")
        first_path = items[index].decode("utf-8", errors="surrogateescape")
        index += 1
        if status_text.startswith(("R", "C")):
            if index >= len(items):
                raise GitStateError("malformed Git rename/copy inventory")
            second_path = items[index].decode("utf-8", errors="surrogateescape")
            index += 1
            result.append(
                {
                    "path": second_path,
                    "previous_path": first_path,
                    "status": status_text,
                }
            )
        else:
            result.append({"path": first_path, "status": status_text})
    return sorted(result, key=lambda item: (item["path"], item["status"]))


def _workspace_capture(repository: Path, base_revision: str) -> dict[str, object]:
    root = _repository_root(repository)
    exact_revision = _resolve_commit(root, "HEAD")
    branch_process = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    branch = (
        branch_process.stdout.decode("utf-8", errors="strict").strip()
        if branch_process.returncode == 0
        else None
    )
    staged = _nul_paths(
        _git(root, "diff", "--cached", "--name-only", "-z", "--").stdout
    )
    unstaged = _nul_paths(_git(root, "diff", "--name-only", "-z", "--").stdout)
    untracked = _nul_paths(
        _git(root, "ls-files", "--others", "--exclude-standard", "-z", "--").stdout
    )
    conflicts = _nul_paths(
        _git(root, "diff", "--name-only", "--diff-filter=U", "-z", "--").stdout
    )
    staged_patch = _git(
        root,
        "diff",
        "--cached",
        "--binary",
        "--no-ext-diff",
        "--no-textconv",
        "HEAD",
        "--",
    ).stdout
    unstaged_patch = _git(
        root,
        "diff",
        "--binary",
        "--no-ext-diff",
        "--no-textconv",
        "--",
    ).stdout
    inventory = {
        "committed": _committed_inventory(root, base_revision),
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "declared_ignored": [],
    }
    tracked_material = {
        "exact_revision": exact_revision,
        "staged_patch": digest_bytes(staged_patch),
        "unstaged_patch": digest_bytes(unstaged_patch),
        "conflicts": conflicts,
    }
    return {
        "path": str(root),
        "git_dir": _git_text(root, "rev-parse", "--absolute-git-dir"),
        "branch": branch,
        "exact_revision": exact_revision,
        "conflict_paths": conflicts,
        "candidate_inventory": inventory,
        "tracked_state_fingerprint": digest_json(tracked_material),
    }


def _lexical_absolute(path: Path, primary_root: Path) -> Path:
    candidate = path if path.is_absolute() else primary_root / path
    return Path(os.path.abspath(os.fspath(candidate)))


def _owning_worktree(path: Path, worktrees: Sequence[Path]) -> tuple[Path, str]:
    matches: list[tuple[int, Path, str]] = []
    for root in worktrees:
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        matches.append((len(root.parts), root, relative.as_posix()))
    if not matches:
        raise GitStateError(f"artifact is outside participating worktrees: {path}")
    _, root, relative = max(matches, key=lambda match: match[0])
    if not relative or relative == "." or relative == ".git" or relative.startswith(".git/"):
        raise GitStateError(f"artifact path is not a reviewable worktree artifact: {path}")
    return root, relative


def _artifact_entries(path: Path) -> list[dict[str, str]]:
    try:
        mode = path.lstat().st_mode
    except OSError as error:
        raise GitStateError(f"cannot fingerprint artifact {path}: {error}") from error
    if stat.S_ISLNK(mode):
        return [
            {
                "path": ".",
                "kind": "symlink",
                "digest": digest_bytes(os.fsencode(os.readlink(path))),
            }
        ]
    if stat.S_ISREG(mode):
        try:
            content = path.read_bytes()
        except OSError as error:
            raise GitStateError(f"cannot read artifact {path}: {error}") from error
        return [{"path": ".", "kind": "file", "digest": digest_bytes(content)}]
    if not stat.S_ISDIR(mode):
        raise GitStateError(f"unsupported artifact type: {path}")

    entries: list[dict[str, str]] = []
    for directory, directory_names, file_names in os.walk(path, followlinks=False):
        directory_path = Path(directory)
        directory_names.sort()
        file_names.sort()
        for name in list(directory_names):
            child = directory_path / name
            if child.is_symlink():
                entries.append(
                    {
                        "path": child.relative_to(path).as_posix(),
                        "kind": "symlink",
                        "digest": digest_bytes(os.fsencode(os.readlink(child))),
                    }
                )
                directory_names.remove(name)
        for name in file_names:
            child = directory_path / name
            relative = child.relative_to(path).as_posix()
            if child.is_symlink():
                entries.append(
                    {
                        "path": relative,
                        "kind": "symlink",
                        "digest": digest_bytes(os.fsencode(os.readlink(child))),
                    }
                )
            else:
                try:
                    content = child.read_bytes()
                except OSError as error:
                    raise GitStateError(f"cannot read artifact {child}: {error}") from error
                entries.append(
                    {"path": relative, "kind": "file", "digest": digest_bytes(content)}
                )
    return entries


def _fingerprint_artifact(
    artifact: Path,
    primary_root: Path,
    worktrees: Sequence[Path],
    expected_channel: str,
) -> dict[str, str]:
    absolute = _lexical_absolute(artifact, primary_root)
    root, relative = _owning_worktree(absolute, worktrees)
    ignored_process = _git(root, "check-ignore", "--quiet", "--", relative, check=False)
    is_ignored = ignored_process.returncode == 0
    untracked = set(
        _nul_paths(
            _git(root, "ls-files", "--others", "--exclude-standard", "-z", "--").stdout
        )
    )
    is_untracked = relative in untracked or any(
        candidate.startswith(f"{relative.rstrip('/')}/") for candidate in untracked
    )
    if expected_channel == "untracked":
        if is_ignored:
            raise GitStateError(
                f"ignored artifact must use the explicit declared-ignored channel: {relative}"
            )
        if not is_untracked:
            raise GitStateError(f"included-untracked artifact is not untracked: {relative}")
    elif not is_ignored:
        raise GitStateError(f"declared ignored artifact is not ignored by Git: {relative}")
    entries = _artifact_entries(absolute)
    kind = "directory" if absolute.is_dir() and not absolute.is_symlink() else entries[0]["kind"]
    return {
        "workspace": str(root),
        "path": relative,
        "kind": kind,
        "digest": digest_json(entries),
    }


def capture_git_state(
    repository: Path,
    base: str = "HEAD",
    review_boundary_digest: str = "unconfirmed",
    included_untracked: Iterable[Path] = (),
    declared_ignored: Iterable[Path] = (),
    participating_worktrees: Iterable[Path] = (),
    relevant_environment: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Return a deterministic state token plus a non-deterministic capture time."""

    primary_root = _repository_root(Path(repository))
    base_revision = _resolve_commit(primary_root, base)
    requested = list(participating_worktrees) or [primary_root]
    roots = sorted({_repository_root(Path(path)) for path in requested}, key=str)
    if primary_root not in roots:
        roots.insert(0, primary_root)
    known_roots = _worktree_roots(primary_root)
    unknown = [root for root in roots if root not in known_roots]
    if unknown:
        raise GitStateError(f"not a linked Git worktree: {unknown[0]}")

    common_dir_text = _git_text(primary_root, "rev-parse", "--git-common-dir")
    common_dir = Path(common_dir_text)
    if not common_dir.is_absolute():
        common_dir = primary_root / common_dir
    common_dir = Path(os.path.abspath(os.fspath(common_dir)))
    for root in roots:
        candidate_text = _git_text(root, "rev-parse", "--git-common-dir")
        candidate = Path(candidate_text)
        if not candidate.is_absolute():
            candidate = root / candidate
        if Path(os.path.abspath(os.fspath(candidate))) != common_dir:
            raise GitStateError(f"participating worktree belongs to another repository: {root}")

    workspace_captures = [_workspace_capture(root, base_revision) for root in roots]
    untracked_fingerprints = sorted(
        (
            _fingerprint_artifact(
                Path(path),
                primary_root,
                roots,
                "untracked",
            )
            for path in included_untracked
        ),
        key=lambda item: (item["workspace"], item["path"]),
    )
    ignored_fingerprints = sorted(
        (
            _fingerprint_artifact(
                Path(path),
                primary_root,
                roots,
                "ignored",
            )
            for path in declared_ignored
        ),
        key=lambda item: (item["workspace"], item["path"]),
    )

    for capture in workspace_captures:
        workspace_path = capture["path"]
        capture["candidate_inventory"]["declared_ignored"] = [
            item["path"]
            for item in ignored_fingerprints
            if item["workspace"] == workspace_path
        ]

    worktree_fingerprints: list[dict[str, str]] = []
    for capture in workspace_captures:
        workspace_path = capture["path"]
        material = {
            "exact_revision": capture["exact_revision"],
            "tracked_state_fingerprint": capture["tracked_state_fingerprint"],
            "candidate_inventory": capture["candidate_inventory"],
            "included_untracked": [
                item
                for item in untracked_fingerprints
                if item["workspace"] == workspace_path
            ],
            "declared_ignored": [
                item
                for item in ignored_fingerprints
                if item["workspace"] == workspace_path
            ],
        }
        worktree_fingerprints.append(
            {"workspace": str(workspace_path), "digest": digest_json(material)}
        )

    tracked_state_fingerprint = digest_json(
        [
            {
                "workspace": capture["path"],
                "digest": capture["tracked_state_fingerprint"],
            }
            for capture in workspace_captures
        ]
    )
    conflict_paths = sorted(
        {
            f"{capture['path']}::{path}"
            for capture in workspace_captures
            for path in capture["conflict_paths"]
        }
    )
    primary_capture = next(
        capture for capture in workspace_captures if capture["path"] == str(primary_root)
    )
    candidate_inventory = dict(primary_capture["candidate_inventory"])
    candidate_inventory["by_workspace"] = [
        {
            "workspace": capture["path"],
            "inventory": capture["candidate_inventory"],
        }
        for capture in workspace_captures
    ]
    object_format_process = _git(
        primary_root,
        "rev-parse",
        "--show-object-format",
        check=False,
    )
    object_format = (
        object_format_process.stdout.decode("ascii").strip()
        if object_format_process.returncode == 0
        else "sha1"
    )
    environment = dict(sorted((relevant_environment or {}).items()))
    if not all(isinstance(key, str) and isinstance(value, str) for key, value in environment.items()):
        raise GitStateError("relevant_environment keys and values must be strings")
    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )
    return {
        "contract": CONTRACT_ID,
        "record": RECORD_NAME,
        "provider": "git",
        "repository_identity": {
            "common_dir": str(common_dir),
            "object_format": object_format,
        },
        "workspace_identity": {
            "path": str(primary_root),
            "git_dir": primary_capture["git_dir"],
        },
        "base_revision": base_revision,
        "exact_revision": primary_capture["exact_revision"],
        "recovery_identity": primary_capture["branch"] or primary_capture["exact_revision"],
        "conflict_state": {"present": bool(conflict_paths), "paths": conflict_paths},
        "review_boundary_digest": review_boundary_digest,
        "tracked_state_fingerprint": tracked_state_fingerprint,
        "candidate_inventory": candidate_inventory,
        "included_untracked_fingerprints": untracked_fingerprints,
        "declared_ignored_fingerprints": ignored_fingerprints,
        "participating_worktrees": workspace_captures,
        "participating_worktree_fingerprints": worktree_fingerprints,
        "relevant_environment": environment,
        "captured_at": captured_at,
    }


def parse_environment(values: Sequence[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        key, separator, item = value.partition("=")
        if not separator or not key:
            raise GitStateError(f"environment must use KEY=VALUE: {value!r}")
        result[key] = item
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Capture read-only mechanical Git state for usable-loop/v1; "
            "semantic task relevance is intentionally out of scope."
        )
    )
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("--review-boundary-digest", default="unconfirmed")
    parser.add_argument("--include-untracked", action="append", type=Path, default=[])
    parser.add_argument("--declare-ignored", action="append", type=Path, default=[])
    parser.add_argument("--participating-worktree", action="append", type=Path, default=[])
    parser.add_argument("--environment", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_args(argv)
    try:
        token = capture_git_state(
            repository=arguments.repository,
            base=arguments.base,
            review_boundary_digest=arguments.review_boundary_digest,
            included_untracked=arguments.include_untracked,
            declared_ignored=arguments.declare_ignored,
            participating_worktrees=arguments.participating_worktree,
            relevant_environment=parse_environment(arguments.environment),
        )
    except GitStateError as error:
        print(f"git-state capture failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(token, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
