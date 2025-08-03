import tkinter as tk
from tkinter import messagebox
from app_utils.utils import CARDS_FILE
from app_utils.storage import JsonStore

class CardSettingsWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel, store: JsonStore, cards: dict, card_name: str, on_create=None):
        super().__init__(parent)
        self.store, self.cards, self.card_name, self.on_create = store, cards, card_name, on_create
        self.settings = self.cards.setdefault(card_name, {}).setdefault("settings", {})

        self.title(f"{'Создать' if on_create else 'Настройки'}: {card_name}")
        self.geometry("250x120")

        self.var_test = tk.BooleanVar(value=self.settings.get("test", False))
        tk.Checkbutton(self, text="test", variable=self.var_test).pack(padx=10, pady=10)

        tk.Button(self, text="Сохранить", command=self._save).pack(side="bottom", padx=10, pady=10)

    def _save(self):
        self.settings["test"] = self.var_test.get()
        self.store.save(self.cards)
        if self.on_create:
            self.on_create(self.card_name)
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
        frame = tk.Frame(self)
        frame.pack(side="bottom", fill="x", padx=10, pady=10)

        tk.Button(frame, text="Удалить выбранную", command=self._delete_selected).pack(side="left", expand=True)
        tk.Button(frame, text="Настройки карточки", command=self._edit_selected).pack(side="left", expand=True)

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
        if not messagebox.askokcancel("Удалить", "Удалить выбранную карточку?"):
            return
        sel = self.lb.curselection()
        if not sel:
            return
        name = self.lb.get(sel[0])
        self.cards.pop(name, None)
        self.store.save(self.cards)
        self.lb.delete(sel[0])
