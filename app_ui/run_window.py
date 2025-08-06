import logging, tkinter as tk
import threading
import time
from tkinter import messagebox

from app_ui.license_window import LicenseWindow
from app_utils import utils
from app_utils.storage import JsonStore
from app_utils.subscription import SubscriptionChecker
from app_utils.utils import CARDS_FILE
from yandex_flow.runner.runner import Runner

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
        self.var_auto = tk.BooleanVar()
        tk.Checkbutton(f, text="Бесконечно проходить по карточкам", variable=self.var_infinity).pack(anchor="w", pady=(0, 5))
        tk.Checkbutton(f, text="Режим сбора позиций", variable=self.var_position).pack(anchor="w", pady=(0, 5))
        tk.Checkbutton(f, text="Headless", variable=self.var_headless).pack(anchor="w", pady=(0, 5))
        row = tk.Frame(f); row.pack(anchor="w", pady=(0, 5))
        tk.Checkbutton(row, text="Автозапуск ежедневно в", variable=self.var_auto,
                       command=self._toggle_time).pack(side="left")
        self.entry_time = tk.Entry(row, width=5); self.entry_time.insert(0, "09:00")
        self.entry_time.configure(state="disabled"); self.entry_time.pack(side="left", padx=5)
        tk.Label(f, text="Потоки").pack(anchor="w")
        self.var_threads = tk.IntVar(value=1)
        tk.Scale(f, from_=1, to=15, orient="horizontal", variable=self.var_threads).pack(fill="x")

    def _toggle_time(self):  # enable / disable поле времени
        self.entry_time.configure(state="normal" if self.var_auto.get() else "disabled")

    def _build_btns(self):
        b = tk.Frame(self)
        b.pack(fill="x", padx=10, pady=10)
        tk.Button(b, text="Старт", command=self._run).pack(fill="x")

    def _run(self):
        if SubscriptionChecker(test=self.test).status()[0] != "Активна":
            LicenseWindow(self, lambda: None); return

        sel = [n for n, v in self.card_vars.items() if v.get()]
        if not sel:
            messagebox.showerror("Ошибка", "Не выбрана ни одна карточка"); return

        auto = self.var_auto.get()
        tstr = self.entry_time.get().strip() if auto else ""
        if auto:
            try:
                hh, mm = map(int, tstr.split(":"))
                if not (0 <= hh < 24 and 0 <= mm < 60): raise ValueError
            except Exception:
                messagebox.showerror("Ошибка", "Формат времени HH:MM"); return

        log.info(f"Запуск: {{'cards': sel, 'headless': {self.var_headless.get()}, "
                 f"'threads': {self.var_threads.get()}, 'position': {self.var_position.get()}, "
                 f"'infinity': {self.var_infinity.get()}, 'autorun': {auto}, 'time': '{tstr}'}}")
        self.destroy()

        def _once(next_ts: float | None):
            Runner(sel, self.var_headless.get(), self.var_threads.get(),
                   self.var_position.get(), self.var_infinity.get(), next_ts).run()

        if not auto:
            threading.Thread(target=lambda: _once(None), daemon=True).start(); return

        def _scheduler():
            class _Dummy:
                def __init__(self, ts): self.ts = ts
                def stats_str(self):  # строка для MonitoringWindow
                    return ("Авторежим             : включён\n"
                            f"Следующий автозапуск  : "
                            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.ts))}")
            while True:
                now = time.time()
                lt = time.localtime(now)
                target = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, hh, mm, 0, 0, 0, -1))
                if target <= now: target += 86400
                utils.current_runner = _Dummy(target)        # показ в мониторинге
                time.sleep(max(0, target - time.time()))
                utils.current_runner = None                  # освободить перед запуском
                _once(target + 86400)

        threading.Thread(target=_scheduler, daemon=True).start()
