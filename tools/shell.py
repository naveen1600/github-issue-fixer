from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from tools.filesystem import ToolError

TEST_RUNNERS: list[tuple[str, list[str]]] = [
    ("pytest.ini", ["python", "-m", "pytest"]),
    ("setup.cfg", ["python", "-m", "pytest"]),
    ("pyproject.toml", ["python", "-m", "pytest"]),
    ("package.json", ["npm", "test", "--"]),
    ("go.mod", ["go", "test", "./..."]),
    ("Cargo.toml", ["cargo", "test"]),
    ("pom.xml", ["mvn", "test", "-q"]),
]

SAFE_EXTRA_ARGS = re.compile(r"^[a-zA-Z0-9_./:= \-]+$")


def _detect_runner(workspace: Path) -> list[str]:
    for marker, cmd in TEST_RUNNERS:
        if (workspace / marker).exists():
            return cmd
    return ["python", "-m", "pytest"]  # default


def run_tests(inputs: dict, workspace: Path, **_) -> str:
    cmd = list(_detect_runner(workspace))

    test_path = inputs.get("test_path")
    if test_path:
        # Basic sanitisation: no shell metacharacters
        if not SAFE_EXTRA_ARGS.match(test_path):
            raise ToolError(f"Unsafe test_path: {test_path!r}")
        cmd.append(test_path)

    extra_args = inputs.get("extra_args", "")
    if extra_args:
        if not SAFE_EXTRA_ARGS.match(extra_args):
            raise ToolError(f"Unsafe extra_args: {extra_args!r}")
        cmd.extend(extra_args.split())

    env = {**os.environ, "CI": "true", "PYTHONDONTWRITEBYTECODE": "1"}

    try:
        result = subprocess.run(
            cmd,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return "ERROR: Test run timed out after 120 seconds."
    except FileNotFoundError:
        return f"ERROR: Test runner not found: {cmd[0]!r}"

    out = (
        f"EXIT CODE: {result.returncode}\n"
        f"STDOUT:\n{result.stdout[-8_000:]}\n"
        f"STDERR:\n{result.stderr[-4_000:]}"
    )
    return out
