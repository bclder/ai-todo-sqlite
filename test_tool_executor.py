import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from tool_executor import execute_tool_call


class ToolExecutorTests(unittest.TestCase):
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
    
if __name__ == "__main__":
    unittest.main()