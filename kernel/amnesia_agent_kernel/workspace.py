"""Kernel-owned persistent workspace state."""

import json
import os
import re
import shutil
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path
from typing import Any

from amnesia_agent_kernel.errors import AgentError
from amnesia_agent_kernel.history import Message

DEFAULT_WORKSPACE = Path.home() / ".amnesia-agent"
WORKSPACE_FILES: tuple[str, ...] = (
    "system_prompt.md",
    "memory.md",
)
HISTORY_DIRECTORY = "history"
HISTORY_FILENAME = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})\.jsonl")


def _packaged_data(name: str) -> Any:
    return files("amnesia_agent_kernel").joinpath("data", name)


class Workspace:
    """Persistent kernel state, excluding frontend-owned configuration.

    Construction creates the workspace and seeds missing kernel-owned files.
    The workspace never reads or writes frontend configuration.
    """

    def __init__(
        self,
        root: str | os.PathLike[str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.root: Path = Path(root).expanduser().absolute() if root else DEFAULT_WORKSPACE
        self._clock = clock or (lambda: datetime.now(timezone.utc))
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

    def _today(self) -> str:
        now = self._clock()
        if now.tzinfo is None:
            current = now
        else:
            current = now.astimezone(timezone.utc)
        return current.date().isoformat()

    @staticmethod
    def _validate_date(value: str) -> str:
        if not isinstance(value, str):
            raise AgentError("History date must be an ISO date in YYYY-MM-DD format")
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as e:
            raise AgentError(
                f"Invalid history date {value!r}; expected YYYY-MM-DD"
            ) from e
        if parsed.isoformat() != value:
            raise AgentError(f"Invalid history date {value!r}; expected YYYY-MM-DD")
        return value

    def _history_path(self, date: str) -> Path:
        return self._path(HISTORY_DIRECTORY) / f"{date}.jsonl"

    def list_history(self) -> list[str]:
        """Return available daily history dates, newest first."""
        directory = self._path(HISTORY_DIRECTORY)
        if not directory.is_dir():
            return []
        dates: list[str] = []
        for path in directory.iterdir():
            match = HISTORY_FILENAME.fullmatch(path.name)
            if not match or not path.is_file():
                continue
            try:
                date = self._validate_date(match.group("date"))
            except AgentError:
                continue
            dates.append(date)
        return sorted(dates, reverse=True)

    def read_history(self, date: str | None = None) -> list[Message]:
        available_dates = self.list_history() if date is None else []
        selected_date = available_dates[0] if available_dates else date
        if selected_date is None:
            return []
        selected_date = self._validate_date(selected_date)
        path = self._history_path(selected_date)
        if not path.exists():
            return []
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

    def update_history(self, messages: Sequence[Message], date: str | None = None) -> None:
        selected_date = self._validate_date(date) if date is not None else self._today()
        path = self._history_path(selected_date)
        try:
            if not messages:
                path.unlink(missing_ok=True)
                if path.parent.is_dir() and not any(path.parent.iterdir()):
                    path.parent.rmdir()
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "".join(json.dumps(message) + "\n" for message in messages),
                encoding="utf-8",
            )
        except (OSError, TypeError, ValueError) as e:
            raise AgentError(f"Cannot write history {path}: {e}", path=str(path)) from e

    def append_history(self, message: Message) -> None:
        path = self._history_path(self._today())
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(message) + "\n")
        except (OSError, TypeError, ValueError) as e:
            raise AgentError(f"Cannot append history {path}: {e}", path=str(path)) from e

    def reset_history(self) -> None:
        directory = self._path(HISTORY_DIRECTORY)
        for date in self.list_history():
            path = self._history_path(date)
            try:
                path.unlink()
            except OSError as e:
                raise AgentError(f"Cannot reset history {path}: {e}", path=str(path)) from e
        try:
            if directory.is_dir() and not any(directory.iterdir()):
                directory.rmdir()
        except OSError as e:
            raise AgentError(
                f"Cannot reset history directory {directory}: {e}", path=str(directory)
            ) from e
