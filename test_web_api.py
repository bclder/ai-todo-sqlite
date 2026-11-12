import unittest
from fastapi.testclient import TestClient
from web_api import app
from unittest.mock import patch

class WebApiTests(unittest.TestCase):
    def test_health(self):
        with TestClient(app) as client:
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
    
    def test_list_todos_passes_status(self):
        expected = [
            {
                "id": 1,
                "content": "学习接口测试",
                "status": "未完成",
                "deadline": "2026-12-31"
            }
        ]

        with patch(
            "web_api.database.get_todos",
            return_value=expected
        ) as fake_get:
            with TestClient(app) as client:
                response = client.get(
                    "/todos",
                    params={"status": "未完成"}
                )

        fake_get.assert_called_once_with(status="未完成")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    def test_list_todos_without_status(self):
        with patch(
            "web_api.database.get_todos",
            return_value=[]
        ) as fake_get:
            with TestClient(app) as client:
                response = client.get("/todos")

        fake_get.assert_called_once_with(status=None)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_list_todos_with_invalid_status(self):
        error_message = "状态必须是已完成或未完成"

        with patch(
            "web_api.database.get_todos",
            side_effect=ValueError(error_message)
        ) as fake_get:
            with TestClient(app) as client:
                response = client.get(
                    "/todos",
                    params={"status": "随便写"}
                )

        fake_get.assert_called_once_with(status="随便写")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": error_message}
        )
    
    def test_todo_stats(self):
        expected = {
            "total": 3,
            "pending": 2,
            "completed": 1
        }

        with patch(
            "web_api.database.get_todo_stats",
            return_value=expected
        ) as fake_stats:
            with TestClient(app) as client:
                response = client.get("/todos/stats")

        fake_stats.assert_called_once_with()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)