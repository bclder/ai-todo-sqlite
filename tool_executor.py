import json
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