from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent.loop import AgentLimitError, run_agent_loop
from git_ops import brancher, cloner, committer
from git_ops.committer import CommitError
from github_api import issue_reader, pr_creator
from github_api.fork_manager import get_or_create_fork, has_push_access
from github_api.issue_reader import IssueContext
from utils import workspace as ws_utils
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FixResult:
    """Holds everything needed to create the PR after human review."""
    issue: IssueContext
    branch: str
    summary: str
    files_written: list[str]
    fork_full_name: str | None


async def run_fix_pipeline(
    repo_full_name: str,
    issue_number: int,
    dry_run: bool = False,
    auto_pr: bool = False,
) -> str | None:
    """
    Full pipeline: fetch issue → clone → branch → agent loop → commit → push.

    After pushing, pauses and returns a FixResult for human review.
    The PR is only created when create_pr() is called explicitly.

    If auto_pr=True the PR is created immediately (webhook mode).
    Returns the PR URL when auto_pr=True, otherwise None (CLI handles PR step).
    """
    workspace: Path | None = None
    try:
        logger.info({"action": "pipeline_start", "repo": repo_full_name, "issue": issue_number})

        # 1. Fetch issue details
        issue = issue_reader.fetch_issue(repo_full_name, issue_number)

        # 2. Detect access level — fork if needed
        fork_full_name: str | None = None
        if has_push_access(repo_full_name):
            clone_from = repo_full_name
            logger.info({"action": "access_direct", "repo": repo_full_name})
        else:
            fork_full_name = get_or_create_fork(repo_full_name)
            clone_from = fork_full_name
            logger.info({"action": "access_forked", "fork": fork_full_name})

        # 3. Create isolated workspace
        workspace = ws_utils.create_workspace(issue_number)

        # 4. Clone and link upstream if forked
        cloner.clone_repo(
            clone_from,
            workspace,
            upstream_full_name=repo_full_name if fork_full_name else None,
        )

        # 5. Create fix branch
        branch = brancher.create_branch(workspace / "repo", issue_number, issue.title)

        # 6. Run the agentic loop
        state = run_agent_loop(issue, workspace)

        if not state.files_written:
            logger.warning({"action": "no_files_written", "issue": issue_number})
            return None

        # 7. Commit and push
        committer.commit_and_push(
            workspace / "repo",
            branch,
            issue,
            state.final_summary,
            dry_run=dry_run,
            push_to=fork_full_name,
        )

        if dry_run:
            logger.info({"action": "dry_run_complete", "files_written": state.files_written})
            return None

        fix_result = FixResult(
            issue=issue,
            branch=branch,
            summary=state.final_summary,
            files_written=state.files_written,
            fork_full_name=fork_full_name,
        )

        if auto_pr:
            return create_pr(fix_result)

        # Return fix_result via a module-level store so cli.py can retrieve it
        _pending_fix[issue_number] = fix_result
        return None

    except CommitError as exc:
        logger.error({"action": "commit_error", "error": str(exc)})
    except AgentLimitError as exc:
        logger.error({"action": "agent_limit", "error": str(exc)})
    except Exception as exc:
        logger.exception({"action": "pipeline_error", "error": str(exc)})
    finally:
        if workspace:
            ws_utils.delete_workspace(workspace)

    return None


# Stores FixResult between pipeline completion and PR creation
_pending_fix: dict[int, FixResult] = {}


def pop_fix_result(issue_number: int) -> FixResult | None:
    return _pending_fix.pop(issue_number, None)


def create_pr(fix: FixResult) -> str:
    pr_url = pr_creator.create_pull_request(
        fix.issue, fix.branch, fix.summary, fork_full_name=fix.fork_full_name
    )
    logger.info({"action": "pr_created", "pr_url": pr_url})
    return pr_url
