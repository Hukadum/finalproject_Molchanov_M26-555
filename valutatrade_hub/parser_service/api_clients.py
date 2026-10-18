from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig

config = ParserConfig()


class BaseApiClient(ABC):
    @abstractmethod
    def fetch_rates(self) -> dict:
        pass


class CoinGeckoClient(BaseApiClient):
    def fetch_rates(self) -> dict:
        ids = ",".join(config.CRYPTO_ID_MAP.values())
        params = {"ids": ids, "vs_currencies": "usd"}
        try:
            res = requests.get(config.COINGECKO_URL, params=params, timeout=config.REQUEST_TIMEOUT)
            if res.status_code != 200:
                raise ApiRequestError(f"CoinGecko вернул статус {res.status_code}")
            data = res.json()
            return {
                "BTC_USD": data["bitcoin"]["usd"],
                "ETH_USD": data["ethereum"]["usd"],
                "SOL_USD": data["solana"]["usd"]
            }
        except Exception as e:
            raise ApiRequestError(f"Сбой сети CoinGecko: {e}") from e


class ExchangeRateApiClient(BaseApiClient):
    def fetch_rates(self) -> dict:
        url = f"{config.EXCHANGERATE_API_URL}/{config.EXCHANGERATE_API_KEY}/latest/{config.BASE_CURRENCY}"
        try:
            res = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            if res.status_code != 200:
                raise ApiRequestError(f"Exchange Rate-API вернул статус {res.status_code}")
            data = res.json()
            rates = data.get("conversion_rates", {})
            output = {}
            for t in config.FIAT_CURRENCIES:
                if t in rates and rates[t] != 0:
                    output[f"{t}_USD"] = 1.0 / rates[t]
            return output
        except Exception as e:
            raise ApiRequestError(f"Сбой сети ExchangeRate: {e}") from e
