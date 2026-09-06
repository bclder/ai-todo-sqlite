import unittest
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
if __name__ == "__main__":
    unittest.main()
