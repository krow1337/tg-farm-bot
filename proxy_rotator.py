import aiohttp,asyncio,random,os
class ProxyRotator:
    def __init__(self):self.proxies=[]
    async def update_proxies(self):
        urls=["https://api.proxyscrape.com/v2/?request=get&protocol=socks5","https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt"]
        self.proxies=[]
        async with aiohttp.ClientSession() as s:
            for u in urls:
                try:self.proxies+=[f"socks5://{p.strip()}" for p in (await s.get(u)).text().splitlines() if ':' in p]
                except:pass
        with open("proxies/proxies.txt","w") as f:f.write("\n".join(self.proxies))
        print(f"✅ {len(self.proxies)} прокси")
    def get_next(self):return random.choice(self.proxies) if self.proxies else None
proxy_rotator=ProxyRotator()