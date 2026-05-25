from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from modules.whatsapp_feed import WhatsAppFeedModule
from ui.icons import _icon_btn, _refresh_icon, _ic_whatsapp


class WhatsAppWidget(QWidget):
    open_popup = pyqtSignal()

    def __init__(self, whatsapp: WhatsAppFeedModule, parent=None):
        super().__init__(parent)
        self.setProperty("class", "section")
        self._whatsapp = whatsapp
        self._status = 'disconnected'
        self._build_ui()
        
        self._whatsapp.updated.connect(self._on_updated)
        self._whatsapp.status_changed.connect(self._on_status_changed)

    def _build_ui(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(4, 0, 4, 0)
        h.setSpacing(4)

        self.btn = _icon_btn(_ic_whatsapp)
        self.btn.setToolTip("WhatsApp")
        h.addWidget(self.btn)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("font-weight: bold; color: #25D366; font-size: 10px;")
        h.addWidget(self.count_lbl)

        self.btn.clicked.connect(self.open_popup.emit)

    def _on_status_changed(self, status):
        self._status = status
        if status == 'ready':
            self.btn.setToolTip("WhatsApp Conectado")
        elif status == 'qr_ready':
            self.btn.setToolTip("WhatsApp - Escanear QR Code")
            self.count_lbl.setText("!")
        else:
            self.btn.setToolTip(f"WhatsApp - {status}")
            self.count_lbl.setText("")

    def _on_updated(self, messages):
        count = len(messages)
        self.count_lbl.setText(str(count) if count > 0 else "")

    def refresh_icons(self, color: QColor):
        _refresh_icon(self.btn, _ic_whatsapp, color=color)
