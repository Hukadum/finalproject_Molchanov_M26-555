import functools
from datetime import UTC, datetime

from valutatrade_hub.logging_config import logger


def log_action(action_name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timestamp = datetime.now(UTC).isoformat() + "Z"
            user_id = args[0] if args else kwargs.get("user_id", "unknown")
            currency = args[1] if len(args) > 1 else kwargs.get("currency_code", "N/A")
            amount = args[2] if len(args) > 2 else kwargs.get("amount", 0.0)
            try:
                result = func(*args, **kwargs)
                logger.info(f"{timestamp} {action_name.upper()} user_id={user_id} currency='{currency}' amount={amount} result=OK")
                return result
            except Exception as e:
                logger.error(f"{timestamp} {action_name.upper()} user_id={user_id} currency='{currency}' amount={amount} result=ERROR error_type={type(e).__name__} error_message='{e!s}'")
                raise
        return wrapper
    return decorator
