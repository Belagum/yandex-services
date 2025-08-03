import requests
from app_utils.storage import JsonStore
from app_utils.utils import API_URL, SETTINGS_FILE

class SubscriptionChecker:
    def __init__(self, store: JsonStore | None = None, test: bool = False):
        self.store = store or JsonStore(SETTINGS_FILE)
        self.test = test

    def status(self) -> tuple[str, str]:
        print(self.test)
        if self.test:
            return "Активна", "Тестовый режим"
        settings = self.store.load()
        key = settings.get('license_key', '')
        if not key:
            return 'Нет лицензии', 'Введите ключ во вкладке «Лицензия»'
        try:
            r = requests.get(f'{API_URL}/check_subscription',
                             params={'license_key': key}, timeout=8)
            r.raise_for_status()
            data = r.json()
        except (requests.exceptions.RequestException, ValueError, KeyError):
            return 'Неактивна', 'Сервер недоступен'
        return ('Активна', data['subscription_end']) if data.get('active') \
               else ('Неактивна', 'Подписка истекла')