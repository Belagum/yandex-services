import logging
import requests
from app_utils.storage import JsonStore
from app_utils.utils import API_URL, SETTINGS_FILE

log = logging.getLogger(__name__)

class SubscriptionChecker:
    def __init__(self, store: JsonStore | None = None, test: bool = False):
        self.store = store or JsonStore(SETTINGS_FILE)
        self.test = test
        log.debug(f"SubscriptionChecker initialized, test={self.test}")

    def status(self) -> tuple[str, str]:
        if self.test:
            log.info("Тестовый режим, подписка активна")
            return "Активна", "Тестовый режим"
        settings = self.store.load()
        key = settings.get("license_key", "")
        if not key:
            log.warning("Лицензионный ключ не задан")
            return "Нет лицензии", "Введите ключ во вкладке «Лицензия»"
        try:
            log.debug(f"Запрос статуса подписки для ключа {key}")
            r = requests.get(f"{API_URL}/check_subscription", params={"license_key": key}, timeout=8)
            r.raise_for_status()
            data = r.json()
            active = data.get("active", False)
            log.info(f"Подписка {'активна' if active else 'неактивна'}")
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            log.error(f"Ошибка при проверке подписки: {e}")
            return "Неактивна", "Сервер недоступен"
        return ("Активна", data["subscription_end"]) if active else ("Неактивна", "Подписка истекла")
