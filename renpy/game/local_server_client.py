"""Small standard-library client used by the Ren'Py project.

This file intentionally does not import FastAPI, LiteLLM, or the kernel. The
local server runs in a separate normal-Python process.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import renpy  # type: ignore[import-not-found]
except ImportError:  # Allows the parser/client helpers to be tested outside Ren'Py.
    renpy = None  # type: ignore[assignment]


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


class LocalServerError(RuntimeError):
    """Raised when the local server cannot be reached or reports an error."""


class TurnHandle:
    """A cancellable direct SSE request."""

    def __init__(self) -> None:
        self._cancelled = threading.Event()
        self._response: Any = None
        self._lock = threading.Lock()

    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set()

    def attach(self, response: Any) -> None:
        with self._lock:
            self._response = response
            if self.cancelled:
                response.close()

    def cancel(self) -> None:
        self._cancelled.set()
        with self._lock:
            response = self._response
        if response is not None:
            response.close()


class LocalServerClient:
    """Own the child process and expose synchronous/background HTTP helpers."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        python_command: str | None = None,
        startup_timeout: float = 15.0,
    ) -> None:
        self.host = host
        self.port = port
        self.python_command = python_command or os.environ.get(
            "AMNESIA_AGENT_PYTHON", "python"
        )
        self.startup_timeout = startup_timeout
        self.process: subprocess.Popen[Any] | None = None
        self.instance_id: str | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        """Start our child and verify that the fixed port belongs to it."""
        if self.process is not None and self.process.poll() is None:
            return
        self.instance_id = uuid.uuid4().hex
        command = [
            self.python_command,
            "-m",
            "amnesia_agent_local_server",
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--instance-id",
            self.instance_id,
        ]
        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
            )
        except OSError as error:
            raise LocalServerError(f"Cannot start local server: {error}") from error

        deadline = time.monotonic() + self.startup_timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise LocalServerError("Local server exited before becoming ready")
            try:
                health = self.request_json("GET", "/v1/health", timeout=0.5)
            except LocalServerError:
                time.sleep(0.1)
                continue
            if health.get("instance_id") != self.instance_id:
                self.stop()
                raise LocalServerError(
                    f"Port {self.port} is already occupied by another local server"
                )
            return
        self.stop()
        raise LocalServerError(f"Local server did not become ready on port {self.port}")

    def stop(self) -> None:
        """Request graceful shutdown, then terminate only our child process."""
        process = self.process
        self.process = None
        if process is None:
            return
        if process.poll() is None:
            try:
                self.request_json("POST", "/v1/shutdown", timeout=1.0)
            except LocalServerError:
                pass
            try:
                process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    def request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            self.base_url + path,
            data=body,
            headers={"Content-Type": "application/json"} if body is not None else {},
            method=method,
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except (HTTPError, URLError, OSError) as error:
            raise LocalServerError(f"Local server request failed: {error}") from error
        try:
            value: Any = json.loads(raw)
        except json.JSONDecodeError as error:
            raise LocalServerError("Local server returned invalid JSON") from error
        if not isinstance(value, dict):
            raise LocalServerError("Local server returned a non-object response")
        if "detail" in value:
            raise LocalServerError(str(value["detail"]))
        return value

    def stream_turn(
        self,
        text: str,
        on_event: Callable[[dict[str, Any]], None],
        on_error: Callable[[Exception], None],
        on_complete: Callable[[], None],
    ) -> TurnHandle:
        """Stream one turn on a background thread until completion or cancellation."""
        handle = TurnHandle()

        def run() -> None:
            request = Request(
                self.base_url + "/v1/turn",
                data=json.dumps({"text": text}).encode("utf-8"),
                headers={
                    "Accept": "text/event-stream",
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                },
                method="POST",
            )
            try:
                with urlopen(request, timeout=None) as response:
                    handle.attach(response)
                    for event in parse_sse(response):
                        if handle.cancelled:
                            return
                        dispatch(on_event, event)
                        if event.get("type") == "done":
                            dispatch(on_complete)
                            return
            except (HTTPError, URLError, OSError) as error:
                if not handle.cancelled:
                    dispatch(
                        on_error, LocalServerError(f"Turn request failed: {error}")
                    )
            except Exception as error:
                if not handle.cancelled:
                    dispatch(on_error, error)

        threading.Thread(target=run, name="amnesia-agent-turn", daemon=True).start()
        return handle


def parse_sse(lines: Iterator[Any]) -> Iterator[dict[str, Any]]:
    """Parse the small SSE subset emitted by local_server."""
    for raw_line in lines:
        if isinstance(raw_line, bytes):
            line = raw_line.decode("utf-8")
        else:
            line = str(raw_line)
        line = line.rstrip("\r\n")
        if not line.startswith("data:"):
            continue
        try:
            value: Any = json.loads(line[5:].lstrip())
        except json.JSONDecodeError as error:
            raise LocalServerError(
                "Local server returned malformed SSE JSON"
            ) from error
        if isinstance(value, dict):
            yield value


def dispatch(callback: Callable[..., None], *args: Any) -> None:
    """Run callbacks on Ren'Py's main thread when inside the game."""
    if renpy is not None:
        renpy.invoke_in_main_thread(callback, *args)
    else:
        callback(*args)
