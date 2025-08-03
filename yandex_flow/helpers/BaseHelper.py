from patchright.async_api import Page

class BaseHelper:
    def __init__(self, page: Page):
        self.page = page

        from .MouseHelper   import MouseHelper
        from .FormHelper    import FormHelper
        from .LocatorHelpers import LocatorHelper

        self.mouse = MouseHelper(page)
        self.form = FormHelper(page)
        self.locators = LocatorHelper(page)

        # делегаты
        self.click = self.mouse.click
        self.fill = self.form.fill
        self.is_present = self.locators.is_present
