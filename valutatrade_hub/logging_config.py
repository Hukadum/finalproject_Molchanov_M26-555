import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("valutatrade")
    logger.setLevel(logging.DEBUG)
    file_handler = RotatingFileHandler("logs/actions.log", maxBytes=1024*1024, backupCount=5, encoding="utf-8")
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    return logger

logger = setup_logging()

def add_console_logger():
    root_logger = logging.getLogger("valutatrade")
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    console_handler.set_name("console_handler")
    root_logger.addHandler(console_handler)

def remove_console_logger():
    root_logger = logging.getLogger("valutatrade")
    for handler in root_logger.handlers[:]:
        if handler.name == "console_handler":
            root_logger.removeHandler(handler)
