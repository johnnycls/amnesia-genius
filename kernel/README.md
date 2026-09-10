# amnesia-agent-kernel

The frontend-agnostic kernel for the amnesia agent.

## Install

```text
pip install ./kernel
```

## API

```python
from amnesia_agent_kernel import Agent, RuntimeConfig

config = RuntimeConfig(
    model="openai/example",
    api_key=None,
    base_url=None,
    provider_params=None,
    max_context_message_chars=1000,
)
agent = Agent(config)
```

`Agent(config)` creates and uses `~/.amnesia-agent` by default and seeds missing
kernel-owned files. Pass a custom directory for tests or an embedded application:

```python
agent = Agent(config, workspace_root="/path/to/state")
```

The workspace owns:

- `system_prompt.md`
- `memory.md`
- `history.jsonl`

It does not own or read frontend configuration.

## Turns and events

`Agent.turn(text)` returns an async iterator of:

- `Delta` — streamed assistant text.
- `AssistantMessage` — a complete assistant response, including tool calls.
- `ToolResult` — one result per executed bash call.

The kernel persists user, assistant, and tool messages in `history.jsonl` as the
turn progresses. It does not automatically replay old history into model context.
The model can read the history through its bash capability when needed.

## Workspace operations

The workspace implementation is internal to the kernel. Controlled read, update,
and reset operations are available through `Agent`; callers do not construct or
receive a Workspace object.

```python
agent.read_system_prompt()
agent.update_system_prompt(text)
agent.reset_system_prompt()

agent.read_memory()
agent.update_memory(text)
agent.reset_memory()

agent.read_history()
agent.update_history(messages)
agent.reset_history()
agent.reset_workspace()
```

The bash tool schema is a kernel constant. It is not copied to the workspace and
cannot be changed through workspace files.

## Boundary

The kernel accepts a validated `RuntimeConfig` from a frontend. It has no dependency
on `amnesia_agent_cli` and no knowledge of the frontend configuration path.
