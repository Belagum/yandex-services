import threading
from pathlib import Path

class StatsWriter:
    def __init__(self, file: str | Path):
        self._file, self._lock = Path(file), threading.Lock()

    def write(self, msg: str):
        with self._lock, self._file.open("a", encoding="utf-8") as f:
            f.write(msg + "\n")