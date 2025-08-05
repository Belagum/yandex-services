import random
from dataclasses import dataclass, field
import logging
from patchright.async_api import Page

from helpers.BaseHelper import BaseHelper
from yandex_flow.helpers.CaptchaHelper import CaptchaHelper
from difflib import SequenceMatcher

log = logging.getLogger(__name__)

@dataclass(frozen=True)
class YandexServicesCfg:
    url: str = 'https://ya.ru/'
    timeout: int = 30000
    search_input: str = '#text'
    service_fragment: str = 'uslugi.yandex.ru'
    city_div: str = "div[class*='WorkerGeo-Address']"
    results_selector: str = 'ul.serp-list'
    link_selector_tpl: str = "a[href*='{fragment}']"
    services_search_input: str = 'input.Textinput-Control[name="text"][placeholder="Чем вам помочь?"]'
    services_name_executor_a: str = 'a.Link.WorkerCard-Title'
    search_btn: str = 'a[aria-label=Мессенджер]'
    photo_a: str  = 'a.Link.PhotoGallery-Image'
    next_photo_btn: str = 'div.MediaViewer-ButtonNext'
    close_photo_btn: str = 'div.PhotoViewer-HeaderClose'
    min_wait_in_photo: float = 0.7
    max_wait_in_photo: float = 2.0
    service_name_a: str  = 'div.ProfileServiceCard-MainLeft a.Link'
    expand_services_btn: str  = 'div.SpecializationCard-CollapsibleList a.Link'
    close_service_windows_btn: str = 'div.YdoModal-BackButton'
    examples_div: str = 'div.Scroller-Item > section.WorkerPortfolioViewer-Item'
    close_example_btn: str = 'button.WorkerPortfolioInfo-Close'
    min_wait_in_example: float = 1.5
    max_wait_in_example: float = 2.5
    min_view_services: int = 2
    max_view_services: int = 5
    min_wait_before_close: float = 1.0
    max_wait_before_close: float = 2.5
    min_wait_after_verify_city: int = 3
    max_wait_after_verify_city: int = 6
    block_chance: float = 0.5
    min_photo_view: int = 1
    max_photo_view: int = 5
    phone_btn: str = 'a.Link.PhoneLoader-Link button.PhoneLoader-Button'
    popups: list[str] = field(default_factory=lambda: [
        'button.Distribution-ButtonClose',
        'button[title="Нет, спасибо"]'
    ])

