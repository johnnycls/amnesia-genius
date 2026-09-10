"""Frontend-owned configuration storage and validation."""

import json
import os
import shutil
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

from amnesia_agent_kernel import AgentError, RuntimeConfig, validate_runtime_config

DEFAULT_CONFIG_DIR = Path.home() / ".amnesia-agent-cli"
PROVIDER_PARAM_TYPES: tuple[type, ...] = (str, int, float, bool)
ScalarValue = str | int | float | bool


def _packaged_config() -> Any:
    return files("amnesia_agent_cli").joinpath("data", "config.json")


@dataclass(frozen=True)
class ConfigStore:
    """Persistent frontend configuration, separate from the kernel workspace."""

    root: Path = DEFAULT_CONFIG_DIR

    def __init__(self, root: str | os.PathLike[str] | None = None) -> None:
        object.__setattr__(
            self,
            "root",
            Path(root).expanduser().absolute() if root else DEFAULT_CONFIG_DIR,
        )

    @property
    def path(self) -> Path:
        return self.root / "config.json"

    def setup(self) -> None:
        """Create the config directory and seed a missing config file."""
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                shutil.copyfile(str(_packaged_config()), self.path)
        except OSError as e:
            raise AgentError(
                f"Cannot initialize config {self.path}: {e}", path=str(self.path)
            ) from e

    def reset(self) -> None:
        """Restore the packaged default config file."""
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(str(_packaged_config()), self.path)
        except OSError as e:
            raise AgentError(f"Cannot reset config {self.path}: {e}", path=str(self.path)) from e

    def load(self) -> RuntimeConfig:
        """Load, validate, and preflight the frontend config."""
        raw_value: Any
        try:
            with self.path.open(encoding="utf-8-sig") as f:
                raw_value = json.load(f)
        except OSError as e:
            raise AgentError(f"Cannot read file {self.path}: {e}", path=str(self.path)) from e
        except (UnicodeError, json.JSONDecodeError) as e:
            raise AgentError(f"Malformed JSON in {self.path}: {e}", path=str(self.path)) from e

        config = self._parse(raw_value)
        try:
            validate_runtime_config(config)
        except AgentError as e:
            raise AgentError(str(e), path=str(self.path)) from e
        return config

    def _parse(self, raw_value: Any) -> RuntimeConfig:
        if not isinstance(raw_value, dict):
            raise AgentError("config.json must contain a JSON object.", path=str(self.path))
        raw: dict[str, Any] = raw_value
        context_limit: Any = raw.get("max_context_message_chars")
        missing = [
            key
            for key in ("model", "max_context_message_chars")
            if not raw.get(key)
        ]
        if missing:
            raise AgentError(
                f"Missing or empty {', '.join(repr(k) for k in missing)} "
                f"in {self.path}. Please fill it in.",
                path=str(self.path),
            )
        model: Any = raw["model"]
        if isinstance(model, bool) or not isinstance(model, str) or not model.strip():
            raise AgentError("'model' must be a non-empty string.", path=str(self.path))
        api_key = self._optional_string(raw.get("api_key"), "api_key")
        base_url = self._optional_string(raw.get("base_url"), "base_url")
        provider_params = self._load_provider_params(raw.get("provider_params"))
        return RuntimeConfig(
            model=model,
            api_key=api_key,
            base_url=base_url,
            provider_params=provider_params,
            max_context_message_chars=self._positive_integer(
                context_limit, "max_context_message_chars"
            ),
        )

    def _optional_string(self, value: Any, key: str) -> str | None:
        if value is None or value == "":
            return None
        if isinstance(value, bool) or not isinstance(value, str):
            raise AgentError(f"'{key}' must be a string.", path=str(self.path))
        return cast(str, value)

    def _positive_integer(self, value: Any, key: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise AgentError(f"'{key}' must be a positive integer.", path=str(self.path))
        return cast(int, value)

    def _load_provider_params(self, value: Any) -> dict[str, ScalarValue] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise AgentError("'provider_params' must be a JSON object.", path=str(self.path))
        params: dict[str, ScalarValue] = {}
        for name, param in value.items():
            if not isinstance(param, PROVIDER_PARAM_TYPES):
                raise AgentError(
                    f"'provider_params.{name}' must be a string, number, or boolean.",
                    path=str(self.path),
                )
            params[name] = cast(ScalarValue, param)
        return params
