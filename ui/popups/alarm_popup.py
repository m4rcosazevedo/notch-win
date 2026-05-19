import datetime
import threading

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QWidget,
)
from PyQt6.QtCore import Qt, QTimer

from config import notify, _winsound, _WINSOUND_OK
from ui.popups.base_popup import BasePopup


class _SpinBox(QFrame):
    """Compact ± spinner fully styleable via QSS."""

    def __init__(self, lo: int, hi: int, val: int, parent=None):
        super().__init__(parent)
        self.setObjectName("alarm-spin-box")
        self._lo, self._hi, self._val = lo, hi, val
        h = QHBoxLayout(self); h.setContentsMargins(2, 2, 2, 2); h.setSpacing(0)

        self._btn_m = QPushButton("−"); self._btn_m.setObjectName("alarm-spin-side-btn")
        self._btn_m.setFixedSize(26, 30); self._btn_m.clicked.connect(self._dec)

        self._val_lbl = QLabel(f"{val:02d}"); self._val_lbl.setObjectName("alarm-spin-val")
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._val_lbl.setFixedWidth(34)

        self._btn_p = QPushButton("+"); self._btn_p.setObjectName("alarm-spin-side-btn")
        self._btn_p.setFixedSize(26, 30); self._btn_p.clicked.connect(self._inc)

        h.addWidget(self._btn_m); h.addWidget(self._val_lbl); h.addWidget(self._btn_p)

    def value(self) -> int:
        return self._val

    def setValue(self, v: int):
        self._val = self._lo if v > self._hi else (self._hi if v < self._lo else v)
        self._val_lbl.setText(f"{self._val:02d}")

    def _inc(self):
        self.setValue(self._lo if self._val >= self._hi else self._val + 1)

    def _dec(self):
        self.setValue(self._hi if self._val <= self._lo else self._val - 1)


