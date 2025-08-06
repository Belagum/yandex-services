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

    video_div: str
    min_wait_in_video: int
    max_wait_in_video: int
    min_view_video: int
    max_view_video: int
    close_video_btn: str


class RandomActionsMixin:
    page: Page
    click: Callable[..., Awaitable[Any]]
    actions_cfg: RandomActionsCfg
    is_present: Callable[..., Awaitable[bool]]
    get_random_index: Callable[..., Awaitable[bool]]

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
        if not await self.is_present(self.actions_cfg.photo_a):
            log.debug("Нет фотографий для просмотра, пропуск")
            return
        await self.click(self.actions_cfg.photo_a)

        count = random.randint(self.actions_cfg.min_photo_view, self.actions_cfg.max_photo_view)
        log.debug(f"Буду пролистывать {count} фотографий")

        for i in range(count):
            delay = random.uniform(self.actions_cfg.min_wait_in_photo, self.actions_cfg.max_wait_in_photo) * 1000
            await self.page.wait_for_timeout(delay)

            if not await self.is_present(self.actions_cfg.next_photo_btn):
                log.warning(f"Кнопка следующей фото не найдена на шаге {i + 1}")
                break

            is_disabled = await self.page.locator(self.actions_cfg.next_photo_btn).get_attribute("class")
            if "CircleButton_disabled" in is_disabled:
                log.debug(f"Кнопка отключена на шаге {i + 1}")
                break

            await self.click(self.actions_cfg.next_photo_btn)
            log.debug(f"Перелистнута фотография #{i + 1}")

        if await self.is_present(self.actions_cfg.close_photo_btn):
            await self.click(self.actions_cfg.close_photo_btn)
            log.debug("Закрыт просмотр фотографий")

    async def click_random_videos(self) -> None:
        locator = self.page.locator(self.actions_cfg.video_div)
        total = await locator.count()
        if total == 0:
            log.debug("Нет видео для клика")
            return

        max_count = min(total, self.actions_cfg.max_view_video)
        min_count = min(self.actions_cfg.min_view_video, max_count)
        count = random.randint(min_count, max_count)
        log.debug(f"Буду пролистывать {count} видео из {total}")
        clicked = set()
        for _ in range(count):
            choices = [i for i in range(total) if i not in clicked]
            if not choices:
                break
            idx = random.choice(choices)
            clicked.add(idx)
            log.debug(f"Кликаю на видео индексом {idx}")
            await self.click(self.actions_cfg.video_div, index=idx)
            delay = random.randint(self.actions_cfg.min_wait_in_video, self.actions_cfg.max_wait_in_video) * 1000
            await self.page.wait_for_timeout(delay)
            await self.click(self.actions_cfg.close_video_btn)

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
