#!/usr/bin/env python3
"""Inspect one Git path without putting credential-shaped values in the transcript."""

from __future__ import annotations

import argparse
import math
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

MAX_CONTEXT_LINES = 20
MAX_OUTPUT_LINES = 240
MAX_SCAN_BYTES = 8 * 1024 * 1024

SENSITIVE_PATH_PART = re.compile(
    r"(?:^|[._-])(credential|credentials|private[_-]?key|secret|secrets|token|tokens)(?:$|[._-])",
    re.IGNORECASE,
)
SENSITIVE_KEY = re.compile(
    r"(?:api[_-]?key|access[_-]?key|secret(?:[_-]?key)?|private[_-]?key|"
    r"token|password|passwd|credential|authorization)",
    re.IGNORECASE,
)
ASSIGNMENT = re.compile(
    r"^\s*(?:export\s+)?[\"']?(?P<key>[A-Za-z_][A-Za-z0-9_.-]*)[\"']?"
    r"\s*(?::[^=]+)?\s*(?:=|:)\s*(?P<value>.*)$"
)
SENSITIVE_ASSIGNMENT = re.compile(
    r"(?:api[_-]?key|access[_-]?key|secret(?:[_-]?key)?|private[_-]?key|"
    r"token|password|passwd|credential|authorization)[\"']?\s*(?:=|:)",
    re.IGNORECASE,
)
TOKEN_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^/\s:@]+:[^@\s/]+@"),
)
PLACEHOLDER_MARKERS = (
    "<replace",
    "<your",
    "change-me",
    "changeme",
    "example",
    "placeholder",
    "replace-me",
    "replace-with",
    "your-",
    "xxx",
)


