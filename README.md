# amnesia-agent

> **The only harness that never goes stale is the one that barely exists.**

Every harness expires. The moment the model, the environment, or the user changes, its rules go stale. amnesia-genius was born from refusing to ship rules at all.

## Why

Traditional programming means humans define static rules while AI means algorithms compute strategy dynamically from the environment. The power of AI is the ability to solve problems that can hardly solved by static rules. Wrapping dynamic intelligence in a static harness obviously contradicts the very purpose of AI but we are all building harness.

Every feature we make (e.g. plan mode, goal mode, memory system, sub-agents) is static and fair strategy that help stupid llm to perform fairly well. However as models get smarter, these harnesses stop being scaffolding and start being straitjackets.

So this project makes one design decision: make a minimal core that never changes, then design nothing else. Every operating decision belongs to the model, and it keeps re-deciding as conditions change:

- **Its own memory** — there is no memory system here. A static memory manager can't be optimal in every situation; a blank `memory.md` and a free agent can. What to remember, how to organize it, when to read it back — decided by the model, per task.
- **Its own capabilities** — nothing is impossible with bash: install packages, call APIs, compile code, write scripts. Whatever ability the agent lacks, it builds itself into its workspace, not into this code.
- **Its own workspace** — everything it learns, builds, and improves lives in `~/.amnesia-genius/`. Task after task, the workspace grows while the program running it stays exactly the same.

An agent doesn't need dozens of bespoke tools; it needs **one tool that can do everything**, and the freedom to use it. The harness's only jobs are relaying messages, executing bash, failing loudly when something breaks — and it does them as a **headless kernel**: the terminal CLI is just one front-end, and you can build others (web UIs, bots, voice agents) on the same core.

## Packages

`amnesia-agent` is a minimal self-directed LLM agent split into two independently packaged projects:

- **`amnesia-agent-kernel`** — the frontend-agnostic async agent kernel.
- **`amnesia-agent-cli`** — the minimal terminal CLI demo and CLI-owned configuration store.

## Safety

The kernel executes model-generated shell commands with no sandbox, allowlist, or
confirmation. Run it in a container or virtual machine unless you fully trust the
model and workspace.

## Install the terminal application

```text
pip install ./kernel
pip install ./cli
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
validated, and passed to the kernel as in-memory `ProviderConfig` and `ExecutionPolicy` values.

There is no automatic migration from the previous `~/.amnesia-genius` directory.
Copy files manually if you want to preserve old state.

## Kernel API

```python
import asyncio

from amnesia_agent_kernel import AssistantMessage, Delta, KernelSession, ToolResult
from amnesia_agent_cli.config import ConfigStore


async def run() -> None:
    config_store = ConfigStore()
    config_store.setup()
    loaded = config_store.load()
    session = KernelSession(loaded.provider, loaded.policy)

    async for event in session.turn("hello"):
        if isinstance(event, Delta):
            print(event.text, end="", flush=True)
        elif isinstance(event, AssistantMessage):
            print(event.message.get("content") or "")
        elif isinstance(event, ToolResult):
            print(event.message.get("content") or "")


asyncio.run(run())
```

A frontend can request structured model output for an individual turn by passing
LiteLLM's `response_format` object:

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

async for event in session.turn("hello", response_format=response_format):
    ...
```

The completed assistant event contains the structured response as JSON text in
`event.message["content"]`; the frontend may parse it with `json.loads`.

The kernel does not know about `config.json`, the CLI, terminal rendering, or the
CLI package. Construct a new `KernelSession` when a new validated configuration
snapshot is available.

## Session workspace API

`KernelSession(provider, policy)` defaults to the kernel workspace at
`~/.amnesia-agent`. A custom workspace root can be passed when embedding or
testing:

```python
session = KernelSession(provider, policy, workspace_root="/path/to/state")
```

The kernel exposes controlled state operations through `KernelSession`:

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

History is stored as one JSONL file per UTC date under `history/`. `list_history()`
returns available dates newest first. `read_history()` reads the newest date by
default or an explicitly supplied `YYYY-MM-DD` date. `reset_workspace()` restores
the packaged prompt and memory and clears all daily history files.
Configuration reset is handled separately by `ConfigStore.reset()`.

## Project layout

- [`kernel/README.md`](kernel/README.md) — kernel API and behavior.
- [`cli/README.md`](cli/README.md) — CLI, config, and installation details.
- [`kernel/pyproject.toml`](kernel/pyproject.toml) — kernel distribution metadata.
- [`cli/pyproject.toml`](cli/pyproject.toml) — CLI distribution metadata.
