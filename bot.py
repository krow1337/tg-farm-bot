import os
import sqlite3
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from pyrogram import Client
from config import BOT_TOKEN, API_ID, API_HASH

# База данных
os.makedirs("chats", exist_ok=True)
os.makedirs("sessions", exist_ok=True)
os.makedirs("spam_texts", exist_ok=True)

conn = sqlite3.connect("chats/chats.db")
conn.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT)")
conn.commit()

spam_text = None

def count_sessions():
    if not os.path.exists("sessions"):
        return 0
    return len([f for f in os.listdir("sessions") if f.endswith(".json")])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/farm <число> — запуск фермы\n"
        "/parse <слово> — найти чаты\n"
        "/settext <текст> — текст рассылки\n"
        "/spam — разослать\n"
        "/stats — статистика"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sessions = count_sessions()
    cursor = conn.execute("SELECT COUNT(*) FROM chats")
    chats_count = cursor.fetchone()[0]
    await update.message.reply_text(f"👥 Сессии: {sessions}\n💬 Чатов: {chats_count}")

async def set_spam_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_text
    spam_text = " ".join(context.args)
    await update.message.reply_text(f"✅ Текст сохранён:\n{spam_text}")

async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_text
    if not spam_text:
        await update.message.reply_text("❌ Сначала /settext")
        return
    cursor = conn.execute("SELECT id FROM chats")
    chats = cursor.fetchall()
    for chat_id in chats:
        try:
            await context.bot.send_message(chat_id[0], spam_text)
            await asyncio.sleep(0.3)
        except:
            pass
    await update.message.reply_text("✅ Рассылка завершена")

async def parse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = " ".join(context.args)
    if not keyword:
        await update.message.reply_text("❌ Укажи слово: /parse крипта")
        return
    await update.message.reply_text(f"🔍 Поиск чатов по: {keyword}")
    async with Client("temp_session", API_ID, API_HASH, in_memory=True) as app:
        dialogs = await app.get_dialogs()
        found = 0
        for d in dialogs:
            if keyword.lower() in (d.chat.title or "").lower():
                conn.execute("INSERT OR IGNORE INTO chats VALUES (?, ?)",
                             (str(d.chat.id), d.chat.title))
                found += 1
        conn.commit()
        await update.message.reply_text(f"✅ Найдено {found} чатов")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("settext", set_spam_text))
    app.add_handler(CommandHandler("spam", spam))
    app.add_handler(CommandHandler("parse", parse))
    app.run_polling()

if __name__ == "__main__":
    main()