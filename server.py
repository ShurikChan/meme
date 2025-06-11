from fastapi import FastAPI, HTTPException
import json
import aiofiles
from pathlib import Path

app = FastAPI()

# Путь к файлу базы данных (должен совпадать с вашим текущим скриптом)
DB_FILE = "db.json"

async def load_db():
    """Загружает базу данных из файла."""
    try:
        async with aiofiles.open(DB_FILE, mode="r") as f:
            data = await f.read()
            return json.loads(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

@app.get("/check_id/{twitter_id}")
async def check_id(twitter_id: str):
    """Проверяет, есть ли Twitter ID в базе."""
    db = await load_db()
    exists = twitter_id in db
    return {"exists": exists, "twitter_id": twitter_id}

@app.get("/all_ids")
async def get_all_ids():
    """Возвращает все ID из базы (для отладки)."""
    db = await load_db()
    return {"ids": list(db.keys())}