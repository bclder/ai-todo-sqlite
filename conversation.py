import json

from tool_config import tools
from tool_executor import execute_tool_call


def run_turn(client, messages, max_api_calls=5):
    for api_calls in range(1, max_api_calls + 1):
        print("本轮API调用次数：", api_calls)

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            message = response.choices[0].message

        except Exception as error:
            error_message = f"API请求失败：{error}"
            print(error_message)

            messages.append({
                "role": "assistant",
                "content": error_message,
            })
            return

        messages.append(message)

        if message.tool_calls:
            for tool_call in message.tool_calls:
                result = execute_tool_call(tool_call)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
        else:
            print("模型最终回答：", message.content)
            return

    print("本轮API调用次数达到上限，任务已停止")