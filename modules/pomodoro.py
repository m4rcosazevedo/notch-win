from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class PomodoroModule(QObject):
    tick         = pyqtSignal(str)   # "25:00"
    mode_changed = pyqtSignal(str)   # "work" | "break" | "long_break"
    session_done = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.sessions_done = 0
        self._durations = {"work": 25 * 60, "break": 5 * 60, "long_break": 15 * 60}
        self._mode      = "work"
        self._total     = self._durations["work"]
        self._remaining = self._total
        self._running   = False

        self._timer = QTimer()
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def running(self) -> bool:
        return self._running

    @property
    def mode(self) -> str:
        return self._mode

    def work_minutes(self) -> int:
        return self._durations["work"] // 60

    def set_durations(self, work_mins: int, break_mins: int, long_break_mins: int):
        self._durations = {
            "work":       work_mins * 60,
            "break":      break_mins * 60,
            "long_break": long_break_mins * 60,
        }
        if not self._running:
            self._total     = self._durations[self._mode]
            self._remaining = self._total
            self.tick.emit(self._format(self._remaining))

    def toggle(self):
        if self._running:
            self._timer.stop()
            self._running = False
        else:
            self._timer.start()
            self._running = True

    def reset(self):
        self._timer.stop()
        self._running   = False
        self._remaining = self._total
        self.tick.emit(self._format(self._remaining))

    def skip(self):
        self._advance_mode()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _on_tick(self):
        self._remaining -= 1
        self.tick.emit(self._format(self._remaining))
        if self._remaining <= 0:
            self._advance_mode()

    def _advance_mode(self):
        self._timer.stop()
        self._running = False

        if self._mode == "work":
            self.sessions_done += 1
            if self.sessions_done % 4 == 0:
                self._mode = "long_break"
                self.session_done.emit("Intervalo longo! Hora de descansar.")
            else:
                self._mode = "break"
                self.session_done.emit("Intervalo! Descanse alguns minutos.")
        else:
            self._mode = "work"
            mins = self._durations["work"] // 60
            self.session_done.emit(f"Hora de focar! {mins} minutos.")

        self._total     = self._durations[self._mode]
        self._remaining = self._total
        self.mode_changed.emit(self._mode)
        self.tick.emit(self._format(self._remaining))

    @staticmethod
    def _format(seconds: int) -> str:
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def display(self) -> str:
        return self._format(self._remaining)
