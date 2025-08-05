import asyncio
import logging

from yandex_flow.YandexService import YandexService, YandexServicesCfg
from yandex_flow.start import BrowserSession
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

async def main():
    async with BrowserSession() as page:
        config = YandexServicesCfg()
        service = YandexService(page, config)
        await service.search()
        await service.verify_city()
        await service.find_executor()
        await service.perform_random_action()
        input()

if __name__ == "__main__":
    asyncio.run(main())
