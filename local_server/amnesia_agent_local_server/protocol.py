"""Typed request models and structured-output helpers for the local API."""

from typing import Any

from pydantic import BaseModel, Field


class TurnRequest(BaseModel):
    """One user turn."""

    text: str = Field(min_length=1)


class ContentRequest(BaseModel):
    """Text content for a workspace update."""

    content: str


class ConfigUpdate(BaseModel):
    """Partial config update; omitted values retain their current values."""

    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    provider_params: dict[str, Any] | None = None
    command_timeout_seconds: float | int | None = None
    max_command_output_bytes: int | None = None
    max_context_message_chars: int | None = None


class StructuredAnswer(BaseModel):
    """The stable structured response requested from the provider."""

    answer: str
    choices: list[str]


RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "answer_with_choices",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "choices": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["answer", "choices"],
            "additionalProperties": False,
        },
    },
}
