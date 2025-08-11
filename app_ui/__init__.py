import sys
from tkinter import messagebox

def on_close():
    if messagebox.askyesno("Выход", "Точно закрыть программу?"):
        sys.exit(0)
