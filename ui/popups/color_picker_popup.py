import pyperclip
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor, QScreen, QColor


class ColorPickerPopup(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._screenshot = None

    def start(self):
        # Capture all screens
        screen = QApplication.primaryScreen()
        self._screenshot = screen.grabWindow(0)
        self.setGeometry(screen.geometry())
        self.showFullScreen()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            color = QColor(self._screenshot.toImage().pixelColor(pos))
            hex_color = color.name().upper()
            pyperclip.copy(hex_color)
            self.hide()
        elif event.button() == Qt.MouseButton.RightButton:
            self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()

    def paintEvent(self, event):
        # We don't really need to paint the screenshot if we just want the color,
        # but showing it helps the user know they are in picker mode.
        from PyQt6.QtGui import QPainter
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._screenshot)
        # Add a slight dimming or overlay if desired
        painter.fillRect(self.rect(), QColor(0, 0, 0, 30))
        painter.end()
