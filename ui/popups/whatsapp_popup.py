import base64
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QImage, QColor

from modules.whatsapp_feed import WhatsAppFeedModule
from ui.popups.base_popup import BasePopup, popup_show_at

class WhatsAppPopup(BasePopup):
    def __init__(self, whatsapp_module: WhatsAppFeedModule, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._whatsapp = whatsapp_module
        self._status = 'disconnected'
        self._build_ui()
        
        self._whatsapp.updated.connect(self._on_updated)
        self._whatsapp.qr_code_ready.connect(self._on_qr_ready)
        self._whatsapp.status_changed.connect(self._on_status_changed)

    def _build_ui(self):
        self.setObjectName("wa-popup-outer")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame()
        self._card.setObjectName("wa-card")
        self._card.setFixedWidth(360)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("wa-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(16, 12, 12, 12)
        title_lbl = QLabel("💬  WhatsApp"); title_lbl.setObjectName("wa-title")
        close_btn = QPushButton("✕"); close_btn.setObjectName("wa-close")
        close_btn.setFixedSize(24, 24); close_btn.clicked.connect(self.hide)
        hh.addWidget(title_lbl); hh.addStretch(); hh.addWidget(close_btn)
        v.addWidget(hdr)

        self._status_lbl = QLabel("Sincronizando...")
        self._status_lbl.setObjectName("wa-status")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self._status_lbl)

        self._qr_lbl = QLabel()
        self._qr_lbl.setObjectName("wa-qr")
        self._qr_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._qr_lbl.hide()
        v.addWidget(self._qr_lbl)

        self._scroll = QScrollArea()
        self._scroll.setObjectName("wa-scroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setFixedHeight(450)
        self._scroll.hide()

        self._list_widget = QWidget(); self._list_widget.setObjectName("wa-list")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 8)
        self._list_layout.setSpacing(0)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._list_widget)
        v.addWidget(self._scroll)
        
        outer.addWidget(self._card)

    def _on_status_changed(self, status):
        self._status = status
        if status == 'ready':
            self._status_lbl.hide(); self._qr_lbl.hide(); self._scroll.show()
            self._on_updated(self._whatsapp.messages)
        elif status == 'qr_ready':
            self._status_lbl.setText("Escaneie o QR Code:"); self._status_lbl.show()
            self._qr_lbl.show(); self._scroll.hide()
        else:
            self._status_lbl.setText("Carregando WhatsApp Web..."); self._status_lbl.show()
            self._qr_lbl.hide(); self._scroll.hide()

    def _on_qr_ready(self, qr_b64):
        qr_data = base64.b64decode(qr_b64)
        img = QImage.fromData(qr_data)
        pix = QPixmap.fromImage(img)
        self._qr_lbl.setPixmap(pix.scaled(260, 260, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _on_updated(self, messages):
        if self._status != 'ready': return
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        if not messages:
            lbl = QLabel("Buscando mensagens..."); lbl.setObjectName("wa-empty")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list_layout.insertWidget(0, lbl)
            return

        for i, m in enumerate(messages):
            self._list_layout.insertWidget(i * 2, self._make_row(m))
            if i < len(messages) - 1:
                sep = QFrame(); sep.setObjectName("wa-sep")
                sep.setFixedHeight(1)
                self._list_layout.insertWidget(i * 2 + 1, sep)

    def _make_row(self, m) -> QFrame:
        row = QFrame(); row.setObjectName("wa-row")
        h = QHBoxLayout(row); h.setContentsMargins(16, 12, 16, 12); h.setSpacing(12)
        info = QVBoxLayout(); info.setSpacing(3); info.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout(); top.setSpacing(4)
        sender_lbl = QLabel(m["sender"]); sender_lbl.setObjectName("wa-item-sender")
        if m.get("unread"): sender_lbl.setProperty("unread", True)
        time_lbl = QLabel(m["time"]); time_lbl.setObjectName("wa-item-time")
        top.addWidget(sender_lbl, 1); top.addWidget(time_lbl, 0)
        content_lbl = QLabel(m["content"]); content_lbl.setObjectName("wa-item-content")
        content_lbl.setWordWrap(False)
        if m.get("unread"): content_lbl.setProperty("unread", True)
        info.addLayout(top); info.addWidget(content_lbl)
        h.addLayout(info, 1)
        return row

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light = mode == "light"
        text_col  = "#000000" if is_light else "#f5f5f7"
        muted_col = "rgba(0,0,0,0.6)" if is_light else "rgba(255,255,255,0.5)"
        sep_col   = "rgba(0,0,0,0.1)" if is_light else "rgba(255,255,255,0.1)"
        hover_bg  = "rgba(0,0,0,0.05)" if is_light else "rgba(255,255,255,0.08)"
        
        self.setStyleSheet("background: transparent; border: none;")
        self._card.setStyleSheet(f"""
            QFrame#wa-card {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 16px;
            }}
            QFrame#wa-header {{
                border-bottom: 1px solid {sep_col};
                background: transparent;
            }}
            QLabel {{
                color: {text_col};
                font-family: "SF Pro Text", "Segoe UI", sans-serif;
                background: transparent;
            }}
            QLabel#wa-title {{
                font-weight: 700;
                font-size: 14px;
            }}
            QLabel#wa-status, QLabel#wa-empty {{
                color: {muted_col};
                padding: 40px;
                font-size: 13px;
            }}
            QFrame#wa-qr {{
                background: white;
                margin: 15px;
                padding: 10px;
                border-radius: 12px;
            }}
            QScrollArea {{
                background: transparent;
            }}
            QFrame#wa-row:hover {{
                background-color: {hover_bg};
            }}
            QLabel#wa-item-sender {{
                font-weight: 600;
                font-size: 13px;
            }}
            QLabel#wa-item-sender[unread="true"] {{
                color: #00a884;
                font-weight: 700;
            }}
            QLabel#wa-item-time {{
                color: {muted_col};
                font-size: 11px;
            }}
            QLabel#wa-item-content {{
                color: {muted_col};
                font-size: 12px;
            }}
            QLabel#wa-item-content[unread="true"] {{
                color: {text_col};
                font-weight: 600;
            }}
            QFrame#wa-sep {{
                background-color: {sep_col};
                margin-left: 16px;
                margin-right: 16px;
            }}
            QPushButton#wa-close {{
                background: transparent;
                border: none;
                color: {muted_col};
                font-size: 14px;
            }}
            QPushButton#wa-close:hover {{
                color: #ff453a;
                background: rgba(255, 69, 58, 0.1);
                border-radius: 12px;
            }}
        """)

    def show_at(self, pos: QPoint):
        self._on_updated(self._whatsapp.messages)
        popup_show_at(self, pos)
