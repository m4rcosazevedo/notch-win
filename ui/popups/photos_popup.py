from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QFileDialog,
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QCursor, QPixmap, QColor, QPainter, QPen


class PhotoSlideshow(QWidget):
    _W, _H = 140, 180

    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._photos: list[Path] = []
        self._idx = 0
        self._drag_pos: QPoint | None = None
        self._playing = True

        self._timer = QTimer()
        self._timer.timeout.connect(self._next)
        self._timer.start(5_000)

        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)

        self._card = QFrame(); self._card.setObjectName("slide-card")
        self._card.setFixedSize(self._W + 2, self._H + 30)
        cv = QVBoxLayout(self._card)
        cv.setContentsMargins(1, 1, 1, 0); cv.setSpacing(0)

        self._img_lbl = QLabel()
        self._img_lbl.setObjectName("slide-img")
        self._img_lbl.setFixedSize(self._W, self._H)
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self._set_placeholder()
        cv.addWidget(self._img_lbl)

        ctrl = QFrame(); ctrl.setObjectName("slide-ctrl")
        ch = QHBoxLayout(ctrl); ch.setContentsMargins(4, 2, 4, 2); ch.setSpacing(2)

        def _btn(text, slot):
            b = QPushButton(text); b.setObjectName("slide-btn")
            b.setFixedSize(24, 22); b.clicked.connect(slot)
            return b

        ch.addWidget(_btn("←", self._prev))
        ch.addWidget(_btn("▶", self._toggle_play))
        ch.addWidget(_btn("→", self._next))
        ch.addStretch()
        ch.addWidget(_btn("📁", self._pick_folder))
        ch.addWidget(_btn("✕", self.hide))
        cv.addWidget(ctrl)
        outer.addWidget(self._card)

        self._card.setStyleSheet("""
            QFrame#slide-card {
                background: rgba(20,20,22,220); border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.12);
            }
            QLabel#slide-img {
                border-top-left-radius: 11px; border-top-right-radius: 11px;
                background: rgba(0,0,0,0.4);
            }
            QFrame#slide-ctrl {
                background: transparent; border-top: 1px solid rgba(255,255,255,0.08);
            }
            QPushButton#slide-btn {
                background: transparent; color: rgba(255,255,255,0.65);
                border: none; border-radius: 5px; font-size: 11px;
            }
            QPushButton#slide-btn:hover { background: rgba(255,255,255,0.10); color: #fff; }
        """)

    def _set_placeholder(self):
        px = QPixmap(self._W, self._H)
        px.fill(QColor(30, 30, 34))
        p = QPainter(px)
        p.setPen(QPen(QColor(80, 80, 88), 1))
        p.setFont(self._img_lbl.font())
        p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "📁  Escolha uma pasta")
        p.end()
        self._img_lbl.setPixmap(px)

    def set_folder(self, folder: str):
        exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
        self._photos = sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in exts)
        self._idx = 0
        self._show_current()

    def _show_current(self):
        if not self._photos:
            return
        path = self._photos[self._idx % len(self._photos)]
        px = QPixmap(str(path))
        if px.isNull():
            return
        px = px.scaled(self._W, self._H, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                       Qt.TransformationMode.SmoothTransformation)
        if px.width() > self._W:
            px = px.copy((px.width() - self._W) // 2, 0, self._W, self._H)
        if px.height() > self._H:
            px = px.copy(0, (px.height() - self._H) // 2, self._W, self._H)
        self._img_lbl.setPixmap(px)

    def _next(self):
        if not self._photos:
            return
        self._idx = (self._idx + 1) % len(self._photos)
        self._show_current()

    def _prev(self):
        if not self._photos:
            return
        self._idx = (self._idx - 1) % len(self._photos)
        self._show_current()

    def _toggle_play(self):
        self._playing = not self._playing
        if self._playing:
            self._timer.start(5_000)
        else:
            self._timer.stop()

    def _pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Escolher pasta de fotos")
        if folder:
            self.set_folder(folder)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None
