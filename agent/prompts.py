from __future__ import annotations

from pathlib import Path

from github_api.issue_reader import IssueContext

SYSTEM_PROMPT = """\
You are an expert software engineer fixing GitHub issues in real codebases.

YOUR PROCESS:
1. Read and fully understand the issue title, body, and comments.
2. Explore the repository structure with list_directory.
3. Search for relevant code with search_code before reading specific files.
4. Read relevant files carefully with read_file before modifying anything.
5. Make the minimal necessary changes to fix the issue — do not refactor unrelated code.
6. After making changes, use run_tests to verify you haven't broken anything.
7. If tests fail, read the output carefully and fix your changes.
8. When confident the fix is correct and complete, STOP calling tools.
9. Write a clear summary of exactly what you changed and why as your final response.

CONSTRAINTS:
- Only modify files within the repository. Never access files outside the workspace.
- Make the smallest change that correctly fixes the issue.
- Do not install packages, make network requests, or run arbitrary shell commands.
- If you cannot determine a safe fix, explain why in your final response instead of guessing.
- The fix will be reviewed by a human before merging. Focus on correctness.

FINAL RESPONSE FORMAT (after all tool calls are complete):
## Changes Made
[List each file modified and what changed]

## Why This Fixes The Issue
[Explanation linking the change to the root cause]

## Testing
[What tests you ran and their results]
"""


def build_initial_message(issue: IssueContext, workspace: Path, dir_listing: str) -> str:
    comments_text = (
        "\n\n".join(f"**@{c.user}**: {c.body}" for c in issue.comments)
        if issue.comments
        else "No comments."
    )

    return (
        f"Please fix the following GitHub issue.\n\n"
        f"## Issue #{issue.number}: {issue.title}\n\n"
        f"**Description:**\n{issue.body}\n\n"
        f"**Labels:** {', '.join(issue.labels) or 'none'}\n\n"
        f"**Comments:**\n{comments_text}\n\n"
        f"---\n\n"
        f"## Repository\n\n"
        f"The cloned repository is at: `{workspace}`\n\n"
        f"Top-level contents:\n```\n{dir_listing}\n```\n\n"
        f"Begin by exploring the codebase to understand the structure, "
        f"then locate and fix the issue."
    )
