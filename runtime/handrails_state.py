#!/usr/bin/env python3
"""Deterministic Git boundary runtime for usable-loop/v2.

The runtime inventories bytes and validates caller-supplied semantic
classifications. It never decides task relevance and never accepts a naked
Boundary Digest from its caller.
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

CONTRACT_ID = "usable-loop/v2"
SCHEMA_VERSION = 2
AUTHORIZATION_STATES = {"authorized", "needs-authorization", "not-applicable"}
CLASSIFICATIONS = {
    "claim": {"include-claim", "exclude-proven-unrelated"},
    "review": {
        "include-required",
        "include-scope-creep",
        "include-inherited-dependency",
        "exclude-proven-unrelated",
    },
}


class BoundaryError(RuntimeError):
    """Raised when a deterministic boundary cannot be confirmed."""


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


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
        raise BoundaryError(
            f"git {' '.join(arguments)} failed in {repository}: {detail or completed.returncode}"
        )
    return completed


def _git_text(repository: Path, *arguments: str, check: bool = True) -> str:
    return _git(repository, *arguments, check=check).stdout.decode("utf-8", errors="strict").strip()


def _root(path: Path) -> Path:
    lexical = Path(os.path.abspath(os.fspath(path)))
    return Path(_git_text(lexical, "rev-parse", "--show-toplevel"))


def _resolve(repository: Path, revision: str) -> str:
    completed = _git(repository, "rev-parse", "--verify", f"{revision}^{{commit}}", check=False)
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise BoundaryError(f"cannot resolve commit {revision!r}: {detail}")
    return completed.stdout.decode("ascii").strip()


def _nul_paths(output: bytes) -> list[str]:
    return sorted(
        item.decode("utf-8", errors="surrogateescape") for item in output.split(b"\0") if item
    )


def _common_dir(repository: Path) -> Path:
    raw = Path(_git_text(repository, "rev-parse", "--git-common-dir"))
    if not raw.is_absolute():
        raw = repository / raw
    return Path(os.path.abspath(os.fspath(raw)))


def _known_worktrees(repository: Path) -> set[Path]:
    roots: set[Path] = set()
    for line in _git_text(repository, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            roots.add(Path(line.removeprefix("worktree ")))
    return roots


def _prepare_roots(
    repository: Path,
    participating_worktrees: Iterable[Path],
) -> tuple[Path, list[Path], Path]:
    primary = _root(repository)
    requested = list(participating_worktrees) or [primary]
    roots = sorted({_root(Path(item)) for item in requested} | {primary}, key=str)
    known = _known_worktrees(primary)
    for root in roots:
        if root not in known:
            raise BoundaryError(f"not a linked Git worktree: {root}")
    common = _common_dir(primary)
    for root in roots:
        if _common_dir(root) != common:
            raise BoundaryError(f"participating worktree belongs to another repository: {root}")
    return primary, roots, common


def _artifact_entries(path: Path) -> list[dict[str, str]]:
    try:
        mode = path.lstat().st_mode
    except OSError as error:
        raise BoundaryError(f"cannot fingerprint artifact {path}: {error}") from error
    if stat.S_ISLNK(mode):
        return [
            {
                "path": ".",
                "kind": "symlink",
                "digest": digest_bytes(os.fsencode(os.readlink(path))),
            }
        ]
    if stat.S_ISREG(mode):
        return [{"path": ".", "kind": "file", "digest": digest_bytes(path.read_bytes())}]
    if not stat.S_ISDIR(mode):
        raise BoundaryError(f"unsupported artifact type: {path}")
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
                digest = digest_bytes(os.fsencode(os.readlink(child)))
                kind = "symlink"
            else:
                digest = digest_bytes(child.read_bytes())
                kind = "file"
            entries.append({"path": relative, "kind": kind, "digest": digest})
    return entries


def _candidate_id(workspace: str, layer: str, path: str, fingerprint: str) -> str:
    material = {
        "workspace": workspace,
        "layer": layer,
        "path": path,
        "fingerprint": fingerprint,
    }
    return f"candidate:{digest_json(material)}"


def _hunks(
    patch: bytes,
    *,
    candidate_id: str,
    workspace: str,
    layer: str,
    path: str,
) -> list[dict[str, object]]:
    lines = patch.splitlines(keepends=True)
    chunks: list[list[bytes]] = []
    current: list[bytes] | None = None
    for line in lines:
        if line.startswith(b"@@ "):
            if current is not None:
                chunks.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        chunks.append(current)
    if not chunks and patch:
        chunks = [[patch]]
    result: list[dict[str, object]] = []
    for ordinal, chunk in enumerate(chunks, start=1):
        raw = b"".join(chunk)
        fingerprint = digest_bytes(raw)
        material = {
            "workspace": workspace,
            "layer": layer,
            "path": path,
            "fingerprint": fingerprint,
            "ordinal": ordinal,
        }
        header = chunk[0].decode("utf-8", errors="replace").rstrip("\r\n")
        result.append(
            {
                "hunk_id": f"hunk:{digest_json(material)}",
                "candidate_id": candidate_id,
                "ordinal": ordinal,
                "header": header,
                "fingerprint": fingerprint,
            }
        )
    return result


def _tracked_candidates(
    workspace: Path,
    layer: str,
    base_revision: str,
) -> list[dict[str, object]]:
    if layer == "committed":
        selector = [f"{base_revision}...HEAD"]
    elif layer == "staged":
        selector = ["--cached", "HEAD"]
    elif layer == "unstaged":
        selector = []
    else:  # pragma: no cover - internal invariant
        raise AssertionError(layer)
    paths = _nul_paths(_git(workspace, "diff", *selector, "--name-only", "-z", "--").stdout)
    result: list[dict[str, object]] = []
    for path in paths:
        patch = _git(
            workspace,
            "diff",
            *selector,
            "--binary",
            "--no-ext-diff",
            "--no-textconv",
            "--unified=0",
            "--",
            path,
        ).stdout
        fingerprint = digest_bytes(patch)
        workspace_text = str(workspace)
        candidate_id = _candidate_id(workspace_text, layer, path, fingerprint)
        result.append(
            {
                "candidate_id": candidate_id,
                "workspace": workspace_text,
                "layer": layer,
                "path": path,
                "kind": "tracked-diff",
                "fingerprint": fingerprint,
                "hunks": _hunks(
                    patch,
                    candidate_id=candidate_id,
                    workspace=workspace_text,
                    layer=layer,
                    path=path,
                ),
            }
        )
    return result


def _artifact_candidate(workspace: Path, path: str, layer: str) -> dict[str, object]:
    absolute = workspace / path
    entries = _artifact_entries(absolute)
    fingerprint = digest_json(entries)
    workspace_text = str(workspace)
    return {
        "candidate_id": _candidate_id(workspace_text, layer, path, fingerprint),
        "workspace": workspace_text,
        "layer": layer,
        "path": path,
        "kind": "artifact",
        "fingerprint": fingerprint,
        "hunks": [],
    }


def _declared_ignored(
    primary: Path,
    roots: Sequence[Path],
    artifacts: Iterable[Path],
) -> list[tuple[Path, str]]:
    result: list[tuple[Path, str]] = []
    for requested in artifacts:
        absolute = Path(requested)
        if not absolute.is_absolute():
            absolute = primary / absolute
        absolute = Path(os.path.abspath(os.fspath(absolute)))
        matches: list[tuple[int, Path, str]] = []
        for root in roots:
            try:
                relative = absolute.relative_to(root).as_posix()
            except ValueError:
                continue
            matches.append((len(root.parts), root, relative))
        if not matches:
            raise BoundaryError(f"declared ignored artifact is outside worktrees: {absolute}")
        _, root, relative = max(matches)
        if not relative or relative == "." or relative.startswith(".git/"):
            raise BoundaryError(f"invalid declared ignored artifact: {absolute}")
        ignored = _git(root, "check-ignore", "--quiet", "--", relative, check=False)
        if ignored.returncode != 0:
            raise BoundaryError(f"declared ignored artifact is not ignored: {relative}")
        result.append((root, relative))
    return sorted(set(result), key=lambda item: (str(item[0]), item[1]))


def inventory_git_state(
    repository: Path,
    base: str = "HEAD",
    declared_ignored: Iterable[Path] = (),
    participating_worktrees: Iterable[Path] = (),
    relevant_environment: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Capture a deterministic inventory plus a non-binding timestamp."""

    primary, roots, common = _prepare_roots(repository, participating_worktrees)
    base_revision = _resolve(primary, base)
    environment = dict(sorted((relevant_environment or {}).items()))
    if not all(
        isinstance(key, str) and isinstance(value, str) for key, value in environment.items()
    ):
        raise BoundaryError("environment keys and values must be strings")
    ignored = _declared_ignored(primary, roots, declared_ignored)
    candidates: list[dict[str, object]] = []
    workspaces: list[dict[str, object]] = []
    for root in roots:
        exact_revision = _resolve(root, "HEAD")
        branch_process = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
        branch = (
            branch_process.stdout.decode("utf-8").strip()
            if branch_process.returncode == 0
            else None
        )
        workspaces.append(
            {
                "path": str(root),
                "git_dir": _git_text(root, "rev-parse", "--absolute-git-dir"),
                "exact_revision": exact_revision,
                "recovery_identity": branch or exact_revision,
                "conflict_paths": _nul_paths(
                    _git(
                        root,
                        "diff",
                        "--name-only",
                        "--diff-filter=U",
                        "-z",
                        "--",
                    ).stdout
                ),
            }
        )
        for layer in ("committed", "staged", "unstaged"):
            candidates.extend(_tracked_candidates(root, layer, base_revision))
        untracked = _nul_paths(
            _git(root, "ls-files", "--others", "--exclude-standard", "-z", "--").stdout
        )
        candidates.extend(_artifact_candidate(root, path, "untracked") for path in untracked)
    candidates.extend(_artifact_candidate(root, path, "declared-ignored") for root, path in ignored)
    candidates.sort(
        key=lambda item: (
            str(item["workspace"]),
            str(item["layer"]),
            str(item["path"]),
            str(item["candidate_id"]),
        )
    )
    capture_spec = {
        "repository": str(primary),
        "base": base_revision,
        "participating_worktrees": [str(root) for root in roots],
        "declared_ignored": [str(root / path) for root, path in ignored],
        "relevant_environment": environment,
    }
    payload = {
        "schema": "agent-handrails/boundary-inventory/v2",
        "contract": CONTRACT_ID,
        "base_revision": base_revision,
        "repository_identity": {
            "common_dir": str(common),
            "object_format": _git_text(primary, "rev-parse", "--show-object-format"),
        },
        "workspaces": workspaces,
        "candidates": candidates,
        "capture_spec": capture_spec,
        "relevant_environment": environment,
    }
    return {
        "contract": CONTRACT_ID,
        "record": "boundary-inventory",
        "schema_version": SCHEMA_VERSION,
        "canonical_payload": payload,
        "inventory_digest": digest_json(payload),
        "base_revision": base_revision,
        "repository_identity": payload["repository_identity"],
        "workspaces": workspaces,
        "candidates": candidates,
        "capture_spec": capture_spec,
        "captured_at": _now(),
    }


