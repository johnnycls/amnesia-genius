"""Kernel-owned persistent workspace state."""

import json
import os
import re
import shutil
import stat
import tempfile
import threading
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path
from typing import Any, ClassVar

from amnesia_agent_kernel.errors import WorkspaceError
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
    """Persistent kernel state, excluding frontend-owned configuration."""

    _lock_registry_guard: ClassVar[Any] = threading.Lock()
    _lock_registry: ClassVar[dict[str, Any]] = {}

    @classmethod
    def _lock_for_root(cls, root: Path) -> Any:
        key = os.path.normcase(str(root))
        with cls._lock_registry_guard:
            lock = cls._lock_registry.get(key)
            if lock is None:
                lock = threading.RLock()
                cls._lock_registry[key] = lock
            return lock

    def __init__(
        self,
        root: str | os.PathLike[str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if root is not None and (
            isinstance(root, bool) or not isinstance(root, (str, os.PathLike))
        ):
            raise WorkspaceError(f"Invalid workspace root {root!r}")
        if root == "":
            raise WorkspaceError("Workspace root must not be empty")
        try:
            self.root: Path = (
                Path(root).expanduser().absolute() if root is not None else DEFAULT_WORKSPACE
            )
        except (OSError, TypeError, ValueError) as e:
            raise WorkspaceError(f"Invalid workspace root {root!r}: {e}") from e
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._history_lock = self._lock_for_root(self.root)
        self.setup()

    def _path(self, filename: str) -> Path:
        return self.root / filename

    def _read_text(self, filename: str) -> str:
        path = self._path(filename)
        try:
            return path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as e:
            raise WorkspaceError(f"Cannot read file {path}: {e}", path=str(path)) from e

    def _write_text(self, filename: str, content: str) -> None:
        path = self._path(filename)
        try:
            path.write_text(content, encoding="utf-8")
        except (OSError, UnicodeError, TypeError) as e:
            raise WorkspaceError(f"Cannot write file {path}: {e}", path=str(path)) from e

    def setup(self) -> None:
        """Create the workspace and seed missing kernel-owned files."""
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            for filename in WORKSPACE_FILES:
                path = self._path(filename)
                if not path.exists():
                    shutil.copyfile(str(_packaged_data(filename)), path)
        except (ModuleNotFoundError, OSError, TypeError, ValueError) as e:
            raise WorkspaceError(
                f"Cannot initialize workspace {self.root}: {e}", path=str(self.root)
            ) from e

    def reset(self) -> None:
        """Restore defaults and attempt every reset operation before reporting failures."""
        failures: list[WorkspaceError] = []
        for operation in (
            self.reset_system_prompt,
            self.reset_memory,
            self.reset_history,
        ):
            try:
                operation()
            except WorkspaceError as e:
                failures.append(e)
        if failures:
            details = "; ".join(str(error) for error in failures)
            raise WorkspaceError(
                f"Workspace reset incomplete: {details}", path=str(self.root)
            ) from failures[0]

    def _reset_from_package(self, filename: str) -> None:
        path = self._path(filename)
        try:
            shutil.copyfile(str(_packaged_data(filename)), path)
        except (ModuleNotFoundError, OSError, TypeError, ValueError) as e:
            raise WorkspaceError(f"Cannot reset file {path}: {e}", path=str(path)) from e

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
        try:
            now = self._clock()
            if not isinstance(now, datetime):
                raise TypeError("clock must return datetime")
            current = now if now.tzinfo is None else now.astimezone(timezone.utc)
            return current.date().isoformat()
        except WorkspaceError:
            raise
        except Exception as e:
            raise WorkspaceError(f"Cannot determine current UTC date: {e}") from e

    @staticmethod
    def _validate_date(value: str) -> str:
        if not isinstance(value, str):
            raise WorkspaceError("History date must be an ISO date in YYYY-MM-DD format")
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as e:
            raise WorkspaceError(
                f"Invalid history date {value!r}; expected YYYY-MM-DD"
            ) from e
        if parsed.isoformat() != value:
            raise WorkspaceError(f"Invalid history date {value!r}; expected YYYY-MM-DD")
        return value

    def _history_path(self, date: str) -> Path:
        return self._path(HISTORY_DIRECTORY) / f"{date}.jsonl"

    def list_history(self) -> list[str]:
        """Return available daily history dates, newest first."""
        with self._history_lock:
            return self._list_history_unlocked()

    def _list_history_unlocked(self) -> list[str]:
        directory = self._path(HISTORY_DIRECTORY)
        dates: list[str] = []
        try:
            try:
                directory_mode = directory.stat().st_mode
            except FileNotFoundError:
                return []
            if not stat.S_ISDIR(directory_mode):
                return []
            for path in directory.iterdir():
                match = HISTORY_FILENAME.fullmatch(path.name)
                if not match or not stat.S_ISREG(path.stat().st_mode):
                    continue
                try:
                    date = self._validate_date(match.group("date"))
                except WorkspaceError:
                    continue
                dates.append(date)
        except OSError as e:
            raise WorkspaceError(
                f"Cannot enumerate history directory {directory}: {e}",
                path=str(directory),
            ) from e
        return sorted(dates, reverse=True)

    @staticmethod
    def _validate_history_record(value: Any, number: int) -> Message:
        if not isinstance(value, dict):
            raise ValueError(f"line {number} is not a JSON object")
        if "role" not in value and "kind" not in value:
            raise ValueError(f"line {number} is not a message or history event")
        if "role" in value:
            role = value["role"]
            if role not in ("system", "user", "assistant", "tool"):
                raise ValueError(f"line {number} has an invalid role")
            if "content" in value and value["content"] is not None and not isinstance(
                value["content"], str
            ):
                raise ValueError(f"line {number} has invalid content")
            if role == "tool" and (
                not isinstance(value.get("tool_call_id"), str)
                or not value["tool_call_id"]
            ):
                raise ValueError(f"line {number} has an invalid tool call ID")
        if "kind" in value and not isinstance(value["kind"], str):
            raise ValueError(f"line {number} has an invalid event kind")
        return value

    def read_history(self, date: str | None = None) -> list[Message]:
        with self._history_lock:
            available_dates = self._list_history_unlocked() if date is None else []
            selected_date = available_dates[0] if available_dates else date
            if selected_date is None:
                return []
            selected_date = self._validate_date(selected_date)
            path = self._history_path(selected_date)
            try:
                try:
                    mode = path.stat().st_mode
                except FileNotFoundError:
                    return []
                if not stat.S_ISREG(mode):
                    raise IsADirectoryError(path)
                lines = path.read_text(encoding="utf-8").splitlines()
                history: list[Message] = []
                for number, line in enumerate(lines, start=1):
                    if not line.strip():
                        continue
                    history.append(self._validate_history_record(json.loads(line), number))
                return history
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as e:
                raise WorkspaceError(f"Cannot read history {path}: {e}", path=str(path)) from e

    @staticmethod
    def _serialize_history(messages: Sequence[Message]) -> str:
        try:
            validated = [
                Workspace._validate_history_record(message, number)
                for number, message in enumerate(messages, start=1)
            ]
            return "".join(json.dumps(message, allow_nan=False) + "\n" for message in validated)
        except (TypeError, ValueError, OverflowError) as e:
            raise WorkspaceError(f"Cannot serialize history: {e}") from e

    def update_history(self, messages: Sequence[Message], date: str | None = None) -> None:
        if isinstance(messages, (str, bytes, bytearray)) or not isinstance(messages, Sequence):
            raise WorkspaceError("History messages must be a sequence of message objects")
        selected_date = self._validate_date(date) if date is not None else self._today()
        path = self._history_path(selected_date)
        with self._history_lock:
            try:
                if not messages:
                    path.unlink(missing_ok=True)
                    if path.parent.is_dir() and not any(path.parent.iterdir()):
                        path.parent.rmdir()
                    return
                path.parent.mkdir(parents=True, exist_ok=True)
                content = self._serialize_history(messages)
                self._atomic_replace(path, content)
            except WorkspaceError as e:
                if e.path is None:
                    raise WorkspaceError(str(e), path=str(path)) from e
                raise
            except (OSError, TypeError, ValueError, OverflowError) as e:
                raise WorkspaceError(f"Cannot write history {path}: {e}", path=str(path)) from e

    @staticmethod
    def _atomic_replace(path: Path, content: str) -> None:
        temporary: str | None = None
        try:
            fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            temporary = None
        except OSError:
            raise
        finally:
            if temporary is not None:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass

    def append_history(self, message: Message) -> None:
        path = self._history_path(self._today())
        try:
            content = self._serialize_history([message])
        except WorkspaceError as e:
            raise WorkspaceError(str(e), path=str(path)) from e
        with self._history_lock:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a", encoding="utf-8") as stream:
                    stream.write(content)
                    stream.flush()
                    os.fsync(stream.fileno())
            except (OSError, TypeError, ValueError, OverflowError) as e:
                raise WorkspaceError(f"Cannot append history {path}: {e}", path=str(path)) from e

    def reset_history(self) -> None:
        directory = self._path(HISTORY_DIRECTORY)
        failures: list[WorkspaceError] = []
        with self._history_lock:
            try:
                dates = self.list_history()
            except WorkspaceError:
                raise
            for date in dates:
                path = self._history_path(date)
                try:
                    path.unlink()
                except OSError as e:
                    failures.append(
                        WorkspaceError(f"Cannot reset history {path}: {e}", path=str(path))
                    )
            try:
                try:
                    directory_mode = directory.stat().st_mode
                except FileNotFoundError:
                    directory_mode = None
                if directory_mode is not None and stat.S_ISDIR(directory_mode) and not any(
                    directory.iterdir()
                ):
                    directory.rmdir()
            except OSError as e:
                failures.append(
                    WorkspaceError(
                        f"Cannot reset history directory {directory}: {e}",
                        path=str(directory),
                    )
                )
        if failures:
            details = "; ".join(str(error) for error in failures)
            raise WorkspaceError(
                f"History reset incomplete: {details}", path=str(directory)
            ) from failures[0]
