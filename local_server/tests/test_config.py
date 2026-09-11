import json
import tempfile
import unittest

from fastapi.testclient import TestClient

from amnesia_agent_local_server.app import create_app
from amnesia_agent_local_server.config import ConfigStore


class ConfigTests(unittest.TestCase):
    def test_store_seeds_and_masks_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ConfigStore(directory)
            store.setup()
            values = json.loads(store.path.read_text(encoding="utf-8"))
            values.update({"model": "openai/test", "api_key": "secret"})
            store.path.write_text(json.dumps(values), encoding="utf-8")

            loaded = store.load()
            self.assertEqual(loaded.provider.api_key, "secret")
            from amnesia_agent_local_server.config import public_config

            public = public_config(loaded)
            self.assertTrue(public["api_key_set"])
            self.assertIsNone(public["api_key"])

    def test_blank_default_config_is_available_to_settings_ui(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ConfigStore(directory)
            client = TestClient(create_app(store))
            response = client.get("/v1/config")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["model"], "")

    def test_save_is_readable_and_preserves_provider_params(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ConfigStore(directory)
            store.path.parent.mkdir(parents=True, exist_ok=True)
            store.path.write_text(
                json.dumps(
                    {
                        "model": "openai/test",
                        "provider_params": {"temperature": 0.2},
                    }
                ),
                encoding="utf-8",
            )
            loaded = store.load()
            store.save(loaded)
            self.assertEqual(store.load().provider.provider_params["temperature"], 0.2)


if __name__ == "__main__":
    unittest.main()
