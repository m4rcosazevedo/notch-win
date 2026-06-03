from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.popups.base_popup import BasePopup


class WeatherPopup(BasePopup):
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame()
        self._card.setObjectName("weather-card")
        self._card.setFixedWidth(320)

        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        v.addWidget(self._mk_header())
        v.addWidget(self._mk_body())
        v.addWidget(self._mk_sep())
        v.addWidget(self._mk_section_header("PRÓXIMAS HORAS"))

        self._hourly_frame = QWidget()
        self._hourly_frame.setObjectName("weather-forecast-row")
        hf = QHBoxLayout(self._hourly_frame)
        hf.setContentsMargins(14, 4, 14, 10)
        hf.setSpacing(0)
        v.addWidget(self._hourly_frame)

        v.addWidget(self._mk_sep())
        v.addWidget(self._mk_section_header("PRÓXIMOS DIAS"))

        self._daily_frame = QWidget()
        self._daily_frame.setObjectName("weather-forecast-row")
        df = QHBoxLayout(self._daily_frame)
        df.setContentsMargins(14, 4, 14, 10)
        df.setSpacing(0)
        v.addWidget(self._daily_frame)

        outer.addWidget(self._card)
        self._show_empty()

    def _mk_header(self) -> QFrame:
        hdr = QFrame()
        hdr.setObjectName("weather-header")
        hh = QHBoxLayout(hdr)
        hh.setContentsMargins(14, 10, 10, 10)

        ttl = QLabel("🌤  Clima")
        ttl.setObjectName("weather-title")

        self._city_lbl = QLabel("")
        self._city_lbl.setObjectName("weather-city")

        ref = QPushButton("↺")
        ref.setObjectName("weather-action-btn")
        ref.setFixedSize(22, 22)
        ref.clicked.connect(self.refresh_requested.emit)
        self._refresh_btn = ref

        cls = QPushButton("✕")
        cls.setObjectName("weather-close")
        cls.setFixedSize(22, 22)
        cls.clicked.connect(self.hide)

        hh.addWidget(ttl)
        hh.addStretch()
        hh.addWidget(self._city_lbl)
        hh.addSpacing(6)
        hh.addWidget(ref)
        hh.addWidget(cls)
        return hdr

    def _mk_body(self) -> QWidget:
        body = QWidget()
        body.setObjectName("weather-body")
        bv = QVBoxLayout(body)
        bv.setContentsMargins(18, 16, 18, 12)
        bv.setSpacing(2)

        # Big emoji + temperature
        big = QWidget()
        br  = QHBoxLayout(big)
        br.setContentsMargins(0, 0, 0, 0)
        br.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._emoji_lbl = QLabel("🌤")
        self._emoji_lbl.setObjectName("weather-emoji")
        self._temp_lbl = QLabel("--°C")
        self._temp_lbl.setObjectName("weather-temp")
        br.addWidget(self._emoji_lbl)
        br.addSpacing(10)
        br.addWidget(self._temp_lbl)
        bv.addWidget(big)
        bv.addSpacing(4)

        self._desc_lbl = QLabel("--")
        self._desc_lbl.setObjectName("weather-desc")
        self._desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv.addWidget(self._desc_lbl)

        self._feels_lbl = QLabel("")
        self._feels_lbl.setObjectName("weather-sub")
        self._feels_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv.addWidget(self._feels_lbl)
        bv.addSpacing(10)

        info = QWidget()
        ir   = QHBoxLayout(info)
        ir.setContentsMargins(0, 0, 0, 0)
        ir.setSpacing(0)
        self._hum_lbl  = QLabel("")
        self._wind_lbl = QLabel("")
        for lbl in (self._hum_lbl, self._wind_lbl):
            lbl.setObjectName("weather-info")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ir.addWidget(lbl, 1)
        bv.addWidget(info)
        return body

    def _mk_sep(self) -> QFrame:
        sep = QFrame()
        sep.setObjectName("weather-sep")
        sep.setFrameShape(QFrame.Shape.HLine)
        return sep

    def _mk_section_header(self, text: str) -> QFrame:
        hdr = QFrame()
        hdr.setObjectName("weather-section-hdr")
        h   = QHBoxLayout(hdr)
        h.setContentsMargins(14, 8, 14, 2)
        lbl = QLabel(text)
        lbl.setObjectName("weather-section-title")
        h.addWidget(lbl)
        return hdr

    def _show_empty(self):
        self._city_lbl.setText("")
        self._emoji_lbl.setText("🌤")
        self._temp_lbl.setText("--°C")
        self._desc_lbl.setText("Configure a cidade nas Configurações")
        self._feels_lbl.setText("")
        self._hum_lbl.setText("")
        self._wind_lbl.setText("")

    def update_weather(self, data: dict):
        self._city_lbl.setText(f"{data['city']} · {data['country']}")
        self._emoji_lbl.setText(data["emoji"])
        self._temp_lbl.setText(f"{data['temp']}°C")
        self._desc_lbl.setText(data["desc"])
        self._feels_lbl.setText(f"Sensação: {data['feels_like']}°C")
        self._hum_lbl.setText(f"💧 {data['humidity']}%")
        self._wind_lbl.setText(f"💨 {data['wind']} km/h")
        self._fill_forecast(self._hourly_frame.layout(), data["hourly"], self._mk_hourly_col)
        self._fill_forecast(self._daily_frame.layout(),  data["daily"],  self._mk_daily_col)
        self.adjustSize()

    def _fill_forecast(self, layout, items, mk_col):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for entry in items:
            layout.addWidget(mk_col(entry), 1)

    def _mk_hourly_col(self, h: dict) -> QWidget:
        return self._mk_forecast_col(h["hour"], h["emoji"], f"{h['temp']}°", "weather-hr-lbl", "weather-hr-temp")

    def _mk_daily_col(self, d: dict) -> QWidget:
        return self._mk_forecast_col(d["day"], d["emoji"], f"{d['max']}°/{d['min']}°", "weather-dy-lbl", "weather-dy-temp")

    def _mk_forecast_col(self, top: str, emoji: str, bottom: str, top_obj: str, bot_obj: str) -> QWidget:
        col = QWidget()
        cv  = QVBoxLayout(col)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(1)
        cv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for text, obj_name in ((top, top_obj), (emoji, "weather-fc-emoji"), (bottom, bot_obj)):
            lbl = QLabel(text)
            lbl.setObjectName(obj_name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cv.addWidget(lbl)
        return col

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light = mode == "light"
        text     = "#1c1c1e"            if is_light else "#e5e5ea"
        muted    = "rgba(0,0,0,0.45)"  if is_light else "rgba(255,255,255,0.40)"
        sub      = "rgba(0,0,0,0.55)"  if is_light else "rgba(255,255,255,0.55)"
        sep      = "rgba(0,0,0,0.07)"  if is_light else "rgba(255,255,255,0.07)"

        self._card.setStyleSheet(f"""
            QFrame#weather-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#weather-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#weather-title {{
                color:{text}; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QLabel#weather-city {{
                color:{muted}; font-size:11px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QPushButton#weather-action-btn, QPushButton#weather-close {{
                color:{muted}; background:transparent; border:none; border-radius:11px;
                font-size:12px;
                min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#weather-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QPushButton#weather-action-btn:hover {{ background:rgba(255,255,255,0.10); }}
            QWidget#weather-body {{ background:transparent; }}
            QLabel#weather-emoji {{ font-size:36px; background:transparent; }}
            QLabel#weather-temp {{
                color:{text}; font-size:32px; font-weight:300;
                font-family:"SF Pro Display","Segoe UI",sans-serif; background:transparent;
            }}
            QLabel#weather-desc {{
                color:{text}; font-size:13px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QLabel#weather-sub {{
                color:{muted}; font-size:11px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QLabel#weather-info {{
                color:{sub}; font-size:12px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QFrame#weather-sep {{ color:{sep}; max-height:1px; }}
            QFrame#weather-section-hdr {{ background:transparent; }}
            QLabel#weather-section-title {{
                color:{muted}; font-size:10px; font-weight:700;
                font-family:"SF Pro Text","Segoe UI",sans-serif;
                letter-spacing:0.8px; background:transparent;
            }}
            QWidget#weather-forecast-row {{ background:transparent; }}
            QLabel#weather-hr-lbl, QLabel#weather-dy-lbl {{
                color:{muted}; font-size:10px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QLabel#weather-fc-emoji {{ font-size:16px; background:transparent; }}
            QLabel#weather-hr-temp {{
                color:{text}; font-size:11px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QLabel#weather-dy-temp {{
                color:{text}; font-size:10px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
        """)
