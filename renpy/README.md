# Amnesia Agent Ren'Py frontend

This directory is a normal Ren'Py project. Open it with the Ren'Py launcher and run the game.

The project starts `amnesia-agent-local-server` as a child process and talks to it over
`127.0.0.1:8765`. The Ren'Py side deliberately uses only Python's standard-library HTTP and
SSE client; it does not import LiteLLM, FastAPI, or the kernel.

## Development setup

Install the server into the Python interpreter that should run beside Ren'Py:

```text
pip install ./kernel
pip install ./local_server
```

The client launches `python -m amnesia_agent_local_server` by default. Set
`AMNESIA_AGENT_PYTHON` if the server must use a specific Python executable:

```text
AMNESIA_AGENT_PYTHON=/path/to/python
```

On Windows, configure the equivalent environment variable in the shell that starts Ren'Py.

The local server owns configuration at `~/.amnesia-agent-local-server/config.json`; its kernel
workspace remains at `~/.amnesia-agent`. The Ren'Py project currently provides functional default
screens for chat, settings, system prompt, memory, and history.

## Languages and fonts

The interface includes English, Simplified Chinese, Traditional Chinese, Japanese, and Korean.
Choose a language from **Settings > Interface language**; the selection is saved in Ren'Py's
persistent data. Model responses and workspace contents are not translated, so they can use any
language supported by the configured provider.

The project bundles `game/fonts/NotoSansCJKsc-Regular.otf` and applies it to the default Ren'Py
style. This is intentional: the default Ren'Py font does not reliably contain CJK glyphs, and
switching the interface language without a CJK-capable font produces missing-character boxes.
The font is Noto Sans CJK SC, distributed under the SIL Open Font License 1.1; the license text is
included as `game/fonts/OFL.txt`. Keep both files when redistributing the game. If you replace the
font, use one with coverage for every language you keep enabled.

## Distribution

For distribution, replace the development Python command with a packaged
`amnesia-agent-local-server` executable. The client protocol and Ren'Py project do not need to
change. The server is intentionally loopback-only and executes the kernel's unrestricted bash
tool, so it should only run on a trusted desktop.
