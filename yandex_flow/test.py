import asyncio
import logging

from yandex_flow.YandexService import YandexService, YandexServicesCfg
from yandex_flow.start import BrowserSession
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

async def main():
    async with BrowserSession() as page:
        config = YandexServicesCfg()
        service = YandexService(page, config)
        query = "москва сантехник" + " Яндекс услуги "
        await service.search(query=query)
        await service.verify_city(city="иваново")
        await service.find_executor(name="Николай С.")
        input()

if __name__ == "__main__":
    asyncio.run(main())
