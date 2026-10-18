import threading
import time

from valutatrade_hub.logging_config import logger
from valutatrade_hub.parser_service.updater import RatesUpdater


class BackgroundScheduler:
    def __init__(self, interval_seconds: int = 300):
        self.interval = interval_seconds
        self.updater = RatesUpdater()
        self.running = False
        self._thread = None

    def _loop(self):
        while self.running:
            try: 
                self.updater.run_update()
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Фоновое обновление пропущено: {e}")
            time.sleep(self.interval)

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        self.running = False
