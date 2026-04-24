from __future__ import annotations

import re
from pathlib import Path

import git

from config import config
from utils.logger import get_logger

logger = get_logger(__name__)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:40]


def create_branch(repo_path: Path, issue_number: int, issue_title: str) -> str:
    branch_name = f"fix/issue-{issue_number}-{_slugify(issue_title)}"
    repo = git.Repo(repo_path)
    repo.git.checkout("-b", branch_name)
    logger.info({"action": "branch_created", "branch": branch_name})
    return branch_name
