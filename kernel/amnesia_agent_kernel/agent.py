"""Provider validation, streaming, and turn orchestration."""

import asyncio
import logging
import math
from collections.abc import AsyncIterator, Mapping
from typing import Any, cast

import litellm
from litellm import acompletion

from amnesia_agent_kernel.errors import (
    AgentError,
    ConfigError,
    ProviderError,
    ToolError,
    WorkspaceError,
)
from amnesia_agent_kernel.events import AssistantMessage, Delta, Event, ToolResult
from amnesia_agent_kernel.history import Message
from amnesia_agent_kernel.message import build_messages
from amnesia_agent_kernel.tools import BASH_TOOL, execute_tool_calls
from amnesia_agent_kernel.types import ExecutionPolicy, ProviderConfig
from amnesia_agent_kernel.workspace import Workspace

logger = logging.getLogger(__name__)
_RESERVED_REQUEST_KEYS = {
    "model",
    "messages",
    "tools",
    "stream",
    "api_key",
    "api_base",
    "response_format",
}


def validate_provider_config(config: ProviderConfig) -> None:
    """Validate provider settings for direct kernel callers."""
    if not isinstance(config, ProviderConfig):
        raise ConfigError("config must be a ProviderConfig instance")
    if not isinstance(config.model, str) or not config.model.strip():
        raise ConfigError("model must be a non-empty string")
    if config.api_key is not None and not isinstance(config.api_key, str):
        raise ConfigError("api_key must be a string or None")
    if config.base_url is not None and not isinstance(config.base_url, str):
        raise ConfigError("base_url must be a string or None")
    if config.provider_params is None:
        return
    if not isinstance(config.provider_params, Mapping):
        raise ConfigError("provider_params must be a mapping")
    for name, value in config.provider_params.items():
        if not isinstance(name, str) or not name:
            raise ConfigError("provider_params keys must be non-empty strings")
        if not isinstance(value, (str, int, float, bool)):
            raise ConfigError(f"provider_params.{name} must be a scalar value")
        if isinstance(value, float) and not math.isfinite(value):
            raise ConfigError(f"provider_params.{name} must be finite")


def validate_execution_policy(policy: ExecutionPolicy) -> None:
    """Validate resource and context limits for a session."""
    if not isinstance(policy, ExecutionPolicy):
        raise ConfigError("policy must be an ExecutionPolicy instance")
    if (
        isinstance(policy.command_timeout_seconds, bool)
        or not isinstance(policy.command_timeout_seconds, (int, float))
        or not math.isfinite(policy.command_timeout_seconds)
        or policy.command_timeout_seconds <= 0
    ):
        raise ConfigError("command_timeout_seconds must be a finite positive number")
    for name in (
        "max_command_output_bytes",
        "max_context_message_chars",
    ):
        value = getattr(policy, name)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ConfigError(f"{name} must be a positive integer")


def _snapshot_json_value(value: Any, path: str) -> Any:
    """Validate and defensively copy one JSON-compatible value."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ConfigError(f"{path} must contain finite numbers")
        return value
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ConfigError(f"{path} object keys must be strings")
            copied[key] = _snapshot_json_value(item, f"{path}.{key}")
        return copied
    if isinstance(value, list):
        return [_snapshot_json_value(item, f"{path}[{index}]") for index, item in enumerate(value)]
    raise ConfigError(f"{path} must contain only JSON-compatible values")


def _snapshot_response_format(response_format: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Validate and copy a LiteLLM response format supplied for one turn."""
    if response_format is None:
        return None
    if not isinstance(response_format, Mapping):
        raise ConfigError("response_format must be a JSON object or None")
    return cast(
        dict[str, Any],
        _snapshot_json_value(response_format, "response_format"),
    )


def _request_kwargs(config: ProviderConfig, **extra: Any) -> dict[str, Any]:
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
        if not call_id:
            raise ProviderError("Streamed tool call had no ID")
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


