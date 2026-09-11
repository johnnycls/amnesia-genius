# Amnesia Agent Desktop

Electron desktop client for the Amnesia Agent local server.

**Python >=3.10** | **Node.js >=18** (for development)

## Features

- React, TypeScript, Vite, and Tailwind CSS
- Responsive sidebar, icon rail, and narrow-window navigation drawer
- Icon-first chrome with localized tooltips and `aria-label`s
- English, Simplified Chinese, Traditional Chinese, Japanese, and Korean interfaces
- Streaming chat over the FastAPI Server-Sent Events endpoint
- Markdown/GFM responses, tool activity, structured choice buttons, and cancellation
- Provider settings, system prompt, memory, and read-only daily history browser

## Architecture

```text
Electron main process
  ├─ main.ts              (window, IPC, lifecycle)
  ├─ server.ts            (LocalServerProcess — sidecar/child management)
  └─ preload.ts           (contextBridge → window.desktop API)
       └─ React renderer (src/renderer/)
            ├─ features/  (chat, workspace, history, settings)
            ├─ hooks/
            ├─ i18n/
            └─ layout/    (sidebar, icon rail, nav drawer)
```

The main process manages the FastAPI sidecar (`amnesia-agent-local-server`).
It looks for a packaged executable in `resources/server/`; if absent, it falls
back to `python -m amnesia_agent_local_server`. Set `AMNESIA_AGENT_PYTHON`
when a specific Python executable should be used.

The renderer communicates with the main process exclusively through the
preload bridge (`window.desktop`). The server is verified by its random
`instance_id` on startup.

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

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `AMNESIA_AGENT_PYTHON` | `python` | Python executable for the sidecar |
| `AMNESIA_AGENT_AUTOSTART` | `true` | Auto-start the server on app launch |

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

## Source structure

```text
src/
├── main/                  # Electron main process (TypeScript)
│   ├── main.ts            # Window creation, IPC, lifecycle
│   ├── server.ts          # Sidecar/child process management
│   └── preload.ts         # Context bridge API
├── shared/                # Types and utilities shared across processes
├── renderer/              # React frontend
│   ├── features/          # Feature modules (chat, workspace, history, settings)
│   ├── components/        # Shared UI components
│   ├── hooks/             # React hooks
│   ├── i18n/              # Internationalization (5 languages)
│   ├── layout/            # Sidebar, icon rail, navigation drawer
│   └── lib/               # Utilities
scripts/
└── build-sidecar.py       # PyInstaller sidecar build script
```

Generated files are intentionally ignored by [`electron/.gitignore`](.gitignore). Keep `package-lock.json` committed for reproducible installs.

## Troubleshooting

**Sidecar not found** — In development, the server falls back to
`python -m amnesia_agent_local_server`. Ensure the Python packages are
installed (`pip install -e ../kernel -e ../local_server`). For packaged
builds, run `npm run build:server` before `npm run build`.

**Server won't start** — The server binds to `127.0.0.1:8765`. If another
process is using that port, stop it first. Check the Electron console for
error output.

**TypeScript errors** — Run `npm run typecheck` to see all errors. The
Electron main process and renderer have separate tsconfig files.

**Tests fail** — Run `npm test` (vitest). Tests cover SSE parsing, input
validation, and i18n configuration.
