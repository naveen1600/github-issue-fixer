"""
One-time setup script: configures branch protection on the target repository
so that PRs created by the agent require at least one human approval before merging.

Usage:
    python scripts/setup_protection.py --repo owner/repo
    python scripts/setup_protection.py --repo owner/repo --branch main
"""
from __future__ import annotations

import argparse
import sys

from github import Github, GithubException

from config import config


def setup_branch_protection(repo_full_name: str, branch: str) -> None:
    gh = Github(config.github_token)
    try:
        repo = gh.get_repo(repo_full_name)
    except GithubException as exc:
        print(f"ERROR: Could not access repo {repo_full_name!r}: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        branch_obj = repo.get_branch(branch)
    except GithubException as exc:
        print(f"ERROR: Could not access branch {branch!r}: {exc}", file=sys.stderr)
        sys.exit(1)

    branch_obj.edit_protection(
        required_approving_review_count=1,
        dismiss_stale_reviews=True,
        require_code_owner_reviews=False,
        enforce_admins=False,
    )

    print(f"Branch protection configured on {repo_full_name}:{branch}")
    print("  - Required approving reviews: 1")
    print("  - Dismiss stale reviews: yes")
    print("  - Enforce on admins: no")
    print("\nThe agent's PRs will now require at least one human approval before merging.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Configure branch protection to require human review before merge"
    )
    parser.add_argument("--repo", required=True, help="Repository in owner/repo format")
    parser.add_argument("--branch", default=config.base_branch, help="Branch to protect")
    args = parser.parse_args()

    setup_branch_protection(args.repo, args.branch)


if __name__ == "__main__":
    main()
