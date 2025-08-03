import tkinter as tk

from app_ui.captcha_window import CaptchaSettingsWindow
from app_ui.cards_window import CardsManagerWindow
from app_utils.subscription import SubscriptionChecker
from app_utils.utils import version
from app_ui.license_window import LicenseWindow

class MainWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent or tk.Tk())
        self.title("Яндекс услуги")
        self.geometry("300x200")

        sub_status, _ = SubscriptionChecker().status()
        self._build_status(sub_status)
        self._build_buttons()
        self._build_version()

    def _build_status(self, status_text):
        tk.Label(self, text=f"Подписка: {status_text}").pack(pady=(5, 0), fill='x')

    def _build_buttons(self):
        frame = tk.Frame(self)
        frame.pack(expand=True, pady=5)
        tk.Button(frame, text="Запустить", command=lambda: print("Run")).pack(pady=3, fill="x")
        tk.Button(frame, text="Управление карточками", command=self._open_cards).pack(pady=3, fill="x")
        tk.Button(frame, text="Решение капчи", command=self._open_captcha).pack(pady=3, fill="x")

    def _open_captcha(self):
        CaptchaSettingsWindow(self)

    def _build_version(self):
        tk.Label(self, text=version).pack(side='bottom', fill='x', pady=5)

    def _open_cards(self):
        CardsManagerWindow(self)


def _start_main(root): MainWindow(root)

def run_app(test=False):
    if test:
        root = tk.Tk()
        root.withdraw()
        MainWindow(root)
        root.mainloop()
        return

    root = tk.Tk()
    root.withdraw()

    if SubscriptionChecker().status()[0] == "Активна":
        root.deiconify()
        MainWindow(root)
    else:
        LicenseWindow(root, lambda: MainWindow(root))

    root.mainloop()
