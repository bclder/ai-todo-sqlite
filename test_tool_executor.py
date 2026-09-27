import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch
from tool_executor import execute_tool_call
import database
import tool_config


class ToolExecutorTests(unittest.TestCase):
    def test_delete_requires_exact_confirmation(self):
        todo = {"id": 42, "content": "学习 Python"}
        for answer in ("y", "n", "Y", ""):
            with self.subTest(answer=answer):
                tool_call = SimpleNamespace(function=SimpleNamespace(
                    name="delete_todo", arguments='{"todo_id": 42}'
                ))
                fake_delete = Mock(return_value=todo)
                with patch("tool_executor.get_todo", return_value=todo) as fake_get:
                    with patch("builtins.input", return_value=answer) as fake_input:
                        with patch.dict(
                            "tool_executor.available_functions",
                            {"delete_todo": fake_delete},
                        ):
                            result = execute_tool_call(tool_call)
                fake_get.assert_called_once_with(todo_id=42)
                fake_input.assert_called_once()
                prompt = fake_input.call_args.args[0]
                self.assertIn("42", prompt)
                self.assertIn("学习 Python", prompt)
                if answer == "y":
                    fake_delete.assert_called_once_with(todo_id=42)
                    self.assertEqual(result, {"success": True, "data": todo})
                else:
                    fake_delete.assert_not_called()
                    self.assertEqual(result, {
                        "success": False,
                        "cancelled": True,
                        "error": "用户取消删除，待办未删除",
                    })

    def test_delete_invalid_or_missing_todo_does_not_ask(self):
        cases = [
            ("abc", ValueError("待办编号必须是正整数"), "待办编号必须是正整数"),
            (999, None, "待办编号不存在"),
        ]
        for todo_id, lookup_result, error in cases:
            with self.subTest(todo_id=todo_id):
                tool_call = SimpleNamespace(function=SimpleNamespace(
                    name="delete_todo", arguments=json.dumps({"todo_id": todo_id})
                ))
                fake_delete = Mock()
                with patch("tool_executor.get_todo") as fake_get:
                    if isinstance(lookup_result, Exception):
                        fake_get.side_effect = lookup_result
                    else:
                        fake_get.return_value = lookup_result
                    with patch("builtins.input") as fake_input:
                        with patch.dict(
                            "tool_executor.available_functions",
                            {"delete_todo": fake_delete},
                        ):
                            result = execute_tool_call(tool_call)
                fake_get.assert_called_once_with(todo_id=todo_id)
                fake_input.assert_not_called()
                fake_delete.assert_not_called()
                self.assertEqual(result, {"success": False, "error": error})

    def test_query_does_not_require_confirmation(self):
        tool_call = SimpleNamespace(function=SimpleNamespace(
            name="get_todos", arguments="{}"
        ))
        fake_get = Mock(return_value=[])
        with patch("builtins.input") as fake_input:
            with patch.dict(
                "tool_executor.available_functions", {"get_todos": fake_get}
            ):
                result = execute_tool_call(tool_call)
        fake_input.assert_not_called()
        fake_get.assert_called_once_with()
        self.assertEqual(result, {"success": True, "data": []})

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
class DeleteConfirmationIntegrationTests(unittest.TestCase):
    def setUp(self):
        original_data_file = database.DATA_FILE
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.addCleanup(setattr, database, "DATA_FILE", original_data_file)
        database.DATA_FILE = Path(temp_dir.name) / "test_todos.db"
        database.create_database()

    def test_confirmed_delete_removes_todo(self):
        todo = database.add_todo("确认删除测试", "2026-12-31")
        tool_call = SimpleNamespace(function=SimpleNamespace(
            name="delete_todo",
            arguments=json.dumps({"todo_id": todo["id"]}),
        ))

        with patch("builtins.input", return_value="y"):
            result = execute_tool_call(tool_call)

        self.assertEqual(result, {"success": True, "data": todo})
        self.assertIsNone(database.get_todo(todo["id"]))

    def test_cancelled_delete_preserves_complete_todo(self):
        todo = database.add_todo("取消删除测试", "2026-12-31")
        tool_call = SimpleNamespace(function=SimpleNamespace(
            name="delete_todo",
            arguments=json.dumps({"todo_id": todo["id"]}),
        ))

        with patch("builtins.input", return_value="n"):
            result = execute_tool_call(tool_call)

        self.assertEqual(result, {
            "success": False,
            "cancelled": True,
            "error": "用户取消删除，待办未删除",
        })
        self.assertEqual(database.get_todo(todo["id"]), todo)


if __name__ == "__main__":
    unittest.main()
