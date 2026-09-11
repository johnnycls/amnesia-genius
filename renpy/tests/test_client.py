import sys
import tempfile
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "game"))

import local_server_client
from local_server_client import LocalServerError, parse_sse


class ClientTests(unittest.TestCase):
    def test_parse_sse_decodes_data_lines(self) -> None:
        events = list(
            parse_sse(
                [
                    b": keepalive\n",
                    b"data: {\"type\":\"delta\",\"data\":{\"text\":\"hi\"}}\n",
                    b"\n",
                    b"data: {\"type\":\"done\",\"data\":{}}\n",
                ]
            )
        )
        self.assertEqual(events[0]["type"], "delta")
        self.assertEqual(events[1]["type"], "done")

    def test_parse_sse_rejects_malformed_json(self) -> None:
        with self.assertRaises(LocalServerError):
            list(parse_sse([b"data: not-json\n"]))

    def test_bundled_server_path_uses_game_directory(self) -> None:
        original_renpy = local_server_client.renpy
        try:
            with tempfile.TemporaryDirectory() as directory:
                server_directory = Path(directory) / "server"
                server_directory.mkdir()
                server_path = server_directory / local_server_client.BUNDLED_SERVER_NAME
                server_path.touch()
                local_server_client.renpy = types.SimpleNamespace(
                    config=types.SimpleNamespace(gamedir=directory)
                )
                self.assertEqual(
                    local_server_client.bundled_server_path(), str(server_path)
                )
        finally:
            local_server_client.renpy = original_renpy


if __name__ == "__main__":
    unittest.main()
