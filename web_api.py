from pathlib import Path
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import database

app = FastAPI()

class TodoCreate(BaseModel):
    content: str
    deadline: str

@app.get("/")
def home():
    html_path = Path(__file__).resolve().parent / "static" / "index.html"
    return FileResponse(html_path)


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/todos")
def list_todos(status: str | None = None):
    try:
        return database.get_todos(status=status)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

@app.get("/todos/stats")
def todo_stats():
    return database.get_todo_stats()

@app.post("/todos", status_code=201)
def create_todo(todo: TodoCreate):
    try:
        return database.add_todo(
            content=todo.content,
            deadline=todo.deadline
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )