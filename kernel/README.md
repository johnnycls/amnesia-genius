# amnesia-agent-kernel

The frontend-agnostic kernel for the amnesia agent.

## Install

```text
pip install ./kernel
```

## API

```python
from amnesia_agent_kernel import ExecutionPolicy, KernelSession, ProviderConfig

provider = ProviderConfig(
    model="openai/example",
    api_key=None,
    base_url=None,
    provider_params=None,
)
policy = ExecutionPolicy(
    max_context_message_chars=1000,
)
session = KernelSession(provider, policy)
```

`ProviderConfig` contains only LiteLLM/provider settings. `ExecutionPolicy` contains
kernel execution and context limits. Its conservative defaults are:

- 120-second command timeout
- 256 KiB combined command output
- 1000 characters for non-user context messages

These are guardrails for trusted-local execution, not a sandbox. The bash tool
still has host filesystem, network, and process access. Use a container or VM when
the model or provider is not trusted.

## Turns and events

`KernelSession.turn(text, response_format=None)` returns an async iterator of:

- `Delta` — streamed assistant text.
- `AssistantMessage` — a complete assistant response, including tool calls.
- `ToolResult` — one result per executed bash call.

`response_format` is an optional JSON object passed to LiteLLM for providers that
support structured outputs. For example:

```python
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "answer",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
            "additionalProperties": False,
        },
    },
}

async for event in session.turn("Answer this", response_format=response_format):
    ...
```

The kernel validates that the format contains only JSON-compatible values and
makes a defensive copy before sending it to the provider. The structured result
is still exposed as the model's JSON text in `AssistantMessage.message["content"]`;
the frontend can parse it with `json.loads` after receiving the complete message.
Provider support for a particular structured-output format varies by model.

Concurrent turns on one session are queued and serialized. Tool commands are
executed concurrently. Command timeout and output-limit failures are returned as
tool-result text so the model can recover.
The process group is terminated on timeout or output overflow.

Cancellation re-raises `asyncio.CancelledError`, after persisting partial assistant
text and a `turn_cancelled` history event when possible.

## Workspace operations

The workspace implementation is internal to the kernel. Controlled read, update,
and reset operations are available through `KernelSession`; callers do not
construct or receive a Workspace object.

```python
session.read_system_prompt()
session.update_system_prompt(text)
session.reset_system_prompt()

session.read_memory()
session.update_memory(text)
session.reset_memory()

session.list_history()                 # newest ISO dates first
session.read_history()                 # newest daily history
session.read_history("2026-08-28")    # one UTC date
session.update_history(messages, "2026-08-28")
session.reset_history()
session.reset_workspace()
```

History input and persisted records are validated. Empty valid sequences remove a
history file; malformed inputs raise `WorkspaceError` without deleting it.

The bash tool schema is a kernel constant. It is not copied to the workspace and
cannot be changed through workspace files.

## Boundary

The kernel accepts a `ProviderConfig` and `ExecutionPolicy` from a frontend and
validates them during `KernelSession` initialization, including LiteLLM provider
preflight. It has no dependency on frontend configuration paths.

Expected failures use `AgentError` subclasses: `ConfigError`, `WorkspaceError`,
`ProviderError` and `ToolError`. Provider and workspace failures
propagate to the caller; ordinary shell failures and bounded execution failures
are returned to the model as tool-result text.
