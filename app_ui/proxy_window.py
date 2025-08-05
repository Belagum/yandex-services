import logging, tkinter as tk
from tkinter import messagebox
from app_utils.storage import JsonStore
from app_utils.utils import PROXIES_FILE, CARDS_FILE

log = logging.getLogger(__name__)

class ProxyManagerWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel):
        super().__init__(parent)
        self.store = JsonStore(PROXIES_FILE)
        self.proxies: list[dict] = self.store.load() or []
        self.title("Прокси"); self.geometry("350x430")
        self._build_input(); self._build_list()

    def _build_input(self):
        f = tk.Frame(self); f.pack(fill="x", padx=10, pady=(10, 5))
        tk.Label(f, text="ip:port:login:pass").pack(anchor="w")
        self.entry = tk.Entry(f); self.entry.pack(fill="x", pady=(0, 5))
        tk.Button(f, text="Добавить", command=self._add).pack(fill="x")

    def _build_list(self):
        box = tk.LabelFrame(self, text="Все прокси"); box.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.listbox = tk.Listbox(box, selectmode=tk.EXTENDED, exportselection=False); self.listbox.pack(fill="both", expand=True)
        for p in self.proxies: self.listbox.insert("end", f'{p["ip"]}:{p["port"]}:{p["login"]}:{p["password"]}')
        self.listbox.bind('<Control-a>', self._select_all_event)
        btnf = tk.Frame(self); btnf.pack(fill="x", padx=10, pady=(5,10))
        for c in range(2): btnf.columnconfigure(c, weight=1, uniform="btn_grp")
        actions = [
            ("Выделить все", self._toggle_select_all),
            ("Удалить выбранные", self._delete_selected),
            ("Привязать к карточкам", self._bind_to_cards),
            ("Отвязать от карточек", self._unbind_from_cards)
        ]
        for i, (text, cmd) in enumerate(actions):
            tk.Button(btnf, text=text, command=cmd).grid(row=i//2, column=i%2, sticky="ew", padx=5, pady=5)

    def _bind_to_cards(self):
        sel = list(self.listbox.curselection()); count = len(sel)
        if not sel or not messagebox.askyesno("Привязка прокси", f"Точно ли вы хотите привязать {count} прокси к всем карточкам?"): return
        store = JsonStore(CARDS_FILE); cards = store.load() or {}
        for card in cards.values(): card.setdefault("settings", {})["proxy_idx"] = sel.copy()
        store.save(cards); log.info(f"Привязаны прокси {sel} к всем карточкам")

    def _unbind_from_cards(self):
        sel = list(self.listbox.curselection()); count = len(sel)
        if not sel or not messagebox.askyesno("Отвязка прокси", f"Точно ли вы хотите удалить {count} прокси из всех карточек?"): return
        store = JsonStore(CARDS_FILE); cards = store.load() or {}
        for card in cards.values():
            idx = card.get("settings", {}).get("proxy_idx", [])
            new = [i for i in idx if i not in sel]
            if new: card["settings"]["proxy_idx"] = new
            else: card["settings"].pop("proxy_idx", None)
        store.save(cards); log.info(f"Отвязаны прокси {sel} от карточек")

    def _select_all_event(self, event) -> str:
        self._toggle_select_all(); return "break"

    def _toggle_select_all(self):
        if len(self.listbox.curselection()) == self.listbox.size():
            self.listbox.selection_clear(0, "end")
        else:
            self.listbox.selection_set(0, "end")

    def _delete_selected(self):
        sel = list(self.listbox.curselection())
        if not sel: return
        count = len(sel)
        if not messagebox.askyesno("Подтвердите удаление", f"Точно ли вы хотите удалить {count} прокси?"): return
        for i in reversed(sel):
            self.listbox.delete(i); del self.proxies[i]
        self.store.save(self.proxies)
        log.info(f"Удалены прокси: {sel}")

    def _add(self):
        raw = self.entry.get().strip()
        parts = raw.split(":")
        if len(parts) != 4:
            messagebox.showerror("Ошибка", "Формат: ip:port:login:pass"); return

        ip, port, login, password = parts
        if any(p["ip"] == ip and p["port"] == port and p["login"] == login and p["password"] == password for p in self.proxies):
            messagebox.showinfo("Внимание", "Прокси уже существует"); return

        proxy = {
            "ip": ip,
            "port": port,
            "login": login,
            "password": password
        }
        self.proxies.append(proxy)
        self.store.save(self.proxies)
        self.listbox.insert("end", raw)
        self.entry.delete(0, "end")
        log.info(f"Добавлен прокси {raw}")
