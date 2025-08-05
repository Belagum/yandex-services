import random, asyncio, logging

log = logging.getLogger(__name__)

class FormHelper:
    def __init__(self, page):
        self.page = page

    async def fill(
        self,
        selector: str,
        text: str,
        *,
        delay_range: tuple[float, float] = (0.05, 0.15),
        clear_first: bool = True,
        press_enter: bool = False,
        append: bool = False,
    ) -> None:
        try:
            locator = self.page.locator(selector)
            await locator.wait_for(state="visible", timeout=3000)
            await locator.click()
            log.debug(f"Field located and clicked → selector='{selector}'")

            final_text = text
            if append:
                existing = await locator.input_value()
                final_text = f"{existing.strip()} {text}".strip()
                clear_first = True

            if clear_first:
                await locator.fill("")
                log.debug(f"Field cleared → selector='{selector}'")

            for char in final_text:
                await locator.type(char, delay=random.uniform(*delay_range))
                await asyncio.sleep(random.uniform(0.01, 0.04))

            log.debug(f"Text input simulated → '{final_text}' to selector='{selector}'")

            if press_enter:
                await locator.press("Enter")
                log.debug(f"Enter key pressed → selector='{selector}'")

            log.info(f"Field filled → selector='{selector}', text='{final_text}'")
        except Exception as e:
            log.error(f"Fill failed → selector='{selector}', error={e}")