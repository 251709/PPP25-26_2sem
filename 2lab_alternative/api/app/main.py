"""
main.py — инициализация FastAPI и подключение роутеров.

Запуск:
    uvicorn app.main:app --reload

Документация:
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from app.db import init_db
from app.routes import sources, items, events

app = FastAPI(title="ETL Web Service")


@app.on_event("startup")
def startup():
    init_db()


app.include_router(sources.router)
app.include_router(items.router)
app.include_router(events.router)
