import tkinter as tk
from tkinter import messagebox
from app_utils.utils import CARDS_FILE
from app_utils.storage import JsonStore

class CardSettingsWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel, store: JsonStore,
                 cards: dict, card_name: str, on_create=None):
        super().__init__(parent)
        self.store, self.cards, self.card_name, self.on_create = store, cards, card_name, on_create
        self.settings = self.cards.setdefault(card_name, {}).setdefault("settings", {})

        self.title(f'{"Создать" if on_create else "Настройки"}: {card_name}')
        self.geometry("260x160")
        self.columnconfigure(1, weight=1)

        fields = [
            ("Исполнитель", "name"),
            ("Город", "city"),
            ("Время в карточке, c", "time_on_card")
        ]
        self.vars: dict[str, tk.StringVar] = {}
        for i, (lbl, key) in enumerate(fields):
            tk.Label(self, text=lbl).grid(row=i, column=0, sticky="w", padx=10, pady=4)
            v = tk.StringVar(value=str(self.settings.get(key, "")))
            tk.Entry(self, textvariable=v).grid(row=i, column=1, sticky="ew", padx=10, pady=4)
            self.vars[key] = v

        self.var_click = tk.BooleanVar(value=self.settings.get("click_phone", False))
        tk.Checkbutton(self, text="Нажимать телефон", variable=self.var_click).grid(
            row=len(fields), column=0, columnspan=2, padx=10, pady=4, sticky="w"
        )

        tk.Button(self, text="Сохранить", command=self._save).grid(
            row=len(fields) + 1, column=0, columnspan=2, sticky="ew", padx=10, pady=10
        )

    def _save(self):
        vals = {k: v.get().strip() for k, v in self.vars.items()}
        if "" in vals.values():
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены"); return
        try:
            t = int(vals["time_on_card"])
        except ValueError:
            messagebox.showerror("Ошибка", "Время должно быть числом"); return
        if t < 45:
            messagebox.showerror("Ошибка", "Время не должно быть менее 45 секунд"); return
        self.settings.update(vals)
        self.settings["click_phone"] = self.var_click.get()
        self.store.save(self.cards)
        if self.on_create: self.on_create(self.card_name)
        self.destroy()


class CardsManagerWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Управление карточками")
        self.geometry("300x330")

        self.store = JsonStore(CARDS_FILE)
        self.cards = self.store.load()

        self._build_add_section()
        self._build_list_section()
        self._build_buttons_section()

    def _build_add_section(self):
        frame = tk.Frame(self)
        frame.pack(fill="x", padx=10, pady=(10, 0))

        tk.Label(frame, text="Новая:").pack(side="left")
        self.entry = tk.Entry(frame)
        self.entry.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(frame, text="Добавить", command=self._add_card).pack(side="right")

    def _build_list_section(self):
        tk.Label(self, text="Список карточек:").pack(anchor="w", padx=10, pady=(10, 0))
        self.lb = tk.Listbox(self, height=10, width=40, selectmode=tk.SINGLE)
        for name in self.cards:
            self.lb.insert(tk.END, name)
        self.lb.pack(padx=10, pady=5, fill="both", expand=True)

    def _build_buttons_section(self):
        frame = tk.Frame(self);
        frame.pack(side="bottom", fill="x", padx=10, pady=10)
        tk.Button(frame, text="Удалить выбранную", command=self._delete_selected) \
            .grid(row=0, column=0, sticky="ew", padx=5)
        tk.Button(frame, text="Настройки карточки", command=self._edit_selected) \
            .grid(row=0, column=1, sticky="ew", padx=5)
        tk.Button(frame, text="Изменить ключевые слова", command=self._edit_keywords) \
            .grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(6, 0))
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def _edit_keywords(self):
        sel = self.lb.curselection()
        if not sel:
            messagebox.showerror("Ошибка", "Карточка не выбрана")
            return
        name = self.lb.get(sel[0])
        s = self.cards[name].setdefault("settings", {})
        win = tk.Toplevel(self)
        win.title(f"Ключевые слова: {name}")
        win.geometry("320x340")
        win.rowconfigure(0, weight=1)
        win.columnconfigure(0, weight=1)
        txt = tk.Text(win)
        txt.insert("1.0", "\n".join(s.get("keywords", [])))
        txt.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tk.Button(win, text="Сохранить",
                  command=lambda: self._save_keywords(win, txt, s)).grid(row=1, column=0,
                                                                         sticky="ew", padx=10, pady=(0, 10))

    def _save_keywords(self, win: tk.Toplevel, txt: tk.Text, settings: dict):
        kws = [w.strip() for w in txt.get("1.0", "end").splitlines() if w.strip()]
        if not kws:
            messagebox.showerror("Ошибка", "Список ключевых слов не может быть пустым")
            return
        settings["keywords"] = kws
        self.store.save(self.cards)
        win.destroy()

    def _add_card(self):
        name = self.entry.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Имя не должно быть пустым")
            return
        if any(name.lower() == n.lower() for n in self.cards):
            messagebox.showerror("Ошибка", "Такая карточка уже существует")
            return

        def _on_create(card_name):
            self.lb.insert(tk.END, card_name)

        CardSettingsWindow(self, self.store, self.cards, name, on_create=_on_create)
        self.entry.delete(0, tk.END)

    def _edit_selected(self):
        sel = self.lb.curselection()
        if sel:
            CardSettingsWindow(self, self.store, self.cards, self.lb.get(sel[0]))

    def _delete_selected(self):
        sel = self.lb.curselection()
        if not sel:
            messagebox.showerror("Ошибка", "Карточка не выбрана")
            return
        if not messagebox.askokcancel("Удалить", "Удалить выбранную карточку?"):
            return
        name = self.lb.get(sel[0])
        self.cards.pop(name, None)
        self.store.save(self.cards)
        self.lb.delete(sel[0])
