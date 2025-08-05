import logging, tkinter as tk
import threading
from tkinter import messagebox

from app_ui.license_window import LicenseWindow
from app_utils.storage import JsonStore
from app_utils.subscription import SubscriptionChecker
from app_utils.utils import CARDS_FILE
from yandex_flow.runner import Runner

log = logging.getLogger(__name__)

class RunWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel, test=False):
        super().__init__(parent)
        self.test = test
        self.store = JsonStore(CARDS_FILE)
        self.cards = self.store.load()
        self.title("Запуск"); self.geometry("300x400")
        self._build_cards(); self._build_opts(); self._build_btns()

    def _build_cards(self):
        box = tk.LabelFrame(self, text="Карточки"); box.pack(fill="both", expand=True, padx=10, pady=(10, 5))
        self.card_vars: dict[str, tk.BooleanVar] = {}
        for name in self.cards:
            v = tk.BooleanVar(); tk.Checkbutton(box, text=name, variable=v).pack(anchor="w")
            self.card_vars[name] = v

    def _build_opts(self):
        f = tk.Frame(self); f.pack(fill="x", padx=10)
        self.var_headless = tk.BooleanVar()
        self.var_position = tk.BooleanVar()
        self.var_infinity = tk.BooleanVar()
        tk.Checkbutton(f, text="Бесконечно проходить по карточкам", variable=self.var_infinity).pack(anchor="w", pady=(0, 5))
        tk.Checkbutton(f, text="Режим сбора позиций", variable=self.var_position).pack(anchor="w", pady=(0, 5))
        tk.Checkbutton(f, text="Headless", variable=self.var_headless).pack(anchor="w", pady=(0, 5))
        tk.Label(f, text="Потоки").pack(anchor="w")
        self.var_threads = tk.IntVar(value=1)
        tk.Scale(f, from_=1, to=15, orient="horizontal", variable=self.var_threads).pack(fill="x")

    def _build_btns(self):
        b = tk.Frame(self)
        b.pack(fill="x", padx=10, pady=10)
        tk.Button(b, text="Старт", command=self._run).pack(fill="x")

    def _run(self):
        if SubscriptionChecker(test=self.test).status()[0] != "Активна":
            LicenseWindow(self, lambda: None)
            return
        sel = [n for n, v in self.card_vars.items() if v.get()]
        if not sel:
            messagebox.showerror("Ошибка", "Не выбрана ни одна карточка")
            return

        params = dict(
            cards=sel,
            headless=self.var_headless.get(),
            threads=self.var_threads.get(),
            position=self.var_position.get(),
            infinity=self.var_infinity.get()
        )
        log.info(f"Запуск: {params}")

        self.destroy()

        def _bg():
            Runner(
                sel,
                self.var_headless.get(),
                self.var_threads.get(),
                self.var_position.get(),
                self.var_infinity.get()
            ).run()

        threading.Thread(target=_bg, daemon=True).start()

