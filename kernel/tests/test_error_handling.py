import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from amnesia_agent_kernel import (
    Agent,
    AgentError,
    ConfigError,
    ProviderError,
    ToolError,
    WorkspaceError,
)
from amnesia_agent_kernel.agent import agent_turn, validate_runtime_config
from amnesia_agent_kernel.tools import run_tool_call
from amnesia_agent_kernel.types import RuntimeConfig
from amnesia_agent_kernel.workspace import Workspace


class ErrorHierarchyTests(unittest.TestCase):
    def test_specific_errors_remain_agent_errors(self) -> None:
        self.assertTrue(issubclass(ConfigError, AgentError))
        self.assertTrue(issubclass(ProviderError, AgentError))
        self.assertTrue(issubclass(ToolError, AgentError))
        self.assertTrue(issubclass(WorkspaceError, AgentError))


class ProviderValidationTests(unittest.TestCase):
    def test_malformed_preflight_result_is_provider_error(self) -> None:
        config = RuntimeConfig("openai/test", None, None, None, 100)
        with patch(
            "amnesia_agent_kernel.agent.litellm.validate_environment",
            return_value=None,
        ), self.assertRaises(ProviderError):
            validate_runtime_config(config)

    def test_agent_preflights_before_workspace_setup(self) -> None:
        config = RuntimeConfig("openai/test", None, None, None, 100)
        with patch(
            "amnesia_agent_kernel.agent.litellm.validate_environment",
            side_effect=RuntimeError("missing credentials"),
        ), self.assertRaises(ProviderError):
            Agent(config, tempfile.mkdtemp())


class ToolErrorTests(unittest.IsolatedAsyncioTestCase):
    async def test_process_failure_becomes_tool_result_text(self) -> None:
        call = {
            "id": "c1",
            "function": {"name": "bash", "arguments": '{"command":"echo hi"}'},
        }
        with patch(
            "amnesia_agent_kernel.tools.run_bash",
            new=AsyncMock(side_effect=ToolError("cannot start shell")),
        ):
            result = await run_tool_call(call)
        self.assertIn("error", result)
        self.assertIn("cannot start shell", result)

    async def test_unknown_tool_becomes_tool_result_text(self) -> None:
        call = {
            "id": "c1",
            "function": {"name": "python", "arguments": '{"command":"echo hi"}'},
        }
        result = await run_tool_call(call)
        self.assertIn("unknown tool", result)


class AgentTurnErrorTests(unittest.IsolatedAsyncioTestCase):
    async def test_stream_failure_persists_partial_message_and_sidecar(self) -> None:
        async def broken_stream() -> object:
            yield SimpleNamespace(
                choices=[SimpleNamespace(delta=SimpleNamespace(content="partial", tool_calls=[]))]
            )
            raise RuntimeError("connection reset")

        config = RuntimeConfig("openai/test", None, None, {"test": True}, 100)
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(directory)
            with patch(
                "amnesia_agent_kernel.agent.acompletion",
                new=AsyncMock(return_value=broken_stream()),
            ):
                with self.assertRaises(ProviderError):
                    _ = [
                        event
                        async for event in agent_turn(config, workspace, "hello")
                    ]
            records = workspace.read_history()
        self.assertEqual(records[0]["role"], "user")
        self.assertEqual(records[1], {"role": "assistant", "content": "partial"})
        self.assertEqual(records[2]["kind"], "turn_error")


class WorkspaceErrorTests(unittest.TestCase):
    def test_history_enumeration_os_error_is_typed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(directory)
            history = Path(directory, "history")
            history.mkdir()
            with patch.object(Path, "iterdir", side_effect=OSError("denied")), self.assertRaises(
                WorkspaceError
            ):
                workspace.list_history()

    def test_history_record_must_have_message_or_event_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(directory)
            with self.assertRaises(WorkspaceError):
                workspace.update_history([{"unexpected": True}])


if __name__ == "__main__":
    unittest.main()
