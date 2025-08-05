import random
import time
from dataclasses import dataclass, field
import logging
from patchright.async_api import Page

from yandex_flow.helpers.BaseHelper import BaseHelper
from yandex_flow.helpers.CaptchaHelper import CaptchaHelper
from difflib import SequenceMatcher

from yandex_flow.helpers.RandomActionsMixin import RandomActionsMixin, RandomActionsCfg

log = logging.getLogger(__name__)

@dataclass(frozen=True)
class YandexServicesCfg:
    name: str = ""
    city: str = ""
    time_in_card: int = 45
    click_phone: bool = False
    keyword: str = ""

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
    phone_btn: str = 'button:has-text("Телефон")'
    click_yes_in_phone: float = 0.33
    min_wait_in_phone: int = 7
    max_wait_in_phone: int = 15
    phone_yes_btn: str = 'button:has-text("Да")'
    close_phone_btn: str = 'div.YdoModal-BackButton'

    popups: list[str] = field(default_factory=lambda: [
        'button.Distribution-ButtonClose',
        'button.Distribution-ButtonClose[title="Нет, спасибо"]'
    ])

class YandexService(BaseHelper, RandomActionsMixin):
    def __init__(self, page: Page, config: YandexServicesCfg):
        super().__init__(page)
        self.config = config
        self.actions_cfg = RandomActionsCfg(
            photo_a=config.photo_a,
            next_photo_btn=config.next_photo_btn,
            close_photo_btn=config.close_photo_btn,
            min_wait_in_photo=config.min_wait_in_photo,
            max_wait_in_photo=config.max_wait_in_photo,
            min_photo_view=config.min_photo_view,
            max_photo_view=config.max_photo_view,
            service_name_a=config.service_name_a,
            expand_services_btn=config.expand_services_btn,
            close_service_windows_btn=config.close_service_windows_btn,
            min_view_services=config.min_view_services,
            max_view_services=config.max_view_services,
            min_wait_before_close=config.min_wait_before_close,
            max_wait_before_close=config.max_wait_before_close,
            examples_div=config.examples_div,
            close_example_btn=config.close_example_btn,
            min_wait_in_example=config.min_wait_in_example,
            max_wait_in_example=config.max_wait_in_example,
        )
        self.solve_captcha = CaptchaHelper(page).solve

    def update_page(self, new_page):
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

    async def search(self) -> tuple[bool, str]:
        try:
            await self.open_page()
            await self.close_popups()
            await self.fill(self.config.search_input, self.config.keyword, press_enter=True)
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
            log.exception(f"Ошибка в методе search:")
            return False, f"Ошибка при поиске: {e}"

    async def verify_city(self) -> tuple[bool, str]:
        try:
            locator = self.page.locator(self.config.city_div)
            await locator.first.wait_for(timeout=12_000)
            total = await locator.count()
            sample = min(5, total)
            matches = 0
            log.debug(f"Город '{self.config.city}' | найдено {total} блоков, анализирую {sample}")
            for i in range(sample):
                txt = (await locator.nth(i).inner_text()).strip()
                sim = SequenceMatcher(None, txt, self.config.city).ratio()
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
                text=self.config.city,
                append=True,
                press_enter=True,
            )
            await self.page.wait_for_timeout(random.randint(self.config.min_wait_after_verify_city, self.config.max_wait_after_verify_city) * 1000)
            return True, "Город уточнён запросом"
        except Exception as e:
            log.exception(f"Ошибка в verify_city:")
            return False, f"Ошибка в проверке города: {e}"

    async def find_executor(self, *, max_miss: int = 10, sim_threshold: float = 0.85) -> tuple[bool, str]:
        try:
            loc = self.page.locator(self.config.services_name_executor_a)
            misses = 0
            log.debug(f"start search: '{self.config.name}'")

            while misses < max_miss:
                total = await loc.count()
                if misses < total:
                    el = loc.nth(misses)
                    text = (await el.text_content() or "").partition("\n")[0].strip() # type: ignore
                    sim = SequenceMatcher(None, text, self.config.name).ratio()
                    log.debug(f"#{misses + 1}: {text!r} ~ {self.config.name!r} → {sim:.2f}")

                    if sim >= sim_threshold:
                        waiter = self.page.context.wait_for_event("page")
                        await self.click(el)
                        new_page = await waiter
                        await new_page.wait_for_load_state("domcontentloaded", timeout=self.config.timeout)
                        self.update_page(new_page)
                        log.info(f"'{self.config.name}' найден и открыт")
                        return True, "Исполнитель найден"

                    misses += 1
                else:
                    log.debug(f"просмотрено {misses} карточек, скроллю ниже…")
                    await self.page.mouse.wheel(0, 1200)
                    await self.page.wait_for_timeout(500)

            log.error(f"'{self.config.name}' не найден (проверено {misses} карточек)")
            return False, "Исполнитель не найден"
        except Exception as e:
            log.exception("Ошибка в find_executor:")
            return False, f"Ошибка в поиске исполнителя: {e}"

    async def perform_random_action(self) -> tuple[bool, str]:
        try:
            started = time.monotonic()
            actions = (
                (self.click_random_photos, "фото"),
                (self.click_random_services, "услуг"),
                (self.click_random_examples, "примеров"),
            )
            for coro, title in actions:
                if random.random() < 0.5:
                    log.debug(f"Запускаю действие: {title}")
                    await coro()
                else:
                    log.debug(f"Пропускаю действие: {title}")

            if self.config.click_phone and await self.is_present(self.config.phone_btn):
                await self.click(self.config.phone_btn)
                log.debug("Кликнул кнопку «Телефон»")
                await self.page.wait_for_timeout(
                    random.randint(self.config.min_wait_in_phone, self.config.max_wait_in_phone) * 1000
                )
                if random.random() < self.config.click_yes_in_phone:
                    if await self.is_present(self.config.phone_yes_btn):
                        await self.page.click(self.config.phone_yes_btn)
                        log.debug("Кликнул кнопку «Да» после показа телефона")
                await self.click(self.config.close_phone_btn)
            elapsed = time.monotonic() - started
            if elapsed < self.config.time_in_card:
                wait_left = self.config.time_in_card - elapsed
                log.debug(f"Действия заняли {elapsed:.1f} с — ждём ещё {wait_left:.1f} с")
                await self.page.wait_for_timeout(wait_left * 1000)
            else:
                log.debug(f"Действия заняли {elapsed:.1f} с — лимит {self.config.time_in_card} с перекрыт")
            return True, "Действия завершены успешно"
        except Exception as e:
            log.exception("Ошибка в perform_random_action:")
            return False, f"Ошибка при выполнении действй в perform_random_action: {e}"
