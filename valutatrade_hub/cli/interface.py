import shlex

from prettytable import PrettyTable

from valutatrade_hub.core import usecases
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import CurrencyNotFoundError, ValutaTradeError
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.logging_config import add_console_logger, remove_console_logger
from valutatrade_hub.parser_service.updater import RatesUpdater

db = DatabaseManager()
settings = SettingsLoader()


class Session:
    def __init__(self):
        self.current_user = None


session = Session()


def parse_args(args_list):
    parsed = {}
    iterator = iter(args_list)
    for item in iterator:
        if item.startswith("--"):
            key = item[2:]
            try:
                parsed[key] = next(iterator)
            except StopIteration:
                parsed[key] = True
    return parsed


def run():
    print("=== Платформа Valuta Trade Hub CLI ===")
    while True:
        try:
            cmd_line = input("> ")
            if not cmd_line.strip():
                continue
            parts = shlex.split(cmd_line)
            command = parts[0]
            args = parse_args(parts[1:])

            if command == "exit":
                break

            elif command == "register":
                uid = usecases.register(args.get("username"), args.get("password"))
                print(f"Пользователь '{args.get('username')}' зарегистрирован (id={uid}). Войдите: login --username {args.get('username')} --password ****")

            elif command == "login":
                session.current_user = usecases.login(args.get("username"), args.get("password"))
                print(f"Вы вошли как '{session.current_user.username}'")

            elif command == "show-portfolio":
                if not session.current_user:
                    print("Сначала выполните login")
                    continue
                base = args.get("base", "USD").upper()

                # Строгая проверка базовой валюты по реестру (Ответ на Вопрос 3)
                try:
                    get_currency(base)
                except CurrencyNotFoundError:
                    print(f"Неизвестная базовая валюта '{base}'")
                    continue

                portfolio = usecases.load_portfolio(session.current_user.user_id)
                rates = db.read_json(settings.get("RATES_FILE")).get("pairs", {})
                print(f"Портфель пользователя '{session.current_user.username}' (база: {base}):")

                t = PrettyTable(["Валюта", "Баланс", f"Стоимость ({base})"])
                for code, wallet in portfolio.wallets.items():
                    try:
                        single_p = portfolio.__class__(portfolio.user_id, {code: wallet})
                        cost = single_p.get_total_value(base, rates)
                        t.add_row([code, f"{wallet.balance:.4f}", f"{cost:.2f} {base}"])
                    except Exception:  # noqa: BLE001
                        t.add_row([code, f"{wallet.balance:.4f}", "Нет курса"])
                print(t)
                try:
                    print(f"ИТОГО: {portfolio.get_total_value(base, rates):,.2f} {base}")
                except Exception:  # noqa: BLE001
                    print("ИТОГО: Ошибка расчета.")

            elif command == "buy":
                if not session.current_user:
                    print("Сначала выполните login")
                    continue
                currency = args.get("currency", "").upper()
                amount = float(args.get("amount", 0))
                portfolio_before = usecases.load_portfolio(session.current_user.user_id)
                was_balance = (
                    portfolio_before.wallets.get(currency).balance
                    if currency in portfolio_before.wallets
                    else 0.0
                )

                new_balance = usecases.buy(session.current_user.user_id, currency, amount)

                try:
                    rate, _ = usecases.get_rate(currency, "USD")
                    print(f"Покупка выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}")
                    print(f"Изменения в портфеле:\n{currency}: было {was_balance:.4f} -> стало {new_balance:.4f}")
                    print(f"Оценочная стоимость покупки: {amount * rate:,.2f} USD")
                except Exception:  # noqa: BLE001
                    print(f"Куплено {amount} {currency}.")

            elif command == "sell":
                if not session.current_user:
                    print("Сначала выполните login")
                    continue
                currency = args.get("currency", "").upper()
                amount = float(args.get("amount", 0))
                portfolio_before = usecases.load_portfolio(session.current_user.user_id)
                was_balance = (
                    portfolio_before.wallets.get(currency).balance
                    if currency in portfolio_before.wallets
                    else 0.0
                )

                new_balance = usecases.sell(session.current_user.user_id, currency, amount)

                try:
                    rate, _ = usecases.get_rate(currency, "USD")
                    print(f"Продажа выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}")
                    print(f"Изменения в портфеле:\n{currency}: было {was_balance:.4f} -> стало {new_balance:.4f}")
                    print(f"Оценочная выручка: {amount * rate:,.2f} USD")
                except Exception:  # noqa: BLE001
                    print(f"Продано {amount} {currency}.")

            elif command == "get-rate":
                rate, up = usecases.get_rate(args.get("from", "").upper(), args.get("to", "").upper())
                print(f"Курс: {rate:.8f} (Обновлено: {up})\nОбратный курс: {(1 / rate):.2f}")

            elif command == "update-rates":
                add_console_logger()
                try:
                    success, count, errors = RatesUpdater().run_update(source_filter=args.get("source"))
                    if success and not errors:
                        print(f"Update successful. Total rates updated: {count}.")
                    else:
                        print("Update completed with errors. Check logs/actions.log for details.")
                finally:
                    remove_console_logger()

            elif command == "show-rates":
                rates_data = db.read_json(settings.get("RATES_FILE"))
                pairs = rates_data.get("pairs", {})
                if not pairs:
                    print("Локальный кеш курсов пуст. Выполните 'update-rates', чтобы загрузить данные.")
                    continue

                currency_filter = args.get("currency")
                top_filter = args.get("top")
                base_filter = args.get("base", "USD").upper()

                table = PrettyTable(["Валютная Пара", f"Курс ({base_filter})", "Источник"])
                items = []

                for p, info in pairs.items():
                    c_from, c_to = p.split("_")
                    if currency_filter and currency_filter.upper() not in (c_from, c_to):
                        continue

                    try:
                        if base_filter == "USD":
                            rate_val = info["rate"]
                        else:
                            base_pair_info = pairs.get(f"{base_filter}_USD")
                            if not base_pair_info:
                                continue
                            rate_val = info["rate"] / base_pair_info["rate"]
                        items.append((f"{c_from}_{base_filter}", rate_val, info["source"], info["rate"]))
                    except Exception:  # noqa: BLE001, S110
                        pass

                if top_filter:
                    # Фильтруем только крипту для топа (Ответ на Вопрос 7)
                    crypto_items = [
                        item for item in items if item[0].split("_")[0] in ("BTC", "ETH", "SOL")
                    ]
                    crypto_items.sort(key=lambda x: x[3], reverse=True)
                    items = crypto_items[: int(top_filter)]
                else:
                    items.sort(key=lambda x: x[0])

                for row in items:
                    table.add_row([row[0], f"{row[1]:.6f}", row[2]])

                print(f"Данные из кэша (обновлено: {rates_data.get('last_refresh', 'N/A')}):")
                print(table)

            else:
                print("Неизвестная команда.")

        except ValutaTradeError as vte:
            print(f"Ошибка: {vte}")
        except ValueError as ve:
            print(f"Ошибка: {ve}")
        except Exception as e:  # noqa: BLE001
            print(f"Системный сбой: {e}")
