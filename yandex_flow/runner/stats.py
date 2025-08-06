import math
import threading
import time

from yandex_flow.runner.config import CardConfig


class Stats:
    def __init__(self, cfgs: list[CardConfig], threads: int, infinity: bool, position: bool = False,
                 autorun: bool = False, next_run: float | None = None):
        self._lock = threading.Lock()
        self.position = position
        self.autorun = autorun
        self.next_run = next_run
        self.map = {c.name: {"total": (
                                -1 if infinity else (
                                    len(c.keywords) if position else c.repeat_count
                                )),
                             "done": 0, "ok": 0} for c in cfgs}
        self.dur: list[float] = []
        self.start = time.time()
        self.threads, self.infinity = threads, infinity
        if position:
            self.total_kw = sum(len(c.keywords) for c in cfgs)
        elif infinity:
            self.total_kw = math.inf
        else:
            self.total_kw = sum(len(c.keywords) * c.repeat_count for c in cfgs)

    @staticmethod
    def _fmt(sec: float) -> str:
        h, m = divmod(int(sec), 3600); m, s = divmod(m, 60); return f"{h:02}:{m:02}:{s:02}"

    def update(self, name: str, ok: bool, dur: float):
        with self._lock:
            row = self.map[name]; row["done"] += 1; row["ok"] += ok
            self.dur.append(dur)

    def dump(self) -> str:
        with self._lock:
            done = sum(r["done"] for r in self.map.values())
            ok = sum(r["ok"] for r in self.map.values())
            avg = (sum(self.dur) / len(self.dur)) if self.dur else 0
            left = math.inf if self.infinity else max(self.total_kw - done, 0)
            left_time = math.inf if self.infinity else left / self.threads * avg
            run = time.time() - self.start

            if getattr(self, "autorun", False) and getattr(self, "next_run", None):
                mode = "авторежим"
            elif self.position:
                mode = "сбор позиций"
            elif self.infinity:
                mode = "бесконечный"
            else:
                mode = "обычный"

            head = [
                f"Время запуска         : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start))}",
                f"Режим                 : {mode}",
                f"Потоков в работе      : {self.threads}",
                f"Карточек в работе     : {len(self.map)}",
                f"Суммарный объём фраз  : {'∞' if self.infinity else self.total_kw}",
                f"Обработано фраз (all) : {done}",
                f"Обработано фраз (ok)  : {ok}",
                f"Среднее время/фразу   : {self._fmt(avg)}",
                f"Оставшееся время      : {'∞' if self.infinity else self._fmt(left_time)}",
                f"Всего время в работе  : {self._fmt(run)}",
                ""
            ]

            w = max(map(len, self.map))
            body = [f"{'Имя':<{w}} | целевое/обработано/успешно"]
            body += [f"{n:<{w}} | {'∞' if r['total'] == -1 else r['total']}/{r['done']}/{r['ok']}"
                     for n, r in self.map.items()]
            return "\n".join(head + body)
