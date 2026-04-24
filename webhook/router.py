from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, Request

from agent import orchestrator
from config import config
from utils.logger import get_logger
from webhook.validator import verify_github_signature

logger = get_logger(__name__)
router = APIRouter()


@router.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await verify_github_signature(request)
    event = request.headers.get("X-GitHub-Event", "")
    payload = json.loads(body)

    if event == "issues":
        action = payload.get("action", "")
        issue_number: int = payload["issue"]["number"]
        repo_full_name: str = payload["repository"]["full_name"]

        should_run = action == "opened" or (
            action == "labeled"
            and payload.get("label", {}).get("name") == config.trigger_label
        )

        if should_run:
            logger.info({
                "action": "webhook_trigger",
                "event": event,
                "issue_action": action,
                "issue": issue_number,
                "repo": repo_full_name,
            })
            background_tasks.add_task(
                orchestrator.run_fix_pipeline,
                repo_full_name=repo_full_name,
                issue_number=issue_number,
                auto_pr=True,  # webhook mode: no human at keyboard, create PR immediately
            )
        else:
            logger.info({"action": "webhook_ignored", "event": event, "issue_action": action})

    # Always return 200 quickly — GitHub expects a fast response
    return {"status": "accepted"}


@router.get("/health")
async def health():
    return {"status": "ok"}
