\# AI 待办事项管理器



这是一个使用 Python、DeepSeek API 和 SQLite 开发的待办事项管理项目。



用户可以通过自然语言与 AI 对话，由 AI 调用工具完成待办事项的新增、查询、修改、完成和删除。



\## 主要功能



\- 添加待办事项

\- 查询全部待办

\- 查询未完成待办

\- 修改待办内容和截止日期

\- 标记待办为已完成

\- 删除待办事项

\- 使用 SQLite 保存本地数据

\- 使用 AI 工具调用理解用户指令



\## 项目结构



\- `main.py`：程序入口和 AI 对话流程

\- `database.py`：SQLite 数据库操作

\- `tool\_config.py`：AI 工具定义和调用配置

\- `requirements.txt`：项目第三方依赖

\- `.gitignore`：不上传到 Git 的本地文件



\## 安装依赖



```bash

python -m pip install -r requirements.txt

```



\## 配置 API Key



在 Windows 命令提示符中设置 DeepSeek API Key：



```bat

set DEEPSEEK\_API\_KEY=你的API密钥

```



不要把真实的 API Key 写入本文件。



\## 运行项目



```bash

python main.py

```

