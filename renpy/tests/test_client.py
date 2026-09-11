import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "game"))

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


if __name__ == "__main__":
    unittest.main()
