from datetime import UTC, datetime

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.logging_config import logger
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.storage import Storage


class RatesUpdater:
    def __init__(self):
        self.storage = Storage()
        self.gecko = CoinGeckoClient()
        self.exchangerate = ExchangeRateApiClient()

    def run_update(self, source_filter=None) -> tuple[bool, int, list]:
        errors, merged_pairs = [], {}
        timestamp = datetime.now(UTC).isoformat() + "Z"
        logger.info("Starting rates update...")

        if not source_filter or source_filter == "coingecko":
            try:
                logger.info("Fetching from CoinGecko...")
                rates = self.gecko.fetch_rates()
                for p, val in rates.items():
                    merged_pairs[p] = {"rate": val, "updated_at": timestamp, "source": "CoinGecko"}
                    self.storage.save_history(p, val, timestamp, "CoinGecko")
                logger.info(f"Fetching from CoinGecko... OK ({len(rates)} rates)")
            except Exception as e:  # noqa: BLE001
                errors.append(str(e))
                logger.error(f"Failed to fetch from CoinGecko: {e}")

        if not source_filter or source_filter == "exchangerate":
            try:
                logger.info("Fetching from Exchange Rate-API...")
                rates = self.exchangerate.fetch_rates()
                for p, val in rates.items():
                    merged_pairs[p] = {"rate": val, "updated_at": timestamp, "source": "ExchangeRate-API"}
                    self.storage.save_history(p, val, timestamp, "ExchangeRate-API")
                logger.info(f"Fetching from ExchangeRate-API... OK ({len(rates)} rates)")
            except Exception as e:  # noqa: BLE001
                errors.append(str(e))
                logger.error(f"Failed to fetch from ExchangeRate-API: {e}")

        if not merged_pairs:
            raise ApiRequestError("Не удалось получить новые курсы ни от одного внешнего источника API.")

        cache = self.storage.db.read_json(self.storage.config.RATES_FILE_PATH)
        if "pairs" not in cache: cache = {"pairs": {}}
        cache["pairs"].update(merged_pairs)
        cache["last_refresh"] = timestamp
        self.storage.save_rates(cache)
        return True, len(merged_pairs), errors
