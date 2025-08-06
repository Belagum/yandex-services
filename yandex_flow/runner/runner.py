import asyncio, concurrent.futures as cf, itertools, logging, random, time, json
from pathlib import Path
from typing import Iterable
import app_utils.utils as utils
from app_utils.storage import JsonStore
from app_utils.utils import CARDS_FILE
from yandex_flow.YandexService import YandexService, YandexServicesCfg
from yandex_flow.runner.config import CardConfig
from yandex_flow.runner.stats import Stats
from yandex_flow.runner.writer import StatsWriter
from yandex_flow.start import BrowserSession

log = logging.getLogger(__name__)

class Runner:
    def __init__(self, names: list[str], headless: bool, threads: int, position: bool, infinity: bool):
        data = JsonStore(CARDS_FILE).load()
        self.cfgs = [CardConfig.from_raw(n, data[n]) for n in names if n in data]
        self.proxies: list[dict] = JsonStore(utils.PROXIES_FILE).load() or []
        self.headless, self.position, self.infinity = map(bool, (headless, position, infinity))
        self.threads = max(1, min(threads, 15))
        self._writer = StatsWriter("stats.txt")
        self._stats = Stats(self.cfgs, self.threads, self.infinity)

    def _task_args(self) -> Iterable[tuple[CardConfig, str]]:
        if self.infinity:
            while True:
                for c in self.cfgs:
                    if not c.keywords:
                        self._writer.write(f"{c.name}: skipped, no keywords"); continue
                    yield c, random.choice(c.keywords)
        else:
            for c in self.cfgs:
                if not c.keywords:
                    self._writer.write(f"{c.name}: skipped, no keywords"); continue
                for _ in range(c.repeat_count):
                    yield c, random.choice(c.keywords)

    @staticmethod
    def _load_cookies(card_name: str):
        p = Path(utils.COOKIES_DIR) / f"{card_name}_cookies.json"
        if not p.exists(): return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "cookies" in data: return data["cookies"]
            if isinstance(data, list): return data
        except Exception as e:
            log.debug(f"cookies read error: {e}")
        return None

    async def _do_one(self, cfg: CardConfig, kw: str, proxy: dict | None):
        async with BrowserSession(headless=self.headless, proxy=proxy) as page:
            try:
                cookies = self._load_cookies(cfg.name)
                if cookies:
                    ctx = getattr(page, "context", None)
                    if ctx and hasattr(ctx, "add_cookies"):
                        await ctx.add_cookies(cookies)
            except Exception as e:
                log.debug(f"cookies add error: {e}")
            svc = YandexService(page, YandexServicesCfg(
                name=cfg.executor, city=cfg.city, time_in_card=cfg.time_in_card,
                click_phone=cfg.click_phone, keyword=f"{kw} {cfg.city} Яндекс услуги"))
            ok, msg = await svc.search();   log.debug(msg)
            if not ok: return False
            ok, msg = await svc.verify_city(); log.debug(msg)
            if not ok: return False
            ok, msg = await svc.find_executor()
            if self.position or not ok: return ok
            ok, msg = await svc.perform_random_action(); log.debug(msg)
            return ok

    def _run_task(self, cfg_kw: tuple[CardConfig, str]):
        cfg, kw = cfg_kw; t0 = time.time(); proxy = None
        if cfg.use_proxy and cfg.proxy_idx:
            candidates = [self.proxies[i] for i in cfg.proxy_idx if i < len(self.proxies)]
            if candidates: proxy = random.choice(candidates)
        ok = False
        try: ok = asyncio.run(self._do_one(cfg, kw, proxy))
        except Exception as e: log.exception(e)
        finally: self._stats.update(cfg.name, ok, time.time() - t0)

    def stats_str(self) -> str: return self._stats.dump()

    def run(self):
        utils.current_runner = self
        try:
            if self.infinity:
                while True:
                    batch = list(itertools.islice(self._task_args(), self.threads))
                    if not batch: break
                    with cf.ThreadPoolExecutor(self.threads) as ex:
                        ex.map(self._run_task, batch)
            else:
                tasks = list(self._task_args())
                if not tasks: return
                with cf.ThreadPoolExecutor(min(self.threads, len(tasks))) as ex:
                    ex.map(self._run_task, tasks)
        finally:
            utils.current_runner = None
            self._writer.write(
                self._stats.dump() +
                f"\nВремя окончания       : "
                f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n"
            )