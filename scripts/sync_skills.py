#!/usr/bin/env python3
"""Deploy Agent Handrails skills from the project checkout to a local skills root."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, Mapping, Protocol

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "skills"
DEFAULT_TARGET = Path(
    os.environ.get("AGENT_HANDRAILS_SKILLS_DIR", "~/Workspace/Skills")
).expanduser()
DEFAULT_CODEX_LINK_ROOT = Path("~/.agents/skills").expanduser()
RUNTIME_ROOT = PROJECT_ROOT / "runtime"
MANAGED_DIR_NAME = ".agent-handrails"
LAYOUT_SCHEMA = 1
LAYOUT_FILE = "layout.json"
BUNDLES_DIR = "bundles"
CURRENT_LINK = "current"
TRANSACTIONS_DIR = "transactions"
LEGACY_TRANSACTION = "legacy-v1"
JOURNAL_PHASES = {
    "prepared",
    "migrating-entrypoints",
    "migrating-links",
    "committed",
}
SKILL_NAMES = (
    "branch-sandbox",
    "feedback-loop",
    "grill",
    "plan-lite",
    "spec-lite",
    "two-axis-review",
    "verify-before-claim",
)
Failpoint = Callable[[str], None]


class DigestWriter(Protocol):
    def update(self, data: bytes, /) -> None: ...


@dataclass(frozen=True)
class BundleSpec:
    bundle_id: str
    skill_digests: Mapping[str, str]
    runtime_digest: str | None


@dataclass(frozen=True)
class ApplyResult:
    bundle_id: str
    previous_bundle_id: str | None
    mode: str


@dataclass(frozen=True)
class CheckResult:
    exit_code: int
    lines: tuple[str, ...]


@dataclass(frozen=True)
class PreflightResult:
    mode: str
    missing_discovery_links: tuple[str, ...]


@dataclass(frozen=True)
class CreatedLink:
    path: Path
    device: int
    inode: int
    ctime_ns: int


def no_failpoint(_: str) -> None:
    return None


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
        help="install, migrate, or atomically activate a complete managed bundle",
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


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def update_digest_record(digest: DigestWriter, *parts: bytes) -> None:
    for part in parts:
        digest.update(len(part).to_bytes(8, "big"))
        digest.update(part)


def tree_digest(root: Path) -> str:
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"cannot digest missing or non-directory tree: {root}")
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix().encode()
        executable = str(path.lstat().st_mode & 0o111).encode()
        if path.is_symlink():
            update_digest_record(
                digest,
                b"L",
                relative,
                executable,
                os.readlink(path).encode(),
            )
        elif path.is_dir():
            update_digest_record(digest, b"D", relative, executable)
        elif path.is_file():
            update_digest_record(
                digest,
                b"F",
                relative,
                executable,
                path.read_bytes(),
            )
        else:
            raise RuntimeError(f"unsupported filesystem node in bundle tree: {path}")
    return digest.hexdigest()


def validate_source(
    source_root: Path = SOURCE_ROOT,
    skill_names: tuple[str, ...] = SKILL_NAMES,
) -> None:
    actual = {path.name for path in source_root.iterdir() if path.is_dir()}
    expected = set(skill_names)
    if actual != expected:
        raise RuntimeError(
            "canonical skill set differs from deployment manifest: "
            f"missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )

    for name in skill_names:
        skill_file = source_root / name / "SKILL.md"
        if not skill_file.is_file():
            raise RuntimeError(f"missing canonical skill file: {skill_file}")
        try:
            skill_text = skill_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise RuntimeError(f"cannot read canonical skill file: {skill_file}") from exc
        match = re.search(r"(?m)^name:\s*([^\n]+)$", skill_text)
        declared = match.group(1).strip().strip('"') if match else None
        if declared != name:
            raise RuntimeError(
                f"{skill_file}: declares name={declared!r}, expected {name!r}"
            )


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def atomic_write_json(path: Path, value: object) -> None:
    temporary = path.parent / f".{path.name}.tmp-{uuid.uuid4().hex}"
    try:
        with temporary.open("w", encoding="utf-8") as output:
            output.write(canonical_json(value) + "\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def bundle_id_for(
    skill_digests: Mapping[str, str],
    runtime_digest: str | None,
) -> str:
    digest = hashlib.sha256()
    update_digest_record(digest, b"agent-handrails-bundle", str(LAYOUT_SCHEMA).encode())
    for name, skill_digest in sorted(skill_digests.items()):
        update_digest_record(
            digest,
            b"skill",
            name.encode(),
            skill_digest.encode(),
        )
    update_digest_record(
        digest,
        b"runtime",
        (runtime_digest or "none").encode(),
    )
    return f"v1-sha256-{digest.hexdigest()}"


def bundle_spec(
    skill_roots: Mapping[str, Path],
    runtime_root: Path | None = None,
) -> BundleSpec:
    skill_digests = {
        name: tree_digest(skill_roots[name]) for name in sorted(skill_roots)
    }
    runtime_digest = (
        tree_digest(runtime_root)
        if runtime_root is not None and runtime_root.is_dir()
        else None
    )
    return BundleSpec(
        bundle_id=bundle_id_for(skill_digests, runtime_digest),
        skill_digests=skill_digests,
        runtime_digest=runtime_digest,
    )


def source_skill_roots(
    source_root: Path,
    skill_names: tuple[str, ...] = SKILL_NAMES,
) -> dict[str, Path]:
    return {name: source_root / name for name in skill_names}


def ensure_source_matches(
    source_root: Path,
    runtime_root: Path | None,
    expected: BundleSpec,
    skill_names: tuple[str, ...],
) -> None:
    actual = bundle_spec(source_skill_roots(source_root, skill_names), runtime_root)
    if actual != expected:
        raise RuntimeError("source changed during deployment")


def paths_overlap(first: Path, second: Path) -> bool:
    first_resolved = first.resolve(strict=False)
    second_resolved = second.resolve(strict=False)
    return (
        first_resolved == second_resolved
        or first_resolved.is_relative_to(second_resolved)
        or second_resolved.is_relative_to(first_resolved)
    )


def validate_path_separation(
    source_root: Path,
    target_root: Path,
    codex_link_root: Path | None,
    runtime_root: Path | None = None,
) -> None:
    protected_sources = [("skill source", source_root)]
    if runtime_root is not None:
        protected_sources.append(("runtime source", runtime_root))
    for label, protected in protected_sources:
        if paths_overlap(protected, target_root):
            raise RuntimeError(
                f"deployment target overlaps {label}: {target_root} and {protected}"
            )
        if codex_link_root is not None and paths_overlap(protected, codex_link_root):
            raise RuntimeError(
                f"Codex link root overlaps {label}: {codex_link_root} and {protected}"
            )
    if codex_link_root is not None and paths_overlap(target_root, codex_link_root):
        raise RuntimeError(
            "deployment target and Codex link root must be disjoint: "
            f"{target_root} and {codex_link_root}"
        )


def require_bundle_skill_set(
    spec: BundleSpec,
    skill_names: tuple[str, ...],
) -> None:
    if set(spec.skill_digests) != set(skill_names):
        raise RuntimeError(
            "bundle managed skill set mismatch: "
            f"missing={sorted(set(skill_names) - set(spec.skill_digests))}, "
            f"unexpected={sorted(set(spec.skill_digests) - set(skill_names))}"
        )


def manifest_for(spec: BundleSpec) -> dict[str, object]:
    return {
        "schema": LAYOUT_SCHEMA,
        "bundle_id": spec.bundle_id,
        "skills": dict(spec.skill_digests),
        "runtime": spec.runtime_digest,
    }


def spec_from_manifest(path: Path) -> BundleSpec:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"bundle manifest is missing or not a regular file: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid bundle manifest: {path}: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schema") != LAYOUT_SCHEMA:
        raise RuntimeError(f"unsupported bundle manifest: {path}")
    expected_fields = {"schema", "bundle_id", "skills", "runtime"}
    if set(raw) != expected_fields:
        raise RuntimeError(f"invalid bundle manifest fields: {path}")
    bundle_id = raw.get("bundle_id")
    skills = raw.get("skills")
    runtime = raw.get("runtime")
    if not isinstance(bundle_id, str) or not isinstance(skills, dict):
        raise RuntimeError(f"invalid bundle manifest fields: {path}")
    if runtime is not None and not isinstance(runtime, str):
        raise RuntimeError(f"invalid runtime digest in bundle manifest: {path}")
    if not all(
        isinstance(name, str)
        and re.fullmatch(r"[a-z0-9][a-z0-9-]*", name)
        and isinstance(value, str)
        and re.fullmatch(r"[0-9a-f]{64}", value)
        for name, value in skills.items()
    ):
        raise RuntimeError(f"invalid skill digests in bundle manifest: {path}")
    if runtime is not None and re.fullmatch(r"[0-9a-f]{64}", runtime) is None:
        raise RuntimeError(f"invalid runtime digest in bundle manifest: {path}")
    calculated_id = bundle_id_for(skills, runtime)
    if bundle_id != calculated_id:
        raise RuntimeError(
            f"bundle id does not match manifest payload digests: {path}"
        )
    return BundleSpec(bundle_id, dict(skills), runtime)


def create_bundle_tree(
    destination: Path,
    skill_roots: Mapping[str, Path],
    runtime_root: Path | None,
    spec: BundleSpec,
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    skills_destination = destination / "skills"
    skills_destination.mkdir()
    for name in sorted(skill_roots):
        shutil.copytree(
            skill_roots[name],
            skills_destination / name,
            symlinks=True,
        )
    runtime_destination = destination / "runtime"
    if runtime_root is not None and runtime_root.is_dir():
        shutil.copytree(runtime_root, runtime_destination, symlinks=True)
    else:
        runtime_destination.mkdir()
    (destination / "manifest.json").write_text(
        canonical_json(manifest_for(spec)) + "\n",
        encoding="utf-8",
    )


def verify_bundle(
    bundle: Path,
    expected: BundleSpec | None = None,
) -> BundleSpec:
    if bundle.is_symlink() or not bundle.is_dir():
        raise RuntimeError(f"bundle is missing or not a directory: {bundle}")
    actual_top_level = {path.name for path in bundle.iterdir()}
    expected_top_level = {"manifest.json", "skills", "runtime"}
    if actual_top_level != expected_top_level:
        raise RuntimeError(
            "bundle top-level entries mismatch: "
            f"missing={sorted(expected_top_level - actual_top_level)}, "
            f"unexpected={sorted(actual_top_level - expected_top_level)}"
        )
    actual = spec_from_manifest(bundle / "manifest.json")
    if expected is not None and actual != expected:
        raise RuntimeError(f"bundle manifest mismatch: {bundle}")
    expected_skills = set(actual.skill_digests)
    skills_root = bundle / "skills"
    if skills_root.is_symlink() or not skills_root.is_dir():
        raise RuntimeError(f"bundle skills directory missing or invalid: {bundle}")
    actual_skills = {path.name for path in skills_root.iterdir()}
    if actual_skills != expected_skills:
        raise RuntimeError(
            f"bundle skill set mismatch: missing={sorted(expected_skills - actual_skills)}, "
            f"unexpected={sorted(actual_skills - expected_skills)}"
        )
    for name, expected_digest in actual.skill_digests.items():
        skill_root = skills_root / name
        if skill_root.is_symlink() or not skill_root.is_dir():
            raise RuntimeError(f"bundle skill path is not a directory: {name}")
        if tree_digest(skill_root) != expected_digest:
            raise RuntimeError(f"bundle skill digest mismatch: {name}")
    runtime_root = bundle / "runtime"
    if runtime_root.is_symlink() or not runtime_root.is_dir():
        raise RuntimeError(f"bundle runtime directory missing: {bundle}")
    if actual.runtime_digest is None:
        runtime_digest = None
        if any(runtime_root.rglob("*")):
            raise RuntimeError(f"unexpected runtime payload in bundle: {bundle}")
    else:
        runtime_digest = tree_digest(runtime_root)
    if runtime_digest != actual.runtime_digest:
        raise RuntimeError(f"bundle runtime digest mismatch: {bundle}")
    if bundle.name != actual.bundle_id and not bundle.name.startswith(".staging-"):
        raise RuntimeError(
            f"bundle directory/name mismatch: {bundle.name} != {actual.bundle_id}"
        )
    return actual


def managed_root(target_root: Path) -> Path:
    return target_root / MANAGED_DIR_NAME


def expected_entrypoint_target(target_root: Path, name: str) -> Path:
    return managed_root(target_root) / CURRENT_LINK / "skills" / name


def expected_entrypoint_raw(name: str) -> str:
    return f"{MANAGED_DIR_NAME}/{CURRENT_LINK}/skills/{name}"


def logical_link_target(link: Path) -> Path:
    raw = Path(os.readlink(link))
    if raw.is_absolute():
        return Path(os.path.normpath(str(raw)))
    return Path(os.path.abspath(os.path.join(link.parent, raw)))


def symlink_state(link: Path, expected_target: Path) -> str:
    if not path_exists(link):
        return "missing"
    if not link.is_symlink():
        return "unmanaged-path-type"
    return (
        "up-to-date"
        if logical_link_target(link) == Path(os.path.abspath(expected_target))
        else "different-target"
    )


def current_bundle_id(target_root: Path) -> str:
    current = managed_root(target_root) / CURRENT_LINK
    if not current.is_symlink():
        raise RuntimeError(f"managed current pointer is missing or not a symlink: {current}")
    raw = Path(os.readlink(current))
    if raw.is_absolute() or len(raw.parts) != 2 or raw.parts[0] != BUNDLES_DIR:
        raise RuntimeError(f"managed current pointer has invalid target: {current} -> {raw}")
    return raw.parts[1]


def valid_legacy_skill(path: Path, expected_name: str) -> bool:
    if path.is_symlink() or not path.is_dir():
        return False
    skill_file = path / "SKILL.md"
    if not skill_file.is_file():
        return False
    try:
        skill_text = skill_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    match = re.search(r"(?m)^name:\s*([^\n]+)$", skill_text)
    declared = match.group(1).strip().strip('"') if match else None
    return declared == expected_name


def layout_document(skill_names: tuple[str, ...]) -> dict[str, object]:
    return {
        "schema": LAYOUT_SCHEMA,
        "skills": list(skill_names),
    }


def validate_managed_layout(
    target_root: Path,
    skill_names: tuple[str, ...],
) -> None:
    root = managed_root(target_root)
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"managed layout is not a directory: {root}")
    marker = root / LAYOUT_FILE
    try:
        actual = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid managed layout marker: {marker}: {exc}") from exc
    if actual != layout_document(skill_names):
        raise RuntimeError(f"unsupported managed layout: {marker}")


def path_exists(path: Path) -> bool:
    return os.path.lexists(path)


def transaction_root(target_root: Path) -> Path:
    return managed_root(target_root) / TRANSACTIONS_DIR / LEGACY_TRANSACTION


def transaction_journal(target_root: Path) -> Path:
    return transaction_root(target_root) / "journal.json"


def preflight_apply(
    source_root: Path,
    target_root: Path,
    codex_link_root: Path | None,
    skill_names: tuple[str, ...] = SKILL_NAMES,
) -> PreflightResult:
    validate_path_separation(source_root, target_root, codex_link_root)
    validate_source(source_root, skill_names)
    root = managed_root(target_root)
    if path_exists(root):
        validate_managed_layout(target_root, skill_names)
        if transaction_journal(target_root).is_file():
            return PreflightResult("recovery", ())
        active_id = current_bundle_id(target_root)
        active_spec = verify_bundle(root / BUNDLES_DIR / active_id)
        require_bundle_skill_set(active_spec, skill_names)
        for name in skill_names:
            state = symlink_state(
                target_root / name,
                expected_entrypoint_target(target_root, name),
            )
            if state != "up-to-date":
                raise RuntimeError(
                    f"managed entrypoint conflict for {name}: {state}"
                )
        mode = "managed"
    else:
        states = []
        for name in skill_names:
            path = target_root / name
            if not path_exists(path):
                states.append("missing")
            elif valid_legacy_skill(path, name):
                states.append("legacy")
            else:
                states.append("conflict")
        if all(state == "missing" for state in states):
            mode = "first-install"
        elif all(state == "legacy" for state in states):
            mode = "legacy-migration"
        else:
            details = {
                name: state for name, state in zip(skill_names, states, strict=True)
            }
            raise RuntimeError(f"managed target layout conflict: {details}")

    missing_links: list[str] = []
    if codex_link_root is not None:
        for name in skill_names:
            state = symlink_state(
                codex_link_root / name,
                target_root / name,
            )
            if state == "missing":
                missing_links.append(name)
            elif state != "up-to-date":
                raise RuntimeError(
                    f"discovery link conflict for {name}: {state}"
                )
    return PreflightResult(mode, tuple(missing_links))


@contextmanager
def deployment_lock(target_root: Path) -> Iterator[None]:
    directory_fd = os.open(target_root.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(directory_fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(directory_fd, fcntl.LOCK_UN)
        os.close(directory_fd)


def atomic_symlink_replace(link: Path, raw_target: str) -> None:
    temporary = link.parent / f".{link.name}.tmp-{uuid.uuid4().hex}"
    temporary.symlink_to(raw_target, target_is_directory=True)
    try:
        os.replace(temporary, link)
    finally:
        temporary.unlink(missing_ok=True)


def install_symlink(link: Path, raw_target: str) -> CreatedLink:
    if path_exists(link):
        raise RuntimeError(f"refusing to replace existing path with symlink: {link}")
    try:
        link.symlink_to(raw_target, target_is_directory=True)
    except FileExistsError as exc:
        raise RuntimeError(
            f"path appeared while creating managed symlink; refusing to replace it: {link}"
        ) from exc
    stat = link.lstat()
    return CreatedLink(link, stat.st_dev, stat.st_ino, stat.st_ctime_ns)


def is_same_created_link(created: CreatedLink, expected_target: Path) -> bool:
    try:
        stat = created.path.lstat()
    except FileNotFoundError:
        return False
    return (
        created.path.is_symlink()
        and stat.st_dev == created.device
        and stat.st_ino == created.inode
        and stat.st_ctime_ns == created.ctime_ns
        and symlink_state(created.path, expected_target) == "up-to-date"
    )


def stage_bundle(
    bundles: Path,
    skill_roots: Mapping[str, Path],
    runtime_root: Path | None,
    spec: BundleSpec,
    failpoint: Failpoint = no_failpoint,
) -> tuple[Path, bool]:
    destination = bundles / spec.bundle_id
    if path_exists(destination):
        if not destination.is_dir() or destination.is_symlink():
            raise RuntimeError(f"bundle path conflict: {destination}")
        verify_bundle(destination, spec)
        return destination, False

    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=bundles))
    published = False
    try:
        failpoint("stage.before-copy")
        create_bundle_tree(staging, skill_roots, runtime_root, spec)
        failpoint("stage.after-copy")
        verify_bundle(staging, spec)
        current_source = bundle_spec(skill_roots, runtime_root)
        if current_source != spec:
            raise RuntimeError("source changed while staging bundle")
        os.replace(staging, destination)
        published = True
        verify_bundle(destination, spec)
        return destination, True
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        if published and destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        raise


def remove_created_bundle(bundle: Path, created: bool) -> None:
    if created and bundle.is_dir() and not bundle.is_symlink():
        shutil.rmtree(bundle)


def ensure_discovery_links(
    target_root: Path,
    codex_link_root: Path | None,
    missing: tuple[str, ...],
    failpoint: Failpoint = no_failpoint,
) -> list[CreatedLink]:
    if codex_link_root is None or not missing:
        return []
    root_created = not codex_link_root.exists()
    codex_link_root.mkdir(parents=True, exist_ok=True)
    created: list[CreatedLink] = []
    try:
        for name in missing:
            failpoint(f"links.before:{name}")
            link = codex_link_root / name
            created.append(install_symlink(link, str(target_root / name)))
            failpoint(f"links.after:{name}")
        return created
    except BaseException:
        for created_link in reversed(created):
            if is_same_created_link(
                created_link,
                target_root / created_link.path.name,
            ):
                created_link.path.unlink()
        if root_created:
            try:
                codex_link_root.rmdir()
            except OSError:
                pass
        raise


def remove_created_links(
    links: list[CreatedLink],
    target_root: Path,
    codex_link_root: Path | None,
    root_was_missing: bool,
) -> None:
    for created_link in reversed(links):
        if is_same_created_link(
            created_link,
            target_root / created_link.path.name,
        ):
            created_link.path.unlink()
    if codex_link_root is not None and root_was_missing:
        try:
            codex_link_root.rmdir()
        except OSError:
            pass


def verify_active_installation(
    source_spec: BundleSpec,
    target_root: Path,
    codex_link_root: Path | None,
    skill_names: tuple[str, ...],
) -> None:
    active_id = current_bundle_id(target_root)
    if active_id != source_spec.bundle_id:
        raise RuntimeError(
            f"active bundle mismatch: {active_id} != {source_spec.bundle_id}"
        )
    active_bundle = managed_root(target_root) / BUNDLES_DIR / active_id
    verify_bundle(active_bundle, source_spec)
    for name in skill_names:
        entry_state = symlink_state(
            target_root / name,
            expected_entrypoint_target(target_root, name),
        )
        if entry_state != "up-to-date":
            raise RuntimeError(f"entrypoint verification failed for {name}: {entry_state}")
        if codex_link_root is not None:
            link_state_value = symlink_state(
                codex_link_root / name,
                target_root / name,
            )
            if link_state_value != "up-to-date":
                raise RuntimeError(
                    f"discovery link verification failed for {name}: "
                    f"{link_state_value}"
                )


def read_journal(target_root: Path) -> dict[str, object]:
    path = transaction_journal(target_root)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid migration journal: {path}: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema") != LAYOUT_SCHEMA:
        raise RuntimeError(f"unsupported migration journal: {path}")
    expected_fields = {
        "schema",
        "mode",
        "phase",
        "skills",
        "source_bundle_id",
        "initial_bundle_id",
        "target_root",
        "missing_discovery_links",
        "created_discovery_links",
        "codex_link_root",
        "codex_root_created",
        "current_action",
    }
    if set(value) != expected_fields:
        raise RuntimeError(f"invalid migration journal fields: {path}")

    mode = value.get("mode")
    phase = value.get("phase")
    raw_skills = value.get("skills")
    raw_missing = value.get("missing_discovery_links")
    raw_created_links = value.get("created_discovery_links")
    if mode not in {"first-install", "legacy-migration"}:
        raise RuntimeError(f"invalid migration journal mode: {path}")
    if phase not in JOURNAL_PHASES:
        raise RuntimeError(f"invalid migration journal phase: {path}")
    if not isinstance(raw_skills, list) or not raw_skills:
        raise RuntimeError(f"invalid migration journal skill set: {path}")
    if not all(
        isinstance(name, str)
        and re.fullmatch(r"[a-z0-9][a-z0-9-]*", name)
        for name in raw_skills
    ) or len(set(raw_skills)) != len(raw_skills):
        raise RuntimeError(f"invalid migration journal skill names: {path}")
    try:
        layout = json.loads(
            (managed_root(target_root) / LAYOUT_FILE).read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot validate migration journal layout: {path}") from exc
    if not isinstance(layout, dict) or raw_skills != layout.get("skills"):
        raise RuntimeError(f"migration journal skill set differs from layout: {path}")

    bundle_id_pattern = r"v1-sha256-[0-9a-f]{64}"
    source_bundle_id = value.get("source_bundle_id")
    initial_bundle_id = value.get("initial_bundle_id")
    if not isinstance(source_bundle_id, str) or re.fullmatch(
        bundle_id_pattern,
        source_bundle_id,
    ) is None:
        raise RuntimeError(f"invalid source bundle id in migration journal: {path}")
    if not isinstance(initial_bundle_id, str) or re.fullmatch(
        bundle_id_pattern,
        initial_bundle_id,
    ) is None:
        raise RuntimeError(f"invalid initial bundle id in migration journal: {path}")
    bundles = managed_root(target_root) / BUNDLES_DIR
    verify_bundle(bundles / source_bundle_id)
    verify_bundle(bundles / initial_bundle_id)

    if value.get("target_root") != str(target_root):
        raise RuntimeError(f"migration journal target root mismatch: {path}")
    if not isinstance(raw_missing, list) or not all(
        isinstance(name, str) and name in raw_skills for name in raw_missing
    ) or len(set(raw_missing)) != len(raw_missing):
        raise RuntimeError(f"invalid discovery set in migration journal: {path}")
    if not isinstance(raw_created_links, list):
        raise RuntimeError(f"invalid created-link records in migration journal: {path}")
    created_names: set[str] = set()
    for record in raw_created_links:
        if not isinstance(record, dict) or set(record) != {
            "name",
            "device",
            "inode",
            "ctime_ns",
        }:
            raise RuntimeError(
                f"invalid created-link record in migration journal: {path}"
            )
        name = record.get("name")
        device = record.get("device")
        inode = record.get("inode")
        ctime_ns = record.get("ctime_ns")
        if (
            not isinstance(name, str)
            or name not in raw_missing
            or name in created_names
            or not isinstance(device, int)
            or isinstance(device, bool)
            or device < 0
            or not isinstance(inode, int)
            or isinstance(inode, bool)
            or inode <= 0
            or not isinstance(ctime_ns, int)
            or isinstance(ctime_ns, bool)
            or ctime_ns <= 0
        ):
            raise RuntimeError(
                f"invalid created-link ownership in migration journal: {path}"
            )
        created_names.add(name)
    raw_codex_root = value.get("codex_link_root")
    if raw_codex_root is not None and (
        not isinstance(raw_codex_root, str) or not Path(raw_codex_root).is_absolute()
    ):
        raise RuntimeError(f"invalid Codex root in migration journal: {path}")
    if not isinstance(value.get("codex_root_created"), bool):
        raise RuntimeError(f"invalid Codex root state in migration journal: {path}")
    current_action = value.get("current_action")
    valid_actions = (
        {None}
        | {f"entrypoint:{name}" for name in raw_skills}
        | {f"discovery:{name}" for name in raw_missing}
    )
    if current_action is not None and not isinstance(current_action, str):
        raise RuntimeError(f"invalid migration action in journal: {path}")
    if current_action not in valid_actions:
        raise RuntimeError(f"invalid migration action in journal: {path}")
    return value


def write_journal(target_root: Path, value: dict[str, object]) -> None:
    atomic_write_json(transaction_journal(target_root), value)


def rollback_initial_migration(
    target_root: Path,
    journal: Mapping[str, object],
) -> None:
    mode = journal.get("mode")
    raw_skill_names = journal.get("skills")
    if mode not in {"first-install", "legacy-migration"} or not isinstance(
        raw_skill_names,
        list,
    ):
        raise RuntimeError("migration journal has invalid rollback metadata")
    skill_names = tuple(str(name) for name in raw_skill_names)
    raw_codex_root = journal.get("codex_link_root")
    codex_link_root = (
        Path(raw_codex_root) if isinstance(raw_codex_root, str) else None
    )
    created_discovery = journal.get("created_discovery_links", [])
    backups = transaction_root(target_root) / "backups"

    if codex_link_root is not None:
        recorded_names = {
            str(record["name"])
            for record in created_discovery
            if isinstance(record, dict) and "name" in record
        }
        current_action = journal.get("current_action")
        if isinstance(current_action, str) and current_action.startswith("discovery:"):
            pending_name = current_action.removeprefix("discovery:")
            pending_link = codex_link_root / pending_name
            if pending_name not in recorded_names and path_exists(pending_link):
                raise RuntimeError(
                    "cannot prove ownership of discovery link created during "
                    f"interrupted migration: {pending_link}"
                )
        for record in reversed(created_discovery):
            if not isinstance(record, dict):
                continue
            name = str(record["name"])
            created_link = CreatedLink(
                codex_link_root / name,
                int(record["device"]),
                int(record["inode"]),
                int(record["ctime_ns"]),
            )
            if is_same_created_link(created_link, target_root / name):
                created_link.path.unlink()

    for name in reversed(skill_names):
        entrypoint = target_root / name
        backup = backups / name
        if entrypoint.is_symlink() and symlink_state(
            entrypoint,
            expected_entrypoint_target(target_root, name),
        ) == "up-to-date":
            entrypoint.unlink()
        if backup.is_dir() and not backup.is_symlink():
            if path_exists(entrypoint):
                raise RuntimeError(
                    f"cannot restore legacy entrypoint over unexpected path: {entrypoint}"
                )
            os.replace(backup, entrypoint)

    for name in skill_names:
        entrypoint = target_root / name
        if mode == "first-install" and path_exists(entrypoint):
            raise RuntimeError(
                f"first-install rollback left an unexpected entrypoint: {entrypoint}"
            )
        if mode == "legacy-migration" and not valid_legacy_skill(
            entrypoint,
            name,
        ):
            raise RuntimeError(
                f"legacy rollback did not restore entrypoint: {entrypoint}"
            )
    if backups.is_dir() and any(backups.iterdir()):
        raise RuntimeError("migration rollback left unaccounted legacy backups")

    root = managed_root(target_root)
    if root.is_dir() and not root.is_symlink():
        shutil.rmtree(root)
    if codex_link_root is not None and bool(journal.get("codex_root_created")):
        try:
            codex_link_root.rmdir()
        except OSError:
            pass


def recover_interrupted_migration(target_root: Path) -> None:
    journal = read_journal(target_root)
    if journal.get("phase") == "committed":
        skill_names = tuple(str(name) for name in journal["skills"])
        source_bundle_id = str(journal["source_bundle_id"])
        source_spec = verify_bundle(
            managed_root(target_root) / BUNDLES_DIR / source_bundle_id
        )
        require_bundle_skill_set(source_spec, skill_names)
        raw_codex_root = journal["codex_link_root"]
        codex_link_root = (
            Path(str(raw_codex_root)) if raw_codex_root is not None else None
        )
        verify_active_installation(
            source_spec,
            target_root,
            codex_link_root,
            skill_names,
        )
        shutil.rmtree(transaction_root(target_root))
        return
    rollback_initial_migration(target_root, journal)


def prepare_bootstrap(
    source_root: Path,
    target_root: Path,
    codex_link_root: Path | None,
    preflight: PreflightResult,
    source_spec: BundleSpec,
    runtime_root: Path | None,
    skill_names: tuple[str, ...],
    failpoint: Failpoint,
) -> tuple[Path, str]:
    bootstrap = target_root / f"{MANAGED_DIR_NAME}.bootstrap-{uuid.uuid4().hex}"
    bootstrap.mkdir()
    try:
        (bootstrap / BUNDLES_DIR).mkdir()
        (bootstrap / TRANSACTIONS_DIR / LEGACY_TRANSACTION / "backups").mkdir(
            parents=True
        )
        (bootstrap / LAYOUT_FILE).write_text(
            canonical_json(layout_document(skill_names)) + "\n",
            encoding="utf-8",
        )

        legacy_id: str | None = None
        if preflight.mode == "legacy-migration":
            legacy_roots = {
                name: target_root / name for name in skill_names
            }
            legacy_spec = bundle_spec(legacy_roots, None)
            stage_bundle(
                bootstrap / BUNDLES_DIR,
                legacy_roots,
                None,
                legacy_spec,
                failpoint,
            )
            legacy_id = legacy_spec.bundle_id

        stage_bundle(
            bootstrap / BUNDLES_DIR,
            source_skill_roots(source_root, skill_names),
            runtime_root,
            source_spec,
            failpoint,
        )
        initial_id = legacy_id or source_spec.bundle_id
        (bootstrap / CURRENT_LINK).symlink_to(
            f"{BUNDLES_DIR}/{initial_id}",
            target_is_directory=True,
        )
        journal = {
            "schema": LAYOUT_SCHEMA,
            "mode": preflight.mode,
            "phase": "prepared",
            "skills": list(skill_names),
            "source_bundle_id": source_spec.bundle_id,
            "initial_bundle_id": initial_id,
            "target_root": str(target_root),
            "missing_discovery_links": list(preflight.missing_discovery_links),
            "created_discovery_links": [],
            "codex_link_root": (
                str(codex_link_root) if codex_link_root is not None else None
            ),
            "codex_root_created": bool(
                codex_link_root is not None and not codex_link_root.exists()
            ),
            "current_action": None,
        }
        atomic_write_json(
            bootstrap / TRANSACTIONS_DIR / LEGACY_TRANSACTION / "journal.json",
            journal,
        )
        failpoint("bootstrap.before-publish")
        os.replace(bootstrap, managed_root(target_root))
        failpoint("bootstrap.after-publish")
        return managed_root(target_root), initial_id
    except BaseException:
        if bootstrap.exists():
            shutil.rmtree(bootstrap)
        elif transaction_journal(target_root).is_file():
            rollback_initial_migration(target_root, read_journal(target_root))
        raise


def migrate_initial_layout(
    source_root: Path,
    target_root: Path,
    codex_link_root: Path | None,
    source_spec: BundleSpec,
    runtime_root: Path | None,
    initial_bundle_id: str,
    skill_names: tuple[str, ...],
    failpoint: Failpoint,
) -> None:
    journal = read_journal(target_root)
    backups = transaction_root(target_root) / "backups"

    committed = False
    try:
        ensure_source_matches(
            source_root,
            runtime_root,
            source_spec,
            skill_names,
        )
        journal["phase"] = "migrating-entrypoints"
        write_journal(target_root, journal)
        for name in skill_names:
            journal["current_action"] = f"entrypoint:{name}"
            write_journal(target_root, journal)
            failpoint(f"migration.before-entry:{name}")
            entrypoint = target_root / name
            if journal["mode"] == "legacy-migration":
                os.replace(entrypoint, backups / name)
            install_symlink(entrypoint, expected_entrypoint_raw(name))
            failpoint(f"migration.after-entry:{name}")

        journal["phase"] = "migrating-links"
        journal["current_action"] = None
        write_journal(target_root, journal)
        missing_discovery = tuple(
            str(name) for name in journal["missing_discovery_links"]
        )
        if codex_link_root is not None and missing_discovery:
            codex_link_root.mkdir(parents=True, exist_ok=True)
            for name in missing_discovery:
                journal["current_action"] = f"discovery:{name}"
                write_journal(target_root, journal)
                try:
                    failpoint(f"links.before:{name}")
                    created_link = install_symlink(
                        codex_link_root / name,
                        str(target_root / name),
                    )
                    created_records = journal["created_discovery_links"]
                    if not isinstance(created_records, list):
                        raise RuntimeError(
                            "migration journal lost created-link progress list"
                        )
                    created_records.append(
                        {
                            "name": name,
                            "device": created_link.device,
                            "inode": created_link.inode,
                            "ctime_ns": created_link.ctime_ns,
                        }
                    )
                    write_journal(target_root, journal)
                    failpoint(f"links.after:{name}")
                except BaseException:
                    journal["current_action"] = None
                    raise
        journal["current_action"] = None
        write_journal(target_root, journal)

        for name in skill_names:
            if symlink_state(
                target_root / name,
                expected_entrypoint_target(target_root, name),
            ) != "up-to-date":
                raise RuntimeError(f"entrypoint migration verification failed: {name}")

        ensure_source_matches(
            source_root,
            runtime_root,
            source_spec,
            skill_names,
        )
        if initial_bundle_id != source_spec.bundle_id:
            failpoint("activation.before-replace")
            atomic_symlink_replace(
                managed_root(target_root) / CURRENT_LINK,
                f"{BUNDLES_DIR}/{source_spec.bundle_id}",
            )
            failpoint("activation.after-replace")
        verify_active_installation(
            source_spec,
            target_root,
            codex_link_root,
            skill_names,
        )
        ensure_source_matches(
            source_root,
            runtime_root,
            source_spec,
            skill_names,
        )
        journal["phase"] = "committed"
        journal["current_action"] = None
        write_journal(target_root, journal)
        committed = True
    except BaseException:
        if not committed:
            rollback_initial_migration(target_root, journal)
        raise
    try:
        shutil.rmtree(transaction_root(target_root))
    except OSError:
        # A committed journal is safe to clean on the next apply.
        pass


def apply_managed_upgrade(
    source_root: Path,
    target_root: Path,
    codex_link_root: Path | None,
    preflight: PreflightResult,
    source_spec: BundleSpec,
    runtime_root: Path | None,
    skill_names: tuple[str, ...],
    failpoint: Failpoint,
) -> ApplyResult:
    root = managed_root(target_root)
    bundles = root / BUNDLES_DIR
    previous_id = current_bundle_id(target_root)
    bundle, bundle_created = stage_bundle(
        bundles,
        source_skill_roots(source_root, skill_names),
        runtime_root,
        source_spec,
        failpoint,
    )
    codex_root_was_missing = bool(
        codex_link_root is not None and not codex_link_root.exists()
    )
    created_links: list[CreatedLink] = []
    activated = False
    try:
        created_links = ensure_discovery_links(
            target_root,
            codex_link_root,
            preflight.missing_discovery_links,
            failpoint,
        )
        ensure_source_matches(
            source_root,
            runtime_root,
            source_spec,
            skill_names,
        )
        if previous_id != source_spec.bundle_id:
            failpoint("activation.before-replace")
            atomic_symlink_replace(
                root / CURRENT_LINK,
                f"{BUNDLES_DIR}/{source_spec.bundle_id}",
            )
            activated = True
            failpoint("activation.after-replace")
        verify_active_installation(
            source_spec,
            target_root,
            codex_link_root,
            skill_names,
        )
        ensure_source_matches(
            source_root,
            runtime_root,
            source_spec,
            skill_names,
        )
        return ApplyResult(
            source_spec.bundle_id,
            previous_id if previous_id != source_spec.bundle_id else None,
            "up-to-date" if previous_id == source_spec.bundle_id else "upgraded",
        )
    except BaseException:
        if activated:
            atomic_symlink_replace(
                root / CURRENT_LINK,
                f"{BUNDLES_DIR}/{previous_id}",
            )
        remove_created_links(
            created_links,
            target_root,
            codex_link_root,
            codex_root_was_missing,
        )
        remove_created_bundle(bundle, bundle_created)
        raise


def apply_bundle(
    source_root: Path,
    target_root: Path,
    codex_link_root: Path | None = None,
    *,
    runtime_root: Path | None = None,
    skill_names: tuple[str, ...] = SKILL_NAMES,
    failpoint: Failpoint = no_failpoint,
) -> ApplyResult:
    source_root = source_root.expanduser().resolve()
    target_root = target_root.expanduser().resolve(strict=False)
    codex_link_root = (
        codex_link_root.expanduser().resolve(strict=False)
        if codex_link_root is not None
        else None
    )
    runtime_root = (
        runtime_root.expanduser().resolve()
        if runtime_root is not None
        else None
    )
    validate_path_separation(
        source_root,
        target_root,
        codex_link_root,
        runtime_root,
    )

    recovery_pending = transaction_journal(target_root).is_file()
    if not recovery_pending:
        preflight_apply(
            source_root,
            target_root,
            codex_link_root,
            skill_names,
        )
    target_root.parent.mkdir(parents=True, exist_ok=True)
    with deployment_lock(target_root):
        target_created = not target_root.exists()
        target_root.mkdir(exist_ok=True)
        try:
            if transaction_journal(target_root).is_file():
                validate_managed_layout(target_root, skill_names)
                recover_interrupted_migration(target_root)
            current_preflight = preflight_apply(
                source_root,
                target_root,
                codex_link_root,
                skill_names,
            )
            source_spec = bundle_spec(
                source_skill_roots(source_root, skill_names),
                runtime_root,
            )
            if current_preflight.mode == "managed":
                return apply_managed_upgrade(
                    source_root,
                    target_root,
                    codex_link_root,
                    current_preflight,
                    source_spec,
                    runtime_root,
                    skill_names,
                    failpoint,
                )

            _, initial_id = prepare_bootstrap(
                source_root,
                target_root,
                codex_link_root,
                current_preflight,
                source_spec,
                runtime_root,
                skill_names,
                failpoint,
            )
            migrate_initial_layout(
                source_root,
                target_root,
                codex_link_root,
                source_spec,
                runtime_root,
                initial_id,
                skill_names,
                failpoint,
            )
            return ApplyResult(
                source_spec.bundle_id,
                initial_id if initial_id != source_spec.bundle_id else None,
                current_preflight.mode,
            )
        except BaseException:
            if target_created:
                try:
                    target_root.rmdir()
                except OSError:
                    pass
            raise


def check_installation(
    source_root: Path,
    target_root: Path,
    codex_link_root: Path | None = None,
    *,
    runtime_root: Path | None = None,
    skill_names: tuple[str, ...] = SKILL_NAMES,
) -> CheckResult:
    source_root = source_root.expanduser().resolve()
    target_root = target_root.expanduser().resolve(strict=False)
    codex_link_root = (
        codex_link_root.expanduser().resolve(strict=False)
        if codex_link_root is not None
        else None
    )
    runtime_root = (
        runtime_root.expanduser().resolve()
        if runtime_root is not None
        else None
    )
    lines: list[str] = []
    try:
        validate_path_separation(
            source_root,
            target_root,
            codex_link_root,
            runtime_root,
        )
        validate_source(source_root, skill_names)
        source_spec = bundle_spec(
            source_skill_roots(source_root, skill_names),
            runtime_root,
        )
        root = managed_root(target_root)
        if not path_exists(root):
            states = []
            for name in skill_names:
                path = target_root / name
                if not path_exists(path):
                    state = "missing"
                elif valid_legacy_skill(path, name):
                    state = compare(source_root / name, path)
                else:
                    state = "conflict"
                states.append(state)
                lines.append(f"{name}: {state}")
            layout_state = (
                "migration-required"
                if all(state in {"up-to-date", "different"} for state in states)
                else "missing-or-conflicting"
            )
            lines.insert(0, f"bundle/layout: {layout_state}")
            if codex_link_root is not None:
                for name in skill_names:
                    state = symlink_state(
                        codex_link_root / name,
                        target_root / name,
                    )
                    lines.append(f"codex-link/{name}: {state}")
            return CheckResult(1, tuple(lines))

        validate_managed_layout(target_root, skill_names)
        if transaction_journal(target_root).is_file():
            return CheckResult(1, ("bundle/layout: recovery-required",))
        active_id = current_bundle_id(target_root)
        active_bundle = root / BUNDLES_DIR / active_id
        active_spec = verify_bundle(active_bundle)
        require_bundle_skill_set(active_spec, skill_names)
        current_state = (
            "up-to-date"
            if active_spec.bundle_id == source_spec.bundle_id
            else "different"
        )
        lines.append("bundle/layout: managed")
        lines.append(f"bundle/current: {current_state} ({active_id})")
        all_current = current_state == "up-to-date"
        for name in skill_names:
            state = symlink_state(
                target_root / name,
                expected_entrypoint_target(target_root, name),
            )
            lines.append(f"{name}: {state}")
            all_current = all_current and state == "up-to-date"
        if codex_link_root is not None:
            for name in skill_names:
                state = symlink_state(
                    codex_link_root / name,
                    target_root / name,
                )
                lines.append(f"codex-link/{name}: {state}")
                all_current = all_current and state == "up-to-date"
        return CheckResult(0 if all_current else 1, tuple(lines))
    except (OSError, RuntimeError) as exc:
        lines.append(f"ERROR: {exc}")
        return CheckResult(2, tuple(lines))


def compare(source: Path, target: Path) -> str:
    if not path_exists(target):
        return "missing"
    if target.is_symlink() or not target.is_dir():
        return "unmanaged-path-type"
    return "up-to-date" if tree_digest(source) == tree_digest(target) else "different"


def main() -> int:
    args = parse_args()
    target_root = args.target.expanduser().resolve()
    codex_link_root = (
        args.codex_link_root.expanduser().resolve()
        if args.codex_link_root is not None
        else None
    )

    runtime_root = RUNTIME_ROOT if RUNTIME_ROOT.is_dir() else None
    if args.check:
        result = check_installation(
            SOURCE_ROOT,
            target_root,
            codex_link_root,
            runtime_root=runtime_root,
        )
        for line in result.lines:
            stream = sys.stderr if line.startswith("ERROR:") else sys.stdout
            print(line, file=stream)
        return result.exit_code

    try:
        applied = apply_bundle(
            SOURCE_ROOT,
            target_root,
            codex_link_root,
            runtime_root=runtime_root,
        )
    except (OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    checked = check_installation(
        SOURCE_ROOT,
        target_root,
        codex_link_root,
        runtime_root=runtime_root,
    )
    for line in checked.lines:
        stream = sys.stderr if line.startswith("ERROR:") else sys.stdout
        print(line, file=stream)
    if checked.exit_code != 0:
        print("ERROR: deployment verification failed", file=sys.stderr)
        return 2

    action = "already active" if applied.mode == "up-to-date" else "activated"
    print(f"Bundle {action}: {applied.bundle_id}")
    if applied.previous_bundle_id is not None:
        print(f"Previous bundle retained: {applied.previous_bundle_id}")
    print(f"Deployment verified: {target_root}")
    if codex_link_root is not None:
        print(f"Codex discovery links verified: {codex_link_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
