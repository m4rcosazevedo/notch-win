from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtGui import QColor

from ui.icons import _icon_btn, _refresh_icon


class ToolWidget(QWidget):
    """Single-button notch section. Wraps one icon button with standard margins."""

    def __init__(self, icon_fn, tooltip: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "section")
        self._icon_fn = icon_fn

        h = QHBoxLayout(self)
        h.setContentsMargins(4, 0, 4, 0)
        h.setSpacing(6)

        self.btn = _icon_btn(icon_fn)
        if tooltip:
            self.btn.setToolTip(tooltip)
        h.addWidget(self.btn)

    def refresh_icons(self, color: QColor):
        _refresh_icon(self.btn, self._icon_fn, color=color)
