import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

SETTINGS_FILE = str(BASE_DIR / "config.json")
CARDS_FILE    = str(BASE_DIR / "cards.json")
PROXIES_FILE  = str(BASE_DIR / "proxies.json")
COOKIES_DIR   = str(BASE_DIR / "cookies")

API_URL = "http://yandextopbot.ru"
version = "v1"
current_runner = None
