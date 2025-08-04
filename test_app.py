import logging

from app_ui.main_window import run_app

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

if __name__ == '__main__':
    run_app(test=True)
