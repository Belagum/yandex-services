import logging, tkinter as tk, app_utils.utils as utils

logger = logging.getLogger(__name__)

class MonitoringWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Мониторинг")
        self.txt = tk.Text(self, state="disabled", wrap="none")
        self.txt.grid(padx=5, pady=5)
        self._refresh()

    def _refresh(self):
        data = utils.current_runner.stats_str() if utils.current_runner else "Ничего не запущено"
        lines = data.split("\n")
        h, w = len(lines), max((len(l) for l in lines), default=1)
        self.txt.config(state="normal", height=h, width=w)
        self.txt.delete("1.0", "end"); self.txt.insert("1.0", data); self.txt.config(state="disabled")
        self.update_idletasks()
        self.geometry(f"{self.txt.winfo_reqwidth()+10}x{self.txt.winfo_reqheight()+10}")
        self.after(1000, self._refresh)
