"""LLM turn orchestration, streaming, and tool dispatch."""

import asyncio
import math
from collections.abc import AsyncIterator, Mapping
from typing import Any

import litellm
from litellm import acompletion

from amnesia_agent_kernel.errors import ConfigError, ProviderError, WorkspaceError
from amnesia_agent_kernel.events import AssistantMessage, Delta, Event, ToolResult
from amnesia_agent_kernel.history import Message
from amnesia_agent_kernel.message import build_messages
from amnesia_agent_kernel.tools import BASH_TOOL, execute_tool_calls
from amnesia_agent_kernel.types import RuntimeConfig
from amnesia_agent_kernel.workspace import Workspace

_RESERVED_REQUEST_KEYS = {"model", "messages", "tools", "stream", "api_key", "api_base"}


def validate_runtime_values(config: RuntimeConfig) -> None:
    """Validate RuntimeConfig values for direct kernel callers."""
    if not isinstance(config, RuntimeConfig):
        raise ConfigError("config must be a RuntimeConfig instance")
    if not isinstance(config.model, str) or not config.model.strip():
        raise ConfigError("model must be a non-empty string")
    if config.api_key is not None and not isinstance(config.api_key, str):
        raise ConfigError("api_key must be a string or None")
    if config.base_url is not None and not isinstance(config.base_url, str):
        raise ConfigError("base_url must be a string or None")
    if (
        isinstance(config.max_context_message_chars, bool)
        or not isinstance(config.max_context_message_chars, int)
        or config.max_context_message_chars <= 0
    ):
        raise ConfigError("max_context_message_chars must be a positive integer")
    if config.provider_params is None:
        return
    if not isinstance(config.provider_params, dict):
        raise ConfigError("provider_params must be a dictionary")
    for name, value in config.provider_params.items():
        if not isinstance(name, str) or not name:
            raise ConfigError("provider_params keys must be non-empty strings")
        if not isinstance(value, (str, int, float, bool)):
            raise ConfigError(f"provider_params.{name} must be a scalar value")
        if isinstance(value, float) and not math.isfinite(value):
            raise ConfigError(f"provider_params.{name} must be finite")


def _request_kwargs(config: RuntimeConfig, **extra: Any) -> dict[str, Any]:
    """Build LiteLLM kwargs, with kernel-controlled request values winning."""
    kwargs: dict[str, Any] = {
        key: value
        for key, value in (config.provider_params or {}).items()
        if key not in _RESERVED_REQUEST_KEYS
    }
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
    tool_calls: list[dict[str, Any]] = []
    for index, slot in sorted(calls.items()):
        if not isinstance(index, int) or index < 0 or not isinstance(slot, dict):
            raise ProviderError("Malformed streamed tool call index")
        function = slot.get("function")
        if not isinstance(function, dict):
            raise ProviderError("Malformed streamed tool call function")
        name = function.get("name", "")
        arguments = function.get("arguments", "")
        call_id = slot.get("id", "")
        if not all(isinstance(value, str) for value in (call_id, name, arguments)):
            raise ProviderError("Malformed streamed tool call fields")
        if not name:
            raise ProviderError("Streamed tool call had no function name")
        tool_calls.append(
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": arguments},
            }
        )
    if tool_calls:
        message["tool_calls"] = tool_calls
    return message


