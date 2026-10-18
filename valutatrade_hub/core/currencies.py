from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    def __init__(self, name: str, code: str):
        if not name or not name.strip(): raise ValueError("Имя не может быть пустым")
        if not (2 <= len(code) <= 5) or not code.isupper() or " " in code:
            raise ValueError("Код должен быть в верхнем регистре и содержать от 2 до 5 символов")
        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str: pass

class FiatCurrency(Currency):
    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country
    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} - {self.name} (Issuing: {self.issuing_country})"

class CryptoCurrency(Currency):
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap
    def get_display_info(self) -> str:
        return f"[CRYPTO] {self.code} - {self.name} (Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"

_REGISTRY = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russian Federation"),
    "GBP": FiatCurrency("British Pound", "GBP", "United Kingdom"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11),
    "SOL": CryptoCurrency("Solana", "SOL", "Proof of History", 6.5e10)
}

def get_currency(code: str) -> Currency:
    c_code = code.upper()
    if c_code not in _REGISTRY: raise CurrencyNotFoundError(c_code)
    return _REGISTRY[c_code]
