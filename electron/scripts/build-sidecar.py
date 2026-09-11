"""Build the local FastAPI server as a platform-native PyInstaller sidecar.

Run from the electron directory after installing the local packages and PyInstaller:
    pip install ../kernel ../local_server pyinstaller
    python scripts/build-sidecar.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ELECTRON_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = ELECTRON_DIR.parent
OUTPUT_DIR = ELECTRON_DIR / "resources" / "server"
BUILD_DIR = ELECTRON_DIR / ".sidecar-build"
ENTRYPOINT = ELECTRON_DIR / ".sidecar-entry.py"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in OUTPUT_DIR.iterdir():
        if path.name != ".gitkeep":
            shutil.rmtree(path) if path.is_dir() else path.unlink()

    ENTRYPOINT.write_text(
        "from amnesia_agent_local_server.__main__ import main\nmain()\n",
        encoding="utf-8",
    )
    separator = ";" if os.name == "nt" else ":"
    data_source = REPO_DIR / "local_server" / "amnesia_agent_local_server" / "data"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        "amnesia-agent-local-server",
        "--distpath",
        str(OUTPUT_DIR),
        "--workpath",
        str(BUILD_DIR / "work"),
        "--specpath",
        str(BUILD_DIR),
        "--paths",
        str(REPO_DIR / "kernel"),
        "--paths",
        str(REPO_DIR / "local_server"),
        "--add-data",
        f"{data_source}{separator}amnesia_agent_local_server/data",
        str(ENTRYPOINT),
    ]
    try:
        subprocess.run(command, cwd=ELECTRON_DIR, check=True)
    finally:
        ENTRYPOINT.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
