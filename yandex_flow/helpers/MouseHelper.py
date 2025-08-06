import random, asyncio, logging

from patchright.async_api import Locator

log = logging.getLogger(__name__)

class MouseHelper:
    def __init__(self, page, *, jitter=(-4,4), steps=(20,35),
                 pause=(.1,.3), delay=(30,90)):
        self.page = page
        self.jitter, self.steps, self.pause, self.delay = jitter, steps, pause, delay
        self._x = self._y = 0.0

    async def click(self, target, *, index: int = 0, last: bool = False) -> None:
        try:
            if isinstance(target, str):
                loc: Locator = self.page.locator(target)
                for _ in range(30):
                    cnt = await loc.count()
                    if cnt > 0:
                        break
                    await asyncio.sleep(0.1)
                else:
                    log.error(f"Selector not found → '{target}'")
                    raise ValueError(f"No elements for selector '{target}'")
                element = loc.nth(cnt - 1) if last else loc.nth(index)
            else:
                element = target

            if isinstance(element, Locator):
                await element.scroll_into_view_if_needed()
                await element.wait_for(state="visible", timeout=3000)
                await element.hover()
            else:
                await element.evaluate("el => el.scrollIntoView()")

            await asyncio.sleep(random.uniform(*self.pause))
            delay = random.randint(*self.delay)
            try:
                await element.click(delay=delay)
                log.debug(f"Clicked → {target}, delay={delay}ms")
            except Exception as e:
                log.warning(f"Click failed, fallback to JS → {e}")
                await element.evaluate("el => el.click()")
                log.debug(f"Clicked via JS → {target}")
        except Exception as e:
            log.error(f"Click failed → {e}")
