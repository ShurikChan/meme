import asyncio
import websockets
import json
import time
import aiohttp
import aiofiles  # Для асинхронной работы с файлами
from datetime import datetime
from utils import fetch_twitter_community_id

# Путь к файлу базы данных
DB_FILE = "meme_db/db.json"

async def load_db():
    """Загружает базу данных из файла или создает новую."""
    try:
        async with aiofiles.open(DB_FILE, mode="r") as f:
            data = await f.read()
            return json.loads(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Если файла нет или он пуст, возвращаем пустой словарь

async def save_db(db):
    """Сохраняет базу данных в файл."""
    async with aiofiles.open(DB_FILE, mode="w") as f:
        await f.write(json.dumps(db, indent=2))

async def subscribe():
    uri = "wss://pumpportal.fun/api/data"
    db = await load_db()  # Загружаем базу при старте

    async with websockets.connect(uri) as websocket:
        payload = {"method": "subscribeNewToken"}
        await websocket.send(json.dumps(payload))
        
        async for message in websocket:
            data = json.loads(message)
            mint = data.get("mint")
            if mint is not None:
                ipfs = data.get("uri")
                twitter_comunity_id = await fetch_twitter_community_id(ipfs)
                
                if twitter_comunity_id is not None:
                    # Проверяем, есть ли ID в базе (O(1))
                    if twitter_comunity_id not in db:
                        db[twitter_comunity_id] = True  # Добавляем (O(1))
                        await save_db(db)  # Сохраняем в файл
                        print(f" New ID added: {twitter_comunity_id}")
                    else:
                        print(f" ID already exists: {twitter_comunity_id}")

async def main():
    while True:
        try:
            await subscribe()
        except Exception as e:
            print(f"Error occurred: {e}")
            await asyncio.sleep(1)  # Ждем 1 секунду перед переподключением

if __name__ == "__main__":
    asyncio.run(main())