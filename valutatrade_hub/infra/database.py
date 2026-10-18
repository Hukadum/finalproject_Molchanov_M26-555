import json
import os
from typing import Any


class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def read_json(self, file_path: str) -> Any:
        if not os.path.exists(file_path):
            return [] if "rates" not in file_path else {"pairs": {}}
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return [] if "rates" not in file_path else {"pairs": {}}

    def write_json_atomic(self, file_path: str, data: Any):
        tmp_path = f"{file_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(tmp_path, file_path)
