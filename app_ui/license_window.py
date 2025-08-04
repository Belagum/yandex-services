import tkinter as tk
from app_utils.storage import JsonStore
from app_utils.subscription import SubscriptionChecker
from app_utils.utils import SETTINGS_FILE

class LicenseWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, on_ok):
        super().__init__(parent)
        self.on_ok = on_ok

        self.store = JsonStore(SETTINGS_FILE)
        self.checker = SubscriptionChecker(self.store)

        self.title("Лицензия"); self.geometry("300x140")
        frame = tk.Frame(self); frame.pack(side="top", fill="both", expand=True)

        self.msg = tk.Label(frame, fg="red"); self.msg.pack(pady=(10, 0))
        tk.Label(frame, text="Ключ:").pack(anchor="w", padx=10)

        self.var_key = tk.StringVar(value=self.store.load().get("license_key", ""))

        tk.Entry(frame, textvariable=self.var_key).pack(fill="x", padx=10)
        tk.Button(self, text="Сохранить", command=self._save).pack(side="bottom", padx=10, pady=10)
        self._validate()


    def _validate(self):
        status, _ = self.checker.status()
        self.msg.config(text="" if status == "Активна" else "Ключ неактивен")
        if status == "Активна":
            self.master.destroy()
            self.destroy()
            self.on_ok()

    def _save(self):
        data = self.store.load()
        data["license_key"] = self.var_key.get().strip()
        self.store.save(data)
        self._validate()
