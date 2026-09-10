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
- `history/YYYY-MM-DD.jsonl` daily history files (UTC dates)

It does not own or read frontend configuration.

## Turns and events

`Agent.turn(text)` returns an async iterator of:

- `Delta` — streamed assistant text.
- `AssistantMessage` — a complete assistant response, including tool calls.
- `ToolResult` — one result per executed bash call.

The kernel persists user, assistant, and tool messages in the current UTC day's
`history/YYYY-MM-DD.jsonl` as the turn progresses. It does not automatically replay
old history into model context. The model can read the history files through its bash
capability when needed.

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

agent.list_history()                 # newest ISO dates first
agent.read_history()                 # newest daily history
agent.read_history("2026-08-28")    # one UTC date
agent.update_history(messages, "2026-08-28")
agent.reset_history()
agent.reset_workspace()
```

The bash tool schema is a kernel constant. It is not copied to the workspace and
cannot be changed through workspace files.

The old root-level `history.jsonl`, if present from an earlier version, is retained
but ignored. New workspaces do not seed that legacy file.

## Boundary

The kernel accepts a `RuntimeConfig` from a frontend and validates it again during
`Agent(config)` initialization, including LiteLLM provider preflight. It has no
dependency on `amnesia_agent_cli` and no knowledge of the frontend configuration path.

Expected failures use `AgentError` subclasses: `ConfigError`, `WorkspaceError`,
`ProviderError`, and `ToolError`. Provider and workspace failures propagate to the
caller; ordinary shell failures are returned to the model as tool-result text.
