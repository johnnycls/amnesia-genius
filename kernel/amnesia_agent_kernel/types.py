"""Public configuration types for the kernel."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, TypeAlias

Message: TypeAlias = dict[str, Any]
ScalarValue: TypeAlias = str | int | float | bool


@dataclass(frozen=True)
class ProviderConfig:
    """LiteLLM configuration supplied by a frontend."""

    model: str
    api_key: str | None = None
    base_url: str | None = None
    provider_params: Mapping[str, ScalarValue] | None = None

    def snapshot(self) -> "ProviderConfig":
        """Return an immutable defensive copy of this provider configuration."""
        params = (
            MappingProxyType(dict(self.provider_params))
            if self.provider_params is not None
            else None
        )
        return ProviderConfig(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            provider_params=params,
        )


@dataclass(frozen=True)
class ExecutionPolicy:
    """Validated limits for one kernel session.

    The defaults are guardrails for trusted-local execution, not a sandbox.
    Shell commands still have access to the host unless the deployment provides
    isolation separately.
    """

    command_timeout_seconds: float = 120.0
    max_command_output_bytes: int = 256 * 1024
    max_context_message_chars: int = 1000
