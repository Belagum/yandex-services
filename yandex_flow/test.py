import asyncio
from yandex_flow.YandexService import YandexService, YandexServicesCfg
from yandex_flow.start import BrowserSession

async def main():
    async with BrowserSession() as page:
        config = YandexServicesCfg()
        service = YandexService(page, config)
        await service.search()
        input()

if __name__ == "__main__":
    asyncio.run(main())
