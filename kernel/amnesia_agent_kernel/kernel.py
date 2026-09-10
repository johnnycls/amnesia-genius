"""Public kernel Agent API."""

import os
from collections.abc import AsyncIterator, Sequence

from amnesia_agent_kernel.agent import agent_turn
from amnesia_agent_kernel.events import Event
from amnesia_agent_kernel.history import Message
from amnesia_agent_kernel.types import RuntimeConfig
from amnesia_agent_kernel.workspace import Workspace


class Agent:
    """Frontend-agnostic agent bound to one config snapshot and workspace root."""

    def __init__(
        self,
        config: RuntimeConfig,
        workspace_root: str | os.PathLike[str] | None = None,
    ) -> None:
        self.config = config
        self._workspace = Workspace(workspace_root)

    def turn(self, user_input: str) -> AsyncIterator[Event]:
        """Return an async event iterator for one user turn."""
        return agent_turn(self.config, self._workspace, user_input)

    def read_system_prompt(self) -> str:
        return self._workspace.read_system_prompt()

    def update_system_prompt(self, content: str) -> None:
        self._workspace.update_system_prompt(content)

    def reset_system_prompt(self) -> None:
        self._workspace.reset_system_prompt()

    def read_memory(self) -> str:
        return self._workspace.read_memory()

    def update_memory(self, content: str) -> None:
        self._workspace.update_memory(content)

    def reset_memory(self) -> None:
        self._workspace.reset_memory()

    def read_history(self, date: str | None = None) -> list[Message]:
        return self._workspace.read_history(date)

    def list_history(self) -> list[str]:
        return self._workspace.list_history()

    def update_history(self, messages: Sequence[Message], date: str | None = None) -> None:
        self._workspace.update_history(messages, date)

    def reset_history(self) -> None:
        self._workspace.reset_history()

    def reset_workspace(self) -> None:
        self._workspace.reset()
