from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from config import config

app = FastAPI(title="GitHub Issue Fixer Agent", version="1.0.0")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=False,
    )
