import asyncio
import aiohttp
from aiohttp import BasicAuth

USER_URL = 'http://127.0.0.1:8080/user/'
STICKER_URL = 'http://127.0.0.1:8080/sticker/'
# user1:user1
BASICTOKEN1 = 'dXNlcjE6dXNlcjE='
# user2:user2
BASICTOKEN2 = 'dXNlcjI6dXNlcjI='


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(STICKER_URL+'1', auth=BasicAuth('user1', 'user1')) as resp:
            print(resp.status)
            print(await resp.text())

if __name__ == '__main__':
    asyncio.run(main())
