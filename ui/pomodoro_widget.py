from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QMenu
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QAction, QColor

from modules.pomodoro import PomodoroModule
from ui.icons import (
    _icon_btn, _refresh_icon, _DEFAULT_DARK,
    _ic_timer, _ic_reset, _ic_play, _ic_pause,
)
from config import notify, POMO_PRESETS, MENU_QSS


class PomodoroWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "section")
        self._pomodoro = PomodoroModule()
        self._color: QColor = _DEFAULT_DARK
        self._build_ui()
        self._connect()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(4, 0, 4, 0)
        h.setSpacing(6)

        self._icon_btn = _icon_btn(_ic_timer)
        self._icon_btn.setToolTip("Alterar duração do Pomodoro")
        self._icon_btn.clicked.connect(self._show_picker)

        self._time_lbl = QLabel(self._pomodoro.display())
        self._time_lbl.setObjectName("pomodoro-time")
        self._time_lbl.setFixedWidth(48)

        self._toggle_btn = _icon_btn(_ic_play)
        self._reset_btn  = _icon_btn(_ic_reset)

        h.addWidget(self._icon_btn)
        h.addWidget(self._time_lbl)
        h.addWidget(self._toggle_btn)
        h.addWidget(self._reset_btn)

    def _connect(self):
        self._pomodoro.tick.connect(lambda text: self._time_lbl.setText(text))
        self._pomodoro.mode_changed.connect(self._on_mode)
        self._pomodoro.session_done.connect(lambda msg: notify("Pomodoro", msg))
        self._toggle_btn.clicked.connect(self._toggle)
        self._reset_btn.clicked.connect(self._pomodoro.reset)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_mode(self, mode: str):
        self._time_lbl.setProperty("mode", mode)
        self._time_lbl.style().unpolish(self._time_lbl)
        self._time_lbl.style().polish(self._time_lbl)
        if not self._pomodoro.running:
            _refresh_icon(self._toggle_btn, _ic_play, color=self._color)
            self._toggle_btn.setObjectName("")
            self._toggle_btn.style().unpolish(self._toggle_btn)
            self._toggle_btn.style().polish(self._toggle_btn)

    def _toggle(self):
        self._pomodoro.toggle()
        if self._pomodoro.running:
            _refresh_icon(self._toggle_btn, _ic_pause, color=self._color)
            self._toggle_btn.setObjectName("pomo-btn-active")
        else:
            _refresh_icon(self._toggle_btn, _ic_play, color=self._color)
            self._toggle_btn.setObjectName("")
        self._toggle_btn.style().unpolish(self._toggle_btn)
        self._toggle_btn.style().polish(self._toggle_btn)

    # ── Duration picker ───────────────────────────────────────────────────────

    def _show_picker(self):
        menu = QMenu(self)
        menu.setStyleSheet(MENU_QSS)

        header = QAction("⏱  Duração do Pomodoro", self)
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()

        current_work = self._pomodoro.work_minutes()
        for label, work, brk, long_brk in POMO_PRESETS:
            mark = "✓  " if work == current_work else "    "
            action = QAction(f"{mark}{label}", self)
            action.setToolTip(f"Foco: {work}min · Pausa: {brk}min · Pausa longa: {long_brk}min")
            action.triggered.connect(
                lambda _, w=work, b=brk, lb=long_brk: self._set_duration(w, b, lb)
            )
            menu.addAction(action)

        btn_pos = self._icon_btn.mapToGlobal(
            QPoint(self._icon_btn.width() // 2, self._icon_btn.height() + 4)
        )
        menu.exec(btn_pos)

    def _set_duration(self, work: int, brk: int, long_brk: int):
        self._pomodoro.set_durations(work, brk, long_brk)
        if self._pomodoro.running:
            self._pomodoro.reset()
            _refresh_icon(self._toggle_btn, _ic_play, color=self._color)
            self._toggle_btn.setObjectName("")
            self._toggle_btn.style().unpolish(self._toggle_btn)
            self._toggle_btn.style().polish(self._toggle_btn)

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def running(self) -> bool:
        return self._pomodoro.running

    def refresh_icons(self, color: QColor):
        self._color = color
        _refresh_icon(self._icon_btn,   _ic_timer, color=color)
        _refresh_icon(self._reset_btn,  _ic_reset, color=color)
        fn = _ic_pause if self._pomodoro.running else _ic_play
        _refresh_icon(self._toggle_btn, fn,        color=color)