class SafeDiffError(RuntimeError):
    """An inspection failure whose details must stay out of the transcript."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--base", required=True, help="review base revision")
    parser.add_argument("--path", required=True, help="one repository-relative path")
    parser.add_argument("--context", type=int, default=MAX_CONTEXT_LINES)
    parser.add_argument("--max-lines", type=int, default=MAX_OUTPUT_LINES)
    parser.add_argument("--hunk", type=int, help="one-based hunk to print after a safe preflight")
    parser.add_argument("--chunk", type=int, help="one-based chunk of an oversized selected hunk")
    arguments = parser.parse_args()
    if not 0 <= arguments.context <= MAX_CONTEXT_LINES:
        parser.error(f"--context must be between 0 and {MAX_CONTEXT_LINES}")
    if not 20 <= arguments.max_lines <= MAX_OUTPUT_LINES:
        parser.error(f"--max-lines must be between 20 and {MAX_OUTPUT_LINES}")
    if arguments.hunk is not None and arguments.hunk < 1:
        parser.error("--hunk must be a positive integer")
    if arguments.chunk is not None and (arguments.hunk is None or arguments.chunk < 1):
        parser.error("--chunk requires --hunk and must be a positive integer")
    return arguments


def git(repository: Path, *arguments: str, check: bool = True) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and completed.returncode != 0:
        raise SafeDiffError("git command failed")
    return completed.stdout


def repository_root(repository: Path) -> Path:
    raw = git(repository, "rev-parse", "--show-toplevel").decode("utf-8", errors="strict").strip()
    return Path(raw)


def validate_relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or value == "."
        or ".." in path.parts
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise SafeDiffError("invalid repository path")
    return path.as_posix()


def resolve_base(repository: Path, base: str) -> str:
    return (
        git(repository, "rev-parse", "--verify", f"{base}^{{commit}}")
        .decode("ascii", errors="strict")
        .strip()
    )


def read_base(repository: Path, base: str, path: str) -> bytes:
    return git(repository, "show", f"{base}:{path}", check=False)


def read_current(repository: Path, path: str) -> bytes:
    candidate = repository / path
    try:
        metadata = candidate.lstat()
    except FileNotFoundError:
        return b""
    if candidate.is_symlink():
        return os.readlink(candidate).encode("utf-8", errors="surrogateescape")
    if not candidate.is_file():
        return b""
    try:
        candidate.resolve().relative_to(repository.resolve())
    except ValueError as error:
        raise SafeDiffError("repository path escapes through a symlink") from error
    with candidate.open("rb") as file_object:
        return file_object.read(min(metadata.st_size, MAX_SCAN_BYTES) + 1)


def candidate_diff(repository: Path, base: str, path: str, context: int) -> bytes:
    result = git(
        repository,
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--no-color",
        f"--unified={context}",
        base,
        "--",
        path,
    )
    if result:
        return result

    current = read_current(repository, path)
    base_content = read_base(repository, base, path)
    if current and not base_content:
        text = current.decode("utf-8", errors="replace").splitlines()
        prefix = [f"diff --git a/{path} b/{path}", "new file", "--- /dev/null", f"+++ b/{path}"]
        return ("\n".join(prefix + [f"+{line}" for line in text]) + "\n").encode()
    return result


def path_is_sensitive(path: str) -> bool:
    lowered = PurePosixPath(path.lower())
    name = lowered.name
    if name == ".env" or name.startswith(".env."):
        return True
    if name in {".netrc", ".npmrc", "credentials", "credentials.json"}:
        return True
    if lowered.suffix in {".key", ".p12", ".pfx", ".pem"}:
        return True
    return any(SENSITIVE_PATH_PART.search(part) for part in lowered.parts)


def text_has_sensitive_assignment(text: str) -> bool:
    for line in text.splitlines():
        match = ASSIGNMENT.match(line.lstrip("+- "))
        if match and SENSITIVE_KEY.search(match.group("key")):
            return True
        if SENSITIVE_ASSIGNMENT.search(line):
            return True
    return False


def text_has_token_shape(text: str) -> bool:
    return any(pattern.search(text) for pattern in TOKEN_PATTERNS)


def sensitivity_reasons(path: str, *contents: bytes) -> list[str]:
    reasons: list[str] = []
    if path_is_sensitive(path):
        reasons.append("sensitive-path")
    if any(len(content) > MAX_SCAN_BYTES for content in contents):
        reasons.append("oversized-content")
    texts = [content[:MAX_SCAN_BYTES].decode("utf-8", errors="replace") for content in contents]
    if any(text_has_sensitive_assignment(text) for text in texts):
        reasons.append("sensitive-assignment")
    if any(text_has_token_shape(text) for text in texts):
        reasons.append("credential-shaped-token")
    return reasons


def value_class(value: str) -> str:
    normalized = value.strip().strip("\"'").strip().lower()
    if not normalized:
        return "empty"
    if any(marker in normalized for marker in PLACEHOLDER_MARKERS):
        return "placeholder"
    if normalized in {"true", "false"}:
        return "boolean"
    if normalized.startswith(("http://localhost", "https://localhost", "http://127.0.0.1")):
        return "local-default"
    return "configured-value"


def changed_lines(diff: str) -> tuple[list[tuple[str, str]], Counter[str]]:
    changes: list[tuple[str, str]] = []
    counts: Counter[str] = Counter()
    for line in diff.splitlines():
        if line.startswith("@@"):
            counts["hunks"] += 1
        elif line.startswith("+++") or line.startswith("---"):
            continue
        elif line.startswith("+"):
            counts["added"] += 1
            changes.append(("added", line[1:]))
        elif line.startswith("-"):
            counts["removed"] += 1
            changes.append(("removed", line[1:]))
        elif line.startswith(" "):
            counts["context"] += 1
    return changes, counts


def emit_redacted(path: str, reasons: list[str], diff: str, current: bytes) -> None:
    changes, counts = changed_lines(diff)
    assignments: dict[str, dict[str, Counter[str]]] = defaultdict(lambda: defaultdict(Counter))
    unparsed = 0
    for direction, content in changes:
        match = ASSIGNMENT.match(content)
        if match:
            assignments[match.group("key")][direction][value_class(match.group("value"))] += 1
        elif content.strip() and not content.lstrip().startswith("#"):
            unparsed += 1

    if not changes and current:
        for content in current.decode("utf-8", errors="replace").splitlines():
            match = ASSIGNMENT.match(content)
            if match:
                assignments[match.group("key")]["current"][value_class(match.group("value"))] += 1

    print("contract: usable-loop/v2")
    print("record: safe-diff")
    print("inspection: redacted")
    print(f"path: {path}")
    for reason in reasons:
        print(f"reason: {reason}")
    print(
        "changed: "
        f"hunks={counts['hunks']} added={counts['added']} removed={counts['removed']} "
        f"context={counts['context']}"
    )
    for key in sorted(assignments):
        fields = []
        for direction in ("removed", "added", "current"):
            for classification, count in sorted(assignments[key][direction].items()):
                suffix = f"x{count}" if count > 1 else ""
                fields.append(f"{direction}={classification}{suffix}")
        print(f"assignment: {key} {' '.join(fields)}")
    print(f"unparsed-changed-lines: {unparsed}")


def split_hunks(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    header: list[str] = []
    hunks: list[list[str]] = []
    for line in lines:
        if line.startswith("@@"):
            hunks.append([line])
        elif hunks:
            hunks[-1].append(line)
        else:
            header.append(line)
    return header, hunks


def emit_raw(
    path: str,
    diff: str,
    max_lines: int,
    selected_hunk: int | None,
    selected_chunk: int | None,
) -> None:
    lines = diff.splitlines()
    header, hunks = split_hunks(lines)
    if selected_hunk is not None:
        if selected_hunk > len(hunks):
            raise SafeDiffError("selected hunk does not exist")
        selected = hunks[selected_hunk - 1]
        lines = header + selected
        if len(lines) + 5 > max_lines:
            capacity = max(1, max_lines - len(header) - 6)
            chunks = max(1, math.ceil(max(0, len(selected) - 1) / capacity))
            if selected_chunk is None:
                print("contract: usable-loop/v2")
                print("record: safe-diff")
                print("inspection: hunk-too-large")
                print(f"path: {path}")
                print(f"hunk: {selected_hunk}")
                print(f"lines: {len(lines)}")
                print(f"chunks: {chunks}")
                return
            if selected_chunk > chunks:
                raise SafeDiffError("selected chunk does not exist")
            start = (selected_chunk - 1) * capacity
            stop = start + capacity
            lines = header + selected[:1] + selected[1:][start:stop]
    elif len(lines) + 5 > max_lines:
        print("contract: usable-loop/v2")
        print("record: safe-diff")
        print("inspection: requires-hunk-selection")
        print(f"path: {path}")
        print(f"hunks: {len(hunks)}")
        for index, hunk in enumerate(hunks, start=1):
            print(f"hunk-summary: index={index} lines={len(hunk)}")
        return

    print("contract: usable-loop/v2")
    print("record: safe-diff")
    print("inspection: raw" if lines else "inspection: no-changes")
    print(f"path: {path}")
    print("sensitive: false")
    if lines:
        print("\n".join(lines))


def main() -> int:
    arguments = parse_args()
    try:
        root = repository_root(arguments.repository)
        path = validate_relative_path(arguments.path)
        base = resolve_base(root, arguments.base)
        diff_bytes = candidate_diff(root, base, path, arguments.context)
        base_content = read_base(root, base, path)
        current_content = read_current(root, path)
        reasons = sensitivity_reasons(path, base_content, current_content, diff_bytes)
        diff = diff_bytes.decode("utf-8", errors="replace")
        if reasons:
            emit_redacted(path, reasons, diff, current_content)
        elif b"\0" in diff_bytes or b"\0" in base_content or b"\0" in current_content:
            print("contract: usable-loop/v2")
            print("record: safe-diff")
            print("inspection: binary")
            print(f"path: {path}")
        else:
            emit_raw(path, diff, arguments.max_lines, arguments.hunk, arguments.chunk)
    except (OSError, UnicodeError, SafeDiffError, subprocess.SubprocessError):
        print(
            "ERROR: safe diff inspection failed without emitting repository content",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
