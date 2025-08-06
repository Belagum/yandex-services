import logging
import tkinter as tk
from app_ui.captcha_window import CaptchaSettingsWindow
from app_ui.cards_window import CardsManagerWindow
from app_ui.monitoring_window import MonitoringWindow
from app_ui.proxy_window import ProxyManagerWindow
from app_utils.subscription import SubscriptionChecker
from app_utils.utils import version
from app_ui.license_window import LicenseWindow
from app_ui.run_window import RunWindow

log = logging.getLogger(__name__)

class MainWindow(tk.Toplevel):
    def __init__(self, parent, test=False):
        super().__init__(parent)
        self.test = test
        status, end, _ = SubscriptionChecker(test=test).status()
        log.info(f"MainWindow открыто, статус подписки: {status}, до {end}")
        self.title("Яндекс услуги")
        self.geometry("300x200")
        self._build_status(status, end)
        self._build_buttons()
        self._build_version()

    def _build_status(self, status_text: str, end_text: str):
        tk.Label(self, text=f"Подписка: {status_text} до {end_text}")\
            .pack(pady=(5, 0), fill='x')

    def _build_buttons(self):
        frame = tk.Frame(self); frame.pack(expand=True, pady=5)
        tk.Button(frame, text="Запустить", command=self._open_run).pack(pady=3, fill="x")
        tk.Button(frame, text="Управление карточками", command=self._open_cards).pack(pady=3, fill="x")
        tk.Button(frame, text="Мониторинг", command=self._open_monitoring_window).pack(pady=3, fill="x")
        tk.Button(frame, text="Прокси", command=self._open_proxy_window).pack(pady=3, fill="x")  # new
        tk.Button(frame, text="Решение капчи", command=self._open_captcha).pack(pady=3, fill="x")

    def _open_run(self):
        if SubscriptionChecker(test=self.test).status()[0] == "Активна":
            RunWindow(self, test=self.test)
        else:
            LicenseWindow(self, lambda: RunWindow(self, test=self.test))

    def _open_cards(self):
        if SubscriptionChecker(test=self.test).status()[0] == "Активна":
            CardsManagerWindow(self, test=self.test)
        else:
            LicenseWindow(self, lambda: CardsManagerWindow(self))

    def _open_monitoring_window(self):
        log.info("Открыто окно мониторинга")
        MonitoringWindow(self)

    def _open_proxy_window(self):
        log.info("Открыто окно управления прокси")
        ProxyManagerWindow(self)

    def _open_captcha(self):
        log.info("Открыто окно решения капчи")
        CaptchaSettingsWindow(self)


    def _build_version(self):
        tk.Label(self, text=version).pack(side='bottom', fill='x', pady=5)

def run_app(test=False):
    log.info(f"Запуск приложения, test={test}")
    root = tk.Tk(); root.withdraw()
    checker = SubscriptionChecker(test=test)
    status = checker.status()[0]
    log.debug(f"Статус подписки: {status}")
    if status == "Активна":
        MainWindow(root, test=test)
    else:
        LicenseWindow(root, lambda: MainWindow(root, test=test))
    root.mainloop()
