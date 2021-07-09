import aiohttp
import asyncio

from classes.super6 import Super6


async def main():
    async with aiohttp.ClientSession() as session:
        s6 = Super6(session)
        await s6.update_database()
        s6.print_calculations()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
