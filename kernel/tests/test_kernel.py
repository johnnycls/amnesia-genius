import tempfile
import unittest
from pathlib import Path

from amnesia_agent_kernel import Agent, RuntimeConfig


class KernelTests(unittest.TestCase):
    def make_config(self) -> RuntimeConfig:
        return RuntimeConfig(
            model="openai/test",
            api_key=None,
            base_url=None,
            provider_params=None,
            max_context_message_chars=1000,
        )

    def test_workspace_constructor_seeds_kernel_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            agent = Agent(self.make_config(), directory)
            for name in ("system_prompt.md", "memory.md", "history.jsonl"):
                self.assertTrue((agent._workspace.root / name).exists(), name)
            self.assertFalse((agent._workspace.root / "config.json").exists())

    def test_workspace_reset_restores_prompt_memory_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            agent = Agent(self.make_config(), directory)
            agent.update_system_prompt("changed")
            agent.update_memory("changed")
            agent.update_history([{"role": "user", "content": "hi"}])
            agent.reset_workspace()
            self.assertIn("# System Prompt", agent.read_system_prompt())
            self.assertIn("# Memory", agent.read_memory())
            self.assertEqual(agent.read_history(), [])

    def test_agent_uses_supplied_config_and_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            agent = Agent(self.make_config(), directory)
            self.assertEqual(agent.config.model, "openai/test")
            self.assertEqual(agent._workspace.root, Path(directory).absolute())


if __name__ == "__main__":
    unittest.main()
