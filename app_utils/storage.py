import json, os

class JsonStore:
    def __init__(self, path: str): self.path = path
    def load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f: return json.load(f)
        return {}
    def save(self, data: dict) -> None:
        with open(self.path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)
