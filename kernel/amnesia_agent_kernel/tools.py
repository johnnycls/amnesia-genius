"""Bash command execution and tool-call dispatch."""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
from collections.abc import Sequence
from typing import Any

from amnesia_agent_kernel.errors import ToolError
from amnesia_agent_kernel.history import Message

logger = logging.getLogger(__name__)

BASH_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": (
            "Run a shell command and return its exit code plus combined stdout/stderr "
            "as plain text. Use it for everything: file operations, running scripts, "
            "API calls, and memory management."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to run.",
                }
            },
            "required": ["command"],
        },
    },
}


def _process_options() -> dict[str, Any]:
    """Return subprocess options that start an independent process group."""
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    if sys.platform.startswith(("linux", "darwin", "freebsd", "openbsd", "netbsd", "aix")):
        return {"start_new_session": True}
    raise ToolError(f"Unsupported process-group platform: {sys.platform}", tool="bash")


async def _terminate_process(proc: asyncio.subprocess.Process) -> None:
    """Terminate the shell and all descendants started for the command."""
    if proc.returncode is not None:
        return
    try:
        if sys.platform == "win32":
            killer = await asyncio.create_subprocess_exec(
                "taskkill",
                "/PID",
                str(proc.pid),
                "/T",
                "/F",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await killer.wait()
            if proc.returncode is None:
                proc.kill()
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except (OSError, TypeError, ValueError) as e:
        raise ToolError(f"Could not terminate bash process: {e}", tool="bash") from e
    try:
        await proc.wait()
    except (OSError, TypeError, ValueError) as e:
        raise ToolError(f"Could not wait for bash process: {e}", tool="bash") from e


async def run_bash(command: str) -> str:
    """Run a shell command and return its exit code plus combined output."""
    try:
        options = _process_options()
        proc: asyncio.subprocess.Process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **options,
        )
    except ToolError:
        raise
    except (OSError, TypeError, ValueError) as e:
        raise ToolError(f"Could not start bash command: {e}", tool="bash", command=command) from e

    if proc.stdout is None or proc.stderr is None:
        try:
            await _terminate_process(proc)
        except ToolError:
            logger.error("Bash process cleanup failed after missing output pipes", exc_info=True)
        raise ToolError("Bash process did not provide output pipes", tool="bash", command=command)
    try:
        stdout, stderr = await proc.communicate()
    except asyncio.CancelledError:
        try:
            await _terminate_process(proc)
        except ToolError:
            logger.error("Bash process cleanup failed after cancellation", exc_info=True)
        raise
    except Exception as e:
        try:
            await _terminate_process(proc)
        except ToolError:
            logger.error("Bash process cleanup also failed", exc_info=True)
        raise ToolError(
            f"Could not collect bash output: {type(e).__name__}: {e}",
            tool="bash",
            command=command,
        ) from e
    output: str = (
        stdout.decode("utf-8", "replace") + stderr.decode("utf-8", "replace")
    ).strip() or "(no output)"
    return f"exit code: {proc.returncode}\noutput: {output}"


def _parse_command(raw_arguments: str) -> str:
    """Extract the 'command' string from a tool-call arguments JSON blob."""
    arguments: Any = json.loads(raw_arguments)
    if not isinstance(arguments, dict):
        raise TypeError("tool arguments must be a JSON object")
    command: Any = arguments["command"]
    if not isinstance(command, str):
        raise TypeError("'command' must be a string")
    return command


def _tool_error_text(error: Exception) -> str:
    return f"error: {type(error).__name__}: {error}"


async def run_tool_call(call: dict[str, Any]) -> str:
    """Parse a tool call and run its bash command, returning the result text."""
    try:
        if not isinstance(call, dict):
            raise ToolError("tool call must be an object", tool="bash")
        function = call.get("function", {})
        if not isinstance(function, dict) or function.get("name") != "bash":
            raise ToolError("unknown tool; expected 'bash'", tool="bash")
        command = _parse_command(function.get("arguments", ""))
    except (AttributeError, json.JSONDecodeError, KeyError, TypeError, ToolError) as e:
        return _tool_error_text(e)
    try:
        return await run_bash(command)
    except ToolError as e:
        return _tool_error_text(e)


def _tool_message(call: dict[str, Any], content: str) -> Message:
    """Build a tool-result message matching the given tool call."""
    return {
        "role": "tool",
        "tool_call_id": call.get("id", "") if isinstance(call, dict) else "",
        "content": content,
    }


async def execute_tool_calls(
    tool_calls: Sequence[dict[str, Any]],
) -> list[Message]:
    """Execute independent calls concurrently and return results in call order."""
    tasks = [asyncio.create_task(run_tool_call(call)) for call in tool_calls]
    try:
        results = await asyncio.gather(*tasks)
    except BaseException:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
    return [
        _tool_message(call, result)
        for call, result in zip(tool_calls, results, strict=True)
    ]
