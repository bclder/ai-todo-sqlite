from database import (
    add_todo,
    get_todos,
    get_todo,
    complete_todo,
    delete_todo,
    get_pending_todos,
    update_todo
)

available_functions = {
    "add_todo":add_todo,
    "get_todos":get_todos,
    "get_todo":get_todo,
    "complete_todo":complete_todo,
    "delete_todo":delete_todo,
    "get_pending_todos":get_pending_todos,
    "update_todo": update_todo
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "add_todo",
            "description": "添加一条待办事项",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "待办内容"
                    },
                    "deadline": {
                        "type": "string",
                        "description": "截止日期，格式为YYYY-MM-DD"
                    }
                },
                "required": ["content", "deadline"]
                }
            }
        },
        {
        "type": "function",
        "function": {
            "name": "get_todos",
            "description": "查看所有待办事项",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
                }
            }
        },
        {
        "type": "function",
        "function": {
            "name": "get_todo",
            "description": "根据编号查看指定待办事项",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "编号"
                    }

                },
                "required": ["todo_id"]
                }
            }
        },
        {
        "type": "function",
        "function": {
            "name": "complete_todo",
            "description": "根据编号将一条待办事项状态变为已完成",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "编号"
                    }

                },
                "required": ["todo_id"]
                }
            }
        },
        {
        "type": "function",
        "function": {
            "name": "delete_todo",
            "description": "根据编号删除指定待办事项",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "编号"
                    }

                },
                "required": ["todo_id"]
                }
            }
        },
        {
        "type": "function",
        "function": {
            "name": "get_pending_todos",
            "description": "获取所有状态为未完成的待办事项，并根据截止日期从小到大排序",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
                }
            }
        },
        {
        "type": "function",
        "function": {
            "name": "update_todo",
            "description": "根据编号修改待办事项的内容和截止日期",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "待办事项编号"
                    },
                    "content": {
                        "type": "string",
                        "description": "修改后的待办内容"
                    },
                    "deadline": {
                        "type": "string",
                        "description": "修改后的截止日期，格式为 YYYY-MM-DD"
                    }

                },
                "required": ["todo_id", "content", "deadline"]
                }
            }
        }
        ]
if __name__ == "__main__":
    print(available_functions.keys())

    for tool in tools:
        print(tool["function"]["name"])
