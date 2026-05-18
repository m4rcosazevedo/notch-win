"""
Painel de configurações do Notch Win.
Aparece como popup abaixo da barra quando acionado.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QFileDialog, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QCursor


# ── Toggle switch customizado ─────────────────────────────────────────────────

class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    _ON_TRACK  = QColor(48, 209, 88)
    _OFF_TRACK = QColor(58, 58, 62)
    _THUMB     = QColor(255, 255, 255)

    def __init__(self, checked: bool = True, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 26)
        self._checked = checked
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, val: bool, emit: bool = False):
        if self._checked != val:
            self._checked = val
            self.update()
            if emit:
                self.toggled.emit(val)

    def mousePressEvent(self, _):
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._ON_TRACK if self._checked else self._OFF_TRACK))
        p.drawRoundedRect(0, 3, 44, 20, 10, 10)
        p.setBrush(QBrush(self._THUMB))
        x = 24 if self._checked else 2
        p.drawEllipse(x, 5, 16, 16)
        p.end()

    def set_light_mode(self, is_light: bool):
        self._OFF_TRACK = QColor(190, 190, 195) if is_light else QColor(58, 58, 62)
        self.update()


# ── Settings Window ───────────────────────────────────────────────────────────

class SettingsWindow(QWidget):
    section_toggled = pyqtSignal(str, bool)   # key, visible
    youtube_connect = pyqtSignal(str)          # path to client_secrets.json
    youtube_refresh = pyqtSignal()

    _SECTIONS = [
        ("spotify",   "🎵  Spotify"),
        ("pomodoro",  "⏱  Pomodoro"),
        ("clipboard", "⊞  Clipboard"),
        ("youtube",   "▶  YouTube"),
        ("calc",      "⊟  Calculadora"),
        ("notes",     "✎  Notas"),
        ("alarm",     "⏰  Despertador"),
        ("quotes",    "❝  Motivação"),
        ("todo",      "☑  Tarefas"),
        ("photos",    "🖼  Fotos"),
        ("hcalc",     "⏱  Cal. Horas"),
        ("pokemon",   "⬟  Pokémon"),
        ("stress",    "💢  Anti-Stress"),
    ]

    def __init__(self, sections: dict, yt_status: str = "Não conectado", parent=None):
        super().__init__(parent,
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._sections_state = sections
        self._toggles: dict[str, ToggleSwitch] = {}
        self._secrets_path = ""
        self._build_ui(yt_status)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self, yt_status: str):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame()
        self._card.setObjectName("settings-card")
        self._card.setMinimumWidth(320)
        self._card.setMaximumHeight(540)

        card_v = QVBoxLayout(self._card)
        card_v.setContentsMargins(0, 0, 0, 0)
        card_v.setSpacing(0)

        card_v.addWidget(self._mk_header())

        # Scrollable content area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content.setObjectName("settings-content")
        cv = QVBoxLayout(content)
        cv.setContentsMargins(0, 10, 0, 14)
        cv.setSpacing(0)

        cv.addWidget(self._mk_group_label("Seções visíveis"), 0, Qt.AlignmentFlag.AlignLeft)
        cv.addSpacing(2)
        cv.addWidget(self._mk_sections_block())
        cv.addSpacing(14)
        cv.addWidget(self._mk_group_label("YouTube"), 0, Qt.AlignmentFlag.AlignLeft)
        cv.addSpacing(6)
        cv.addWidget(self._mk_youtube_block(yt_status))
        cv.addStretch()

        self._scroll.setWidget(content)
        card_v.addWidget(self._scroll)

        outer.addWidget(self._card)

    def _mk_header(self) -> QWidget:
        hdr = QFrame()
        hdr.setObjectName("settings-header")
        h = QHBoxLayout(hdr)
        h.setContentsMargins(16, 12, 12, 12)

        title = QLabel("⚙  Configurações")
        title.setObjectName("settings-title")

        close = QPushButton("✕")
        close.setObjectName("settings-close-btn")
        close.setFixedSize(22, 22)
        close.clicked.connect(self.close)

        h.addWidget(title)
        h.addStretch()
        h.addWidget(close)
        return hdr

    def _mk_group_label(self, text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setObjectName("settings-group-lbl")
        lbl.setContentsMargins(16, 0, 16, 0)
        return lbl

    def _mk_sections_block(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 0, 16, 0)
        v.setSpacing(0)

        for key, label in self._SECTIONS:
            checked = self._sections_state.get(key, True)
            v.addWidget(self._mk_toggle_row(label, key, checked))
            sep = QFrame()
            sep.setObjectName("settings-row-sep")
            sep.setFrameShape(QFrame.Shape.HLine)
            v.addWidget(sep)

        # Remove last separator
        if v.count() > 0:
            item = v.takeAt(v.count() - 1)
            if item.widget():
                item.widget().deleteLater()
        return w

    def _mk_toggle_row(self, label: str, key: str, checked: bool) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 8, 0, 8)

        lbl = QLabel(label)
        lbl.setObjectName("settings-row-lbl")

        toggle = ToggleSwitch(checked)
        toggle.toggled.connect(lambda val, k=key: self.section_toggled.emit(k, val))
        self._toggles[key] = toggle

        h.addWidget(lbl)
        h.addStretch()
        h.addWidget(toggle)
        return row

    def _mk_youtube_block(self, yt_status: str) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 0, 16, 0)
        v.setSpacing(6)

        # Status atual
        self._yt_status_lbl = QLabel(yt_status)
        self._yt_status_lbl.setObjectName("settings-yt-status")
        v.addWidget(self._yt_status_lbl)

        # ── Passo 1 ──────────────────────────────────────────────────────────
        self._add_yt_step(v, "1", "Crie um projeto no Google Cloud e ative a YouTube Data API v3:")
        link = QLabel(
            '<a href="https://console.cloud.google.com/apis/library/youtube.googleapis.com">'
            'Abrir Google Cloud Console ↗</a>'
        )
        link.setObjectName("settings-link")
        link.setOpenExternalLinks(True)
        link.setContentsMargins(26, 0, 0, 0)
        v.addWidget(link)

        # ── Passo 2 ──────────────────────────────────────────────────────────
        self._add_yt_step(v, "2",
            'No Console, vá em "APIs e Serviços" → "Credenciais" → '
            '"Criar credencial" → "ID do cliente OAuth 2.0" → '
            'tipo "App para computador". Clique em baixar (⬇) e salve o arquivo JSON.')
        file_row = QWidget()
        fh = QHBoxLayout(file_row)
        fh.setContentsMargins(26, 2, 0, 0)
        fh.setSpacing(8)
        self._secrets_lbl = QLabel("Nenhum arquivo selecionado")
        self._secrets_lbl.setObjectName("settings-file-lbl")
        pick = QPushButton("Escolher arquivo")
        pick.setObjectName("settings-sm-btn")
        pick.setFixedHeight(26)
        pick.clicked.connect(self._pick_secrets)
        fh.addWidget(self._secrets_lbl, 1)
        fh.addWidget(pick, 0)
        v.addWidget(file_row)

        # ── Passo 3 ──────────────────────────────────────────────────────────
        self._add_yt_step(v, "3",
            "Clique em Conectar — o browser abrirá para você fazer login e "
            "autorizar o acesso à sua conta Google.")
        conn = QPushButton("Conectar ao YouTube")
        conn.setObjectName("settings-primary-btn")
        conn.clicked.connect(self._on_connect)
        v.addWidget(conn)

        ref = QPushButton("Atualizar Feed")
        ref.setObjectName("settings-secondary-btn")
        ref.clicked.connect(self.youtube_refresh.emit)
        v.addWidget(ref)

        return w

    def _add_yt_step(self, layout: QVBoxLayout, num: str, text: str):
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 6, 0, 0)
        h.setSpacing(8)
        h.setAlignment(Qt.AlignmentFlag.AlignTop)

        badge = QLabel(num)
        badge.setObjectName("settings-step-badge")
        badge.setFixedSize(18, 18)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc = QLabel(text)
        desc.setObjectName("settings-step-lbl")
        desc.setWordWrap(True)

        h.addWidget(badge)
        h.addWidget(desc, 1)
        layout.addWidget(row)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _pick_secrets(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar arquivo de credenciais",
            str(Path.home()), "JSON (*.json)"
        )
        if path:
            self._secrets_path = path
            self._secrets_lbl.setText(Path(path).name)

    def _on_connect(self):
        self.youtube_connect.emit(self._secrets_path)

    # ── Public API ────────────────────────────────────────────────────────────

    def update_yt_status(self, msg: str):
        self._yt_status_lbl.setText(msg)

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light   = mode == "light"
        text       = "#1c1c1e"             if is_light else "#e5e5ea"
        muted      = "rgba(0,0,0,0.45)"   if is_light else "rgba(255,255,255,0.40)"
        row_sep    = "rgba(0,0,0,0.07)"   if is_light else "rgba(255,255,255,0.07)"
        sm_bg      = "rgba(0,0,0,0.07)"   if is_light else "rgba(255,255,255,0.09)"
        sm_hover   = "rgba(0,0,0,0.12)"   if is_light else "rgba(255,255,255,0.16)"
        close_h    = "rgba(255,80,80,0.15)"
        link_color = "#0055cc"             if is_light else "#0a84ff"
        scroll_h   = "rgba(0,0,0,0.15)"   if is_light else "rgba(255,255,255,0.15)"

        for t in self._toggles.values():
            t.set_light_mode(is_light)

        self._card.setStyleSheet(f"""
            QFrame#settings-card {{
                background-color: {bg};
                border-radius: 16px;
                border: 1px solid {border};
            }}
            QFrame#settings-header {{
                background: transparent;
                border-bottom: 1px solid {row_sep};
            }}
            QLabel#settings-title {{
                color: {text};
                font-size: 13px;
                font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                background: transparent;
            }}
            QPushButton#settings-close-btn {{
                color: {muted};
                background: transparent;
                border: none;
                border-radius: 11px;
                font-size: 12px;
                min-width:22px; max-width:22px;
                min-height:22px; max-height:22px;
                padding:0px;
            }}
            QPushButton#settings-close-btn:hover {{
                background: {close_h};
                color: #ff453a;
            }}
            QLabel#settings-group-lbl {{
                color: {muted};
                font-size: 10px;
                font-weight: 700;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                letter-spacing: 0.8px;
                background: transparent;
            }}
            QLabel#settings-row-lbl {{
                color: {text};
                font-size: 12px;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                background: transparent;
            }}
            QFrame#settings-row-sep {{
                color: {row_sep};
                max-height: 1px;
            }}
            QLabel#settings-yt-status {{
                color: {muted};
                font-size: 11px;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                background: transparent;
            }}
            QLabel#settings-step-badge {{
                background: #0a84ff;
                color: #ffffff;
                border-radius: 9px;
                font-size: 10px;
                font-weight: 700;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
            }}
            QLabel#settings-step-lbl {{
                color: {text};
                font-size: 11px;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                background: transparent;
            }}
            QLabel#settings-file-lbl {{
                color: {muted};
                font-size: 10px;
                font-family: "Consolas","Cascadia Code",monospace;
                background: transparent;
            }}
            QLabel#settings-link {{
                color: {link_color};
                font-size: 11px;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                background: transparent;
            }}
            QPushButton#settings-sm-btn {{
                background: {sm_bg};
                color: {text};
                border: none;
                border-radius: 7px;
                font-size: 11px;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                padding: 0px 10px;
            }}
            QPushButton#settings-sm-btn:hover {{ background: {sm_hover}; }}
            QPushButton#settings-primary-btn {{
                background: #0a84ff;
                color: #ffffff;
                border: none;
                border-radius: 9px;
                font-size: 12px;
                font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                padding: 7px 14px;
                text-align: left;
            }}
            QPushButton#settings-primary-btn:hover {{ background: #0070e0; }}
            QPushButton#settings-secondary-btn {{
                background: {sm_bg};
                color: {text};
                border: none;
                border-radius: 9px;
                font-size: 12px;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                padding: 7px 14px;
                text-align: left;
            }}
            QPushButton#settings-secondary-btn:hover {{ background: {sm_hover}; }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QWidget#settings-content {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 4px;
                margin: 4px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {scroll_h};
                border-radius: 2px;
                min-height: 16px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
