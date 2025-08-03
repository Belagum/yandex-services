import tkinter as tk
from tkinter import messagebox

from app_utils.json_io import load_json, save_json
from app_utils.utils import CARDS_FILE

def _build_list(parent: tk.Widget, items: dict) -> tk.Listbox:
    lb = tk.Listbox(parent, height=10, width=40, selectmode=tk.SINGLE)
    for name in items:
        lb.insert(tk.END, name)
    lb.pack(padx=10, pady=5, fill="both", expand=True)
    return lb

def _delete_selected(lb: tk.Listbox, cards: dict) -> None:
    if not messagebox.askokcancel("Удалить", "Удалить выбранную карточку?"):
        return
    sel = lb.curselection()
    if not sel:
        return
    name = lb.get(sel[0])
    cards.pop(name, None)
    save_json(cards, CARDS_FILE)
    lb.delete(sel[0])

def _card_settings_window(parent: tk.Toplevel,
                          cards: dict,
                          card_name: str,
                          lb: tk.Listbox | None = None,
                          is_new: bool = False) -> None:
    stg = cards.setdefault(card_name, {}).setdefault("settings", {})

    win = tk.Toplevel(parent)
    win.title(f"{'Создать' if is_new else 'Настройки'}: {card_name}")
    win.geometry("250x120")

    var_test = tk.BooleanVar(value=stg.get("test", False))
    tk.Checkbutton(win, text="test", variable=var_test).pack(padx=10, pady=10)

    def _save():
        stg["test"] = var_test.get()
        save_json(cards, CARDS_FILE)
        if is_new and lb is not None:
            lb.insert(tk.END, card_name)
        win.destroy()

    tk.Button(win, text="Сохранить", command=_save).pack(side="bottom", padx=10, pady=10)

def open_cards_window(root: tk.Tk) -> None:
    win = tk.Toplevel(root)
    win.title("Управление карточками")
    win.geometry("300x330")

    # верх: ввод + «Добавить»
    add_frame = tk.Frame(win)
    add_frame.pack(fill="x", padx=10, pady=(10, 0))

    tk.Label(add_frame, text="Новая:").pack(side="left")
    entry = tk.Entry(add_frame)
    entry.pack(side="left", fill="x", expand=True, padx=5)

    cards = load_json(CARDS_FILE)

    tk.Label(win, text="Список карточек:").pack(anchor="w",
                                                padx=10, pady=(10, 0))
    lb = _build_list(win, cards)

    # нижние кнопки
    btn_frame = tk.Frame(win)
    btn_frame.pack(side="bottom", fill="x", padx=10, pady=10)

    tk.Button(btn_frame, text="Удалить выбранную",
              command=lambda: _delete_selected(lb, cards)).pack(side="left",
                                                               expand=True)

    tk.Button(btn_frame, text="Настройки карточки",
              command=lambda: _card_settings_window(win, cards,
                                                    lb.get(lb.curselection()[0])
                                                    if lb.curselection() else "",
                                                    lb, is_new=False)
              ).pack(side="left", expand=True)

    def _add_card():
        name = entry.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Имя не должно быть пустым")
            return
        if any(name.lower() == n.lower() for n in cards):
            messagebox.showerror("Ошибка", "Такая карточка уже существует")
            return
        entry.delete(0, tk.END)
        _card_settings_window(win, cards, name, lb, is_new=True)

    tk.Button(add_frame, text="Добавить", command=_add_card).pack(side="right")
