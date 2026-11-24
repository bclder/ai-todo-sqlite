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

    def test_home_returns_html(self):
        with TestClient(app) as client:
            response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("我的待办事项", response.text)

    def test_create_todo(self):
        expected = {
            "id": 1,
            "content": "学习 POST 请求",
            "status": "未完成",
            "deadline": "2026-12-01"
        }

        with patch(
            "web_api.database.add_todo",
            return_value=expected
        ) as fake_add:
            with TestClient(app) as client:
                response = client.post(
                    "/todos",
                    json={
                        "content": "学习 POST 请求",
                        "deadline": "2026-12-01"
                    }
                )

            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json(), expected)
            fake_add.assert_called_once_with(
                content="学习 POST 请求",
                deadline="2026-12-01"
            )

    def test_create_todo_with_invalid_content(self):
        error_message = "待办内容不能为空"

        with patch(
            "web_api.database.add_todo",
            side_effect=ValueError(error_message)
        ) as fake_add:
            with TestClient(app) as client:
                response = client.post(
                    "/todos",
                    json={
                        "content": "",
                        "deadline": "2026-12-01"
                    }
                )

            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json(),
                {"detail": error_message}
            )
            fake_add.assert_called_once_with(
                content="",
                deadline="2026-12-01"
            )

    def test_create_todo_without_deadline(self):
        with patch("web_api.database.add_todo") as fake_add:
            with TestClient(app) as client:
                response = client.post(
                    "/todos",
                    json={"content": "学习 POST 请求"}
                )

            self.assertEqual(response.status_code, 422)
            fake_add.assert_not_called()