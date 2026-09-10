"""Typed errors raised by the kernel and its frontends."""


class AgentError(Exception):
    """Base class for expected application errors."""

    def __init__(self, message: str, path: str | None = None) -> None:
        super().__init__(message)
        self.path: str | None = path


class ConfigError(AgentError):
    """A configuration value or configuration resource is invalid."""


class WorkspaceError(AgentError):
    """A kernel workspace operation failed."""


class ProviderError(AgentError):
    """An LLM provider or provider response failed."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.model = model


class ToolError(AgentError):
    """A tool could not be parsed, started, or completed."""

    def __init__(
        self,
        message: str,
        tool: str | None = None,
        command: str | None = None,
    ) -> None:
        super().__init__(message)
        self.tool = tool
        self.command = command
