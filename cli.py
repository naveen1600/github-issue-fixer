"""
CLI entry point — trigger the agent by providing a GitHub issue URL.

Usage:
    python cli.py https://github.com/owner/repo/issues/42
    python cli.py https://github.com/owner/repo/issues/42 --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import re
import sys

from agent.orchestrator import create_pr, pop_fix_result, run_fix_pipeline
from utils.logger import get_logger

logger = get_logger("cli")

_ISSUE_URL_RE = re.compile(
    r"https?://github\.com/(?P<repo>[^/]+/[^/]+)/issues/(?P<number>\d+)"
)


def parse_issue_url(url: str) -> tuple[str, int]:
    m = _ISSUE_URL_RE.match(url.strip())
    if not m:
        print(
            f"ERROR: Could not parse issue URL: {url!r}\n"
            "Expected format: https://github.com/owner/repo/issues/42",
            file=sys.stderr,
        )
        sys.exit(1)
    return m.group("repo"), int(m.group("number"))


def main() -> None:
    parser = argparse.ArgumentParser(description="GitHub Issue Fixer — provide an issue URL to fix")
    parser.add_argument("url", help="GitHub issue URL, e.g. https://github.com/owner/repo/issues/42")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the agent and commit locally but skip git push and PR creation",
    )
    args = parser.parse_args()

    repo, issue_number = parse_issue_url(args.url)
    print(f"\nStarting agent for {repo}#{issue_number} (dry_run={args.dry_run})\n")

    asyncio.run(
        run_fix_pipeline(
            repo_full_name=repo,
            issue_number=issue_number,
            dry_run=args.dry_run,
        )
    )

    if args.dry_run:
        print("\nDry run complete. No PR created.")
        return

    fix = pop_fix_result(issue_number)
    if not fix:
        print("\nAgent finished with no changes. No PR will be created.", file=sys.stderr)
        sys.exit(1)

    # Show the agent's summary for human review
    print("\n" + "=" * 60)
    print("AGENT SUMMARY — please review before raising the PR")
    print("=" * 60)
    print(f"\nFiles changed: {', '.join(fix.files_written)}")
    print(f"\n{fix.summary}")
    print("\n" + "=" * 60)

    fork_note = f" (from fork {fix.fork_full_name})" if fix.fork_full_name else ""
    print(f"\nThis will open a PR on {fix.issue.repo_full_name}{fork_note}.")
    answer = input("Create the PR? [y/N] ").strip().lower()

    if answer == "y":
        pr_url = create_pr(fix)
        print(f"\nPR created: {pr_url}")
    else:
        print(
            f"\nPR skipped. Your fix is already pushed to branch '{fix.branch}'.\n"
            f"You can open the PR manually later if you wish."
        )


if __name__ == "__main__":
    main()
