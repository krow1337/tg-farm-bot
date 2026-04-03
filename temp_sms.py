import re,aiohttp
async def get_free_sms(phone):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://www.receive-sms-free.cc/api/phone/{phone[-10:]}") as r:
                if r.status==200:text=await r.text();return re.search(r'\b\d{4,6}\b',text).group()
    except:return None