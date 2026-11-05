"""模型与思考档位的请求隔离、参数映射及回合传递。"""
import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException
from infrastructure import container
from modules.chat_api.service import TurnRequest, TurnService
from schemas.protocols import TaskIntent


class ChatOptionsTests(unittest.TestCase):
    @patch.object(container, "_LLM_PROVIDER", "deepseek")
    def test_reasoning_levels_reach_provider_without_changing_default(self):
        shared = container._llm
        with patch("langchain_openai.ChatOpenAI") as create:
            for effort in ("off", "low", "high", "max"):
                container.get_turn_llm("deepseek-v4-pro", effort)
                body = create.call_args.kwargs["extra_body"]
                self.assertEqual(create.call_args.kwargs["model"], "deepseek-v4-pro")
                self.assertEqual(body["thinking"]["type"], "disabled" if effort == "off" else "enabled")
                self.assertEqual(body.get("reasoning_effort"), None if effort == "off" else effort)
        self.assertIs(container._llm, shared)

    def test_omitted_settings_keep_shared_default(self):
        with patch.object(container, "get_llm", return_value=Mock()) as default:
            self.assertIs(container.get_turn_llm(), default.return_value)

    @patch("modules.chat_api.service.get_chat_options", return_value={"models": ["deepseek-v4-pro"], "reasoning_levels": ["max"]})
    def test_turn_passes_selection_to_graph(self, _options):
        intent = TaskIntent(task_type="emotion", persona="bina", urgency_level=1, pain_level=2, raw_input="你好")
        with patch("modules.chat_api.service.get_chat_history"), patch("modules.chat_api.service.get_hindsight_memory"), patch("modules.chat_api.service.run_router_traced", return_value=({"final_response": "你好", "intent": intent}, [])) as run:
            TurnService().run(TurnRequest(text="你好", model="deepseek-v4-pro", reasoning_effort="max"), "test")
            state = run.call_args.args[1]
            self.assertEqual(state["model"], "deepseek-v4-pro")
            self.assertEqual(state["reasoning_effort"], "max")

    @patch("modules.chat_api.service.get_chat_options", return_value={"models": ["configured"], "reasoning_levels": []})
    def test_invalid_selection_rejected_before_memory_calls(self, _options):
        with patch("modules.chat_api.service.get_hindsight_memory") as memory:
            for settings in ({"model": "unknown"}, {"reasoning_effort": "max"}):
                with self.assertRaises(HTTPException) as caught:
                    TurnService().run(TurnRequest(text="你好", **settings), "test")
                self.assertEqual(caught.exception.status_code, 422)
            memory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
