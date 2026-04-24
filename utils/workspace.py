from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)


def create_workspace(issue_number: int) -> Path:
    uid = uuid.uuid4().hex[:8]
    tmp = Path(tempfile.gettempdir()) / f"fixer-{issue_number}-{uid}"
    tmp.mkdir(parents=True, exist_ok=True)
    logger.info({"action": "workspace_created", "path": str(tmp)})
    return tmp


def delete_workspace(path: Path) -> None:
    try:
        shutil.rmtree(path, ignore_errors=True)
        logger.info({"action": "workspace_deleted", "path": str(path)})
    except Exception as exc:
        logger.warning({"action": "workspace_delete_failed", "path": str(path), "error": str(exc)})
