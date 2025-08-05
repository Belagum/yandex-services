import random, logging
from typing import Callable, Awaitable, Any
from patchright.async_api import Page
from dataclasses import dataclass

log = logging.getLogger(__name__)

@dataclass(frozen=True, slots=True)
class RandomActionsCfg:
    photo_a: str
    next_photo_btn: str
    close_photo_btn: str
    min_wait_in_photo: float
    max_wait_in_photo: float
    min_photo_view: int
    max_photo_view: int

    service_name_a: str
    expand_services_btn: str
    close_service_windows_btn: str
    min_view_services: int
    max_view_services: int
    min_wait_before_close: float
    max_wait_before_close: float

    examples_div: str
    close_example_btn: str
    min_wait_in_example: float
    max_wait_in_example: float

class RandomActionsMixin:
    page: Page
    click: Callable[..., Awaitable[Any]]
    actions_cfg: RandomActionsCfg
    is_present: Callable[..., Awaitable[bool]]

    async def _click_random_items(
        self,
        item_selector: str,
        close_selector: str,
        *,
        min_view: int,
        max_view: int,
        min_wait: float,
        max_wait: float,
        description: str,
    ) -> None:
        loc = self.page.locator(item_selector)
        total = await loc.count()
        n = min(total, random.randint(min_view, max_view))
        if n == 0:
            log.error(f"Нет {description} для клика")
            return

        indices = random.sample(range(total), n)
        log.debug(f"Кликаю по {n}/{total} {description}: {indices}")
        for idx in indices:
            await self.click(item_selector, index=idx)
            await self.page.wait_for_timeout(random.uniform(min_wait, max_wait))
            if await self.is_present(close_selector):
                await self.click(close_selector)
                log.debug(f"Закрыл {description} #{idx}")

    async def click_random_photos(self) -> None:
        if await self.is_present(self.actions_cfg.photo_a):
            await self.click(self.actions_cfg.photo_a)
            log.debug("Открыта первая фотография")

        count = random.randint(self.actions_cfg.min_photo_view, self.actions_cfg.max_photo_view)
        log.debug(f"Буду пролистывать {count} фотографий")

        for i in range(count):
            delay = random.uniform(self.actions_cfg.min_wait_in_photo, self.actions_cfg.max_wait_in_photo) * 1000
            await self.page.wait_for_timeout(delay)
            if not await self.is_present(self.actions_cfg.next_photo_btn):
                log.warning(f"Кнопка следующей фото не найдена на шаге {i + 1}")
                break
            await self.click(self.actions_cfg.next_photo_btn)
            log.debug(f"Перелистнута фотография #{i + 1}")

        if await self.is_present(self.actions_cfg.close_photo_btn):
            await self.click(self.actions_cfg.close_photo_btn)
            log.debug("Закрыт просмотр фотографий")

    async def click_random_examples(self) -> None:
        await self._click_random_items(
            item_selector=self.actions_cfg.examples_div,
            close_selector=self.actions_cfg.close_example_btn,
            min_view=self.actions_cfg.min_view_services,
            max_view=self.actions_cfg.max_view_services,
            min_wait=self.actions_cfg.min_wait_in_example,
            max_wait=self.actions_cfg.max_wait_in_example,
            description="примеров работ",
        )

    async def click_random_services(self) -> None:
        if await self.is_present(self.actions_cfg.expand_services_btn):
            await self.click(self.actions_cfg.expand_services_btn)
            log.debug("Раскрыт список услуг")
        await self._click_random_items(
            item_selector=self.actions_cfg.service_name_a,
            close_selector=self.actions_cfg.close_service_windows_btn,
            min_view=self.actions_cfg.min_view_services,
            max_view=self.actions_cfg.max_view_services,
            min_wait=self.actions_cfg.min_wait_before_close,
            max_wait=self.actions_cfg.max_wait_before_close,
            description="услуг",
        )
