import logging
from patchright.async_api import async_playwright

logger = logging.getLogger(__name__)

class BrowserSession:
    def __init__(self, headless: bool = False, channel: str = "chrome"):
        self.headless = headless; self.channel = channel
        self.playwright = None; self.browser = None; self.context = None; self.page = None

    async def __aenter__(self):
        logger.info(f"Запуск Playwright: headless={self.headless}, канал={self.channel}")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(channel=self.channel, headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        logger.info("Контекст браузера создан и страница открыта")
        return self.page

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Ошибка в сессии браузера: {exc_val}")
        logger.info("Закрытие браузера")
        await self.browser.close()
        await self.playwright.stop()
        logger.info("Playwright остановлен")