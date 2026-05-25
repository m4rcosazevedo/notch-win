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
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame(); self._card.setObjectName("wa-popup")
        self._card.setFixedWidth(350)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("wa-popup-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        title_lbl = QLabel("💬  WhatsApp"); title_lbl.setObjectName("wa-popup-title")
        close_btn = QPushButton("✕"); close_btn.setObjectName("wa-popup-close")
        close_btn.setFixedSize(22, 22); close_btn.clicked.connect(self.hide)
        hh.addWidget(title_lbl); hh.addStretch(); hh.addWidget(close_btn)
        v.addWidget(hdr)

        # Loading / Status Label
        self._status_lbl = QLabel("Iniciando WhatsApp...")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setStyleSheet("padding: 40px; color: #555;")
        v.addWidget(self._status_lbl)

        # QR Code Label
        self._qr_lbl = QLabel()
        self._qr_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._qr_lbl.setStyleSheet("padding: 20px; background: white; margin: 10px; border-radius: 10px;")
        self._qr_lbl.hide()
        v.addWidget(self._qr_lbl)

        # Lista de Mensagens
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setFixedHeight(400)
        self._scroll.hide()

        self._list_widget = QWidget(); self._list_widget.setObjectName("wa-list")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 4, 0, 4)
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
            self._status_lbl.setText("Carregando conversas..."); self._status_lbl.show()
            self._qr_lbl.hide(); self._scroll.hide()

    def _on_qr_ready(self, qr_b64):
        qr_data = base64.b64decode(qr_b64)
        img = QImage.fromData(qr_data)
        pix = QPixmap.fromImage(img)
        self._qr_lbl.setPixmap(pix.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))

    def _on_updated(self, messages):
        if self._status != 'ready': return
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        if not messages:
            lbl = QLabel("Buscando conversas..."); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("padding: 40px; color: #555;"); self._list_layout.insertWidget(0, lbl)
            return

        for i, m in enumerate(messages):
            self._list_layout.insertWidget(i * 2, self._make_row(m))
            if i < len(messages) - 1:
                sep = QFrame(); sep.setObjectName("wa-row-sep")
                sep.setFrameShape(QFrame.Shape.HLine)
                self._list_layout.insertWidget(i * 2 + 1, sep)

    def _make_row(self, m) -> QFrame:
        row = QFrame(); row.setObjectName("wa-row")
        h = QHBoxLayout(row); h.setContentsMargins(14, 10, 14, 10); h.setSpacing(12)
        info = QVBoxLayout(); info.setSpacing(2); info.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout(); top.setSpacing(4)
        
        sender_lbl = QLabel(m["sender"]); sender_lbl.setObjectName("wa-sender")
        
        # Bolinha verde para nao lidas (Bullet Verde)
        unread_indicator = ""
        if m.get("unread"):
            unread_indicator = " <span style='color: #00a884;'>●</span>"
            sender_lbl.setText(m["sender"] + " " + unread_indicator)
            sender_lbl.setStyleSheet("color: #00a884; font-weight: bold;")
        else:
            sender_lbl.setText(m["sender"])
        
        time_lbl = QLabel(m["time"]); time_lbl.setObjectName("wa-time")
        top.addWidget(sender_lbl, 1); top.addWidget(time_lbl, 0)
        
        content_lbl = QLabel(m["content"]); content_lbl.setObjectName("wa-content")
        content_lbl.setWordWrap(True)
        if m.get("unread"):
            content_lbl.setStyleSheet("font-weight: 500; color: #333;")
        
        info.addLayout(top); info.addWidget(content_lbl)
        h.addLayout(info, 1)
        return row

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light  = mode == "light"
        text_col  = "#000000" if is_light else "#e5e5ea"
        muted_col = "#444444" if is_light else "rgba(255,255,255,0.40)"
        sep_color = "rgba(0,0,0,0.1)" if is_light else "rgba(255,255,255,0.1)"
        hover_bg  = "rgba(0,0,0,0.05)" if is_light else "rgba(255,255,255,0.05)"

        self._card.setStyleSheet(f"""
            QFrame#wa-popup {{ background-color: {bg}; border-radius: 16px; border: 1px solid {border}; }}
            QLabel {{ color: {text_col}; font-family: "SF Pro Text", sans-serif; background: transparent; }}
            QLabel#wa-popup-title {{ font-weight: 700; font-size: 14px; }}
            QLabel#wa-sender {{ font-weight: 600; font-size: 13px; }}
            QLabel#wa-time {{ color: {muted_col}; font-size: 10px; }}
            QLabel#wa-content {{ color: {muted_col}; font-size: 12.5px; }}
            QFrame#wa-row:hover {{ background: {hover_bg}; border-radius: 8px; }}
            QFrame#wa-row-sep {{ color: {sep_color}; max-height: 1px; }}
            QPushButton#wa-popup-close {{ background: transparent; border: none; color: {muted_col}; }}
        """)

    def show_at(self, pos: QPoint):
        self._on_updated(self._whatsapp.messages)
        popup_show_at(self, pos)
