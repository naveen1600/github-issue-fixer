from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from google import genai
from google.genai import types

from agent.prompts import SYSTEM_PROMPT, build_initial_message
from config import config
from github_api.issue_reader import IssueContext
from tools import executor, registry
from tools.filesystem import list_directory
from utils.logger import get_logger

logger = get_logger(__name__)

_client = genai.Client(api_key=config.gemini_api_key)


class AgentLimitError(Exception):
    pass


@dataclass
class LoopState:
    iteration: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    files_written: list[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    final_summary: str = ""


def run_agent_loop(issue: IssueContext, workspace: Path) -> LoopState:
    dir_listing = list_directory({"path": "repo"}, workspace=workspace)
    repo_path = workspace / "repo"
    initial_message = build_initial_message(issue, repo_path, dir_listing)

    state = LoopState(start_time=time.time())

    # Build conversation history
    contents: list[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=initial_message)])
    ]

    consecutive_malformed = 0

    while True:
        # Safety gates
        if state.iteration >= config.max_iterations:
            raise AgentLimitError(f"Reached max iterations ({config.max_iterations})")
        elapsed = time.time() - state.start_time
        if elapsed > config.max_duration_seconds:
            raise AgentLimitError(f"Exceeded max duration ({config.max_duration_seconds}s)")
        total_tokens = state.total_input_tokens + state.total_output_tokens
        if total_tokens > config.token_budget:
            raise AgentLimitError(f"Exceeded token budget ({config.token_budget})")

        logger.info({
            "action": "loop_iteration",
            "iteration": state.iteration,
            "elapsed_s": round(elapsed, 1),
            "tokens": total_tokens,
        })

        response = _client.models.generate_content(
            model=config.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[registry.GEMINI_TOOLS],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )

        # Track token usage
        if response.usage_metadata:
            state.total_input_tokens += response.usage_metadata.prompt_token_count or 0
            state.total_output_tokens += response.usage_metadata.candidates_token_count or 0

        candidate = response.candidates[0]

        # Guard against empty content (safety filter or malformed function call)
        if not candidate.content or not candidate.content.parts:
            finish_reason = getattr(candidate, "finish_reason", "UNKNOWN")
            logger.warning({"action": "empty_content", "finish_reason": str(finish_reason)})
            if str(finish_reason) == "FinishReason.MALFORMED_FUNCTION_CALL":
                consecutive_malformed += 1
                if consecutive_malformed >= 3:
                    state.final_summary = "Agent stopped: too many malformed function calls."
                    break
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(text=(
                        "Your last function call was malformed — likely the content argument was too large. "
                        "Break large file writes into smaller edits, or simplify the change. "
                        "Retry with a valid, smaller function call."
                    ))]
                ))
                state.iteration += 1
                continue
            state.final_summary = f"Agent stopped: model returned no content (reason: {finish_reason})"
            break

        consecutive_malformed = 0  # reset on successful response

        # Append model turn to history
        contents.append(types.Content(role="model", parts=candidate.content.parts))

        # Collect function calls
        function_calls = [
            part.function_call
            for part in candidate.content.parts
            if part.function_call and part.function_call.name
        ]

        if not function_calls:
            # No function calls — extract text and finish
            state.final_summary = "\n".join(
                part.text for part in candidate.content.parts if part.text
            ).strip()
            logger.info({"action": "loop_complete", "iteration": state.iteration})
            break

        # Execute all function calls and collect responses
        response_parts: list[types.Part] = []
        for fc in function_calls:
            result = executor.execute(
                name=fc.name,
                inputs=dict(fc.args),
                workspace=repo_path,
                state=state,
                issue=issue,
            )
            response_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fc.name,
                        response={"result": result},
                    )
                )
            )

        # Append tool results as a user turn
        contents.append(types.Content(role="user", parts=response_parts))
        state.iteration += 1

    return state
