"""LLM turn orchestration, streaming, and tool dispatch."""

from collections.abc import AsyncIterator
from typing import Any

import litellm
from litellm import acompletion

from amnesia_agent_kernel.errors import AgentError
from amnesia_agent_kernel.events import AssistantMessage, Delta, Event, ToolResult
from amnesia_agent_kernel.history import Message
from amnesia_agent_kernel.message import build_messages
from amnesia_agent_kernel.tools import BASH_TOOL, execute_tool_calls
from amnesia_agent_kernel.types import RuntimeConfig
from amnesia_agent_kernel.workspace import Workspace


def _request_kwargs(config: RuntimeConfig, **extra: Any) -> dict[str, Any]:
    """Build LiteLLM kwargs, with explicit request values winning."""
    kwargs: dict[str, Any] = dict(config.provider_params) if config.provider_params else {}
    kwargs.update(extra)
    kwargs["model"] = config.model
    if config.api_key is not None:
        kwargs["api_key"] = config.api_key
    if config.base_url is not None:
        kwargs["api_base"] = config.base_url
    return kwargs


def _assistant_message(parts: list[str], calls: dict[int, dict[str, Any]]) -> Message:
    """Build the assistant message from streamed content and tool-call slots."""
    message: Message = {"role": "assistant", "content": "".join(parts)}
    tool_calls = [
        {"id": slot["id"], "type": "function", "function": slot["function"]}
        for _, slot in sorted(calls.items())
    ]
    if tool_calls:
        message["tool_calls"] = tool_calls
    return message


def validate_runtime_config(config: RuntimeConfig) -> None:
    """Perform LiteLLM's cheap environment check for a validated config."""
    try:
        result: dict[str, Any] = litellm.validate_environment(config.model)
    except Exception as e:
        raise AgentError(f"LLM config check failed: {type(e).__name__}: {e}") from e
    if (
        not result.get("keys_in_environment", True)
        and result.get("missing_keys")
        and config.api_key is None
        and not config.provider_params
    ):
        raise AgentError(
            f"LLM config check failed: set {' or '.join(result['missing_keys'])} "
            "in the environment, or provide credentials in the frontend config."
        )


async def agent_turn(
    config: RuntimeConfig,
    workspace: Workspace,
    user_input: str,
) -> AsyncIterator[Event]:
    """Run one user turn until the model stops calling tools."""
    workspace.append_history({"role": "user", "content": user_input})
    turn_messages: list[Message] = []
    while True:
        messages: list[Message] = build_messages(
            workspace.read_system_prompt(),
            user_input,
            turn_messages,
            config.max_context_message_chars,
            workspace,
        )
        response: Any = await acompletion(
            **_request_kwargs(config, messages=messages, tools=[BASH_TOOL], stream=True)
        )
        parts: list[str] = []
        calls: dict[int, dict[str, Any]] = {}
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue
            content = getattr(delta, "content", None)
            if content:
                parts.append(content)
                yield Delta(content)
            for call in getattr(delta, "tool_calls", None) or []:
                index = call.index if call.index is not None else 0
                slot = calls.setdefault(
                    index, {"id": "", "function": {"name": "", "arguments": ""}}
                )
                if call.id:
                    slot["id"] = call.id
                function = getattr(call, "function", None)
                if function is not None:
                    if function.name:
                        slot["function"]["name"] = function.name
                    if function.arguments:
                        slot["function"]["arguments"] += function.arguments
        message = _assistant_message(parts, calls)
        workspace.append_history(message)
        yield AssistantMessage(message)
        if not message.get("tool_calls"):
            return
        turn_messages.append(message)
        tool_messages: list[Message] = await execute_tool_calls(message["tool_calls"])
        for tool_message in tool_messages:
            workspace.append_history(tool_message)
            yield ToolResult(tool_message)
        turn_messages.extend(tool_messages)
