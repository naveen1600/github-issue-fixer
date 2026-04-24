from __future__ import annotations

import time

from github import GithubException

from github_api.client import get_github_client
from utils.logger import get_logger

logger = get_logger(__name__)


def has_push_access(repo_full_name: str) -> bool:
    gh = get_github_client()
    try:
        repo = gh.get_repo(repo_full_name)
        return repo.permissions.push
    except GithubException:
        return False


def get_or_create_fork(upstream_full_name: str) -> str:
    """
    Returns the full name (owner/repo) of the authenticated user's fork.
    Creates the fork if it doesn't exist yet and waits for it to be ready.
    """
    gh = get_github_client()
    upstream = gh.get_repo(upstream_full_name)
    user = gh.get_user()

    fork_full_name = f"{user.login}/{upstream.name}"

    # Check if fork already exists
    try:
        gh.get_repo(fork_full_name)
        logger.info({"action": "fork_exists", "fork": fork_full_name})
        return fork_full_name
    except GithubException:
        pass

    # Create the fork
    logger.info({"action": "forking", "upstream": upstream_full_name})
    user.create_fork(upstream)

    # Wait for fork to be ready (GitHub forks are async)
    for _ in range(12):
        time.sleep(5)
        try:
            gh.get_repo(fork_full_name)
            logger.info({"action": "fork_ready", "fork": fork_full_name})
            return fork_full_name
        except GithubException:
            continue

    raise RuntimeError(f"Fork {fork_full_name} was not ready after 60 seconds")
