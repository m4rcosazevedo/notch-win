from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QScrollArea, QLineEdit, QStackedWidget,
    QButtonGroup,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QCursor, QClipboard, QGuiApplication


# ── Toggle switch ─────────────────────────────────────────────────────────────

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
        p.drawEllipse(24 if self._checked else 2, 5, 16, 16)
        p.end()

    def set_light_mode(self, is_light: bool):
        self._OFF_TRACK = QColor(190, 190, 195) if is_light else QColor(58, 58, 62)
        self.update()


# ── Settings Window ───────────────────────────────────────────────────────────

class SettingsWindow(QWidget):
    section_toggled   = pyqtSignal(str, bool)
    youtube_connect   = pyqtSignal(str)
    youtube_refresh   = pyqtSignal()
    spotify_configure = pyqtSignal(str, str)   # client_id, client_secret

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

    def __init__(self, sections: dict, parent=None):
        super().__init__(parent,
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._sections_state = sections
        self._toggles: dict[str, ToggleSwitch] = {}
        self._secrets_path = ""
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame()
        self._card.setObjectName("settings-card")
        self._card.setFixedWidth(360)
        self._card.setMaximumHeight(560)

        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        v.addWidget(self._mk_header())
        v.addWidget(self._mk_tab_bar())
        v.addWidget(self._mk_tab_line())

        self._stack = QStackedWidget()
        self._stack.addWidget(self._mk_sections_page())
        self._stack.addWidget(self._mk_youtube_page())
        self._stack.addWidget(self._mk_spotify_page())
        v.addWidget(self._stack)

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

    def _mk_tab_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("settings-tab-bar")
        h = QHBoxLayout(bar)
        h.setContentsMargins(12, 10, 12, 0)
        h.setSpacing(4)

        self._tab_btns: dict[str, QPushButton] = {}
        group = QButtonGroup(self)
        group.setExclusive(True)

        for idx, (key, label) in enumerate([
            ("sections", "Seções"),
            ("youtube",  "YouTube"),
            ("spotify",  "Spotify"),
        ]):
            btn = QPushButton(label)
            btn.setObjectName("settings-tab-btn")
            btn.setCheckable(True)
            btn.setChecked(idx == 0)
            btn.clicked.connect(lambda _, k=key, i=idx: self._switch_tab(k, i))
            group.addButton(btn)
            self._tab_btns[key] = btn
            h.addWidget(btn)

        h.addStretch()
        return bar

    def _mk_tab_line(self) -> QFrame:
        line = QFrame()
        line.setObjectName("settings-tab-line")
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        return line

    def _switch_tab(self, key: str, idx: int):
        self._stack.setCurrentIndex(idx)

    # ── Seções page ───────────────────────────────────────────────────────────

    def _mk_sections_page(self) -> QScrollArea:
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sa.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        sa.setFrameShape(QFrame.Shape.NoFrame)
        sa.setObjectName("settings-scroll")

        content = QWidget()
        content.setObjectName("settings-content")
        cv = QVBoxLayout(content)
        cv.setContentsMargins(0, 10, 0, 14)
        cv.setSpacing(0)
        cv.addWidget(self._mk_group_label("Seções visíveis"), 0, Qt.AlignmentFlag.AlignLeft)
        cv.addSpacing(4)
        cv.addWidget(self._mk_sections_block())
        cv.addStretch()

        sa.setWidget(content)
        return sa

    # ── YouTube page ──────────────────────────────────────────────────────────

    def _mk_youtube_page(self) -> QScrollArea:
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sa.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        sa.setFrameShape(QFrame.Shape.NoFrame)
        sa.setObjectName("settings-scroll")

        content = QWidget()
        content.setObjectName("settings-content")
        cv = QVBoxLayout(content)
        cv.setContentsMargins(0, 10, 0, 14)
        cv.setSpacing(0)
        cv.addWidget(self._mk_group_label("YouTube Data API"), 0, Qt.AlignmentFlag.AlignLeft)
        cv.addSpacing(6)
        cv.addWidget(self._mk_youtube_block())
        cv.addStretch()

        sa.setWidget(content)
        return sa

    # ── Spotify page ──────────────────────────────────────────────────────────

    def _mk_spotify_page(self) -> QScrollArea:
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sa.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        sa.setFrameShape(QFrame.Shape.NoFrame)
        sa.setObjectName("settings-scroll")

        content = QWidget()
        content.setObjectName("settings-content")
        cv = QVBoxLayout(content)
        cv.setContentsMargins(0, 10, 0, 14)
        cv.setSpacing(0)
        cv.addWidget(self._mk_group_label("Spotify for Developers"), 0, Qt.AlignmentFlag.AlignLeft)
        cv.addSpacing(6)
        cv.addWidget(self._mk_spotify_block())
        cv.addStretch()

        sa.setWidget(content)
        return sa

    # ── Shared block builders ─────────────────────────────────────────────────

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

    def _mk_youtube_block(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 0, 16, 0)
        v.setSpacing(6)

        self._yt_status_lbl = QLabel("Não conectado")
        self._yt_status_lbl.setObjectName("settings-status-lbl")
        v.addWidget(self._yt_status_lbl)

        self._add_step(v, "1", "Crie um projeto no Google Cloud e ative a YouTube Data API v3:")
        link = QLabel(
            '<a href="https://console.cloud.google.com/apis/library/youtube.googleapis.com">'
            'Abrir Google Cloud Console ↗</a>'
        )
        link.setObjectName("settings-link")
        link.setOpenExternalLinks(True)
        link.setContentsMargins(26, 0, 0, 0)
        v.addWidget(link)

        self._add_step(v, "2",
            'Em "Credenciais" → "Criar credencial" → "ID do cliente OAuth 2.0" → '
            '"App para computador". Baixe o JSON.')
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

        self._add_step(v, "3",
            "Clique em Conectar — o browser abrirá para autorizar o acesso.")
        conn = QPushButton("▶  Conectar ao YouTube")
        conn.setObjectName("settings-primary-btn")
        conn.clicked.connect(self._on_yt_connect)
        v.addWidget(conn)

        ref = QPushButton("↺  Atualizar Feed")
        ref.setObjectName("settings-secondary-btn")
        ref.clicked.connect(self.youtube_refresh.emit)
        v.addWidget(ref)

        return w

    def _mk_spotify_block(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(16, 0, 16, 0)
        v.setSpacing(6)

        self._sp_status_lbl = QLabel("Não configurado")
        self._sp_status_lbl.setObjectName("settings-status-lbl")
        v.addWidget(self._sp_status_lbl)

        self._add_step(v, "1", "Crie um app no Spotify for Developers:")
        link = QLabel('<a href="https://developer.spotify.com/dashboard">Abrir Dashboard ↗</a>')
        link.setObjectName("settings-link")
        link.setOpenExternalLinks(True)
        link.setContentsMargins(26, 0, 0, 0)
        v.addWidget(link)

        redirect_row = QWidget()
        rh = QHBoxLayout(redirect_row)
        rh.setContentsMargins(26, 2, 0, 0)
        rh.setSpacing(6)
        redirect_lbl = QLabel("http://127.0.0.1:8888/callback")
        redirect_lbl.setObjectName("settings-code-lbl")
        copy_btn = QPushButton("Copiar")
        copy_btn.setObjectName("settings-sm-btn")
        copy_btn.setFixedHeight(24)
        copy_btn.clicked.connect(lambda: QGuiApplication.clipboard().setText("http://127.0.0.1:8888/callback"))
        rh.addWidget(redirect_lbl, 1)
        rh.addWidget(copy_btn)
        v.addWidget(redirect_row)

        self._add_step(v, "2", 'Cole as credenciais do app criado (aba "Settings"):')

        for attr, label, secret in [
            ("_sp_id_edit",     "Client ID",     False),
            ("_sp_secret_edit", "Client Secret", True),
        ]:
            field_row = QWidget()
            fh = QHBoxLayout(field_row)
            fh.setContentsMargins(26, 2, 0, 2)
            fh.setSpacing(6)
            lbl = QLabel(label)
            lbl.setObjectName("settings-field-lbl")
            lbl.setFixedWidth(90)
            edit = QLineEdit()
            edit.setObjectName("settings-field-edit")
            edit.setEchoMode(QLineEdit.EchoMode.Password if secret else QLineEdit.EchoMode.Normal)
            setattr(self, attr, edit)
            fh.addWidget(lbl)
            fh.addWidget(edit, 1)
            if secret:
                eye = QPushButton("👁")
                eye.setObjectName("settings-sm-btn")
                eye.setFixedSize(26, 26)
                eye.clicked.connect(lambda _, e=edit: e.setEchoMode(
                    QLineEdit.EchoMode.Normal
                    if e.echoMode() == QLineEdit.EchoMode.Password
                    else QLineEdit.EchoMode.Password
                ))
                fh.addWidget(eye)
            v.addWidget(field_row)

        self._add_step(v, "3", "Clique em Conectar — o browser abrirá para autorizar:")
        conn_btn = QPushButton("🎵  Conectar ao Spotify")
        conn_btn.setObjectName("settings-primary-btn")
        conn_btn.clicked.connect(self._on_sp_connect)
        v.addWidget(conn_btn)

        return w

    def _add_step(self, layout: QVBoxLayout, num: str, text: str):
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
            self, "Selecionar credenciais", str(Path.home()), "JSON (*.json)"
        )
        if path:
            self._secrets_path = path
            self._secrets_lbl.setText(Path(path).name)

    def _on_yt_connect(self):
        self.youtube_connect.emit(self._secrets_path)

    def _on_sp_connect(self):
        cid = self._sp_id_edit.text().strip()
        cs  = self._sp_secret_edit.text().strip()
        if cid and cs:
            self.spotify_configure.emit(cid, cs)

    # ── Public API ────────────────────────────────────────────────────────────

    def update_yt_status(self, msg: str):
        self._yt_status_lbl.setText(msg)

    def update_spotify_status(self, msg: str):
        self._sp_status_lbl.setText(msg)

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light  = mode == "light"
        text      = "#1c1c1e"            if is_light else "#e5e5ea"
        muted     = "rgba(0,0,0,0.45)"  if is_light else "rgba(255,255,255,0.40)"
        row_sep   = "rgba(0,0,0,0.07)"  if is_light else "rgba(255,255,255,0.07)"
        sm_bg     = "rgba(0,0,0,0.06)"  if is_light else "rgba(255,255,255,0.08)"
        sm_hover  = "rgba(0,0,0,0.12)"  if is_light else "rgba(255,255,255,0.16)"
        tab_active= "rgba(0,0,0,0.08)"  if is_light else "rgba(255,255,255,0.10)"
        inp_bg    = "rgba(0,0,0,0.05)"  if is_light else "rgba(255,255,255,0.07)"
        inp_brd   = "rgba(0,0,0,0.12)"  if is_light else "rgba(255,255,255,0.14)"
        link_col  = "#0055cc"           if is_light else "#0a84ff"
        scroll_h  = "rgba(0,0,0,0.15)"  if is_light else "rgba(255,255,255,0.15)"

        for t in self._toggles.values():
            t.set_light_mode(is_light)

        self._card.setStyleSheet(f"""
            QFrame#settings-card {{
                background: {bg};
                border-radius: 16px;
                border: 1px solid {border};
            }}
            QFrame#settings-header {{
                background: transparent;
                border-bottom: 1px solid {row_sep};
            }}
            QLabel#settings-title {{
                color: {text}; font-size: 13px; font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QPushButton#settings-close-btn {{
                color: {muted}; background: transparent; border: none;
                border-radius: 11px; font-size: 12px;
                min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#settings-close-btn:hover {{ background: rgba(255,80,80,0.15); color: #ff453a; }}

            QWidget#settings-tab-bar {{ background: transparent; }}
            QPushButton#settings-tab-btn {{
                background: transparent; color: {muted}; border: none;
                border-radius: 8px; font-size: 12px; font-weight: 500;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                padding: 5px 14px;
            }}
            QPushButton#settings-tab-btn:checked {{
                background: {tab_active}; color: {text}; font-weight: 600;
            }}
            QPushButton#settings-tab-btn:hover:!checked {{ background: {sm_bg}; }}
            QFrame#settings-tab-line {{ color: {row_sep}; }}

            QScrollArea#settings-scroll {{ background: transparent; border: none; }}
            QWidget#settings-content   {{ background: transparent; }}

            QLabel#settings-group-lbl {{
                color: {muted}; font-size: 10px; font-weight: 700;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                letter-spacing: 0.8px; background: transparent;
            }}
            QLabel#settings-row-lbl {{
                color: {text}; font-size: 12px;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QFrame#settings-row-sep {{ color: {row_sep}; max-height: 1px; }}
            QLabel#settings-status-lbl {{
                color: {muted}; font-size: 11px;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QLabel#settings-step-badge {{
                background: #0a84ff; color: #fff; border-radius: 9px;
                font-size: 10px; font-weight: 700;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
            }}
            QLabel#settings-step-lbl {{
                color: {text}; font-size: 11px;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QLabel#settings-file-lbl {{
                color: {muted}; font-size: 10px;
                font-family: "Consolas","Cascadia Code",monospace; background: transparent;
            }}
            QLabel#settings-code-lbl {{
                color: {muted}; font-size: 10px;
                font-family: "Consolas","Cascadia Code",monospace; background: transparent;
            }}
            QLabel#settings-field-lbl {{
                color: {muted}; font-size: 11px;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QLabel#settings-link {{
                color: {link_col}; font-size: 11px;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QLineEdit#settings-field-edit {{
                background: {inp_bg}; color: {text}; border: 1px solid {inp_brd};
                border-radius: 7px; font-size: 12px;
                font-family: "Consolas","Cascadia Code",monospace;
                padding: 4px 8px; selection-background-color: #0a84ff;
            }}
            QLineEdit#settings-field-edit:focus {{ border: 1px solid rgba(10,132,255,0.55); }}
            QPushButton#settings-sm-btn {{
                background: {sm_bg}; color: {text}; border: none; border-radius: 7px;
                font-size: 11px; font-family: "SF Pro Text","Segoe UI",sans-serif;
                padding: 0px 10px;
            }}
            QPushButton#settings-sm-btn:hover {{ background: {sm_hover}; }}
            QPushButton#settings-primary-btn {{
                background: #0a84ff; color: #fff; border: none; border-radius: 9px;
                font-size: 12px; font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                padding: 8px 14px; margin-left: 26px;
            }}
            QPushButton#settings-primary-btn:hover {{ background: #0070e0; }}
            QPushButton#settings-secondary-btn {{
                background: {sm_bg}; color: {text}; border: none; border-radius: 9px;
                font-size: 12px; font-family: "SF Pro Text","Segoe UI",sans-serif;
                padding: 8px 14px; margin-left: 26px;
            }}
            QPushButton#settings-secondary-btn:hover {{ background: {sm_hover}; }}
            QScrollBar:vertical {{
                background: transparent; width: 4px; margin: 4px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {scroll_h}; border-radius: 2px; min-height: 16px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
