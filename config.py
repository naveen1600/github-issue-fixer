from __future__ import annotations

import json
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # Gemini
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_model: str = Field("gemini-2.0-flash")

    # GitHub
    github_token: str = Field(..., description="GitHub Fine-Grained PAT")
    trigger_label: str = Field("ai-fix")
    base_branch: str = Field("main")
    required_reviewers: list[str] = Field(default_factory=list)

    # Agent limits
    max_iterations: int = Field(30)
    max_duration_seconds: int = Field(600)
    token_budget: int = Field(200_000)

    # Server
    host: str = Field("0.0.0.0")
    port: int = Field(8000)

    @field_validator("required_reviewers", mode="before")
    @classmethod
    def parse_reviewers(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v  # type: ignore[return-value]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


config = Config()  # type: ignore[call-arg]
