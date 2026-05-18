from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from modules.clipboard import ClipboardModule
from ui.icons import _icon_btn, _refresh_icon, _DEFAULT_DARK, _ic_clip_open


class ClipboardWidget(QWidget):
    open_popup = pyqtSignal()

    def __init__(self, clipboard: ClipboardModule, parent=None):
        super().__init__(parent)
        self.setProperty("class", "section")
        self._clipboard = clipboard
        self._color: QColor = _DEFAULT_DARK
        self._build_ui()
        self._connect()

    def _build_ui(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(4, 0, 4, 0)
        h.setSpacing(6)

        self._icon_lbl = QLabel("⊞")
        self._icon_lbl.setFixedWidth(16)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet("font-size:15px; color: rgba(255,255,255,0.45);")

        self._count_lbl = QLabel("0")
        self._count_lbl.setObjectName("clip-count")
        self._count_lbl.setFixedWidth(18)

        self.clip_btn = _icon_btn(_ic_clip_open)

        h.addWidget(self._icon_lbl)
        h.addWidget(self._count_lbl)
        h.addWidget(self.clip_btn)

    def _connect(self):
        self._clipboard.history_changed.connect(
            lambda: self._count_lbl.setText(str(self._clipboard.count()))
        )
        self.clip_btn.clicked.connect(self.open_popup)

    def refresh_icons(self, color: QColor):
        self._color = color
        _refresh_icon(self.clip_btn, _ic_clip_open, color=color)

    def update_label_color(self, mode: str):
        color = "rgba(0,0,0,0.40)" if mode == "light" else "rgba(255,255,255,0.45)"
        self._icon_lbl.setStyleSheet(f"font-size:15px; color: {color};")
