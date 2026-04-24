from __future__ import annotations

from dataclasses import dataclass, field

from github_api.client import get_github_client
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class IssueComment:
    user: str
    body: str


@dataclass
class IssueContext:
    repo_full_name: str
    number: int
    title: str
    body: str
    labels: list[str]
    comments: list[IssueComment] = field(default_factory=list)


def fetch_issue(repo_full_name: str, issue_number: int) -> IssueContext:
    gh = get_github_client()
    repo = gh.get_repo(repo_full_name)
    issue = repo.get_issue(issue_number)

    comments = [
        IssueComment(user=c.user.login, body=c.body)
        for c in issue.get_comments()
    ]

    ctx = IssueContext(
        repo_full_name=repo_full_name,
        number=issue_number,
        title=issue.title,
        body=issue.body or "",
        labels=[lbl.name for lbl in issue.labels],
        comments=comments,
    )
    logger.info({"action": "issue_fetched", "issue": issue_number, "comments": len(comments)})
    return ctx
