import os
import sqlite3
import asyncio
import subprocess
import zipfile
import io
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from pyrogram import Client
from config import BOT_TOKEN, API_ID, API_HASH

# ========== НАСТРОЙКИ ==========
os.makedirs("chats", exist_ok=True)
os.makedirs("sessions", exist_ok=True)
os.makedirs("spam_texts", exist_ok=True)
os.makedirs("free_data", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# ========== БАЗА ДАННЫХ ==========
conn = sqlite3.connect("chats/chats.db")
conn.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT)")
conn.commit()

spam_text = None

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def count_sessions():
    if not os.path.exists("sessions"):
        return 0
    return len([f for f in os.listdir("sessions") if f.endswith(".json")])

# ========== КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *TG Farm Bot*\n\n"
        "📌 *Команды:*\n"
        "/generate_phones <число> — сгенерировать номера\n"
        "/farm <число> — запустить ферму\n"
        "/sessions — количество сессий\n"
        "/download_sessions — скачать все сессии архивом\n"
        "/parse <слово> — найти чаты\n"
        "/settext <текст> — текст рассылки\n"
        "/spam — разослать текст\n"
        "/stats — общая статистика\n"
        "/monitor — мониторинг сессий\n\n"
        "⚙️ *Пример:*\n"
        "/generate_phones 500\n"
        "/farm 20\n"
        "/parse крипта",
        parse_mode="Markdown"
    )

async def generate_phones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = int(context.args[0]) if context.args else 1000
    await update.message.reply_text(f"📱 Генерация {count} номеров...")
    
    from faker import Faker
    fake = Faker('ru_RU')
    phones = []
    for _ in range(count):
        phone = f"+7{fake.msisdn()[3:6]}{fake.msisdn()[6:]}"
        phones.append(phone)
    
    with open("free_data/free_phones.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(phones))
    
    await update.message.reply_text(f"✅ Сгенерировано {len(phones)} номеров\n📁 free_data/free_phones.txt")

async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = int(context.args[0]) if context.args else 10
    await update.message.reply_text(f"🚜 Запуск фермы на {count} попыток (фон)...")
    
    subprocess.Popen(["python", "farm.py", str(count)])
    await update.message.reply_text(f"✅ Ферма запущена. Результаты появятся в папке sessions/\n📊 Мониторинг: /sessions")

async def sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = count_sessions()
    await update.message.reply_text(f"📁 Всего сессий создано: {count}")

async def download_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists("sessions"):
        await update.message.reply_text("📭 Папка sessions не найдена")
        return
    
    files = os.listdir("sessions")
    if not files:
        await update.message.reply_text("📭 Сессий пока нет")
        return
    
    await update.message.reply_text(f"📦 Создаю архив из {len(files)} файлов...")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            file_path = os.path.join("sessions", file)
            zip_file.write(file_path, file)
    
    zip_buffer.seek(0)
    await update.message.reply_document(
        document=zip_buffer,
        filename="sessions.zip",
        caption=f"📦 Архив с {len(files)} сессиями"
    )

async def parse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = " ".join(context.args)
    if not keyword:
        await update.message.reply_text("❌ Укажи слово для поиска: /parse крипта")
        return
    
    await update.message.reply_text(f"🔍 Поиск чатов по ключевому слову: {keyword}")
    
    async with Client("temp_session", API_ID, API_HASH, in_memory=True) as app:
        dialogs = await app.get_dialogs()
        found = 0
        for d in dialogs:
            title = d.chat.title or ""
            if keyword.lower() in title.lower():
                conn.execute("INSERT OR IGNORE INTO chats VALUES (?, ?)",
                             (str(d.chat.id), title))
                found += 1
        conn.commit()
    
    await update.message.reply_text(f"✅ Найдено чатов: {found}\n💾 База обновлена")

async def set_spam_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_text
    spam_text = " ".join(context.args)
    if not spam_text:
        await update.message.reply_text("❌ Укажи текст после команды: /settext Привет!")
        return
    await update.message.reply_text(f"✅ Текст сохранён:\n\n{spam_text}")

async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_text
    if not spam_text:
        await update.message.reply_text("❌ Сначала установи текст через /settext")
        return
    
    cursor = conn.execute("SELECT id FROM chats")
    chats = cursor.fetchall()
    if not chats:
        await update.message.reply_text("❌ Нет чатов. Сначала выполни /parse")
        return
    
    await update.message.reply_text(f"📨 Рассылка в {len(chats)} чатов...")
    sent = 0
    for chat_id in chats:
        try:
            await context.bot.send_message(chat_id[0], spam_text)
            sent += 1
            await asyncio.sleep(0.3)
        except:
            pass
    
    await update.message.reply_text(f"✅ Рассылка завершена\n📤 Отправлено: {sent} из {len(chats)}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sessions = count_sessions()
    cursor = conn.execute("SELECT COUNT(*) FROM chats")
    chats_count = cursor.fetchone()[0]
    
    await update.message.reply_text(
        f"📊 *Статистика*\n\n"
        f"👥 Сессий: {sessions}\n"
        f"💬 Чатов в базе: {chats_count}\n"
        f"📂 Номера: {'✅' if os.path.exists('free_data/free_phones.txt') else '❌'}\n"
        f"📝 Текст рассылки: {'✅' if spam_text else '❌'}",
        parse_mode="Markdown"
    )

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Мониторинг запущен (обновление каждые 30 секунд)")
    for _ in range(20):
        count = count_sessions()
        await update.message.reply_text(f"📈 Сессий: {count} | {datetime.now().strftime('%H:%M:%S')}")
        await asyncio.sleep(30)

# ========== ЗАПУСК ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate_phones", generate_phones))
    app.add_handler(CommandHandler("farm", farm))
    app.add_handler(CommandHandler("sessions", sessions))
    app.add_handler(CommandHandler("download_sessions", download_sessions))
    app.add_handler(CommandHandler("parse", parse))
    app.add_handler(CommandHandler("settext", set_spam_text))
    app.add_handler(CommandHandler("spam", spam))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("monitor", monitor))
    
    print("🤖 Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()