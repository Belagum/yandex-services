from patchright.async_api import async_playwright

class BrowserSession:
    def __init__(self, headless: bool = False, channel: str = "chrome"):
        self.headless = headless
        self.channel = channel
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(channel=self.channel, headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        return self.page

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.browser.close()
        await self.playwright.stop()
