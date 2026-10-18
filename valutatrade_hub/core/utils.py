def validate_amount(amount: float):
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

def validate_currency_code(code: str):
    if not code or not (2 <= len(code) <= 5) or not code.isupper():
        raise ValueError("Код валюты должен быть в верхнем регистре и содержать от 2 до 5 символов")
