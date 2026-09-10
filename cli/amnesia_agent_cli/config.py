"""Frontend-owned configuration storage and validation."""

import json
import math
import os
import shutil
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

from amnesia_agent_kernel import ConfigError, ExecutionPolicy, ProviderConfig
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

DEFAULT_CONFIG_DIR = Path.home() / ".amnesia-agent-cli"
PACKAGED_CONFIG_RESOURCE = "amnesia_agent_cli/data/config.json"
PROVIDER_PARAM_TYPES: tuple[type, ...] = (str, int, float, bool)
ScalarValue = str | int | float | bool

CONFIG_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["model"],
    "properties": {
        "model": {"type": "string", "minLength": 1},
        "api_key": {"type": ["string", "null"]},
        "base_url": {"type": ["string", "null"]},
        "provider_params": {
            "type": "object",
            "propertyNames": {"minLength": 1},
            "additionalProperties": {"type": ["string", "number", "boolean"]},
        },
        "command_timeout_seconds": {"type": "number", "exclusiveMinimum": 0},
        "max_command_output_bytes": {"type": "integer", "exclusiveMinimum": 0},
        "max_context_message_chars": {"type": "integer", "exclusiveMinimum": 0},
    },
}


@dataclass(frozen=True)
class LoadedConfig:
    """The provider settings and execution policy loaded by the CLI."""

    provider: ProviderConfig
    policy: ExecutionPolicy


def _packaged_config() -> Any:
    return files("amnesia_agent_cli").joinpath("data", "config.json")


def _schema_error_message(error: ValidationError) -> str:
    location = ".".join(str(part) for part in error.absolute_path) or "<root>"
    return f"Invalid config.json at {location}: {error.message}"


@dataclass(frozen=True)
class ConfigStore:
    """Persistent CLI configuration, separate from the kernel workspace."""

    root: Path = DEFAULT_CONFIG_DIR

    def __init__(self, root: str | os.PathLike[str] | None = None) -> None:
        if root is not None and (
            isinstance(root, bool) or not isinstance(root, (str, os.PathLike))
        ):
            raise ConfigError(f"Invalid config root {root!r}")
        if root == "":
            raise ConfigError("Config root must not be empty.")
        try:
            resolved = (
                Path(root).expanduser().absolute() if root is not None else DEFAULT_CONFIG_DIR
            )
        except (OSError, TypeError, ValueError) as e:
            raise ConfigError(f"Invalid config root {root!r}: {e}") from e
        object.__setattr__(self, "root", resolved)

    @property
    def path(self) -> Path:
        return self.root / "config.json"

    def setup(self) -> None:
        """Create the config directory and seed a missing config file."""
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                shutil.copyfile(str(_packaged_config()), self.path)
        except (ModuleNotFoundError, OSError, TypeError, ValueError) as e:
            raise ConfigError(
                f"Cannot initialize config {self.path} from packaged resource "
                f"{PACKAGED_CONFIG_RESOURCE}: {e}",
                path=str(self.path),
            ) from e

    def reset(self) -> None:
        """Restore the packaged default config file."""
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(str(_packaged_config()), self.path)
        except (ModuleNotFoundError, OSError, TypeError, ValueError) as e:
            raise ConfigError(
                f"Cannot reset config {self.path} from packaged resource "
                f"{PACKAGED_CONFIG_RESOURCE}: {e}",
                path=str(self.path),
            ) from e

    def load(self) -> LoadedConfig:
        """Load and validate CLI settings without contacting the provider."""
        if not self.path.exists():
            self.setup()
        try:
            with self.path.open(encoding="utf-8-sig") as f:
                raw_value: Any = json.load(f)
        except OSError as e:
            raise ConfigError(f"Cannot read file {self.path}: {e}", path=str(self.path)) from e
        except (UnicodeError, json.JSONDecodeError) as e:
            raise ConfigError(f"Malformed JSON in {self.path}: {e}", path=str(self.path)) from e

        return self._parse(raw_value)

    def _parse(self, raw_value: Any) -> LoadedConfig:
        try:
            Draft202012Validator(CONFIG_SCHEMA).validate(raw_value)
        except ValidationError as e:
            raise ConfigError(_schema_error_message(e), path=str(self.path)) from e
        except SchemaError as e:
            raise ConfigError(f"Invalid internal config schema: {e}", path=str(self.path)) from e

        if not isinstance(raw_value, dict):
            raise ConfigError("config.json must contain a JSON object.", path=str(self.path))
        raw: dict[str, Any] = raw_value
        model = self._required_string(raw["model"], "model")
        if not model.strip():
            raise ConfigError("'model' must be a non-empty string.", path=str(self.path))
        provider = ProviderConfig(
            model=model,
            api_key=self._optional_string(raw.get("api_key"), "api_key"),
            base_url=self._optional_string(raw.get("base_url"), "base_url"),
            provider_params=self._load_provider_params(raw.get("provider_params")),
        )
        policy = ExecutionPolicy(
            command_timeout_seconds=self._positive_number(
                raw.get("command_timeout_seconds", 120.0), "command_timeout_seconds"
            ),
            max_command_output_bytes=self._positive_integer(
                raw.get("max_command_output_bytes", 256 * 1024),
                "max_command_output_bytes",
            ),
            max_context_message_chars=self._positive_integer(
                raw.get("max_context_message_chars", 1000),
                "max_context_message_chars",
            ),
        )
        return LoadedConfig(provider=provider, policy=policy)

    def _required_string(self, value: Any, key: str) -> str:
        if isinstance(value, bool) or not isinstance(value, str):
            raise ConfigError(f"'{key}' must be a non-empty string.", path=str(self.path))
        return value

    def _optional_string(self, value: Any, key: str) -> str | None:
        if value is None or value == "":
            return None
        if isinstance(value, bool) or not isinstance(value, str):
            raise ConfigError(f"'{key}' must be a string.", path=str(self.path))
        return cast(str, value)

    def _positive_integer(self, value: Any, key: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ConfigError(f"'{key}' must be a positive integer.", path=str(self.path))
        return cast(int, value)

    def _positive_number(self, value: Any, key: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError(f"'{key}' must be a positive number.", path=str(self.path))
        if not math.isfinite(value) or value <= 0:
            raise ConfigError(f"'{key}' must be a finite positive number.", path=str(self.path))
        return float(value)

    def _load_provider_params(self, value: Any) -> dict[str, ScalarValue] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ConfigError("'provider_params' must be a JSON object.", path=str(self.path))
        params: dict[str, ScalarValue] = {}
        for name, param in value.items():
            if not isinstance(name, str) or not name:
                raise ConfigError(
                    "'provider_params' keys must be non-empty strings.", path=str(self.path)
                )
            if not isinstance(param, PROVIDER_PARAM_TYPES):
                raise ConfigError(
                    f"'provider_params.{name}' must be a string, number, or boolean.",
                    path=str(self.path),
                )
            if isinstance(param, float) and not math.isfinite(param):
                raise ConfigError(
                    f"'provider_params.{name}' must be finite.", path=str(self.path)
                )
            params[name] = cast(ScalarValue, param)
        return params
