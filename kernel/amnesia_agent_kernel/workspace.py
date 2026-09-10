"""Kernel-owned persistent workspace state."""

import json
import os
import shutil
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path
from typing import Any

from amnesia_agent_kernel.errors import AgentError
from amnesia_agent_kernel.history import Message

DEFAULT_WORKSPACE = Path.home() / ".amnesia-agent"
WORKSPACE_FILES: tuple[str, ...] = (
    "system_prompt.md",
    "memory.md",
    "history.jsonl",
)


def _packaged_data(name: str) -> Any:
    return files("amnesia_agent_kernel").joinpath("data", name)


class Workspace:
    """Persistent kernel state, excluding frontend-owned configuration.

    Construction creates the workspace and seeds missing kernel-owned files.
    The workspace never reads or writes frontend configuration.
    """

    def __init__(self, root: str | os.PathLike[str] | None = None) -> None:
        self.root: Path = Path(root).expanduser().absolute() if root else DEFAULT_WORKSPACE
        self.setup()

    def _path(self, filename: str) -> Path:
        return self.root / filename

    def _read_text(self, filename: str) -> str:
        path = self._path(filename)
        try:
            return path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as e:
            raise AgentError(f"Cannot read file {path}: {e}", path=str(path)) from e

    def _write_text(self, filename: str, content: str) -> None:
        path = self._path(filename)
        try:
            path.write_text(content, encoding="utf-8")
        except (OSError, UnicodeError) as e:
            raise AgentError(f"Cannot write file {path}: {e}", path=str(path)) from e

    def setup(self) -> None:
        """Create the workspace and seed missing kernel-owned files."""
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            for filename in WORKSPACE_FILES:
                path = self._path(filename)
                if not path.exists():
                    shutil.copyfile(str(_packaged_data(filename)), path)
        except OSError as e:
            raise AgentError(
                f"Cannot initialize workspace {self.root}: {e}", path=str(self.root)
            ) from e

    def reset(self) -> None:
        """Restore prompt and memory defaults and clear conversation history."""
        self._reset_from_package("system_prompt.md")
        self._reset_from_package("memory.md")
        self.update_history([])

    def _reset_from_package(self, filename: str) -> None:
        path = self._path(filename)
        try:
            shutil.copyfile(str(_packaged_data(filename)), path)
        except OSError as e:
            raise AgentError(f"Cannot reset file {path}: {e}", path=str(path)) from e

    def read_system_prompt(self) -> str:
        return self._read_text("system_prompt.md")

    def update_system_prompt(self, content: str) -> None:
        self._write_text("system_prompt.md", content)

    def reset_system_prompt(self) -> None:
        self._reset_from_package("system_prompt.md")

    def read_memory(self) -> str:
        return self._read_text("memory.md")

    def update_memory(self, content: str) -> None:
        self._write_text("memory.md", content)

    def reset_memory(self) -> None:
        self._reset_from_package("memory.md")

    def read_history(self) -> list[Message]:
        path = self._path("history.jsonl")
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
            history: list[Message] = []
            for number, line in enumerate(lines, start=1):
                if not line.strip():
                    continue
                value: Any = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"line {number} is not a JSON object")
                history.append(value)
            return history
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as e:
            raise AgentError(f"Cannot read history {path}: {e}", path=str(path)) from e

    def update_history(self, messages: Sequence[Message]) -> None:
        path = self._path("history.jsonl")
        try:
            path.write_text(
                "".join(json.dumps(message) + "\n" for message in messages),
                encoding="utf-8",
            )
        except (OSError, TypeError, ValueError) as e:
            raise AgentError(f"Cannot write history {path}: {e}", path=str(path)) from e

    def append_history(self, message: Message) -> None:
        path = self._path("history.jsonl")
        try:
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(message) + "\n")
        except (OSError, TypeError, ValueError) as e:
            raise AgentError(f"Cannot append history {path}: {e}", path=str(path)) from e

    def reset_history(self) -> None:
        self.update_history([])
