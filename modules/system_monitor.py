import time
import threading
import psutil
try:
    from ping3 import ping
except ImportError:
    ping = lambda x: None

from PyQt6.QtCore import QObject, pyqtSignal


class SystemMonitorModule(QObject):
    stats_updated = pyqtSignal(dict)

    def __init__(self, ping_host="8.8.8.8", interval=2.0):
        super().__init__()
        self.ping_host = ping_host
        self.interval = interval
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        while self._running:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            
            try:
                p = ping(self.ping_host, timeout=1)
                latency = int(p * 1000) if p is not None else -1
            except Exception:
                latency = -1

            self.stats_updated.emit({
                "cpu": cpu,
                "ram": ram,
                "ping": latency
            })
            time.sleep(self.interval)
