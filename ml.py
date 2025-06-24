import asyncio
import websockets
import json
import time
import os
import csv
from datetime import datetime
from collections import defaultdict

WS_URI = "wss://pumpportal.fun/api/data"
tracked_tokens = set()
last_ping = time.time()

os.makedirs("trades", exist_ok=True)

# Состояние по каждому токену
token_states = {}

def init_token_state(mint):
    token_states[mint] = {
        "first_ts": None,
        "wallets_seen": set(),
        "wallet_tx_count": defaultdict(int),
        "tx_number": 0,
        "volume_cum_sol": 0.0,
        "volume_cum_tokens": 0.0
    }

async def save_trade(trade):
    mint = trade.get("mint")
    if not mint:
        return

    timestamp = datetime.utcnow()
    sol = float(trade.get("solAmount", 0))
    tokens = float(trade.get("tokenAmount", 0))
    price = sol / tokens if tokens > 0 else 0
    wallet = trade.get("traderPublicKey", "")

    # Инициализируем состояние токена
    if mint not in token_states:
        init_token_state(mint)

    state = token_states[mint]

    # Установка времени первой сделки
    if state["first_ts"] is None:
        state["first_ts"] = timestamp

    # Обновляем счётчики
    state["tx_number"] += 1
    state["wallet_tx_count"][wallet] += 1
    is_repeat = wallet in state["wallets_seen"]
    state["wallets_seen"].add(wallet)
    state["volume_cum_sol"] += sol
    state["volume_cum_tokens"] += tokens
    is_first_minute = (timestamp - state["first_ts"]).total_seconds() <= 60

    # Запись
    filename = f"meme_ml/trades/{mint}.csv"
    file_exists = os.path.isfile(filename)

    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "mint", "txType", "solAmount", "tokenAmount", "price_per_token",
            "traderPublicKey", "is_repeat_buyer", "tx_count_by_wallet", "tx_number",
            "volume_cum_sol", "volume_cum_tokens", "is_first_minute"
        ])
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": timestamp.isoformat(),
            "mint": mint,
            "txType": trade.get("txType"),
            "solAmount": sol,
            "tokenAmount": tokens,
            "price_per_token": price,
            "traderPublicKey": wallet,
            "is_repeat_buyer": int(is_repeat),
            "tx_count_by_wallet": state["wallet_tx_count"][wallet],
            "tx_number": state["tx_number"],
            "volume_cum_sol": state["volume_cum_sol"],
            "volume_cum_tokens": state["volume_cum_tokens"],
            "is_first_minute": int(is_first_minute)
        })

async def subscribe_token_trades(ws, mint_address):
    if mint_address not in tracked_tokens:
        payload = {
            "method": "subscribeTokenTrade",
            "keys": [mint_address]
        }
        await ws.send(json.dumps(payload))
        tracked_tokens.add(mint_address)
        print(f"[+] Подписался на трейды: {mint_address}")

async def subscribe_loop():
    global last_ping
    while True:
        try:
            print("[*] Подключаюсь к WebSocket...")
            async with websockets.connect(WS_URI, ping_interval=None) as ws:
                print("[*] Подключено")

                await ws.send(json.dumps({"method": "subscribeNewToken"}))
                print("[*] Подписка на новые токены")

                while True:
                    if time.time() - last_ping > 30:
                        try:
                            await ws.ping()
                            last_ping = time.time()
                            print("[PING] отправлен")
                        except:
                            break

                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=60)
                        data = json.loads(message)

                        # Новый токен
                        if "mint" in data and data.get("txType") == "create":
                            mint_clean = data["mint"].replace("pump", "")
                            print(f"[NEW TOKEN] {data.get('name')} ({mint_clean})")
                            await subscribe_token_trades(ws, mint_clean)

                        # Трейды
                        elif data.get("txType") in ["buy", "sell"]:
                            await save_trade(data)

                    except asyncio.TimeoutError:
                        break
                    except Exception as e:
                        print(f"[!] Ошибка: {e}")
                        break

        except Exception as e:
            print(f"[!] Ошибка соединения: {e}")

        print("[*] Переподключение через 5 сек...\n")
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(subscribe_loop())
