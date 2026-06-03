from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor

from modules.weather_feed import WeatherFeedModule
from ui.icons import _icon_btn, _refresh_icon, _ic_weather


class WeatherWidget(QWidget):
    open_popup = pyqtSignal()

    def __init__(self, module: WeatherFeedModule, parent=None):
        super().__init__(parent)
        self.setProperty("class", "section")
        self._build_ui()
        module.weather_updated.connect(self._on_updated)

    def _build_ui(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(4, 0, 4, 0)
        h.setSpacing(4)

        self.btn = _icon_btn(_ic_weather)
        self.btn.setToolTip("Previsão do Tempo")
        self.btn.clicked.connect(self.open_popup.emit)
        h.addWidget(self.btn)

        self._temp_lbl = QLabel("--°")
        self._temp_lbl.setObjectName("sys-label")
        h.addWidget(self._temp_lbl)

    def _on_updated(self, data: dict):
        self._temp_lbl.setText(f"{data['temp']}°")

    def refresh_icons(self, color: QColor):
        _refresh_icon(self.btn, _ic_weather, color=color)
