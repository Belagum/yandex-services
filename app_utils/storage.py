import json, os, logging

log = logging.getLogger(__name__)

class JsonStore:
    def __init__(self, path: str): self.path = path
    def load(self) -> dict:
        if os.path.exists(self.path):
            log.debug(f"Загружаю данные из {self.path}")
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        log.debug(f"Файл не найден: {self.path}")
        return {}
    def save(self, data: dict) -> None:
        log.debug(f"Сохраняю данные в {self.path}")
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
