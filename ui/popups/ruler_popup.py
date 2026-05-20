from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QColor, QPainter, QPen


class PixelRulerPopup(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(100, 40)
        self.resize(400, 60)
        self._drag_pos = None
        self._resizing = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        bg_color = QColor(20, 20, 20, 200)
        painter.setBrush(bg_color)
        painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
        painter.drawRoundedRect(self.rect().adjusted(1,1,-1,-1), 8, 8)

        # Ticks
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
        w = self.width()
        h = self.height()
        
        for x in range(0, w, 10):
            line_h = 5
            if x % 50 == 0:
                line_h = 12
                painter.drawText(x + 2, 25, str(x))
            if x % 100 == 0:
                line_h = 18
            
            painter.drawLine(x, h - line_h, x, h)

        # Label for current width
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{w}px")
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.pos().x() > self.width() - 20 and event.pos().y() > self.height() - 20:
                self._resizing = True
            else:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif event.button() == Qt.MouseButton.RightButton:
            self.hide()

    def mouseMoveEvent(self, event):
        if self._resizing:
            new_w = max(100, event.pos().x())
            new_h = max(40, event.pos().y())
            self.resize(new_w, new_h)
        elif self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resizing = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
