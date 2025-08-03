from .json_io import load_json
from .utils import API_URL, SETTINGS_FILE
import requests

def check_subscription():
    settings = load_json(SETTINGS_FILE)
    license_key = settings.get("license_key", "")

    if not license_key:
        return "Нет лицензии", "Введите ключ во вкладке «Лицензия»"

    try:
        resp = requests.get(f"{API_URL}/check_subscription",
                            params={"license_key": license_key},
                            timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except (requests.exceptions.RequestException,
            ValueError, KeyError):
        return "Неактивна", "Сервер недоступен"

    if data.get("active"):
        return "Активна", data["subscription_end"]
    else:
        return "Неактивна", "Подписка истекла"