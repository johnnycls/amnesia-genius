# Amnesia Agent Desktop

This directory contains the Electron desktop client for the Amnesia Agent local server.

## Features

- React, TypeScript, Vite, and Tailwind CSS
- Responsive sidebar, icon rail, and narrow-window navigation drawer
- Icon-first chrome with localized tooltips and `aria-label`s
- English, 简体中文, 繁體中文, 日本語, and 한국어 interfaces
- Streaming chat over the FastAPI Server-Sent Events endpoint
- Markdown/GFM responses, tool activity, structured choice buttons, and cancellation
- Provider settings, system prompt, memory, and read-only daily history browser

The UI is organized by feature under `src/renderer/features`, with shared components, hooks, localization, and API-facing utilities separated into their own modules.

## Development

From this directory:

```bash
pip install -e ../kernel -e ../local_server
npm ci
npm run dev
```

Electron starts the local server on `127.0.0.1:8765`. If `resources/server` does not contain a packaged sidecar, development falls back to:

```text
python -m amnesia_agent_local_server
```

Set `AMNESIA_AGENT_PYTHON` when a specific Python executable should be used.

## Checks and packaging

```bash
npm run typecheck
npm test
npm run build
```

For a packaged application with a native FastAPI sidecar:

```bash
pip install -e ../kernel -e ../local_server pyinstaller
npm run build:server
npm run build
```

The sidecar must be built on the target operating system. See [`docs/BUILDING.md`](docs/BUILDING.md) for Windows, macOS, Linux, and GitHub Actions packaging guidance.

Generated files are intentionally ignored by [`electron/.gitignore`](.gitignore). Keep `package-lock.json` committed for reproducible installs.
