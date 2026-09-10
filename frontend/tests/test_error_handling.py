import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from amnesia_agent_kernel import ConfigError

from amnesia_agent_cli.config import ConfigStore


class ConfigErrorTests(unittest.TestCase):
    def test_unknown_top_level_key_has_schema_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "config.json").write_text(
                json.dumps(
                    {
                        "model": "openai/test",
                        "max_context_message_chars": 1000,
                        "modle": "typo",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "modle"):
                ConfigStore(directory).load()

    def test_load_auto_seeds_missing_config_then_reports_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ConfigStore(directory)
            with self.assertRaises(ConfigError):
                store.load()
            self.assertTrue(store.path.exists())

    def test_provider_preflight_is_not_run_by_config_load(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "config.json").write_text(
                json.dumps(
                    {
                        "model": "openai/test",
                        "max_context_message_chars": 1000,
                    }
                ),
                encoding="utf-8",
            )
            config = ConfigStore(directory).load()
            self.assertEqual(config.model, "openai/test")


class CliErrorTests(unittest.TestCase):
    def test_editor_nonzero_status_is_reported(self) -> None:
        from amnesia_agent_cli import cli

        completed = MagicMock(returncode=1)
        with patch.object(cli.subprocess, "run", return_value=completed), patch(
            "builtins.print"
        ) as printed:
            cli._open_in_editor("config.json")
        self.assertTrue(printed.called)


if __name__ == "__main__":
    unittest.main()
