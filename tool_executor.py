import json
from database import get_todo
from tool_config import available_functions

def execute_tool_call(tool_call):
    try:
        arguments=json.loads(tool_call.function.arguments)
        if not isinstance(arguments, dict):
            raise ValueError("工具参数必须是 JSON 对象")
        print("模型选择的函数：", tool_call.function.name)
        print("模型提供的参数：", arguments)
        function = available_functions.get(tool_call.function.name)
        if function is None:
            raise ValueError(
            f"无法执行未知工具：{tool_call.function.name}")
        if tool_call.function.name == "delete_todo":
            todo = get_todo(**arguments)
            if todo is None:
                raise ValueError("待办编号不存在")
            confirmation = input(
                f"确认删除待办 {todo['id']}：{todo['content']}？输入 y 删除，其他输入取消："
            )
            if confirmation != "y":
                return {
                    "success": False,
                    "cancelled": True,
                    "error": "用户取消删除，待办未删除",
                }
        result = {
            "success":True,
            "data":function(**arguments)
            }
    except Exception as error:
        result = {
            "success": False,
            "error": str(error)
        }
    return result
