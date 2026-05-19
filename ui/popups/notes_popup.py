from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import QTimer

from config import NOTES_PATH
from ui.popups.base_popup import BasePopup


class NotesPopup(BasePopup):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._save_timer = QTimer(singleShot=True)
        self._save_timer.timeout.connect(self._save)
        self._build_ui()
        self._load()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._card = QFrame(); self._card.setObjectName("notes-card")
        self._card.setFixedWidth(320)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("notes-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        ttl = QLabel("✎  Notas"); ttl.setObjectName("notes-title")
        cls = QPushButton("✕"); cls.setObjectName("notes-close")
        cls.setFixedSize(22, 22); cls.clicked.connect(self.hide)
        hh.addWidget(ttl); hh.addStretch(); hh.addWidget(cls)
        v.addWidget(hdr)

        self._editor = QTextEdit()
        self._editor.setObjectName("notes-editor")
        self._editor.setPlaceholderText("Escreva seus lembretes aqui…")
        self._editor.setFixedHeight(300)
        self._editor.textChanged.connect(lambda: self._save_timer.start(800))
        v.addWidget(self._editor)
        outer.addWidget(self._card)

    def _save(self):
        NOTES_PATH.write_text(self._editor.toPlainText(), encoding="utf-8")

    def _load(self):
        if NOTES_PATH.exists():
            self._editor.blockSignals(True)
            self._editor.setPlainText(NOTES_PATH.read_text(encoding="utf-8"))
            self._editor.blockSignals(False)

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light = mode == "light"
        text  = "#1c1c1e"              if is_light else "#e5e5ea"
        muted = "rgba(0,0,0,0.45)"    if is_light else "rgba(255,255,255,0.40)"
        sep   = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.07)"
        ed_bg = "rgba(0,0,0,0.03)"    if is_light else "rgba(0,0,0,0.25)"
        self._card.setStyleSheet(f"""
            QFrame#notes-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#notes-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#notes-title {{
                color:{text}; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QPushButton#notes-close {{
                color:{muted}; background:transparent; border:none; border-radius:11px;
                font-size:12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#notes-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QTextEdit#notes-editor {{
                background:{ed_bg}; color:{text}; border:none; font-size:12px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; padding:10px 14px;
                border-bottom-left-radius:16px; border-bottom-right-radius:16px;
            }}
        """)
