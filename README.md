# amnesia-agent

> **The only harness that never goes stale is the one that barely exists.**

A minimal self-directed LLM agent. The kernel gives the model one tool (bash) and
lets it manage its own memory, capabilities, and workspace. Every operating
decision belongs to the model.

**Python >=3.10** | **MIT License**

## Why

AI's power is computing strategy dynamically from the environment. But we keep
wrapping that dynamic intelligence in static harnesses — predefined memory
managers, fixed tool sets, hardcoded workflows. Every feature we add (plan mode,
goal mode, sub-agents) is a fair strategy that helps dumb models perform
decently. But as models get smarter, these harnesses stop being scaffolding and
start being straitjackets.

This project makes one design decision: make a minimal core that never changes,
then design nothing else. Every operating decision belongs to the model, and it
keeps re-deciding as conditions change:

- **Its own memory** — there is no memory system here. A static memory manager can't be optimal in every situation; a blank `memory.md` and a free agent can. What to remember, how to organize it, when to read it back — decided by the model, per task.
- **Its own capabilities** — nothing is impossible with bash: install packages, call APIs, compile code, write scripts. Whatever ability the agent lacks, it builds itself into its workspace, not into this code.
- **Its own workspace** — everything it learns, builds, and improves lives in `~/.amnesia-agent/`. Task after task, the workspace grows while the program running it stays exactly the same.

An agent doesn't need dozens of bespoke tools; it needs **one tool that can do everything**, and the freedom to use it. The harness's only jobs are relaying messages, executing bash, failing loudly when something breaks — and it does them as a **headless kernel**: the terminal CLI is just one front-end, and you can build others (web UIs, bots, voice agents) on the same core.

## Quick start

```text
pip install ./kernel
pip install ./cli
amnesia-agent
```

Set your model and API key in `~/.amnesia-agent-cli/config.json` (the CLI opens
it automatically when configuration is missing).

## Packages

`amnesia-agent` is a minimal self-directed LLM agent split into five sub-projects:

| Package | Description |
|---|---|
| [`kernel/`](kernel/) | Frontend-agnostic async agent kernel — the core. |
| [`cli/`](cli/) | Minimal terminal CLI and configuration store. |
| [`local_server/`](local_server/) | Reusable loopback FastAPI server for desktop frontends. |
| [`electron/`](electron/) | Responsive Electron + React + TypeScript desktop client. |
| [`renpy/`](renpy/) | Ren'Py client that launches the local server and streams agent events. |

## Project structure

```text
amnesia-agent/
├── kernel/                  # amnesia-agent-kernel (pip package)
│   └── amnesia_agent_kernel/
├── cli/                     # amnesia-agent-cli (pip package)
│   └── amnesia_agent_cli/
├── local_server/            # amnesia-agent-local-server (pip package)
│   └── amnesia_agent_local_server/
├── electron/                # amnesia-agent-desktop (npm package)
│   └── src/
├── renpy/                   # Ren'Py game project
│   └── game/
└── .github/workflows/ci.yml
```

The **kernel** is the core. The **CLI** and **local server** both depend on it.
The **Electron** app and **Ren'Py** frontend both talk to the local server over
HTTP, streaming agent events via Server-Sent Events.

## Development

Install all Python packages in editable mode:

```text
pip install -e ./kernel -e ./cli -e ./local_server
```

Run linters and type checks:

```text
cd kernel && ruff check . && mypy
cd cli && ruff check . && mypy
cd local_server && ruff check . && mypy
```

Run tests:

```text
cd kernel && python -m unittest discover
cd cli && python -m unittest discover
cd local_server && python -m unittest discover
cd renpy && python -m unittest discover
cd electron && npm test
```

See each sub-project's README for specific setup instructions.

## Safety

The kernel executes model-generated shell commands with no sandbox, allowlist, or
confirmation. Run it in a container or virtual machine unless you fully trust the
model and workspace.

## License

MIT -- see [LICENSE](LICENSE).
