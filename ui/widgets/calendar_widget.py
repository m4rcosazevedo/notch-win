from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from modules.calendar_feed import CalendarFeedModule
from ui.icons import _icon_btn, _refresh_icon, _ic_calendar, _ic_refresh_action


class CalendarWidget(QWidget):
    open_popup = pyqtSignal()

    def __init__(self, cal: CalendarFeedModule, parent=None):
        super().__init__(parent)
        self.setProperty("class", "section")
        self._cal = cal
        self._build_ui()

    def _build_ui(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(4, 0, 4, 0)
        h.setSpacing(6)

        self.btn = _icon_btn(_ic_calendar)
        self.btn.setToolTip("Calendário")
        h.addWidget(self.btn)

        self.btn.clicked.connect(self.open_popup.emit)

    def refresh_icons(self, color: QColor):
        _refresh_icon(self.btn, _ic_calendar, color=color)
