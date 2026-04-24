from __future__ import annotations

import fnmatch
import re
from pathlib import Path

MAX_FILE_BYTES = 100_000  # 100 KB cap per read


class ToolError(Exception):
    pass


def _safe_path(workspace: Path, relative: str) -> Path:
    resolved = (workspace / relative).resolve()
    try:
        resolved.relative_to(workspace.resolve())
    except ValueError:
        raise ToolError(f"Path traversal denied: {relative!r}")
    return resolved


def read_file(inputs: dict, workspace: Path, **_) -> str:
    path = _safe_path(workspace, inputs["path"])
    if not path.exists():
        raise ToolError(f"File not found: {inputs['path']!r}")
    if not path.is_file():
        raise ToolError(f"Not a file: {inputs['path']!r}")

    content = path.read_text(encoding="utf-8", errors="replace")

    start = inputs.get("start_line")
    end = inputs.get("end_line")
    if start is not None or end is not None:
        lines = content.splitlines(keepends=True)
        s = (start or 1) - 1
        e = end or len(lines)
        content = "".join(lines[s:e])

    if len(content.encode()) > MAX_FILE_BYTES:
        content = content[:MAX_FILE_BYTES] + "\n... [TRUNCATED — use start_line/end_line to read more] ..."

    return content


def write_file(inputs: dict, workspace: Path, state, **_) -> str:
    path = _safe_path(workspace, inputs["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(inputs["content"], encoding="utf-8")
    state.files_written.append(inputs["path"])
    return f"Written {len(inputs['content'])} chars to {inputs['path']}"


def list_directory(inputs: dict, workspace: Path, **_) -> str:
    path = _safe_path(workspace, inputs.get("path", "."))
    if not path.exists():
        raise ToolError(f"Directory not found: {inputs['path']!r}")
    if not path.is_dir():
        raise ToolError(f"Not a directory: {inputs['path']!r}")

    recursive: bool = inputs.get("recursive", False)

    lines: list[str] = []
    if recursive:
        for p in sorted(path.rglob("*")):
            if _is_ignored(p):
                continue
            rel = p.relative_to(workspace)
            suffix = "/" if p.is_dir() else ""
            lines.append(str(rel) + suffix)
    else:
        for p in sorted(path.iterdir()):
            if _is_ignored(p):
                continue
            rel = p.relative_to(workspace)
            suffix = "/" if p.is_dir() else ""
            lines.append(str(rel) + suffix)

    return "\n".join(lines) if lines else "(empty)"


def search_code(inputs: dict, workspace: Path, **_) -> str:
    pattern = inputs["pattern"]
    file_glob = inputs.get("file_glob", "*")
    flags = 0 if inputs.get("case_sensitive", True) else re.IGNORECASE

    try:
        regex = re.compile(pattern, flags)
    except re.error as exc:
        raise ToolError(f"Invalid regex: {exc}")

    results: list[str] = []
    for filepath in workspace.rglob("*"):
        if not filepath.is_file():
            continue
        if _is_ignored(filepath):
            continue
        if not fnmatch.fnmatch(filepath.name, file_glob):
            continue
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if regex.search(line):
                rel = filepath.relative_to(workspace)
                results.append(f"{rel}:{lineno}: {line.rstrip()}")
                if len(results) >= 500:
                    results.append("... [SEARCH TRUNCATED at 500 matches] ...")
                    return "\n".join(results)

    return "\n".join(results) if results else "No matches found."


def _is_ignored(path: Path) -> bool:
    ignored_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
    return any(part in ignored_dirs for part in path.parts)