def _targets(inventory: Mapping[str, object]) -> dict[str, dict[str, object]]:
    targets: dict[str, dict[str, object]] = {}
    for candidate_value in inventory["candidates"]:
        candidate = dict(candidate_value)
        hunks = list(candidate.get("hunks", []))
        if hunks:
            for hunk_value in hunks:
                hunk = dict(hunk_value)
                targets[str(hunk["hunk_id"])] = {
                    "target_id": hunk["hunk_id"],
                    "candidate_id": candidate["candidate_id"],
                    "workspace": candidate["workspace"],
                    "layer": candidate["layer"],
                    "path": candidate["path"],
                    "candidate_fingerprint": candidate["fingerprint"],
                    "target_fingerprint": hunk["fingerprint"],
                    "hunk_ordinal": hunk["ordinal"],
                }
        else:
            targets[str(candidate["candidate_id"])] = {
                "target_id": candidate["candidate_id"],
                "candidate_id": candidate["candidate_id"],
                "workspace": candidate["workspace"],
                "layer": candidate["layer"],
                "path": candidate["path"],
                "candidate_fingerprint": candidate["fingerprint"],
                "target_fingerprint": candidate["fingerprint"],
            }
    return targets


def _normalize_classifications(
    kind: str,
    classifications: Mapping[str, object],
    inventory: Mapping[str, object],
) -> list[dict[str, object]]:
    if kind not in CLASSIFICATIONS:
        raise BoundaryError(f"unsupported boundary kind: {kind}")
    units = classifications.get("logical_units")
    if not isinstance(units, list):
        raise BoundaryError("logical_units must be a list")
    targets = _targets(inventory)
    seen: set[str] = set()
    normalized: list[dict[str, object]] = []
    for index, value in enumerate(units):
        if not isinstance(value, dict):
            raise BoundaryError(f"logical unit {index} must be an object")
        target_id = value.get("target_id")
        if not isinstance(target_id, str) or target_id not in targets:
            raise BoundaryError(f"unknown target in logical unit {index}: {target_id!r}")
        if target_id in seen:
            raise BoundaryError(f"target classified more than once: {target_id}")
        seen.add(target_id)
        classification = value.get("classification")
        if classification not in CLASSIFICATIONS[kind]:
            raise BoundaryError(
                f"invalid {kind} classification for {target_id}: {classification!r}"
            )
        rationale = value.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            raise BoundaryError(f"classification rationale is required for {target_id}")
        authorization = value.get("authorization")
        if authorization not in AUTHORIZATION_STATES:
            raise BoundaryError(f"invalid authorization for {target_id}: {authorization!r}")
        if classification == "exclude-proven-unrelated":
            valid_authorization = authorization == "not-applicable"
        elif classification == "include-inherited-dependency":
            valid_authorization = authorization in {"authorized", "not-applicable"}
        else:
            valid_authorization = authorization == "authorized"
        if not valid_authorization:
            raise BoundaryError(
                f"classification/authorization conflict for {target_id}: "
                f"{classification}/{authorization}"
            )
        normalized.append(
            {
                **targets[target_id],
                "classification": classification,
                "rationale": rationale.strip(),
                "authorization": authorization,
            }
        )
    missing = sorted(set(targets) - seen)
    if missing:
        raise BoundaryError(f"unclassified logical units: {', '.join(missing)}")
    return sorted(normalized, key=lambda item: str(item["target_id"]))


