from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from tools import filesystem, shell, github_tools
from tools.filesystem import ToolError
from utils.logger import get_logger

if TYPE_CHECKING:
    from agent.loop import LoopState
    from github_api.issue_reader import IssueContext

logger = get_logger(__name__)

MAX_RESULT_CHARS = 50_000


def execute(
    name: str,
    inputs: dict,
    workspace: Path,
    state: "LoopState",
    issue: "IssueContext",
) -> str:
    logger.info({"action": "tool_call", "tool": name, "inputs_keys": list(inputs.keys())})

    handlers = {
        "read_file": lambda: filesystem.read_file(inputs, workspace=workspace),
        "write_file": lambda: filesystem.write_file(inputs, workspace=workspace, state=state),
        "list_directory": lambda: filesystem.list_directory(inputs, workspace=workspace),
        "search_code": lambda: filesystem.search_code(inputs, workspace=workspace),
        "run_tests": lambda: shell.run_tests(inputs, workspace=workspace),
        "get_issue_comments": lambda: github_tools.get_issue_comments(inputs, issue=issue),
    }

    handler = handlers.get(name)
    if not handler:
        return f"ERROR: Unknown tool '{name}'"

    try:
        result = handler()
        return str(result)[:MAX_RESULT_CHARS]
    except ToolError as exc:
        return f"ERROR: {exc}"
    except Exception as exc:
        logger.exception({"action": "tool_crash", "tool": name, "error": str(exc)})
        return f"ERROR: Internal error in tool '{name}': {exc}"
