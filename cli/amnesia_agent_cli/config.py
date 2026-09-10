"""Frontend-owned configuration storage and validation."""

import json
import os
import shutil
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

from amnesia_agent_kernel import (
    ConfigError,
    ExecutionPolicy,
    ProviderConfig,
    validate_execution_policy,
    validate_provider_config,
)
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

DEFAULT_CONFIG_DIR = Path.home() / ".amnesia-agent-cli"
PACKAGED_CONFIG_RESOURCE = "amnesia_agent_cli/data/config.json"
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


class ConfigStore:
    """Persistent CLI configuration, separate from the kernel workspace."""

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
        self.root = resolved

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

        raw: dict[str, Any] = cast(dict[str, Any], raw_value)
        model = cast(str, raw["model"])
        if not model.strip():
            raise ConfigError("'model' must be a non-empty string.", path=str(self.path))
        provider = ProviderConfig(
            model=model,
            api_key=cast(str | None, raw.get("api_key")) or None,
            base_url=cast(str | None, raw.get("base_url")) or None,
            provider_params=cast(
                dict[str, ScalarValue] | None,
                raw.get("provider_params"),
            ),
        )
        policy = ExecutionPolicy(
            command_timeout_seconds=float(
                cast(int | float, raw.get("command_timeout_seconds", 120.0))
            ),
            max_command_output_bytes=cast(
                int, raw.get("max_command_output_bytes", 256 * 1024)
            ),
            max_context_message_chars=cast(
                int, raw.get("max_context_message_chars", 1000)
            ),
        )
        try:
            validate_provider_config(provider)
            validate_execution_policy(policy)
        except ConfigError as e:
            raise ConfigError(str(e), path=str(self.path)) from e
        return LoadedConfig(provider=provider, policy=policy)
