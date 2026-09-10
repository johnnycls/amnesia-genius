import tempfile
import unittest

from amnesia_agent_kernel.workspace import Workspace


class HistoryTests(unittest.TestCase):
    def test_history_can_be_read_replaced_and_reset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(directory)
            workspace.append_history({"role": "user", "content": "hi"})
            self.assertEqual(workspace.read_history(), [{"role": "user", "content": "hi"}])
            workspace.update_history([{"role": "assistant", "content": "ok"}])
            self.assertEqual(workspace.read_history(), [{"role": "assistant", "content": "ok"}])
            workspace.reset_history()
            self.assertEqual(workspace.read_history(), [])


if __name__ == "__main__":
    unittest.main()
