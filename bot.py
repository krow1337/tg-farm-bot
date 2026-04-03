from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio
import os
import json
import sqlite3
import subprocess
import time
from datetime import datetime
from pyrogram import Client
from config import BOT_TOKEN, API_ID, API_HASH

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База данных
os.makedirs("chats", exist_ok=True)
os.makedirs("sessions", exist_ok=True)
os.makedirs("spam_texts", exist_ok=True)
os.makedirs("logs", exist_ok=True)

conn = sqlite3.connect("chats/chats.db")
conn.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT)")
conn.commit()

# Режим скорости (slow, fast, parallel)
speed_mode = "slow"

# Текст для рассылки
spam_text = None

def count_sessions():
    if not os.path.exists("sessions"):
        return 0
    return len([f for f in os.listdir("sessions") if f.endswith(".json")])

@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer(
        "/farm <число> — запуск фермы\n"
        "/fast — быстрый режим (меньше задержек)\n"
        "/slow — медленный режим (безопасный)\n"
        "/parallel — параллельный режим\n"
        "/settext <текст> — установить текст рассылки\n"
        "/spam — разослать текст в чаты\n"
        "/parse <слово> — найти чаты\n"
        "/stats — статистика\n"
        "/monitor — мониторинг в реальном времени"
    )

@dp.message(Command("fast"))
async def set_fast(m: types.Message):
    global speed_mode
    speed_mode = "fast"
    await m.answer("⚡ Быстрый режим включён (минимальные задержки)")

@dp.message(Command("slow"))
async def set_slow(m: types.Message):
    global speed_mode
    speed_mode = "slow"
    await m.answer("🐢 Медленный режим включён (безопасно)")

@dp.message(Command("parallel"))
async def set_parallel(m: types.Message):
    global speed_mode
    speed_mode = "parallel"
    await m.answer("🚀 Параллельный режим включён (ускоренная ферма)")

@dp.message(Command("settext"))
async def set_spam_text(m: types.Message):
    global spam_text
    spam_text = m.text.replace("/settext", "").strip()
    if spam_text:
        await m.answer(f"✅ Текст рассылки сохранён:\n\n{spam_text}")
    else:
        await m.answer("❌ Укажи текст после команды. Пример:\n/settext Привет! Скидка 50%")

@dp.message(Command("spam"))
async def spam(m: types.Message):
    global spam_text
    if not spam_text:
        await m.answer("❌ Сначала установи текст рассылки через /settext")
        return

    cursor = conn.execute("SELECT id FROM chats")
    chats = cursor.fetchall()
    if not chats:
        await m.answer("❌ Нет чатов. Сначала выполни /parse")
        return

    await m.answer(f"📨 Рассылка в {len(chats)} чатов...")
    for chat_id in chats:
        try:
            await bot.send_message(chat_id[0], spam_text)
            await asyncio.sleep(0.3)
        except:
            pass
    await m.answer("✅ Рассылка завершена")

@dp.message(Command("farm"))
async def farm(m: types.Message):
    args = m.text.split()
    count = args[1] if len(args) > 1 else "100"

    if speed_mode == "fast":
        delay = "5"
        parallel = "1"
    elif speed_mode == "parallel":
        delay = "2"
        parallel = "20"
    else:
        delay = "30"
        parallel = "1"

    cmd = f"python main.py {count} {delay} {parallel} > logs/farm.log 2>&1 &"
    os.system(cmd)
    await m.answer(f"🚜 Ферма запущена ({count} попыток, режим: {speed_mode})")

@dp.message(Command("parse"))
async def parse(m: types.Message):
    keyword = m.text.replace("/parse", "").strip()
    if not keyword:
        await m.answer("❌ Укажи ключевое слово. Пример: /parse крипта")
        return

    await m.answer(f"🔍 Поиск чатов по: {keyword}")

    async with Client("temp_session", API_ID, API_HASH, in_memory=True) as app:
        try:
            dialogs = await app.get_dialogs()
            found = []
            for d in dialogs:
                if keyword.lower() in (d.chat.title or "").lower():
                    found.append(d.chat)
                    conn.execute("INSERT OR IGNORE INTO chats VALUES (?, ?)",
                                 (str(d.chat.id), d.chat.title))
            conn.commit()
            await m.answer(f"✅ Найдено {len(found)} чатов. База обновлена.")
        except Exception as e:
            await m.answer(f"❌ Ошибка: {e}")

@dp.message(Command("stats"))
async def stats(m: types.Message):
    sessions = count_sessions()
    cursor = conn.execute("SELECT COUNT(*) FROM chats")
    chats_count = cursor.fetchone()[0]
    await m.answer(f"👥 Сессии: {sessions}\n💬 Чатов в базе: {chats_count}\n⚡ Режим: {speed_mode}")

@dp.message(Command("monitor"))
async def monitor(m: types.Message):
    await m.answer("📊 Мониторинг запущен (обновление каждые 30 сек)")
    for _ in range(20):
        sessions = count_sessions()
        await bot.send_message(m.chat.id, f"📈 Сессий: {sessions} | {datetime.now().strftime('%H:%M:%S')}")
        await asyncio.sleep(30)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())