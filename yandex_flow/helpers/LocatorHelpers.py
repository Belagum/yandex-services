import logging
from typing import Literal

from patchright.async_api import TimeoutError

log = logging.getLogger(__name__)

class LocatorHelper:
    def __init__(self, page):
        self.page = page

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