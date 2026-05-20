from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QScrollArea, QApplication,
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor

from modules.clipboard import ClipboardModule


class ClipboardPopup(QWidget):
    def __init__(self, clip_module: ClipboardModule, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._clip = clip_module
        self._build_ui()
        self._clip.history_changed.connect(self._refresh)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame()
        self._card.setObjectName("clip-popup")
        self._card.setFixedWidth(360)
        self._card.setMinimumHeight(200)

        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("clip-popup-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        title = QLabel("⊞  Histórico"); title.setObjectName("clip-popup-title")
        close_btn = QPushButton("✕"); close_btn.setObjectName("clip-popup-close")
        close_btn.setFixedSize(22, 22); close_btn.clicked.connect(self.close)
        hh.addWidget(title); hh.addStretch(); hh.addWidget(close_btn)
        v.addWidget(hdr)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setMaximumHeight(430)

        self._items_widget = QWidget(); self._items_widget.setObjectName("clip-items")
        self._list_layout = QVBoxLayout(self._items_widget)
        self._list_layout.setContentsMargins(0, 4, 0, 4)
        self._list_layout.setSpacing(0)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._items_widget)
        v.addWidget(self._scroll)

        self._clear_btn = QPushButton("Limpar histórico")
        self._clear_btn.setObjectName("clip-clear-btn")
        self._clear_btn.setFixedHeight(32)
        self._clear_btn.clicked.connect(self._clip.clear)
        v.addWidget(self._clear_btn)

        outer.addWidget(self._card)

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light  = mode == "light"
        text      = "#1c1c1e"              if is_light else "#e5e5ea"
        muted     = "rgba(0,0,0,0.45)"    if is_light else "rgba(255,255,255,0.40)"
        sep_color = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.07)"
        hover_bg  = "rgba(0,0,0,0.04)"    if is_light else "rgba(255,255,255,0.05)"
        close_h   = "rgba(255,80,80,0.15)"
        clear_color = "#880000"            if is_light else "rgba(255,80,80,0.70)"
        clear_hover = "#550000"            if is_light else "#ff453a"
        scroll_h  = "rgba(0,0,0,0.15)"    if is_light else "rgba(255,255,255,0.15)"

        self._card.setStyleSheet(f"""
            QFrame#clip-popup {{
                background-color: {bg}; border-radius: 16px; border: 1px solid {border};
            }}
            QFrame#clip-popup-header {{
                background: transparent; border-bottom: 1px solid {sep_color};
            }}
            QLabel#clip-popup-title {{
                color: {text}; font-size: 13px; font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QPushButton#clip-popup-close {{
                color: {muted}; background: transparent; border: none; border-radius: 11px;
                font-size: 12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#clip-popup-close:hover {{ background: {close_h}; color: #ff453a; }}
            QScrollArea {{ background: transparent; border: none; }}
            QWidget#clip-items {{ background: transparent; }}
            QFrame#clip-item-row {{ background: transparent; border: none; }}
            QFrame#clip-item-row:hover {{ background: {hover_bg}; border-radius: 8px; }}
            QLabel#clip-item-lbl {{
                color: {text}; font-size: 12px;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QLabel#clip-empty {{
                color: {muted}; font-size: 12px;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QFrame#clip-row-sep {{ color: {sep_color}; max-height: 1px; }}
            QPushButton#clip-clear-btn {{
                color: {clear_color}; font-size: 11px;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                border-top: 1px solid {sep_color};
                border-bottom-left-radius: 16px; border-bottom-right-radius: 16px;
                border-top-left-radius: 0px; border-top-right-radius: 0px;
                background: transparent; min-width: 0px; max-width: 32767px;
            }}
            QPushButton#clip-clear-btn:hover {{ color: {clear_hover}; background: {hover_bg}; }}
            QScrollBar:vertical {{ background: transparent; width: 4px; margin: 3px 1px; }}
            QScrollBar::handle:vertical {{
                background: {scroll_h}; border-radius: 2px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

    def _make_item_row(self, text: str, index: int) -> QFrame:
        row = QFrame(); row.setObjectName("clip-item-row")
        row.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        h = QHBoxLayout(row); h.setContentsMargins(14, 8, 14, 8)
        lbl = QLabel(self._clip.preview(text)); lbl.setObjectName("clip-item-lbl")
        lbl.setToolTip(text[:300])
        h.addWidget(lbl)
        row.mousePressEvent = lambda _, ix=index: self._copy(ix)
        return row

    def _refresh(self):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        history = self._clip.get_history()
        if not history:
            lbl = QLabel("Nada copiado ainda"); lbl.setObjectName("clip-empty")
            lbl.setContentsMargins(14, 12, 14, 12)
            self._list_layout.insertWidget(0, lbl)
            return
        for i, text in enumerate(history):
            self._list_layout.insertWidget(i * 2, self._make_item_row(text, i))
            if i < len(history) - 1:
                sep = QFrame(); sep.setObjectName("clip-row-sep")
                sep.setFrameShape(QFrame.Shape.HLine)
                self._list_layout.insertWidget(i * 2 + 1, sep)

    def _copy(self, index: int):
        self._clip.copy(index)
        self.hide()

    def show_at(self, pos: QPoint):
        self._refresh()
        self.adjustSize()
        screen = QApplication.primaryScreen().geometry()
        x = pos.x() - self.width() // 2
        x = max(0, min(x, screen.width() - self.width()))
        self.move(x, pos.y())
        self.show()
