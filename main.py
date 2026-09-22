import os
import sys
from openai import OpenAI
from database import create_database
from datetime import date
from conversation import run_turn

api_key = os.environ.get("DEEPSEEK_API_KEY")

if not api_key:
    print("未检测到DEEPSEEK_API_KEY，请先配置环境变量")
    sys.exit()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

create_database()

MAX_API_CALLS = 5

TODAY = date.today().isoformat()

SYSTEM_PROMPT = f"""
你是AI待办事项助手，可以使用工具添加、查询、修改、删除和完成待办事项。

当前日期是：{TODAY}

要求：
1. 所有回答使用简体中文。
2. 查询或修改待办事项时，必须使用工具获取真实数据。
3. 不要声称已经完成尚未通过工具执行的操作。
4. 待办事项的截止日期使用YYYY-MM-DD格式。
5. 修改待办时，如果用户只要求修改部分字段，必须先查询原待办，并保留用户未要求修改的字段。
"""

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]
while True:
    question = input("请输入需求：")

    if question == "exit":
        break
    
    elif question == "clear":
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        print("对话历史已清空")
        continue

    messages.append({
        "role": "user",
        "content": question
    })
        
    run_turn(client, messages, max_api_calls=MAX_API_CALLS)


