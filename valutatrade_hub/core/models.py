import hashlib
from datetime import datetime

from valutatrade_hub.core.exceptions import InsufficientFundsError


class User:
    def __init__(self, user_id: int, username: str, hashed_password: str, salt: str, registration_date: datetime):
        self._user_id = user_id
        self.username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self) -> int: return self._user_id
    @property
    def username(self) -> str: return self._username

    @username.setter
    def username(self, value: str):
        if not value or not value.strip(): raise ValueError("Имя не может быть пустым")
        self._username = value.strip()

    @property
    def registration_date(self) -> datetime: return self._registration_date

    def get_user_info(self) -> str:
        return f"ID: {self._user_id} | Пользователь: {self._username} | Дата регистрации: {self._registration_date.isoformat()}"

    def change_password(self, new_password: str):
        if len(new_password) < 4: raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = hashlib.sha256((new_password + self._salt).encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        calc_hash = hashlib.sha256((password + self._salt).encode()).hexdigest()
        return calc_hash == self._hashed_password

class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code.upper()
        self.balance = balance

    @property
    def balance(self) -> float: return self._balance

    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)): raise TypeError("Баланс должен быть числом")
        if value < 0: raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float):
        if amount <= 0: raise ValueError("'amount' должен быть положительным числом")
        self.balance += amount

    def withdraw(self, amount: float):
        if amount <= 0: raise ValueError("'amount' должен быть положительным числом")
        if amount > self.balance:
            raise InsufficientFundsError(self.balance, amount, self.currency_code)
        self.balance -= amount

    def get_balance_info(self) -> str:
        return f"{self.currency_code}: {self.balance:.4f}"

class Portfolio:
    def __init__(self, user_id: int, wallets: dict[str, Wallet] | None = None, user=None):
        self._user_id = user_id
        self._wallets = wallets if wallets is not None else {}
        self._user = user

    @property
    def user_id(self) -> int: return self._user_id
    @property
    def user(self): return self._user
    @property
    def wallets(self) -> dict[str, Wallet]: return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        code = currency_code.upper()
        if code in self._wallets: raise ValueError(f"Кошелек {code} уже существует")
        wallet = Wallet(code, 0.0)
        self._wallets[code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet:
        code = currency_code.upper()
        if code not in self._wallets: return self.add_currency(code)
        return self._wallets[code]

    def get_total_value(self, base_currency: str = "USD", rates: dict | None = None) -> float:
        base = base_currency.upper()
        total = 0.0
        fallback_rates = {"EUR_USD": 1.0786, "BTC_USD": 59337.21, "RUB_USD": 0.01016}
        active_rates = rates if rates is not None else fallback_rates

        for code, wallet in self._wallets.items():
            if code == base:
                total += wallet.balance
                continue
            rate_to_usd = 1.0 if code == "USD" else (active_rates.get(f"{code}_USD", {}).get("rate", active_rates.get(f"{code}_USD", 0.0)) if isinstance(active_rates.get(f"{code}_USD"), dict) else active_rates.get(f"{code}_USD", 0.0))
            rate_base_to_usd = 1.0 if base == "USD" else (active_rates.get(f"{base}_USD", {}).get("rate", active_rates.get(f"{base}_USD", 0.0)) if isinstance(active_rates.get(f"{base}_USD"), dict) else active_rates.get(f"{base}_USD", 0.0))
            if not rate_to_usd and code != "USD": raise KeyError(f"Нет курса для {code}")
            if not rate_base_to_usd and base != "USD": raise KeyError(f"Нет курса для {base}")
            total += wallet.balance * rate_to_usd / rate_base_to_usd
        return total
