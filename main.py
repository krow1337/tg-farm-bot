#!/usr/bin/env python3
import asyncio,random,os,json,re
from pyrogram import Client
from pyrogram.errors import *
from proxy_rotator import proxy_rotator
import aiohttp
from faker import Faker
fake=Faker()
os.makedirs("sessions",exist_ok=True);os.makedirs("free_data",exist_ok=True)

class FreeFarm:
    def __init__(self):self.stats={"success":0}
    async def load_phones(self):
        if not os.path.exists("free_data/free_phones.txt"):
            [open("free_data/free_phones.txt",'a').write(f"+7{random.randint(9000000000,9999999999)}\n") for _ in range(1000)]
        return [l.strip() for l in open("free_data/free_phones.txt").readlines()]
    async def create_free_account(self,phone):
        proxy=proxy_rotator.get_next()
        async with Client(f"sessions/free_{phone[-10:]}",API_ID,API_HASH,proxy=proxy) as app:
            try:sent=await app.send_code(phone)
                for otp in [1234,12345,0000,1111,123456]:
                    try:await app.sign_in(phone,sent.phone_code_hash,str(otp));me=await app.get_me()
                        open(f"sessions/free_{phone[-10:]}.json",'w').write(json.dumps({"phone":phone,"user":str(me)}));self.stats["success"]+=1;print(f"✅ FREE: {phone} @{getattr(me,'username','')}");return True
                    except:pass
            except:pass;return False
    async def farm(self,count=100):await proxy_rotator.update_proxies();phones=await self.load_phones();[await self.create_free_account(p)or asyncio.sleep(30) for p in phones[:count]]

asyncio.run(FreeFarm().farm(200))