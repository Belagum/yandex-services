import logging, concurrent.futures as cf
from app_utils.storage import JsonStore
from app_utils.utils import CARDS_FILE

log = logging.getLogger(__name__)

class CardConfig:
    def __init__(self, name: str, raw: dict):
        s = raw.get("settings", {})
        self.name: str = name
        self.executor: str = s.get("name", "")
        self.city: str = s.get("city", "")
        self.time_in_card: int = max(45, int(s.get("time_in_card", 45)))
        self.click_phone: bool = bool(s.get("click_phone", False))
        self.keywords: list[str] = s.get("keywords", [])

class Runner:
    def __init__(self, names: list[str], headless: bool, threads: int):
        data = JsonStore(CARDS_FILE).load()
        self.configs: list[CardConfig] = [CardConfig(n, data[n]) for n in names if n in data]
        self.headless: bool = headless
        self.threads: int = max(1, min(threads, 15))

    def _job(self, cfg: CardConfig):
        log.info(f"Запуск {cfg.name}: executor={cfg.executor}, city={cfg.city}, "
                 f"time={cfg.time_in_card}, click_phone={cfg.click_phone}, "
                 f"keywords={cfg.keywords}, headless={self.headless}, threads={self.threads}")

    def run(self):
        with cf.ThreadPoolExecutor(self.threads) as ex:
            ex.map(self._job, self.configs)
