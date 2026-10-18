from typing import Any


class SettingsLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = {
                "USERS_FILE": "data/users.json",
                "PORTFOLIOS_FILE": "data/portfolios.json",
                "RATES_FILE": "data/rates.json",
                "HISTORY_FILE": "data/exchange_rates.json",
                "RATES_TTL_SECONDS": 300,
                "DEFAULT_BASE_CURRENCY": "USD"
            }
        return cls._instance

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)
