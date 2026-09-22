import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
import json
from copy import deepcopy
from conversation import run_turn


class ConversationTests(unittest.TestCase):
    def test_direct_reply_without_tools(self):
        # 准备模型返回的消息
        reply = SimpleNamespace(
            content="你好，我可以帮你管理待办事项。",
            tool_calls=None,
        )

        # 模拟 API 的返回结构
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=reply)]
        )

        # 用模拟客户端代替真实客户端
        client = Mock()
        client.chat.completions.create.return_value = response

        messages = [
            {"role": "user", "content": "你好"}
        ]

        with patch("conversation.execute_tool_call") as fake_execute:
            run_turn(client, messages)

        # 只请求了一次模型
        client.chat.completions.create.assert_called_once()

        # 没有执行任何工具
        fake_execute.assert_not_called()

        # 用户消息保留，模型回答追加在后面
        self.assertEqual(
            messages,
            [
                {"role": "user", "content": "你好"},
                reply,
            ],
        )
    def test_tool_call_then_final_reply(self):
        # 第一次：模型要求搜索待办
        tool_call = SimpleNamespace(
            id="call_search_1",
            function=SimpleNamespace(
                name="search_todos",
                arguments='{"keyword": "Python"}',
            ),
        )
        tool_reply = SimpleNamespace(
            content=None,
            tool_calls=[tool_call],
        )

        # 第二次：模型给出最终回答
        final_reply = SimpleNamespace(
            content="找到一条：学习 Python。",
            tool_calls=None,
        )

        responses = [
            SimpleNamespace(
                choices=[SimpleNamespace(message=tool_reply)]
            ),
            SimpleNamespace(
                choices=[SimpleNamespace(message=final_reply)]
            ),
        ]

        # 保存每次请求时的消息快照
        sent_messages = []

        def fake_create(**kwargs):
            sent_messages.append(deepcopy(kwargs["messages"]))
            return responses[len(sent_messages) - 1]

        client = Mock()
        client.chat.completions.create.side_effect = fake_create

        tool_result = {
            "success": True,
            "data": [{"id": 1, "content": "学习 Python"}],
        }

        messages = [
            {"role": "user", "content": "搜索 Python"}
        ]

        with patch(
            "conversation.execute_tool_call",
            return_value=tool_result,
        ) as fake_execute:
            run_turn(client, messages)

        # 请求模型两次，执行工具一次
        self.assertEqual(
            client.chat.completions.create.call_count, 2
        )
        fake_execute.assert_called_once_with(tool_call)

        # 第一次请求只有用户消息
        self.assertEqual(
            sent_messages[0],
            [{"role": "user", "content": "搜索 Python"}],
        )

        # 第二次请求已包含工具调用消息和工具结果
        self.assertEqual(len(sent_messages[1]), 3)
        self.assertEqual(sent_messages[1][1], tool_reply)

        tool_message = sent_messages[1][2]
        self.assertEqual(tool_message["role"], "tool")
        self.assertEqual(
            tool_message["tool_call_id"], "call_search_1"
        )
        self.assertEqual(
            json.loads(tool_message["content"]), tool_result
        )

        # 最终回答也被保存到历史中
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[-1], final_reply)

    def test_stop_at_api_call_limit(self):
        tool_call = SimpleNamespace(
            id="call_search",
            function=SimpleNamespace(
                name="search_todos",
                arguments='{"keyword": "Python"}',
            ),
        )

        reply = SimpleNamespace(
            content=None,
            tool_calls=[tool_call],
        )
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=reply)]
        )

        client = Mock()

        # 每次都返回工具调用，让流程持续循环
        client.chat.completions.create.return_value = response

        messages = [
            {"role": "user", "content": "搜索 Python"}
        ]
        tool_result = {"success": True, "data": []}

        with patch(
            "conversation.execute_tool_call",
            return_value=tool_result,
        ) as fake_execute:
            run_turn(client, messages, max_api_calls=2)

        self.assertEqual(
            client.chat.completions.create.call_count, 2
        )
        self.assertEqual(fake_execute.call_count, 2)

        # 1 条用户消息 + 每轮各 1 条模型消息和工具结果
        self.assertEqual(len(messages), 5)
        self.assertEqual(messages[-1]["role"], "tool")
    def test_api_failure_stops_turn(self):
        client = Mock()

        # 模拟请求时发生异常
        client.chat.completions.create.side_effect = RuntimeError(
            "模拟连接失败"
        )

        messages = [
            {"role": "user", "content": "查看全部待办"}
        ]

        with patch("conversation.execute_tool_call") as fake_execute:
            run_turn(client, messages)

        # 本轮请求一次后停止
        client.chat.completions.create.assert_called_once()

        # 没拿到模型回复，因此不应执行工具
        fake_execute.assert_not_called()

        # 保留用户消息，并追加错误提示
        self.assertEqual(
            messages,
            [
                {"role": "user", "content": "查看全部待办"},
                {
                    "role": "assistant",
                    "content": "API请求失败：模拟连接失败",
                },
            ],
        )
if __name__ == "__main__":
    unittest.main()