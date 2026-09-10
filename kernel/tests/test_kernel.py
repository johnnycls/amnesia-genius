import asyncio
import tempfile
import unittest
from collections.abc import AsyncIterator
from types import SimpleNamespace
from unittest.mock import patch

from amnesia_agent_kernel import ExecutionPolicy, KernelSession, ProviderConfig


class KernelTests(unittest.IsolatedAsyncioTestCase):
    def make_config(self) -> ProviderConfig:
        return ProviderConfig(model="openai/test", provider_params={"test": True})

    def test_provider_config_is_snapshotted(self) -> None:
        params = {"temperature": 0.1}
        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "amnesia_agent_kernel.agent.litellm.validate_environment",
                return_value={"keys_in_environment": True},
            ):
                session = KernelSession(
                    ProviderConfig("openai/test", provider_params=params),
                    workspace_root=directory,
                )
            params["unexpected"] = "changed"
            self.assertNotIn("unexpected", session.provider.provider_params or {})

    def test_workspace_constructor_seeds_kernel_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "amnesia_agent_kernel.agent.litellm.validate_environment",
                return_value={"keys_in_environment": True},
            ):
                session = KernelSession(self.make_config(), workspace_root=directory)
            for name in ("system_prompt.md", "memory.md"):
                self.assertTrue((session._workspace.root / name).exists(), name)
            self.assertFalse((session._workspace.root / "history.jsonl").exists())
            self.assertFalse((session._workspace.root / "history").exists())
            self.assertFalse((session._workspace.root / "config.json").exists())

    def test_workspace_reset_restores_prompt_memory_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "amnesia_agent_kernel.agent.litellm.validate_environment",
                return_value={"keys_in_environment": True},
            ):
                session = KernelSession(self.make_config(), workspace_root=directory)
            session.update_system_prompt("changed")
            session.update_memory("changed")
            session.update_history([{"role": "user", "content": "hi"}])
            session.reset_workspace()
            self.assertIn("# System Prompt", session.read_system_prompt())
            self.assertIn("# Memory", session.read_memory())
            self.assertEqual(session.read_history(), [])

    async def test_concurrent_turns_are_serialized(self) -> None:
        started: list[str] = []

        async def fake_completion(**kwargs: object) -> object:
            messages = kwargs["messages"]
            started.append(messages[1]["content"])
            await asyncio.sleep(0.01)

            async def stream() -> object:
                yield SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(content="ok", tool_calls=[])
                        )
                    ]
                )

            return stream()

        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "amnesia_agent_kernel.agent.litellm.validate_environment",
                return_value={"keys_in_environment": True},
            ):
                session = KernelSession(
                    self.make_config(), ExecutionPolicy(), workspace_root=directory
                )
            with patch("amnesia_agent_kernel.agent.acompletion", new=fake_completion):
                await asyncio.gather(
                    *(self._consume(session.turn(text)) for text in ("a", "b", "c"))
                )
            self.assertEqual(started, ["a", "b", "c"])
            users = [
                record["content"]
                for record in session.read_history()
                if record.get("role") == "user"
            ]
            self.assertEqual(users, ["a", "b", "c"])

    @staticmethod
    async def _consume(events: AsyncIterator[object]) -> None:
        async for _ in events:
            pass


if __name__ == "__main__":
    unittest.main()
