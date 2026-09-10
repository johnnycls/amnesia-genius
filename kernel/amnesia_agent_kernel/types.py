"""Public runtime types shared between the kernel and its frontends."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeConfig:
    """Validated model configuration supplied by a frontend."""

    model: str
    api_key: str | None
    base_url: str | None
    provider_params: dict[str, str | int | float | bool] | None
    max_context_message_chars: int