class YandexService(BaseHelper):
    def __init__(self, page: Page, config: YandexServicesCfg):
        super().__init__(page)
        self.config = config
        self.solve_captcha = CaptchaHelper(page).solve

    def update_page(self, new_page):  # noqa: D401
        self.page = new_page
        self.mouse.page = new_page
        self.form.page = new_page
        self.locators.page = new_page
        self.click = self.mouse.click
        self.fill = self.form.fill
        self.is_present = self.locators.is_present
        log.debug(f"Переключено на новую страницу → {new_page.url}")

    async def close_popups(self):
        for popup_selector in self.config.popups:
            if await self.is_present(popup_selector, timeout=500):
                await self.click(popup_selector)
                log.debug(f"Closed popup → '{popup_selector}'")

    async def open_page(self) -> None:
        await self.page.goto(self.config.url, timeout=self.config.timeout, wait_until='domcontentloaded')

    async def search(self, query: str) -> tuple[bool, str]:
        try:
            await self.open_page()
            await self.close_popups()
            await self.fill(self.config.search_input, query, press_enter=True)
            await self.solve_captcha()
            await self.close_popups()
            await self.page.wait_for_selector(self.config.results_selector, timeout=self.config.timeout)
            selector = self.config.link_selector_tpl.format(fragment=self.config.service_fragment)
            link = await self.page.wait_for_selector(selector)
            if not link:
                log.error("Сайт Яндекс услуг не найден в выдаче")
                return False, "Сайт Яндекс услуг не найден в выдаче"
            waiter = self.page.context.wait_for_event('page')
            await self.click(link)
            new_page = await waiter
            await new_page.wait_for_load_state('domcontentloaded', timeout=self.config.timeout)
            self.update_page(new_page)
            return True, "Клик по нужному сайту выполнен"
        except Exception as e:
            log.error(f"Ошибка в методе search: {e}")
            return False, "Ошибка при поиске"

    async def verify_city(self, city: str) -> tuple[bool, str]:
        try:
            locator = self.page.locator(self.config.city_div)
            await locator.first.wait_for(timeout=12_000)
            total = await locator.count()
            sample = min(5, total)
            matches = 0
            log.debug(f"Город '{city}' | найдено {total} блоков, анализирую {sample}")
            for i in range(sample):
                txt = (await locator.nth(i).inner_text()).strip()
                sim = SequenceMatcher(None, txt, city).ratio()
                log.debug(f"#{i + 1}: '{txt}' — сходство {sim:.2f}")
                if sim >= 0.7:
                    matches += 1
            log.debug(f"Совпадения: {matches}/{sample} ({matches / sample * 100:.0f}%)")
            if matches / sample >= 0.7:
                log.info("Город подтверждён")
                return True, "Город подтверждён"
            log.info("Город не совпал, уточняю запрос")
            await self.fill(
                selector=self.config.services_search_input,
                text=city,
                append=True,
                press_enter=True,
            )
            await self.page.wait_for_timeout(random.randint(self.config.min_wait_after_verify_city, self.config.max_wait_after_verify_city) * 1000)
            return True, "Город уточнён запросом"
        except Exception as e:
            log.error(f"verify_city failed: {e}")
            return False, f"Ошибка: {e}"

    async def find_executor(self, name: str, *, max_miss: int = 10, sim_threshold: float = 0.85) -> tuple[bool, str]:
        loc = self.page.locator(self.config.services_name_executor_a)
        misses = 0
        log.debug(f"start search: '{name}'")

        while misses < max_miss:
            total = await loc.count()
            if misses < total:
                el = loc.nth(misses)
                text = (await el.text_content() or "").split("\n", 1)[0].strip()
                sim = SequenceMatcher(None, text, name).ratio()
                log.debug(f"#{misses + 1}: '{text}' ~ '{name}' → {sim:.2f}")

                if sim >= sim_threshold:
                    waiter = self.page.context.wait_for_event("page")
                    await self.click(el)
                    new_page = await waiter
                    await new_page.wait_for_load_state("domcontentloaded", timeout=self.config.timeout)
                    self.update_page(new_page)
                    log.info(f"'{name}' найден и открыт")
                    return True, "Исполнитель найден"

                misses += 1
            else:
                log.debug(f"просмотрено {misses} карточек, скроллю ниже…")
                await self.page.mouse.wheel(0, 1200)
                await self.page.wait_for_timeout(500)

        log.error(f"'{name}' не найден (проверено {misses} карточек)")
        return False, "Исполнитель не найден"

    async def _click_random_items(
            self,
            item_selector: str,
            close_selector: str,
            *,
            min_view: int,
            max_view: int,
            min_wait: int,
            max_wait: int,
            description: str
    ) -> None:
        locator = self.page.locator(item_selector)
        total = await locator.count()
        view_n = min(total, random.randint(min_view, max_view))
        if view_n == 0:
            log.error(f"Нет {description} для клика")
            return

        indices = random.sample(range(total), view_n)
        log.debug(f"Кликаю по {view_n}/{total} {description}: {indices}")
        for i, idx in enumerate(indices, 1):
            await self.click(item_selector, index=idx)
            delay = random.randint(min_wait, max_wait) * 1000
            await self.page.wait_for_timeout(delay)
            if await self.is_present(close_selector):
                await self.click(close_selector)
                log.debug(f"Закрыл {description} #{idx}")

    async def _click_random_examples(self) -> None:
        await self._click_random_items(
            item_selector=self.config.examples_div,
            close_selector=self.config.close_example_btn,
            min_view=self.config.min_view_services,
            max_view=self.config.max_view_services,
            min_wait=self.config.min_wait_in_example,
            max_wait=self.config.max_wait_in_example,
            description="примеров работ"
        )

    async def _click_random_services(self) -> None:
        if await self.is_present(self.config.expand_services_btn):
            await self.click(self.config.expand_services_btn)
            log.debug("Раскрыт список услуг")
        await self._click_random_items(
            item_selector=self.config.service_name_a,
            close_selector=self.config.close_service_windows_btn,
            min_view=self.config.min_view_services,
            max_view=self.config.max_view_services,
            min_wait=self.config.min_wait_before_close,
            max_wait=self.config.max_wait_before_close,
            description="услуг"
        )

    async def _click_random_photos(self) -> None:
        if await self.is_present(self.config.photo_a):
            await self.click(self.config.photo_a)
            log.debug("Открыта первая фотография")

        count = random.randint(self.config.min_photo_view, self.config.max_photo_view)
        log.debug(f"Буду пролистывать {count} фотографий")

        for i in range(count):
            delay = random.randint(self.config.min_wait_in_photo, self.config.max_wait_in_photo) * 1000
            await self.page.wait_for_timeout(delay)
            if not await self.is_present(self.config.next_photo_btn):
                log.warning(f"Кнопка следующей фото не найдена на шаге {i + 1}")
                break
            await self.click(self.config.next_photo_btn)
            log.debug(f"Перелистнута фотография #{i + 1}")

        if await self.is_present(self.config.close_photo_btn):
            await self.click(self.config.close_photo_btn)
            log.debug("Закрыт просмотр фотографий")
