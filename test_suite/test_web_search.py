"""DeepSeek Search 请求和带工具调用的回复回归，不调用外部服务。"""
import json
import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from langchain_core.messages import HumanMessage
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageFunctionToolCall
from openai.types.chat.chat_completion_message_function_tool_call import Function

from modules.web_search.service import reply_with_search, search_web


def answer(content=None, query=None, reasoning=None):
    message = ChatCompletionMessage(role="assistant", content=content, reasoning_content=reasoning)
    if query is not None:
        message.tool_calls = [ChatCompletionMessageFunctionToolCall(id="search-1", type="function", function=Function(name="web_search", arguments=json.dumps({"query": query})))]
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class WebSearchTests(unittest.TestCase):
    @patch("modules.web_search.service.get_deepseek_search_credentials", return_value=("test-key", "https://api.deepseek.com"))
    @patch("modules.web_search.service.urlopen")
    def test_search_uses_official_endpoint_and_bearer_auth(self, open_url, _credentials):
        open_url.return_value.__enter__.return_value = BytesIO(b'{"results":[{"title":"Python","url":"https://python.org","summary":"Official"}]}')
        result = search_web("Python official")
        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.deepseek.com/v1/tools/search")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(json.loads(request.data), {"query": "Python official", "count": 5, "need_content": False})
        self.assertEqual(result["results"][0]["url"], "https://python.org")

    @patch("modules.web_search.service.get_deepseek_search_credentials", return_value=("test-key", "https://api.deepseek.com"))
    @patch("modules.web_search.service.urlopen", side_effect=HTTPError("https://api.deepseek.com/v1/tools/search", 402, "Payment Required", {}, None))
    def test_api_error_is_explicit(self, _url, _credentials):
        with self.assertRaisesRegex(RuntimeError, "HTTP 402"):
            search_web("Python")

    def llm(self, responses):
        llm = Mock(model_name="deepseek-flash", extra_body={"thinking": {"type": "enabled"}})
        llm.root_client.chat.completions.create.side_effect = responses
        return llm

    @patch("modules.web_search.service.search_web")
    def test_chitchat_does_not_search(self, search):
        llm = self.llm([answer("你好")])
        self.assertEqual(reply_with_search(llm, [HumanMessage(content="你好")]), "你好")
        search.assert_not_called()

    @patch("modules.web_search.service.search_web", return_value={"results": [{"title": "Python", "url": "https://python.org"}]})
    def test_search_result_and_reasoning_reach_followup(self, search):
        llm = self.llm([answer(query="Python official", reasoning="check source"), answer("[Python](https://python.org)")])
        reply = reply_with_search(llm, [HumanMessage(content="找 Python 官网")])
        search.assert_called_once_with("Python official")
        messages = llm.root_client.chat.completions.create.call_args.kwargs["messages"]
        self.assertEqual(messages[-2]["reasoning_content"], "check source")
        self.assertEqual(messages[-1]["role"], "tool")
        self.assertIn("https://python.org", messages[-1]["content"])
        self.assertIn("https://python.org", reply)

    @patch("modules.web_search.service.search_web", side_effect=RuntimeError("HTTP 402"))
    def test_failure_passed_to_model(self, _search):
        llm = self.llm([answer(query="Python"), answer("搜索失败")])
        self.assertEqual(reply_with_search(llm, [HumanMessage(content="搜索")]), "搜索失败")
        self.assertIn("HTTP 402", llm.root_client.chat.completions.create.call_args.kwargs["messages"][-1]["content"])

    @patch("modules.web_search.service.search_web", return_value={"results": []})
    def test_search_budget_forces_final_response(self, search):
        llm = self.llm([answer(query="query") for _ in range(3)] + [answer("未找到")])
        self.assertEqual(reply_with_search(llm, [HumanMessage(content="查一下")]), "未找到")
        self.assertEqual(search.call_count, 3)
        self.assertEqual(llm.root_client.chat.completions.create.call_args.kwargs["tool_choice"], "none")


if __name__ == "__main__":
    unittest.main()
