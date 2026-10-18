import uuid
from datetime import UTC, datetime

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    InvalidPasswordError,
    UserNotFoundError,
)
from valutatrade_hub.core.models import Portfolio, User, Wallet
from valutatrade_hub.core.utils import validate_amount, validate_currency_code
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader

settings = SettingsLoader()
db = DatabaseManager()

def register(username, password):
    if len(password) < 4: raise ValueError("Пароль должен быть не короче 4 символов")
    if not username or not username.strip(): raise ValueError("Имя не может быть пустым")
    users_data = db.read_json(settings.get("USERS_FILE"))
    for u in users_data:
        if u["username"] == username: raise ValueError(f"Имя пользователя '{username}' уже занято")
    salt = str(uuid.uuid4())[:6]
    user_id = len(users_data) + 1
    temp_user = User(user_id, username, "", salt, datetime.now(UTC))
    temp_user.change_password(password)
    users_data.append({
        "user_id": user_id, "username": username,
        "hashed_password": temp_user._hashed_password, "salt": salt,
        "registration_date": temp_user.registration_date.isoformat()
    })
    db.write_json_atomic(settings.get("USERS_FILE"), users_data)
    portfolios_data = db.read_json(settings.get("PORTFOLIOS_FILE"))
    portfolios_data.append({"user_id": user_id, "wallets": {}})
    db.write_json_atomic(settings.get("PORTFOLIOS_FILE"), portfolios_data)
    return user_id

def login(username, password):
    users_data = db.read_json(settings.get("USERS_FILE"))
    for u in users_data:
        if u["username"] == username:
            user = User(u["user_id"], u["username"], u["hashed_password"], u["salt"], datetime.fromisoformat(u["registration_date"]))
            if not user.verify_password(password): raise InvalidPasswordError("Неверный пароль")
            return user
    raise UserNotFoundError(f"Пользователь '{username}' не найден")

def load_portfolio(user_id: int) -> Portfolio:
    portfolios_data = db.read_json(settings.get("PORTFOLIOS_FILE"))
    for p in portfolios_data:
        if p["user_id"] == user_id:
            wallets = {code: Wallet(code, w["balance"]) for code, w in p["wallets"].items()}
            return Portfolio(user_id, wallets)
    return Portfolio(user_id)

def save_portfolio(portfolio: Portfolio):
    portfolios_data = db.read_json(settings.get("PORTFOLIOS_FILE"))
    wallets_json = {code: {"balance": w.balance} for code, w in portfolio.wallets.items()}
    for p in portfolios_data:
        if p["user_id"] == portfolio.user_id:
            p["wallets"] = wallets_json
            break
    db.write_json_atomic(settings.get("PORTFOLIOS_FILE"), portfolios_data)

@log_action("buy")
def buy(user_id: int, currency_code: str, amount: float):
    validate_currency_code(currency_code)
    validate_amount(amount)
    get_currency(currency_code)
    portfolio = load_portfolio(user_id)
    wallet = portfolio.get_wallet(currency_code)
    wallet.deposit(amount)
    save_portfolio(portfolio)
    return wallet.balance

@log_action("sell")
def sell(user_id: int, currency_code: str, amount: float):
    validate_currency_code(currency_code)
    validate_amount(amount)
    get_currency(currency_code)
    portfolio = load_portfolio(user_id)
    wallet = portfolio.get_wallet(currency_code)
    wallet.withdraw(amount)
    save_portfolio(portfolio)
    return wallet.balance

def get_rate(from_code: str, to_code: str):
    get_currency(from_code)
    get_currency(to_code)
    rates_data = db.read_json(settings.get("RATES_FILE"))
    last_refresh_str = rates_data.get("last_refresh")
    need_update = False
    if not last_refresh_str:
        need_update = True
    else:
        try:
            ref_time = datetime.fromisoformat(last_refresh_str)
            if (datetime.now(UTC) - ref_time).total_seconds() > settings.get("RATES_TTL_SECONDS"):
                need_update = True
        except Exception: need_update = True  # noqa: BLE001

    if need_update:
        from valutatrade_hub.parser_service.updater import RatesUpdater
        try:
            RatesUpdater().run_update()
            rates_data = db.read_json(settings.get("RATES_FILE"))
        except Exception: pass  # noqa: BLE001, S110

    pairs = rates_data.get("pairs", {})
    def get_price(code):
        if code == "USD": return 1.0
        pair = f"{code}_USD"
        if pair in pairs: return pairs[pair]["rate"]
        raise ApiRequestError(f"Курс {code} USD недоступен. Повторите попытку позже.")
    return get_price(from_code) / get_price(to_code), rates_data.get("last_refresh", "N/A")
