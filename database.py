import sqlite3
from pathlib import Path
from datetime import datetime


DATA_FILE = Path(__file__).with_name("todos.db")


def get_connection():
    conn = sqlite3.connect(DATA_FILE)
    conn.row_factory = sqlite3.Row
    return conn
def create_database():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            status TEXT NOT NULL,
            deadline TEXT NOT NULL
            )
        """
        )
        conn.commit()
        
    except Exception:
        conn.rollback()
        raise
    
    finally:
        cursor.close()
        conn.close()

def add_todo(content, deadline):
    try:
        datetime.strptime(deadline, "%Y-%m-%d")

    except ValueError:
        raise ValueError("截止日期必须是有效的YYYY-MM-DD格式")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO todos (content, status, deadline)
            VALUES (?, ?, ?)
            """,
            (content, "未完成", deadline)
        )
        todo_id = cursor.lastrowid
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
    
    return {
        "id": todo_id,
        "content": content,
        "status": "未完成",
        "deadline": deadline
    }

def get_todos():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, content, status, deadline
            FROM todos
            """
        )
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()
    return result

def get_todo(todo_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, content, status, deadline
            FROM todos
            WHERE id = ?
            """,
            (todo_id,)
        )
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    if row is None:
        return None
    else:
        return dict(row)

def complete_todo(todo_id):
    todo = get_todo(todo_id)
    if todo is None:
        raise ValueError("待办编号不存在")
    if todo["status"] == "已完成":
        raise ValueError("该待办已经完成")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE todos
            SET status = ?
            WHERE id = ?
            """,
            ("已完成", todo_id)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
    return get_todo(todo_id)

def delete_todo(todo_id):
    deleted_todo = get_todo(todo_id)
    if deleted_todo is None:
        raise ValueError("待办编号不存在")
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM todos
            WHERE id = ?
            """,
            (todo_id,)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
    return deleted_todo
def get_pending_todos():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, content, status, deadline
            FROM todos
            WHERE status = ?
            ORDER BY deadline ASC
            """,
            ("未完成",)
        )
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()
    return result
def update_todo(todo_id, content, deadline):
    try:
        datetime.strptime(deadline, "%Y-%m-%d")

    except ValueError:
        raise ValueError("截止日期必须是有效的YYYY-MM-DD格式")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE todos
            SET content = ?, deadline = ?
            WHERE id = ?
            """,
            (content, deadline, todo_id)
        )
        affected_rows = cursor.rowcount
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    if affected_rows == 0:
        raise ValueError("待办编号不存在")

    return get_todo(todo_id)

if __name__ == "__main__":
    create_database()
    print("数据库初始化完成")
