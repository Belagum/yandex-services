import random, asyncio, logging

log = logging.getLogger(__name__)

class MouseHelper:
    def __init__(self, page, *, jitter=(-4,4), steps=(20,35),
                 pause=(.1,.3), delay=(30,90)):
        self.page = page
        self.jitter, self.steps, self.pause, self.delay = jitter, steps, pause, delay
        self._x = self._y = 0.0

    async def click(
            self,
            target,
            *,
            index: int = 0,
            last: bool = False
    ) -> None:
        try:
            if isinstance(target, str):
                loc = self.page.locator(target)
                elements = await loc.all()
                if not elements:
                    log.error(f"Selector not found → '{target}'")
                    raise ValueError(f"No elements for selector '{target}'")
                element = elements[-1] if last else elements[index]
            else:
                element = target

            await element.scroll_into_view_if_needed()
            box = await element.bounding_box()
            if box is None:
                raise ValueError("Element hidden/off-screen")

            tx = box["x"] + box["width"] / 2 + random.uniform(*self.jitter)
            ty = box["y"] + box["height"] / 2 + random.uniform(*self.jitter)

            sx, sy = self._x, self._y
            steps = random.randint(*self.steps)
            for i in range(steps + 1):
                t = i / steps
                ease = 3 * t ** 2 - 2 * t ** 3
                await self.page.mouse.move(
                    sx + (tx - sx) * ease + random.uniform(-1, 1),
                    sy + (ty - sy) * ease + random.uniform(-1, 1)
                )
                await asyncio.sleep(random.uniform(0.004, 0.018))
            self._x, self._y = tx, ty

            await asyncio.sleep(random.uniform(*self.pause))
            delay = random.randint(*self.delay)
            await self.page.mouse.click(tx, ty, delay=delay)
            log.debug(f"Mouse clicked → locator={element}, delay={delay}ms")
        except Exception as e:
            log.error(f"Click failed → {e}")