def validate_runtime_config(config: RuntimeConfig) -> None:
    """Perform LiteLLM's cheap environment check for a validated config."""
    try:
        result: Any = litellm.validate_environment(config.model)
    except Exception as e:
        raise ProviderError(
            f"LLM config check failed: {type(e).__name__}: {e}", model=config.model
        ) from e
    if not isinstance(result, Mapping):
        raise ProviderError(
            "LLM config check returned an invalid result", model=config.model
        )
    keys_in_environment = result.get("keys_in_environment", True)
    missing_keys = result.get("missing_keys")
    if not isinstance(keys_in_environment, bool):
        raise ProviderError("LLM config check returned an invalid keys status", model=config.model)
    if missing_keys is not None and (
        not isinstance(missing_keys, (list, tuple))
        or not all(isinstance(key, str) for key in missing_keys)
    ):
        raise ProviderError("LLM config check returned invalid missing keys", model=config.model)
    if (
        not keys_in_environment
        and missing_keys
        and config.api_key is None
        and not config.provider_params
    ):
        raise ProviderError(
            f"LLM config check failed: set {' or '.join(missing_keys)} "
            "in the environment, or provide credentials in the frontend config.",
            model=config.model,
        )


def _provider_error(error: Exception, config: RuntimeConfig) -> ProviderError:
    if isinstance(error, ProviderError):
        return error
    return ProviderError(
        f"LLM request failed: {type(error).__name__}: {error}", model=config.model
    )


def _record_turn_error(
    workspace: Workspace,
    parts: list[str],
    error: ProviderError,
) -> None:
    """Persist partial output and a sidecar event before re-raising a provider error."""
    if parts:
        workspace.append_history({"role": "assistant", "content": "".join(parts)})
    workspace.append_history(
        {
            "kind": "turn_error",
            "error_type": type(error).__name__,
            "message": str(error),
        }
    )


def _stream_delta(chunk: Any) -> Any:
    choices = getattr(chunk, "choices", None)
    if not isinstance(choices, list) or not choices:
        raise ProviderError("LLM stream returned no choices")
    delta = getattr(choices[0], "delta", None)
    if delta is None:
        raise ProviderError("LLM stream returned no delta")
    return delta


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
        try:
            response: Any = await acompletion(
                **_request_kwargs(config, messages=messages, tools=[BASH_TOOL], stream=True)
            )
        except Exception as e:
            provider_error = _provider_error(e, config)
            try:
                _record_turn_error(workspace, [], provider_error)
            except WorkspaceError as history_error:
                raise history_error from provider_error
            raise provider_error from e

        parts: list[str] = []
        calls: dict[int, dict[str, Any]] = {}
        try:
            async for chunk in response:
                delta = _stream_delta(chunk)
                content = getattr(delta, "content", None)
                if content is not None and not isinstance(content, str):
                    raise ProviderError("LLM stream content was not text")
                if content:
                    parts.append(content)
                    yield Delta(content)
                raw_calls = getattr(delta, "tool_calls", None)
                if raw_calls is not None and not isinstance(raw_calls, list):
                    raise ProviderError("LLM stream tool calls were malformed")
                for call in raw_calls or []:
                    index = getattr(call, "index", None)
                    if index is None:
                        index = 0
                    if not isinstance(index, int) or index < 0:
                        raise ProviderError("LLM stream tool call index was invalid")
                    slot = calls.setdefault(
                        index, {"id": "", "function": {"name": "", "arguments": ""}}
                    )
                    call_id = getattr(call, "id", None)
                    if call_id is not None and not isinstance(call_id, str):
                        raise ProviderError("LLM stream tool call ID was invalid")
                    if call_id:
                        slot["id"] = call_id
                    function = getattr(call, "function", None)
                    if function is None:
                        continue
                    name = getattr(function, "name", None)
                    arguments = getattr(function, "arguments", None)
                    if name is not None and not isinstance(name, str):
                        raise ProviderError("LLM stream tool name was invalid")
                    if arguments is not None and not isinstance(arguments, str):
                        raise ProviderError("LLM stream tool arguments were invalid")
                    if name:
                        slot["function"]["name"] = name
                    if arguments:
                        slot["function"]["arguments"] += arguments
            message = _assistant_message(parts, calls)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            provider_error = _provider_error(e, config)
            try:
                _record_turn_error(workspace, parts, provider_error)
            except WorkspaceError as history_error:
                raise history_error from provider_error
            raise provider_error from e

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
