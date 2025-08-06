import logging, time, requests
from app_utils.storage import JsonStore
from app_utils.utils import API_URL, SETTINGS_FILE

log = logging.getLogger(__name__)

class SubscriptionChecker:
    def __init__(self, store: JsonStore | None = None, test: bool = False):
        self.store = store or JsonStore(SETTINGS_FILE)
        self.test = test
        log.debug(f"SubscriptionChecker initialized, test={self.test}")

    def status(self) -> tuple[str, str, int]:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        if self.test:
            log.info("Тестовый режим, подписка активна")
            return "Активна", now, 0
        settings = self.store.load()
        key = settings.get("license_key", "")
        if not key:
            log.warning("Лицензионный ключ не задан")
            return "Нет лицензии", now, 1
        try:
            log.debug(f"Запрос статуса подписки для ключа {key}")
            r = requests.get(f"{API_URL}/check_subscription_services", params={"license_key": key}, timeout=8)
            r.raise_for_status()
            data = r.json()
            active = bool(data.get("active"))
            max_cards = int(data.get("max_cards", 1))
            end = data.get("subscription_end", now)
            log.info(f"Подписка {'активна' if active else 'неактивна'}")
        except Exception as e:
            log.error(f"Ошибка при проверке подписки: {e}")
            return "Неактивна", now, 1
        return ("Активна", end, max_cards) if active else ("Неактивна", end, max_cards)