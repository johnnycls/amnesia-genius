import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from amnesia_agent_cli.config import ConfigStore
from amnesia_agent_kernel import AgentError


class ConfigTests(unittest.TestCase):
    def write_config(self, directory: str, **updates: object) -> None:
        values: dict[str, object] = {
            "model": "openai/test",
            "max_context_message_chars": 1000,
        }
        values.update(updates)
        Path(directory, "config.json").write_text(json.dumps(values), encoding="utf-8")

    def test_model_must_be_a_non_empty_string(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write_config(directory, model=42)
            store = ConfigStore(directory)
            with self.assertRaises(AgentError):
                store.load()

    def test_config_store_seeds_and_resets_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ConfigStore(directory)
            store.setup()
            self.assertTrue(store.path.exists())
            store.path.write_text('{"model":"changed"}', encoding="utf-8")
            store.reset()
            self.assertIn('"model": ""', store.path.read_text(encoding="utf-8"))

    def test_provider_params_satisfy_missing_env_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write_config(
                directory,
                model="bedrock/us.anthropic.claude-sonnet-4-5",
                api_key="",
                provider_params={
                    "aws_access_key_id": "AKIA",
                    "aws_secret_access_key": "x",
                    "aws_region_name": "us-east-1",
                },
            )
            with patch(
                "amnesia_agent_cli.config.validate_runtime_config"
            ) as validate:
                config = ConfigStore(directory).load()
            validate.assert_called_once_with(config)
            self.assertEqual(config.model, "bedrock/us.anthropic.claude-sonnet-4-5")


if __name__ == "__main__":
    unittest.main()
