from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.parser_service.config import ParserConfig


class Storage:
    def __init__(self):
        self.db = DatabaseManager()
        self.config = ParserConfig()

    def save_rates(self, snapshot: dict):
        self.db.write_json_atomic(self.config.RATES_FILE_PATH, snapshot)

    def save_history(self, pair: str, rate: float, timestamp: str, source: str):
        history = self.db.read_json(self.config.HISTORY_FILE_PATH)
        record_id = f"{pair}_{timestamp}"
        for record in history:
            if record.get("id") == record_id: return
        history.append({
            "id": record_id,
            "from_currency": pair.split("_")[0],
            "to_currency": pair.split("_")[1],
            "rate": rate,
            "timestamp": timestamp,
            "source": source
        })
        self.db.write_json_atomic(self.config.HISTORY_FILE_PATH, history)
