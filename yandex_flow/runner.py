import asyncio, concurrent.futures as cf, logging, random, threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from app_utils.storage import JsonStore
from app_utils.utils import CARDS_FILE
from yandex_flow.YandexService import YandexServicesCfg, YandexService
from yandex_flow.start import BrowserSession

log = logging.getLogger(__name__)


@dataclass(slots=True)
class CardConfig:
    name: str
    executor: str
    city: str
    time_in_card: int
    repeat_count: int
    click_phone: bool
    keywords: list[str] = field(default_factory=list)

    @classmethod
    def from_raw(cls, name: str, raw: dict):
        s = raw.get("settings", {})
        return cls(
            name=name,
            executor=s.get("name", ""),
            city=s.get("city", ""),
            time_in_card=max(45, int(s.get("time_in_card", 45))),
            repeat_count=max(1, int(s.get("repeat_count", 1))),
            click_phone=bool(s.get("click_phone", False)),
            keywords=s.get("keywords", []),
        )


class _StatsWriter:
    def __init__(self, file: str | Path):
        self._file = Path(file)
        self._lock = threading.Lock()

    def write(self, msg: str):
        with self._lock, self._file.open("a", encoding="utf-8") as f:
            f.write(msg + "\n")


class Runner:
    def __init__(self, names: list[str], headless: bool, threads: int, position: bool):
        data = JsonStore(CARDS_FILE).load()
        self.configs: list[CardConfig] = [
            CardConfig.from_raw(n, data[n]) for n in names if n in data
        ]
        self.headless = bool(headless)
        self.position = bool(position)
        self.threads = max(1, min(threads, 15))
        self._writer = _StatsWriter("stats.txt")

    async def _handle_one(self, cfg: CardConfig, kw: str):
        try:
            async with BrowserSession(headless=self.headless) as page:
                svc = YandexService(
                    page,
                    YandexServicesCfg(
                        name=cfg.executor,
                        city=cfg.city,
                        time_in_card=cfg.time_in_card,
                        click_phone=cfg.click_phone,
                        keyword=f"{kw} {cfg.city} Яндекс услуги",
                    ),
                )

                ok, res = await svc.search()
                if not ok:
                    self._writer.write(f"{cfg.name}: {res}")
                    return

                ok, res = await svc.verify_city()
                if not ok:
                    self._writer.write(f"{cfg.name}: {res}")
                    return

                ok, res = await svc.find_executor()
                if self.position or not ok:          # в режиме позиций здесь КОНЧАЕМ
                    self._writer.write(f"{cfg.name}: {res}")
                    return

                ok, res = await svc.perform_random_action()
                self._writer.write(
                    f"{cfg.name}: {res}" if ok else f"{cfg.name}: action error: {res}"
                )
        except Exception as e:
            self._writer.write(f"{cfg.name}: exception: {e}")

    def _task_args(self) -> Iterable[tuple[CardConfig, str]]:
        for cfg in self.configs:
            if not cfg.keywords:
                self._writer.write(f"{cfg.name}: skipped, no keywords")
                continue
            for _ in range(cfg.repeat_count):
                yield cfg, random.choice(cfg.keywords)

    def _job(self, cfg: CardConfig, kw: str):
        asyncio.run(self._handle_one(cfg, kw))

    def run(self):
        tasks = list(self._task_args())
        if not tasks:
            log.warning("No tasks to run")
            return
        with cf.ThreadPoolExecutor(min(self.threads, len(tasks))) as ex:
            ex.map(lambda args: self._job(*args), tasks)
