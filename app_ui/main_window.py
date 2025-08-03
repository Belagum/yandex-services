import tkinter as tk
from app_ui.cards_window import open_cards_window
from app_utils.check_subscription import check_subscription
from app_utils.utils import version


def _status(parent, status_text):
    label = tk.Label(parent, text=f"Подписка: {status_text}")
    label.pack(pady=(5, 0), fill='x')
    return label

def _buttons(parent):
    f = tk.Frame(parent); f.pack(expand=True)
    tk.Button(f, text="Запустить", command=lambda: print("Run")).pack(pady=10)
    tk.Button(f, text="Управление карточками", command=lambda: open_cards_window(parent)).pack()

def _version(parent):
    tk.Label(parent, text=version).pack(side='bottom', fill='x', pady=5)

def run_app():
    root = tk.Tk()
    root.withdraw()  # Сначала скрываем окно

    sub_status, sub_detail, *_ = check_subscription()

    # if sub_status != "Активна":
    #     tk.messagebox.showerror(sub_status, sub_detail)
    #     root.destroy()
    #     return

    root.deiconify() # если все ок показываем
    root.title("Яндекс услуги")
    root.geometry("300x200")

    _status(root, sub_status)
    _buttons(root)
    _version(root)

    root.mainloop()