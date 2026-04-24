from __future__ import annotations

from github_api.issue_reader import IssueContext


def get_issue_comments(inputs: dict, issue: IssueContext, **_) -> str:
    if not issue.comments:
        return "No comments on this issue."
    lines = [f"@{c.user}: {c.body}" for c in issue.comments]
    return "\n\n".join(lines)
