from pathlib import Path

SETTINGS_FILE = str(Path(__file__).resolve().parent.parent / "config.json")
CARDS_FILE = str(Path(__file__).resolve().parent.parent / "cards.json")
PROXIES_FILE = str(Path(__file__).resolve().parent.parent / "proxies.json")
API_URL = "http://yandextopbot.ru"
version = "v1"
current_runner = None