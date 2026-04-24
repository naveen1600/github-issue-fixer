from __future__ import annotations

from pathlib import Path

import git

from config import config
from utils.logger import get_logger

logger = get_logger(__name__)


def clone_repo(repo_full_name: str, workspace: Path, upstream_full_name: str | None = None) -> Path:
    """
    Clone repo_full_name into workspace/repo.
    If upstream_full_name is provided (fork workflow), the upstream is added
    as a remote called 'upstream' so git history is complete.
    """
    clone_url = (
        f"https://x-access-token:{config.github_token}"
        f"@github.com/{repo_full_name}.git"
    )
    dest = workspace / "repo"
    logger.info({"action": "cloning", "repo": repo_full_name, "dest": str(dest)})
    repo = git.Repo.clone_from(clone_url, dest)

    if upstream_full_name:
        upstream_url = f"https://github.com/{upstream_full_name}.git"
        repo.create_remote("upstream", upstream_url)
        logger.info({"action": "upstream_added", "upstream": upstream_full_name})

    logger.info({"action": "cloned", "repo": repo_full_name})
    return dest
