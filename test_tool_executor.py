import unittest
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
from tool_executor import execute_tool_call
import database
import tool_config


class ToolExecutorTests(unittest.TestCase):
    def test_overdue_tool_definition_and_mapping(self):
        definitions = [
            tool["function"] for tool in tool_config.tools
            if tool["function"]["name"] == "get_overdue_todos"
        ]
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["parameters"]["properties"], {})
        self.assertEqual(definitions[0]["parameters"]["required"], [])
        self.assertIs(
            tool_config.available_functions["get_overdue_todos"],
            database.get_overdue_todos,
        )

    def test_overdue_tool_called_without_arguments(self):
        expected = [{"id": 1, "deadline": "2026-09-01", "status": "未完成"}]
        fake_get = Mock(return_value=expected)
        tool_call = SimpleNamespace(function=SimpleNamespace(
            name="get_overdue_todos", arguments="{}"
        ))
        with patch.dict(
            "tool_executor.available_functions", {"get_overdue_todos": fake_get}
        ):
            result = execute_tool_call(tool_call)
        fake_get.assert_called_once_with()
        self.assertEqual(result, {"success": True, "data": expected})

    def test_get_todos_passes_status(self):
        for status in ("已完成", "未完成", None):
            with self.subTest(status=status):
                expected_data = [{"id": 1, "status": status}]
                fake_get = Mock(return_value=expected_data)
                tool_call = SimpleNamespace(
                    function=SimpleNamespace(
                        name="get_todos",
                        arguments=json.dumps({"status": status}),
                    )
                )
                with patch.dict(
                    "tool_executor.available_functions",
                    {"get_todos": fake_get},
                ):
                    result = execute_tool_call(tool_call)
                fake_get.assert_called_once_with(status=status)
                self.assertEqual(result, {"success": True, "data": expected_data})

    def test_unknown_tool(self):
        tool_call = SimpleNamespace(
            function=SimpleNamespace(
                name="unknown_tool",
                arguments="{}"
            )
        )

        result = execute_tool_call(tool_call)

        self.assertEqual(
            result,
            {
                "success": False,
                "error": "无法执行未知工具：unknown_tool"
            }
        )
    def test_invalid_json_arguments(self):
        tool_call = SimpleNamespace(
            function=SimpleNamespace(
                name="search_todos",
                arguments='{"keyword":'
            )
        )

        result = execute_tool_call(tool_call)

        self.assertIs(result["success"], False)
        self.assertIn("error", result)
        self.assertTrue(result["error"])
        self.assertNotIn("data", result)

    def test_search_tool_success(self):
        expected_data = [{"id": 1, "content": "学习 Python"}]
        fake_search = Mock(return_value=expected_data)

        tool_call = SimpleNamespace(
            function=SimpleNamespace(
                name="search_todos",
                arguments='{"keyword": "Python"}'
            )
        )

        with patch.dict(
            "tool_executor.available_functions",
            {"search_todos": fake_search}
        ):
            result = execute_tool_call(tool_call)

        fake_search.assert_called_once_with(keyword="Python")
        self.assertEqual(
            result,
            {"success": True, "data": expected_data}
        )
    def test_tool_execution_error(self):
        fake_search = Mock(
            side_effect=ValueError("搜索关键词不能为空")
        )

        tool_call = SimpleNamespace(
            function=SimpleNamespace(
                name="search_todos",
                arguments='{"keyword": ""}'
            )
        )

        with patch.dict(
            "tool_executor.available_functions",
            {"search_todos": fake_search}
        ):
            result = execute_tool_call(tool_call)

        fake_search.assert_called_once_with(keyword="")
        self.assertEqual(
            result,
            {
                "success": False,
                "error": "搜索关键词不能为空"
            }
        )
    def test_reject_non_object_arguments(self):
        invalid_arguments = ["[]", "null", "123", '"hello"']

        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                fake_search = Mock()

                tool_call = SimpleNamespace(
                    function=SimpleNamespace(
                        name="search_todos",
                        arguments=arguments,
                    )
                )

                with patch.dict(
                    "tool_executor.available_functions",
                    {"search_todos": fake_search},
                ):
                    result = execute_tool_call(tool_call)

                self.assertEqual(
                    result,
                    {
                        "success": False,
                        "error": "工具参数必须是 JSON 对象",
                    },
                )
                fake_search.assert_not_called()
if __name__ == "__main__":
    unittest.main()
