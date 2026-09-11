# Building Amnesia Agent Desktop

The Electron app is self-contained in this directory. The Python service remains in `../local_server` and the kernel remains in `../kernel`.

## Development

Install the Python packages into the interpreter you want Electron to use:

```bash
pip install -e ../kernel -e ../local_server
npm install
npm run dev
```

During development, Electron first looks for a sidecar in `resources/server`. If it is not present, it starts `python -m amnesia_agent_local_server` (or the executable in `AMNESIA_AGENT_PYTHON`). The server always binds to `127.0.0.1:8765` and Electron verifies its generated `instance_id` before marking the connection ready.

## Build a sidecar

Install PyInstaller into the same Python environment as the local packages:

```bash
pip install -e ../kernel -e ../local_server pyinstaller
npm run build:server
```

The script writes the native executable to `resources/server`:

- Windows: `amnesia-agent-local-server.exe`
- macOS/Linux: `amnesia-agent-local-server`

The executable is intentionally not committed. A normal development checkout does not need it.

## Build the Electron app

```bash
npm run typecheck
npm test
npm run build
```

`electron-builder` packages the renderer and Electron process. If a sidecar exists, it is copied into the packaged app’s resources. For a distributable build, run `npm run build:server` before `npm run build`.

## Cross-platform GitHub Actions

The repository's `.github/workflows/ci.yml` builds all three native artifacts by using a matrix. Each runner installs the local Python packages, builds the sidecar on that runner, then builds the Electron package for the same platform. The relevant job follows this pattern:

```yaml
name: desktop-build
on: [push, workflow_dispatch]
jobs:
  package:
    strategy:
      matrix:
        include:
          - os: windows-latest
            artifact: windows
          - os: macos-latest
            artifact: macos
          - os: ubuntu-latest
            artifact: linux
    runs-on: ${{ matrix.os }}
    defaults:
      run:
        working-directory: electron
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ../kernel -e ../local_server pyinstaller
      - run: npm ci
      - run: npm run build:server
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: amnesia-agent-${{ matrix.artifact }}
          path: electron/release/**
```

The sidecar must be built on the target operating system. PyInstaller does not produce a Windows executable from macOS or Linux, so the matrix is required.