def validate_provider_environment(config: ProviderConfig) -> None:
    """Perform LiteLLM's cheap environment check for a validated config."""
    try:
        result: Any = litellm.validate_environment(
            config.model,
            api_key=config.api_key,
            api_base=config.base_url,
        )
    except Exception as e:
        raise ProviderError(
            f"LLM config check failed: {type(e).__name__}: {e}", model=config.model
        ) from e
    if not isinstance(result, Mapping):
        raise ProviderError("LLM config check returned an invalid result", model=config.model)
    keys_in_environment = result.get("keys_in_environment", True)
    missing_keys = result.get("missing_keys")
    if not isinstance(keys_in_environment, bool):
        raise ProviderError("LLM config check returned an invalid keys status", model=config.model)
    if missing_keys is not None and (
        not isinstance(missing_keys, (list, tuple))
        or not all(isinstance(key, str) for key in missing_keys)
    ):
        raise ProviderError("LLM config check returned invalid missing keys", model=config.model)
    if not keys_in_environment and missing_keys and config.api_key is None:
        raise ProviderError(
            f"LLM config check failed: set {' or '.join(missing_keys)} "
            "in the environment, or provide credentials in the provider config.",
            model=config.model,
        )


def _provider_error(error: Exception, config: ProviderConfig) -> ProviderError:
    if isinstance(error, ProviderError):
        return error
    return ProviderError(
        f"LLM request failed: {type(error).__name__}: {error}", model=config.model
    )


def _record_turn_error(workspace: Workspace, error: AgentError) -> None:
    workspace.append_history(
        {
            "kind": "turn_error",
            "error_type": type(error).__name__,
            "message": str(error),
        }
    )


def _record_turn_cancelled(
    workspace: Workspace,
    parts: list[str],
    message_persisted: bool,
) -> None:
    if parts and not message_persisted:
        workspace.append_history({"role": "assistant", "content": "".join(parts)})
    workspace.append_history(
        {
            "kind": "turn_cancelled",
            "partial_assistant_persisted": bool(parts) and not message_persisted,
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
    config: ProviderConfig,
    policy: ExecutionPolicy,
    workspace: Workspace,
    user_input: str,
    response_format: Mapping[str, Any] | None = None,
) -> AsyncIterator[Event]:
    """Run one user turn until the model stops calling tools."""
    if not isinstance(user_input, str):
        raise ConfigError("user_input must be text")
    response_format = _snapshot_response_format(response_format)
    workspace.append_history({"role": "user", "content": user_input})
    turn_messages: list[Message] = []
    parts: list[str] = []
    message_persisted = False
    try:
        while True:
            parts = []
            message_persisted = False
            messages: list[Message] = build_messages(
                workspace.read_system_prompt(),
                user_input,
                turn_messages,
                policy.max_context_message_chars,
                workspace,
            )
            try:
                request_kwargs: dict[str, Any] = {
                    "messages": messages,
                    "tools": [BASH_TOOL],
                    "stream": True,
                }
                if response_format is not None:
                    request_kwargs["response_format"] = response_format
                response: Any = await acompletion(
                    **_request_kwargs(config, **request_kwargs)
                )
            except Exception as e:
                provider_error = _provider_error(e, config)
                try:
                    _record_turn_error(workspace, provider_error)
                except WorkspaceError as history_error:
                    raise history_error from provider_error
                raise provider_error from e

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
            except Exception as e:
                provider_error = _provider_error(e, config)
                try:
                    if parts:
                        workspace.append_history({"role": "assistant", "content": "".join(parts)})
                    _record_turn_error(workspace, provider_error)
                except WorkspaceError as history_error:
                    raise history_error from provider_error
                raise provider_error from e

            workspace.append_history(message)
            message_persisted = True
            yield AssistantMessage(message)
            tool_calls = message.get("tool_calls", [])
            if not tool_calls:
                return
            turn_messages.append(message)
            try:
                tool_messages = await execute_tool_calls(
                    tool_calls,
                    timeout_seconds=policy.command_timeout_seconds,
                    max_output_bytes=policy.max_command_output_bytes,
                )
            except ToolError as tool_error:
                _record_turn_error(workspace, tool_error)
                raise
            for tool_message in tool_messages:
                workspace.append_history(tool_message)
                yield ToolResult(tool_message)
            turn_messages.extend(tool_messages)
    except asyncio.CancelledError:
        try:
            _record_turn_cancelled(workspace, parts, message_persisted)
        except WorkspaceError:
            logger.error("Could not persist turn cancellation", exc_info=True)
        raise
