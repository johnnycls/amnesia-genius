"""Terminal rendering of kernel events for the demo CLI."""

import ctypes
import json
import logging
import re
import sys
from typing import Any

from amnesia_agent_kernel.events import AssistantMessage, Delta, ToolResult

MAX_TOOL_LINES: int = 4
EXIT_PATTERN = re.compile(r"exit code: (-?\d+)")
ENABLE_VIRTUAL_TERMINAL_PROCESSING: int = 0x0004
logger = logging.getLogger(__name__)
_ANSI_ENABLED = True


def _enable_ansi() -> None:
    """Enable ANSI escape processing on Windows consoles when possible."""
    global _ANSI_ENABLED
    if sys.platform != "win32":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            if not kernel32.SetConsoleMode(
                handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            ):
                _ANSI_ENABLED = False
    except (AttributeError, OSError, TypeError, ValueError):
        _ANSI_ENABLED = False
        logger.debug("ANSI terminal support is unavailable", exc_info=True)


_enable_ansi()


def clear() -> None:
    """Clear the terminal screen (only when attached to a real terminal)."""
    try:
        if not sys.stdout.isatty():
            return
        sys.stdout.write("\x1b[2J\x1b[1H")
        sys.stdout.flush()
    except OSError:
        logger.debug("Could not clear terminal", exc_info=True)


def _wrap(code: str, text: str) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if _ANSI_ENABLED else text


def _bold(text: str) -> str:
    return _wrap("1", text)


def _dim(text: str) -> str:
    return _wrap("2", text)


def _green(text: str) -> str:
    return _wrap("32", text)


def _red(text: str) -> str:
    return _wrap("31", text)


def _tool_command(call: dict[str, Any]) -> str:
    """Extract the bash command string from a tool-call argument blob."""
    raw: Any = ""
    try:
        function = call.get("function", {})
        raw = function.get("arguments", "") if isinstance(function, dict) else ""
        arguments: Any = json.loads(raw)
        command: Any = arguments["command"]
        if isinstance(command, str):
            return command
    except (AttributeError, json.JSONDecodeError, TypeError, KeyError):
        pass
    try:
        return str(raw)
    except Exception:
        return "<unreadable tool arguments>"


def _print_tool(content: Any) -> None:
    """Render a tool result, highlighting the exit code and limiting long output."""
    if not isinstance(content, str):
        content = "<invalid tool result>"
    lines: list[str] = content.splitlines()
    match = EXIT_PATTERN.match(lines[0]) if lines else None
    if match is None:
        print(_dim(content))
        return
    code: int = int(match.group(1))
    status: str = _green(f"exit code {code}") if code == 0 else _red(f"exit code {code}")
    print(status)
    body: list[str] = lines[1:]
    if len(body) <= MAX_TOOL_LINES:
        for line in body:
            print(_dim(f"  {line}"))
        return
    half = MAX_TOOL_LINES // 2
    for line in body[:half]:
        print(_dim(f"  {line}"))
    print(_dim("..."))
    for line in body[-half:]:
        print(_dim(f"  {line}"))


class TerminalRenderer:
    """Renders kernel events to the terminal, tracking streamed text."""

    def __init__(self) -> None:
        self._streaming = False

    def reset(self) -> None:
        """Close a half-finished stream (e.g. after an interrupted turn)."""
        if self._streaming:
            self._streaming = False
            try:
                print("\x1b[0m" if _ANSI_ENABLED else "")
            except OSError:
                logger.debug("Could not reset terminal formatting", exc_info=True)

    def render(self, event: Any) -> None:
        """Render one kernel event using safe fallbacks for malformed data."""
        if isinstance(event, Delta):
            text = event.text if isinstance(event.text, str) else str(event.text)
            if not self._streaming:
                self._streaming = True
                print("\x1b[1m" if _ANSI_ENABLED else "", end="", flush=True)
            print(text, end="", flush=True)
        elif isinstance(event, AssistantMessage):
            message = event.message if isinstance(event.message, dict) else {}
            content = message.get("content")
            if not isinstance(content, str):
                content = "" if content is None else str(content)
            if self._streaming:
                self._streaming = False
                print("\x1b[0m" if _ANSI_ENABLED else "")
            elif content:
                print(_bold(content))
            calls = message.get("tool_calls")
            if not isinstance(calls, list):
                calls = []
            for call in calls:
                if isinstance(call, dict):
                    print(_dim(f"$ {_tool_command(call)}"))
        elif isinstance(event, ToolResult):
            message = event.message if isinstance(event.message, dict) else {}
            _print_tool(message.get("content"))
        else:
            logger.debug("Ignoring unknown render event: %r", event)
