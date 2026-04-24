from __future__ import annotations

from functools import lru_cache

from github import Github

from config import config


@lru_cache(maxsize=1)
def get_github_client() -> Github:
    return Github(config.github_token)
