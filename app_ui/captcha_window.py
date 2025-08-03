import tkinter as tk
from app_utils.storage import JsonStore
from app_utils.utils import SETTINGS_FILE

class CaptchaSettingsWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel):  # noqa: D401
        super().__init__(parent)
        self.store = JsonStore(SETTINGS_FILE)
        self.settings = self.store.load().setdefault("captcha", {})

        self.title("Настройки капчи")
        self.geometry("320x200")

        self.var_service = tk.StringVar(value=self.settings.get("captcha_service", "capsola"))
        self.var_capsola = tk.StringVar(value=self.settings.get("capsola_api_key", ""))
        self.var_2captcha = tk.StringVar(value=self.settings.get("2captcha_api_key", ""))

        srv = tk.LabelFrame(self, text="Сервис")
        srv.pack(fill="x", padx=10, pady=(10, 5))
        for name in ("capsola", "2captcha"):
            tk.Radiobutton(srv, text=name, variable=self.var_service, value=name).pack(anchor="w")

        keys = tk.Frame(self)
        keys.pack(fill="x", padx=10)
        tk.Label(keys, text="Capsola key").grid(row=0, column=0, sticky="w")
        tk.Entry(keys, textvariable=self.var_capsola).grid(row=0, column=1, sticky="ew")
        tk.Label(keys, text="2Captcha key").grid(row=1, column=0, sticky="w")
        tk.Entry(keys, textvariable=self.var_2captcha).grid(row=1, column=1, sticky="ew")
        keys.columnconfigure(1, weight=1)

        tk.Button(self, text="Сохранить", command=self._save).pack(side="bottom", padx=10, pady=10)

    def _save(self):
        all_settings = self.store.load()
        all_settings["captcha"] = {
            "captcha_service": self.var_service.get(),
            "capsola_api_key": self.var_capsola.get().strip(),
            "2captcha_api_key": self.var_2captcha.get().strip()
        }
        self.store.save(all_settings)
        self.destroy()