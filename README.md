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
- **`amnesia-agent-local-server`** — a reusable loopback FastAPI server for desktop frontends.
- **`renpy`** — a Ren'Py client project that launches the local server and streams agent events.
- **`electron`** — a responsive Electron + React + TypeScript desktop client with Tailwind CSS, multilingual icon-first UI, and a packaged FastAPI sidecar fallback.

## Safety

The kernel executes model-generated shell commands with no sandbox, allowlist, or
confirmation. Run it in a container or virtual machine unless you fully trust the
model and workspace.
