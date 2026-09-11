import asyncio
import json
import tempfile
import unittest
from unittest.mock import patch

from amnesia_agent_kernel import AssistantMessage, Delta

from amnesia_agent_local_server.config import ConfigStore
from amnesia_agent_local_server.protocol import ConfigUpdate
from amnesia_agent_local_server.service import AgentService, TurnBusyError, event_payload


class FakeSession:
    def __init__(self, provider: object, policy: object) -> None:
        self.provider = provider
        self.policy = policy

    async def turn(self, text: str, response_format: object = None):
        yield Delta('{"answer":"')
        yield AssistantMessage(
            {
                "role": "assistant",
                "content": json.dumps({"answer": f"Echo: {text}", "choices": ["Again"]}),
            }
        )

    def read_system_prompt(self) -> str:
        return "system"

    def update_system_prompt(self, content: str) -> None:
        pass

    def reset_system_prompt(self) -> None:
        pass

    def read_memory(self) -> str:
        return "memory"

    def update_memory(self, content: str) -> None:
        pass

    def reset_memory(self) -> None:
        pass

    def list_history(self) -> list[str]:
        return []

    def read_history(self, date: str | None = None) -> list[dict[str, object]]:
        return []

    def reset_history(self) -> None:
        pass


class ServiceTests(unittest.TestCase):
    def test_event_payload_parses_structured_answer(self) -> None:
        payload = event_payload(
            AssistantMessage(
                {"content": '{"answer":"Choose", "choices":["A", "B"]}'}
            )
        )
        self.assertEqual(payload["type"], "assistant")
        self.assertEqual(payload["data"]["answer"], "Choose")
        self.assertEqual(payload["data"]["choices"], ["A", "B"])
        self.assertTrue(payload["data"]["structured"])

    def test_event_payload_falls_back_to_plain_text(self) -> None:
        payload = event_payload(AssistantMessage({"content": "plain text"}))
        self.assertFalse(payload["data"]["structured"])
        self.assertEqual(payload["data"]["choices"], [])

    def test_stream_turn_emits_done_and_releases_slot(self) -> None:
        async def run() -> list[dict[str, object]]:
            with tempfile.TemporaryDirectory() as directory:
                store = ConfigStore(directory)
                store.path.parent.mkdir(parents=True, exist_ok=True)
                store.path.write_text('{"model":"openai/test"}', encoding="utf-8")
                service = AgentService(store)
                with patch("amnesia_agent_local_server.service.KernelSession", FakeSession):
                    events = [event async for event in service.stream_turn("hello")]
                self.assertFalse(service.active)
                return events

        events = asyncio.run(run())
        self.assertEqual(events[-1]["type"], "done")

    def test_active_turn_blocks_config_update(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ConfigStore(directory)
            store.path.parent.mkdir(parents=True, exist_ok=True)
            store.path.write_text('{"model":"openai/test"}', encoding="utf-8")
            service = AgentService(store)
            service._active = True
            with self.assertRaises(TurnBusyError):
                service.update_config(ConfigUpdate(model="openai/new"))


if __name__ == "__main__":
    unittest.main()
