from dataclasses import dataclass

from helpers.BaseHelper import BaseHelper
from yandex_flow.helpers.CaptchaHelper import CaptchaHelper


@dataclass
class YandexServicesCfg:
    url: str = 'https://ya.ru/'
    wait_ms: int = 30000
    yandex_services: str = 'Яндекс услуги'

class YandexService(BaseHelper):
    def __init__(self, page, config: YandexServicesCfg):
        super().__init__(page)
        self.config = config
        self._captcha = CaptchaHelper(page)
        self.solve = self._captcha.solve


    async def open_page(self):
        await self.page.goto(self.config.url,
                             timeout=self.config.wait_ms,
                             wait_until="domcontentloaded")

    async def search(self):
        await self.open_page()

        query = f"123 {self.config.yandex_services}"

        await self.fill("#text", query, press_enter=True)
        try:
            await self.solve()
        except Exception as e:
            print(e)
        input()