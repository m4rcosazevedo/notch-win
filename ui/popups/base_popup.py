from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint


class BasePopup(QWidget):
    """Base for all Tool-style floating popups.

    Subclasses implement ``_build_ui()`` and ``apply_theme(bg, border, mode)``.
    ``show_at`` is provided here — override only when custom positioning is needed.
    """

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def apply_theme(self, bg: str, border: str, mode: str):
        pass

    def show_at(self, pos: QPoint):
        popup_show_at(self, pos)


def popup_show_at(popup: QWidget, pos: QPoint):
    """Center the popup horizontally on *pos*, keep within screen bounds, toggle visibility."""
    popup.adjustSize()
    screen = QApplication.primaryScreen().geometry()
    x = max(0, min(pos.x() - popup.width() // 2, screen.width() - popup.width()))
    popup.move(x, pos.y())
    if popup.isVisible():
        popup.hide()
    else:
        popup.show()
        popup.raise_()
