"""LLM message assembly and memory loading."""

from typing import Any

from amnesia_agent_kernel.history import Message
from amnesia_agent_kernel.workspace import Workspace


def truncate_middle(text: str, max_chars: int) -> str:
    """Keep both ends of text within the limit, joined by a middle separator."""
    if len(text) <= max_chars:
        return text
    separator = "\n...\n"
    body = max_chars - len(separator)
    if body < 2:
        return separator[:max_chars]
    half = body // 2
    return f"{text[: body - half]}{separator}{text[-half:]}"


def build_messages(
    system_prompt: str,
    user_input: str,
    turn_messages: list[Message],
    max_context_message_chars: int,
    workspace: Workspace,
) -> list[Message]:
    """Assemble system, user, and same-turn messages."""
    messages: list[Message] = [
        {
            "role": "system",
            "content": f"{system_prompt}\n\n{workspace.read_memory()}",
        },
        {"role": "user", "content": user_input},
    ]
    for message in turn_messages:
        content: Any = message.get("content")
        if (
            message.get("role") not in ("user", "system")
            and isinstance(content, str)
            and len(content) > max_context_message_chars
        ):
            message = {
                **message,
                "content": truncate_middle(content, max_context_message_chars),
            }
        messages.append(message)
    return messages
