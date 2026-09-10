# amnesia-agent

`amnesia-agent` is a minimal self-directed LLM agent split into two independently packaged projects:

- **`amnesia-agent-kernel`** — the frontend-agnostic async agent kernel.
- **`amnesia-agent-cli`** — the terminal frontend and frontend-owned configuration store.

The model has one built-in capability: it can execute shell commands. Prompting,
memory organization, planning, and reusable skills are deliberately represented as
files in the kernel workspace rather than fixed framework features.

## Safety

The kernel executes model-generated shell commands with no sandbox, allowlist, or
confirmation. Run it in a container or virtual machine unless you fully trust the
model and workspace.

## Install the terminal application

```text
pip install ./kernel
pip install ./frontend
amnesia-agent
```

The command creates two separate user-owned directories:

```text
~/.amnesia-agent/
├── system_prompt.md
├── memory.md
└── history/
    ├── 2026-08-27.jsonl
    └── 2026-08-28.jsonl

~/.amnesia-agent-cli/
└── config.json
```

The CLI configuration is intentionally outside the kernel workspace. It is loaded,
validated, and passed to the kernel as an in-memory `RuntimeConfig`.

There is no automatic migration from the previous `~/.amnesia-genius` directory.
Copy files manually if you want to preserve old state.

## Kernel API

```python
import asyncio

from amnesia_agent_kernel import Agent, AssistantMessage, Delta, ToolResult
from amnesia_agent_cli.config import ConfigStore


async def run() -> None:
    config_store = ConfigStore()
    config_store.setup()
    config = config_store.load()
    agent = Agent(config)

    async for event in agent.turn("hello"):
        if isinstance(event, Delta):
            print(event.text, end="", flush=True)
        elif isinstance(event, AssistantMessage):
            print(event.message.get("content") or "")
        elif isinstance(event, ToolResult):
            print(event.message.get("content") or "")


asyncio.run(run())
```

The kernel does not know about `config.json`, the CLI, terminal rendering, or the
frontend package. Construct a new `Agent` when a new validated configuration
snapshot is available.

## Agent workspace API

`Agent(config)` defaults to the kernel workspace at `~/.amnesia-agent`. A custom
workspace root can be passed when embedding or testing:

```python
agent = Agent(config, workspace_root="/path/to/state")
```

The kernel exposes controlled state operations through `Agent`:

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

History is stored as one JSONL file per UTC date under `history/`. `list_history()`
returns available dates newest first. `read_history()` reads the newest date by
default or an explicitly supplied `YYYY-MM-DD` date. `reset_workspace()` restores
the packaged prompt and memory and clears all daily history files.
Configuration reset is handled separately by `ConfigStore.reset()`.

## Project layout

- [`kernel/README.md`](kernel/README.md) — kernel API and behavior.
- [`frontend/README.md`](frontend/README.md) — CLI, config, and installation details.
- [`kernel/pyproject.toml`](kernel/pyproject.toml) — kernel distribution metadata.
- [`frontend/pyproject.toml`](frontend/pyproject.toml) — frontend distribution metadata.