def _code_state_token(
    inventory: Mapping[str, object],
    boundary_digest: str,
) -> dict[str, object]:
    payload = {
        "schema": "agent-handrails/code-state-token/v2",
        "contract": CONTRACT_ID,
        "boundary_digest": boundary_digest,
        "inventory_digest": inventory["inventory_digest"],
        "repository_identity": inventory["repository_identity"],
        "base_revision": inventory["base_revision"],
        "workspaces": inventory["workspaces"],
        "relevant_environment": inventory["canonical_payload"]["relevant_environment"],
    }
    return {
        "contract": CONTRACT_ID,
        "record": "code-state-token",
        **payload,
        "token_digest": digest_json(payload),
        "captured_at": _now(),
    }


def confirm_boundary(
    *,
    kind: str,
    classifications: Mapping[str, object],
    repository: Path,
    base: str = "HEAD",
    declared_ignored: Iterable[Path] = (),
    participating_worktrees: Iterable[Path] = (),
    relevant_environment: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Confirm complete classifications against two identical state captures."""

    first = inventory_git_state(
        repository,
        base,
        declared_ignored,
        participating_worktrees,
        relevant_environment,
    )
    expected_digest = classifications.get("inventory_digest")
    if expected_digest != first["inventory_digest"]:
        raise BoundaryError(
            "classification inventory digest does not match current inventory: "
            f"expected {expected_digest!r}, current {first['inventory_digest']!r}"
        )
    conflicts = [
        f"{workspace['path']}::{path}"
        for workspace in first["workspaces"]
        for path in workspace["conflict_paths"]
    ]
    if conflicts:
        raise BoundaryError(f"unmerged conflict blocks confirmation: {conflicts[0]}")
    task_id = classifications.get("task_id")
    outcome_revision = classifications.get("outcome_revision")
    if not isinstance(task_id, str) or not task_id.strip():
        raise BoundaryError("task_id is required")
    if not isinstance(outcome_revision, str) or not outcome_revision.strip():
        raise BoundaryError("outcome_revision is required")
    logical_units = _normalize_classifications(kind, classifications, first)
    payload: dict[str, object] = {
        "schema": f"agent-handrails/{kind}-boundary/v2",
        "contract": CONTRACT_ID,
        "kind": kind,
        "task_id": task_id.strip(),
        "outcome_revision": outcome_revision.strip(),
        "inventory_digest": first["inventory_digest"],
        "repository_identity": first["repository_identity"],
        "base_revision": first["base_revision"],
        "workspaces": first["workspaces"],
        "capture_spec": first["capture_spec"],
        "logical_units": logical_units,
    }
    seed_digest = classifications.get("boundary_seed_digest")
    if seed_digest is not None:
        if not isinstance(seed_digest, str) or not seed_digest:
            raise BoundaryError("boundary_seed_digest must be a non-empty string")
        payload["boundary_seed_digest"] = seed_digest
    boundary_digest = digest_json(payload)
    second = inventory_git_state(
        repository,
        base,
        declared_ignored,
        participating_worktrees,
        relevant_environment,
    )
    if second["inventory_digest"] != first["inventory_digest"]:
        raise BoundaryError("state drifted while confirming the boundary")
    return {
        "contract": CONTRACT_ID,
        "record": f"{kind}-boundary",
        "schema_version": SCHEMA_VERSION,
        "canonical_payload": payload,
        "boundary_digest": boundary_digest,
        "code_state_token": _code_state_token(second, boundary_digest),
        "confirmed_at": _now(),
    }


def _inventory_from_capture_spec(spec: Mapping[str, object]) -> dict[str, object]:
    required = {
        "repository",
        "base",
        "participating_worktrees",
        "declared_ignored",
        "relevant_environment",
    }
    if set(spec) != required:
        raise BoundaryError("boundary capture_spec has an invalid shape")
    return inventory_git_state(
        repository=Path(str(spec["repository"])),
        base=str(spec["base"]),
        participating_worktrees=tuple(Path(str(item)) for item in spec["participating_worktrees"]),
        declared_ignored=tuple(Path(str(item)) for item in spec["declared_ignored"]),
        relevant_environment=dict(spec["relevant_environment"]),
    )


def capture_boundary(boundary: Mapping[str, object]) -> dict[str, object]:
    """Validate a confirmed boundary and capture its exact current state token."""

    payload = boundary.get("canonical_payload")
    digest = boundary.get("boundary_digest")
    if not isinstance(payload, dict) or not isinstance(digest, str):
        raise BoundaryError("confirmed boundary is missing payload or digest")
    if digest_json(payload) != digest:
        raise BoundaryError("boundary digest mismatch")
    if payload.get("contract") != CONTRACT_ID or payload.get("kind") not in CLASSIFICATIONS:
        raise BoundaryError("unsupported boundary contract or kind")
    capture_spec = payload.get("capture_spec")
    if not isinstance(capture_spec, dict):
        raise BoundaryError("boundary capture_spec is missing")
    inventory = _inventory_from_capture_spec(capture_spec)
    if inventory["inventory_digest"] != payload.get("inventory_digest"):
        raise BoundaryError("state drift from confirmed boundary")
    return _code_state_token(inventory, digest)


def _environment(values: Sequence[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        key, separator, item = value.partition("=")
        if not separator or not key:
            raise BoundaryError(f"environment must use KEY=VALUE: {value!r}")
        result[key] = item
    return result


def _add_capture_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("--declare-ignored", action="append", type=Path, default=[])
    parser.add_argument("--participating-worktree", action="append", type=Path, default=[])
    parser.add_argument("--environment", action="append", default=[])
    parser.add_argument(
        "--compact",
        action="store_true",
        help="emit the minimal runtime projection needed by a direct skill call",
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and recapture deterministic usable-loop/v2 boundaries."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    inventory_parser = commands.add_parser("inventory", help="inventory candidates")
    _add_capture_arguments(inventory_parser)
    confirm_parser = commands.add_parser("confirm", help="confirm semantic classifications")
    _add_capture_arguments(confirm_parser)
    confirm_parser.add_argument("--kind", choices=sorted(CLASSIFICATIONS), required=True)
    confirm_parser.add_argument("--classifications", required=True)
    capture_parser = commands.add_parser("capture", help="recapture a confirmed boundary")
    capture_parser.add_argument("--boundary", type=Path, required=True)
    capture_parser.add_argument(
        "--compact",
        action="store_true",
        help="emit only current digest and state-token fields",
    )
    return parser.parse_args(argv)


def _read_json(path: str | Path) -> dict[str, object]:
    try:
        if str(path) == "-":
            value = json.load(sys.stdin)
        else:
            value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BoundaryError(f"cannot read JSON from {path}: {error}") from error
    if not isinstance(value, dict):
        raise BoundaryError(f"JSON from {path} must be an object")
    return value


def _compact_inventory(result: Mapping[str, object]) -> dict[str, object]:
    workspace_indexes = {
        str(workspace["path"]): index for index, workspace in enumerate(result["workspaces"])
    }
    candidates: list[dict[str, object]] = []
    for candidate_value in result["candidates"]:
        candidate = dict(candidate_value)
        hunks = [
            {
                "hunk_id": hunk["hunk_id"],
                "fingerprint": hunk["fingerprint"],
                "header": hunk["header"],
            }
            for hunk in candidate.get("hunks", [])
        ]
        candidates.append(
            {
                "candidate_id": candidate["candidate_id"],
                "fingerprint": candidate["fingerprint"],
                "workspace_index": workspace_indexes[str(candidate["workspace"])],
                "layer": candidate["layer"],
                "path": candidate["path"],
                "hunks": hunks,
            }
        )
    workspaces = [
        {
            "index": index,
            "path": workspace["path"],
            "revision": workspace["exact_revision"],
            "conflicts": workspace["conflict_paths"],
        }
        for index, workspace in enumerate(result["workspaces"])
    ]
    return {
        "inventory_digest": result["inventory_digest"],
        "workspaces": workspaces,
        "candidates": candidates,
    }


def _compact_boundary(result: Mapping[str, object]) -> dict[str, object]:
    token = result["code_state_token"]
    return {
        "contract": result["contract"],
        "record": result["record"],
        "boundary_digest": result["boundary_digest"],
        "code_state_token": token["token_digest"],
        "inventory_digest": token["inventory_digest"],
        "confirmed_at": result["confirmed_at"],
    }


def _compact_token(result: Mapping[str, object]) -> dict[str, object]:
    return {
        "contract": result["contract"],
        "record": result["record"],
        "boundary_digest": result["boundary_digest"],
        "code_state_token": result["token_digest"],
        "inventory_digest": result["inventory_digest"],
        "captured_at": result["captured_at"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_args(argv)
    try:
        if arguments.command == "inventory":
            result = inventory_git_state(
                arguments.repository,
                arguments.base,
                arguments.declare_ignored,
                arguments.participating_worktree,
                _environment(arguments.environment),
            )
        elif arguments.command == "confirm":
            result = confirm_boundary(
                kind=arguments.kind,
                classifications=_read_json(arguments.classifications),
                repository=arguments.repository,
                base=arguments.base,
                declared_ignored=arguments.declare_ignored,
                participating_worktrees=arguments.participating_worktree,
                relevant_environment=_environment(arguments.environment),
            )
        else:
            result = capture_boundary(_read_json(arguments.boundary))
    except BoundaryError as error:
        print(f"handrails-state: {error}", file=sys.stderr)
        return 2
    if arguments.compact:
        if arguments.command == "inventory":
            result = _compact_inventory(result)
        elif arguments.command == "confirm":
            result = _compact_boundary(result)
        else:
            result = _compact_token(result)
    json.dump(
        result,
        sys.stdout,
        ensure_ascii=True,
        sort_keys=True,
        indent=None if arguments.compact else 2,
        separators=(",", ":") if arguments.compact else None,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