class AlarmPopup(BasePopup):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._alarms: list[dict] = []
        self._build_ui()
        self._ticker = QTimer()
        self._ticker.timeout.connect(self._check)
        self._ticker.start(15_000)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._card = QFrame(); self._card.setObjectName("alarm-card")
        self._card.setFixedWidth(280)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("alarm-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        ttl = QLabel("⏰  Despertador"); ttl.setObjectName("alarm-title")
        cls = QPushButton("✕"); cls.setObjectName("alarm-close")
        cls.setFixedSize(22, 22); cls.clicked.connect(self.hide)
        hh.addWidget(ttl); hh.addStretch(); hh.addWidget(cls)
        v.addWidget(hdr)

        add_row = QWidget(); add_row.setObjectName("alarm-add-row")
        ah = QHBoxLayout(add_row); ah.setContentsMargins(14, 10, 14, 10); ah.setSpacing(6)
        self._spin_h = _SpinBox(0, 23, datetime.datetime.now().hour)
        colon = QLabel(":"); colon.setObjectName("alarm-colon")
        colon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spin_m = _SpinBox(0, 59, 0)
        add_btn = QPushButton("Adicionar"); add_btn.setObjectName("alarm-add-btn")
        add_btn.clicked.connect(self._add_alarm)
        ah.addWidget(self._spin_h); ah.addWidget(colon)
        ah.addWidget(self._spin_m); ah.addStretch(); ah.addWidget(add_btn)
        v.addWidget(add_row)

        self._list_widget = QWidget(); self._list_widget.setObjectName("alarm-list")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0); self._list_layout.setSpacing(0)
        v.addWidget(self._list_widget)
        outer.addWidget(self._card)

    def _add_alarm(self):
        h, m = self._spin_h.value(), self._spin_m.value()
        self._alarms.append({"h": h, "m": m, "fired_date": ""})
        self._alarms.sort(key=lambda a: (a["h"], a["m"]))
        self._refresh_list()

    def _refresh_list(self):
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self._alarms:
            empty = QLabel("Nenhum alarme definido"); empty.setObjectName("alarm-empty")
            empty.setContentsMargins(14, 10, 14, 10)
            self._list_layout.addWidget(empty)
            return
        for i, a in enumerate(self._alarms):
            row = QFrame(); row.setObjectName("alarm-item")
            rh = QHBoxLayout(row); rh.setContentsMargins(14, 8, 14, 8)
            lbl = QLabel(f"{a['h']:02d}:{a['m']:02d}"); lbl.setObjectName("alarm-item-time")
            rm = QPushButton("✕"); rm.setObjectName("alarm-rm-btn")
            rm.setFixedSize(20, 20); rm.clicked.connect(lambda _, ix=i: self._remove(ix))
            rh.addWidget(lbl); rh.addStretch(); rh.addWidget(rm)
            self._list_layout.addWidget(row)
        self.adjustSize()

    def _remove(self, idx: int):
        if 0 <= idx < len(self._alarms):
            del self._alarms[idx]
            self._refresh_list()

    def _check(self):
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        for a in self._alarms:
            if f"{a['h']:02d}:{a['m']:02d}" == time_str and a.get("fired_date") != today:
                a["fired_date"] = today
                self._fire(time_str)

    def _fire(self, time_str: str):
        notify("⏰ Despertador", f"Alarme das {time_str}!")
        if _WINSOUND_OK:
            threading.Thread(target=self._beep, daemon=True).start()

    @staticmethod
    def _beep():
        import time
        for _ in range(5):
            _winsound.Beep(880, 350)
            time.sleep(0.15)

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light = mode == "light"
        text   = "#1c1c1e"              if is_light else "#e5e5ea"
        muted  = "rgba(0,0,0,0.45)"    if is_light else "rgba(255,255,255,0.40)"
        sep    = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.07)"
        sm_hov = "rgba(0,0,0,0.12)"    if is_light else "rgba(255,255,255,0.14)"
        sp_bg  = "rgba(0,0,0,0.06)"    if is_light else "rgba(255,255,255,0.09)"
        sp_brd = "rgba(0,0,0,0.14)"    if is_light else "rgba(255,255,255,0.18)"
        self._card.setStyleSheet(f"""
            QFrame#alarm-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#alarm-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#alarm-title {{
                color:{text}; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QPushButton#alarm-close {{
                color:{muted}; background:transparent; border:none; border-radius:11px;
                font-size:12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#alarm-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QWidget#alarm-add-row {{ background:transparent; border-bottom:1px solid {sep}; }}
            QFrame#alarm-spin-box {{ background:{sp_bg}; border:1px solid {sp_brd}; border-radius:9px; }}
            QPushButton#alarm-spin-side-btn {{
                color:{text}; background:transparent; border:none; border-radius:5px;
                font-size:16px; font-weight:bold; font-family:"SF Pro Text","Segoe UI",sans-serif;
            }}
            QPushButton#alarm-spin-side-btn:hover {{ background:{sm_hov}; }}
            QLabel#alarm-spin-val {{
                color:{text}; font-size:17px; font-weight:700;
                font-family:"Consolas","Cascadia Code",monospace; background:transparent;
            }}
            QLabel#alarm-colon {{
                color:{text}; font-size:18px; font-weight:bold;
                font-family:"Segoe UI",sans-serif; background:transparent;
            }}
            QPushButton#alarm-add-btn {{
                background:#0a84ff; color:#fff; border:none; border-radius:8px;
                font-size:11px; font-family:"SF Pro Text","Segoe UI",sans-serif; padding:5px 12px;
            }}
            QPushButton#alarm-add-btn:hover {{ background:#0070e0; }}
            QWidget#alarm-list {{ background:transparent; }}
            QFrame#alarm-item {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#alarm-item-time {{
                color:{text}; font-size:18px; font-weight:700;
                font-family:"Consolas","Cascadia Code",monospace; background:transparent;
            }}
            QPushButton#alarm-rm-btn {{
                color:{muted}; background:transparent; border:none; border-radius:10px; font-size:11px;
            }}
            QPushButton#alarm-rm-btn:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QLabel#alarm-empty {{
                color:{muted}; font-size:12px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
        """)
        self._refresh_list()

    def show_at(self, pos):
        self._refresh_list()
        super().show_at(pos)
