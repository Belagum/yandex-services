import logging
import random
from typing import Literal

from patchright.async_api import TimeoutError

log = logging.getLogger(__name__)

class LocatorHelper:
    def __init__(self, page):
        self.page = page

    async def count(self, sel: str, *, timeout: int = 1500) -> int:
        try:
            await self.page.wait_for_selector(sel, timeout=timeout)
        except TimeoutError:
            log.error(f"Timeout → '{sel}'")
            return 0
        n = await self.page.locator(sel).count()
        log.info(f"Count={n} → '{sel}'")
        await self.page.wait_for_timeout(random.uniform(0.1, 0.3) * 1000)
        return n

    async def get_random_index(self, sel: str, *, timeout: int = 1500) -> int | None:
        total = await self.count(sel, timeout=timeout)
        return None if total == 0 else random.randint(0, total - 1)

    async def is_present(
        self,
        selector: str,
        *,
        timeout: int = 3_000,
        visible: bool = False,
        wait: bool = True,
    ) -> bool:
        state: Literal["attached", "visible"] = "visible" if visible else "attached"
        try:
            if wait:
                await self.page.wait_for_selector(selector, timeout=timeout, state=state)
            else:
                if not await self.page.query_selector(selector):
                    raise TimeoutError("Element not found")  # элемент не найден
            log.debug("element found — %s (%s)", selector, state)
            return True
        except TimeoutError:
            log.debug("element NOT found — %s (%s)", selector, state)
            return False