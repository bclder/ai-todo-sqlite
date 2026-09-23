import unittest
from datetime import date
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory

import database


class DatabaseTests(unittest.TestCase):

    def setUp(self):
        self.original_data_file = database.DATA_FILE
        self.temp_dir = TemporaryDirectory()

        database.DATA_FILE = (
            Path(self.temp_dir.name) / "test_todos.db"
        )
        database.create_database()

    def tearDown(self):
        database.DATA_FILE = self.original_data_file
        self.temp_dir.cleanup()

    def test_deadline_is_normalized_on_add_and_update(self):
        todo = database.add_todo("日期测试", "2026-9-4")
        self.assertEqual(todo["deadline"], "2026-09-04")
        self.assertEqual(database.get_todo(todo["id"])["deadline"], "2026-09-04")
        updated = database.update_todo(todo["id"], "日期测试", "2026-1-2")
        self.assertEqual(updated["deadline"], "2026-01-02")
        self.assertEqual(database.get_todo(todo["id"])["deadline"], "2026-01-02")

    def test_get_overdue_todos_filters_and_sorts(self):
        later = database.add_todo("昨天", "2026-09-23")
        earlier = database.add_todo("更早", "2026-08-31")
        database.add_todo("今天", "2026-09-24")
        database.add_todo("明天", "2026-09-25")
        completed = database.add_todo("已完成", "2026-08-01")
        database.complete_todo(completed["id"])
        with patch("database.date") as fake_date:
            fake_date.today.return_value = date(2026, 9, 24)
            self.assertEqual(database.get_overdue_todos(), [earlier, later])

    def test_get_overdue_todos_with_no_matches(self):
        with patch("database.date") as fake_date:
            fake_date.today.return_value = date(2026, 9, 24)
            self.assertEqual(database.get_overdue_todos(), [])
            database.add_todo("今天", "2026-09-24")
            database.add_todo("未来", "2026-10-01")
            completed = database.add_todo("已完成", "2026-09-01")
            database.complete_todo(completed["id"])
            self.assertEqual(database.get_overdue_todos(), [])

    def test_get_overdue_todos_reads_today_each_time(self):
        todo = database.add_todo("今天到期", "2026-09-24")
        with patch("database.date") as fake_date:
            fake_date.today.side_effect = [date(2026, 9, 24), date(2026, 9, 25)]
            self.assertEqual(database.get_overdue_todos(), [])
            self.assertEqual(database.get_overdue_todos(), [todo])

    def test_get_overdue_todos_preserves_legacy_dates(self):
        conn = database.get_connection()
        try:
            conn.executemany(
                "INSERT INTO todos (content, status, deadline) VALUES (?, ?, ?)",
                [
                    ("九月", "未完成", "2026-9-4"),
                    ("十月", "未完成", "2026-10-1"),
                    ("二月", "未完成", "2026-2-3"),
                    ("今天", "未完成", "2026-10-2"),
                    ("未来", "未完成", "2026-11-1"),
                    ("已完成", "已完成", "2026-1-1"),
                ],
            )
            conn.commit()
        finally:
            conn.close()
        before = database.get_todos()
        with patch("database.date") as fake_date:
            fake_date.today.return_value = date(2026, 10, 2)
            self.assertEqual(
                database.get_overdue_todos(), [before[2], before[0], before[1]]
            )
        self.assertEqual(database.get_todos(), before)

    def test_get_todos_with_optional_status(self):
        pending = database.add_todo("未完成任务", "2026-12-31")
        completed = database.add_todo("已完成任务", "2026-10-01")
        completed = database.complete_todo(completed["id"])

        self.assertEqual(database.get_todos(), [pending, completed])
        self.assertEqual(database.get_todos(None), [pending, completed])
        self.assertEqual(database.get_todos("未完成"), [pending])
        self.assertEqual(database.get_todos("已完成"), [completed])

    def test_get_todos_with_no_matching_status(self):
        todo = database.add_todo("任务", "2026-12-31")
        self.assertEqual(database.get_todos("已完成"), [])
        database.complete_todo(todo["id"])
        self.assertEqual(database.get_todos("未完成"), [])

    def test_get_todos_with_invalid_status(self):
        for status in ("", "全部", " 已完成 ", 0, True, [], {}):
            with self.subTest(status=status):
                with self.assertRaises(ValueError) as context:
                    database.get_todos(status)
                self.assertEqual(str(context.exception), "状态必须是已完成或未完成")

    def test_add_and_get_todo(self):
        added = database.add_todo(
            "自动化测试",
            "2026-12-31"
        )
        

        found = database.get_todo(added["id"])

        self.assertEqual(found["content"], "自动化测试")
        self.assertEqual(found["status"], "未完成")
        self.assertEqual(found["deadline"], "2026-12-31")
        
    def test_complete_todo(self):
        added = database.add_todo(
            "完成状态测试",
            "2026-12-31"
        )

        completed = database.complete_todo(added["id"])

        self.assertEqual(completed["id"], added["id"])
        self.assertEqual(completed["status"], "已完成")

    def test_update_todo(self):
        added = database.add_todo(
            "修改前内容",
            "2026-12-30"
        )

        updated = database.update_todo(
            added["id"],
            "修改后内容",
            "2026-12-31"
        )

        self.assertEqual(updated["id"], added["id"])
        self.assertEqual(updated["content"], "修改后内容")
        self.assertEqual(updated["deadline"], "2026-12-31")
        self.assertEqual(updated["status"], "未完成")

    def test_delete_todo(self):
        added = database.add_todo(
            "删除测试",
            "2026-12-31"
        )

        deleted = database.delete_todo(added["id"])
        found = database.get_todo(added["id"])

        self.assertEqual(deleted, added)
        self.assertIsNone(found)
        
    def test_add_todo_with_invalid_deadline(self):
        with self.assertRaises(ValueError):
            database.add_todo(
                "无效日期测试",
                "2026-02-30"
            )  

        todos = database.get_todos()
        self.assertEqual(todos, [])

    def test_get_nonexistent_todo(self):
        result = database.get_todo(999)

        self.assertIsNone(result)
    def test_complete_nonexistent_todo(self):
        with self.assertRaises(ValueError) as context:
            database.complete_todo(999)

        self.assertEqual(
            str(context.exception),
            "待办编号不存在"
        )
    def test_delete_nonexistent_todo(self):
        with self.assertRaises(ValueError) as context:
            database.delete_todo(999)
        self.assertEqual(
           str(context.exception),
            "待办编号不存在"
        )

    def test_update_nonexistent_todo(self):
        with self.assertRaises(ValueError) as context:
            database.update_todo(
                999,
                "不存在的待办",
                "2026-12-31"
            )
        self.assertEqual(
           str(context.exception),
            "待办编号不存在"
        )
    def test_complete_already_completed_todo(self):
        added = database.add_todo(
            "自动化测试",
            "2026-12-31"
        )
        database.complete_todo(added["id"])
        with self.assertRaises(ValueError) as context:
            database.complete_todo(added["id"])
        self.assertEqual(
           str(context.exception),
            "该待办已经完成"
        )
    def test_get_pending_todos(self):
        later = database.add_todo(
            "较晚任务",
            "2026-12-31"
        )
        earlier = database.add_todo(
            "较早任务",
            "2026-10-01"
        )
        completed = database.add_todo(
            "已完成任务",
            "2026-09-01"
        )

        database.complete_todo(completed["id"])

        pending = database.get_pending_todos()

        self.assertEqual(len(pending), 2)
        self.assertEqual(pending[0]["id"], earlier["id"])
        self.assertEqual(pending[1]["id"], later["id"])
    def test_add_todo_with_blank_content(self):
        with self.assertRaises(ValueError) as context:
            database.add_todo(
                " ",
                "2026-12-31"
            )
        self.assertEqual(
            str(context.exception),
            "待办内容不能为空"
        )
        self.assertEqual(
            database.get_todos(),
             []
        )
    def test_get_todo_with_invalid_ids(self):
        invalid_ids = ["abc", 0, -1, None]

        for todo_id in invalid_ids:
            with self.subTest(todo_id=todo_id):
                with self.assertRaises(ValueError) as context:
                    database.get_todo(todo_id)

                self.assertEqual(
                    str(context.exception),
                    "待办编号必须是正整数"
                )
    def test_update_todo_with_blank_content(self):
        todo = database.add_todo(
            "原始内容",
            "2026-12-31"
        )

        with self.assertRaises(ValueError) as context:
            database.update_todo(
                todo["id"],
                "   ",
                "2026-12-31"
            )

        self.assertEqual(
            str(context.exception),
            "待办内容不能为空"
        )

        unchanged_todo = database.get_todo(todo["id"])
        self.assertEqual(
            unchanged_todo["content"],
            "原始内容"
        )
    def test_add_todo_with_invalid_deadline_types(self):
        invalid_deadlines = [None, 20261231]

        for deadline in invalid_deadlines:
            with self.subTest(deadline=deadline):
                with self.assertRaises(ValueError) as context:
                    database.add_todo(
                        "测试内容",
                        deadline
                    )

                self.assertEqual(
                    str(context.exception),
                    "截止日期必须是有效的YYYY-MM-DD格式"
                )
    def test_update_todo_with_invalid_id(self):
        with self.assertRaises(ValueError) as context:
            database.update_todo(
                "abc",
                "更新后的内容",
                "2026-12-31"
            )

        self.assertEqual(
            str(context.exception),
            "待办编号必须是正整数"
        )
    def test_update_todo_with_invalid_deadline_type(self):
        todo = database.add_todo(
            "原始内容",
            "2026-12-31"
        )

        with self.assertRaises(ValueError) as context:
            database.update_todo(
                todo["id"],
                "更新后的内容",
                None
            )

        self.assertEqual(
            str(context.exception),
            "截止日期必须是有效的YYYY-MM-DD格式"
        )

        unchanged_todo = database.get_todo(todo["id"])
        self.assertEqual(
            unchanged_todo["content"],
            "原始内容"
        )
    def test_search_todos_by_keyword(self):
        database.add_todo(
            "学习 Python",
            "2026-12-01"
        )
        database.add_todo(
            "购买牛奶",
            "2026-12-02"
        )
        database.add_todo(
            "复习 Python 测试",
            "2026-12-03"
        )

        results = database.search_todos("Python")

        self.assertEqual(len(results), 2)
        self.assertEqual(
            [todo["content"] for todo in results],
            ["学习 Python", "复习 Python 测试"]
        )
    def test_search_todos_by_keyword(self):
        database.add_todo(
            "学习 Python",
            "2026-12-01"
        )
        database.add_todo(
            "购买牛奶",
            "2026-12-02"
        )
        database.add_todo(
            "复习 Python 测试",
            "2026-12-03"
        )

        results = database.search_todos("Python")

        self.assertEqual(len(results), 2)
        self.assertEqual(
            [todo["content"] for todo in results],
            ["学习 Python", "复习 Python 测试"]
        )
    def test_search_todos_with_no_match(self):
        database.add_todo("购买牛奶", "2026-12-01")

        results = database.search_todos("Python")

        self.assertEqual(results, [])
    def test_search_todos_with_invalid_keywords(self):
        invalid_keywords = ["", "   ", None, 123]

        for keyword in invalid_keywords:
            with self.subTest(keyword=keyword):
                with self.assertRaises(ValueError) as context:
                    database.search_todos(keyword)

                self.assertEqual(
                    str(context.exception),
                    "搜索关键词不能为空"
                )
    def test_search_todos_with_percent_sign(self):
        database.add_todo("完成进度达到50%", "2026-12-01")
        database.add_todo("购买牛奶", "2026-12-02")

        results = database.search_todos("%")

        self.assertEqual(
            [todo["content"] for todo in results],
            ["完成进度达到50%"]
        )
if __name__ == "__main__":
    unittest.main()
