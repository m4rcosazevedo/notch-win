import json
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QFrame, QMenu, QSystemTrayIcon,
)
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QAction, QCursor, QPixmap, QPainter, QColor, QBrush, QIcon

from modules.pomodoro import PomodoroModule
from modules.clipboard import ClipboardModule
from ui.pomodoro_widget import PomodoroWidget
from ui.clipboard_widget import ClipboardWidget
from modules.spotify import SpotifyModule
from ui.spotify_widget import SpotifyWidget
from modules.youtube_feed import YouTubeFeedModule
from ui.settings_window import SettingsWindow

from ui.popups.clipboard_popup import ClipboardPopup
from ui.popups.youtube_popup import YouTubePopup
from ui.popups.notes_popup import NotesPopup
from ui.popups.alarm_popup import AlarmPopup
from ui.popups.quotes_popup import QuotesPopup
from ui.popups.todo_popup import TodoPopup
from ui.popups.photos_popup import PhotoSlideshow
from ui.popups.hcalc_popup import HoursCalcPopup
from ui.popups.pokemon_popup import PokemonPopup
from ui.popups.stress_popup import StressPopup

from ui.widgets.tool_widget import ToolWidget
from ui.icons import (
    _DEFAULT_DARK, _refresh_icon,
    _ic_youtube, _ic_calc, _ic_notes, _ic_alarm, _ic_quotes,
    _ic_todo, _ic_photo, _ic_hcalc, _ic_pokemon, _ic_stress,
)

from config import COLOR_PRESETS, MENU_QSS, QSS_PATH, SETTINGS_PATH


class NotchWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._sections_state: dict[str, bool] = {
            "spotify": True, "pomodoro": True, "clipboard": True, "youtube": True,
            "calc": True, "notes": True, "alarm": True, "quotes": True,
            "todo": True, "photos": True, "hcalc": True, "pokemon": True, "stress": True,
        }
        self._current_color = "space-gray"
        self._current_mode  = "dark"
        self._icon_color    = _DEFAULT_DARK
        self._yt_status     = "Não conectado"
        self._drag_pos: QPoint | None = None

        self._pomo_w    = PomodoroWidget()
        self._clipboard = ClipboardModule()
        self._clip_w    = ClipboardWidget(self._clipboard)
        self._spotify   = SpotifyModule()
        self._spotify_w = SpotifyWidget(self._spotify)
        self._yt_module = YouTubeFeedModule()

        self._clip_popup    = ClipboardPopup(self._clipboard)
        self._yt_popup      = YouTubePopup(self._yt_module)
        self._notes_popup   = NotesPopup()
        self._alarm_popup   = AlarmPopup()
        self._quotes_popup  = QuotesPopup()
        self._todo_popup    = TodoPopup()
        self._slideshow     = PhotoSlideshow()
        self._hcalc_popup   = HoursCalcPopup()
        self._pokemon_popup = PokemonPopup()
        self._stress_popup  = StressPopup()
        self._settings_win  = SettingsWindow(self._sections_state)

        self._build_ui()
        self._connect_signals()
        self._load_styles()
        self._load_settings()
        self._position_top_center()
        self._setup_tray()

        self._yt_module.start_polling()

        self._is_slid_out = False
        self._setup_autohide()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._pill = QFrame()
        self._pill.setObjectName("pill")
        self._pill.setFixedHeight(44)

        row = QHBoxLayout(self._pill)
        row.setContentsMargins(16, 0, 16, 0)
        row.setSpacing(6)

        self._yt_w      = ToolWidget(_ic_youtube, "YouTube Feed")
        self._calc_w    = ToolWidget(_ic_calc,    "Calculadora")
        self._notes_w   = ToolWidget(_ic_notes,   "Notas")
        self._alarm_w   = ToolWidget(_ic_alarm,   "Despertador")
        self._quotes_w  = ToolWidget(_ic_quotes,  "Motivação")
        self._todo_w    = ToolWidget(_ic_todo,     "Tarefas")
        self._photos_w  = ToolWidget(_ic_photo,   "Fotos")
        self._hcalc_w   = ToolWidget(_ic_hcalc,   "Calculadora de Horas")
        self._pokemon_w = ToolWidget(_ic_pokemon,  "Pokémon Aleatório")
        self._stress_w  = ToolWidget(_ic_stress,   "Zona Anti-Stress")

        sep1  = self._vline(); sep2  = self._vline(); sep3  = self._vline()
        sep4  = self._vline(); sep5  = self._vline(); sep6  = self._vline()
        sep7  = self._vline(); sep8  = self._vline(); sep9  = self._vline()
        sep10 = self._vline(); sep11 = self._vline(); sep12 = self._vline()

        for w in (
            self._spotify_w, sep1, self._pomo_w, sep2, self._clip_w, sep3,
            self._yt_w,      sep4, self._calc_w,   sep5, self._notes_w,  sep6,
            self._alarm_w,   sep7, self._quotes_w, sep8, self._todo_w,   sep9,
            self._photos_w, sep10, self._hcalc_w, sep11, self._pokemon_w, sep12,
            self._stress_w,
        ):
            row.addWidget(w)

        self._section_info: dict[str, tuple] = {
            "spotify":   (self._spotify_w,  None),
            "pomodoro":  (self._pomo_w,     sep1),
            "clipboard": (self._clip_w,     sep2),
            "youtube":   (self._yt_w,       sep3),
            "calc":      (self._calc_w,     sep4),
            "notes":     (self._notes_w,    sep5),
            "alarm":     (self._alarm_w,    sep6),
            "quotes":    (self._quotes_w,   sep7),
            "todo":      (self._todo_w,     sep8),
            "photos":    (self._photos_w,   sep9),
            "hcalc":     (self._hcalc_w,   sep10),
            "pokemon":   (self._pokemon_w, sep11),
            "stress":    (self._stress_w,  sep12),
        }

        root.addWidget(self._pill)

    def _vline(self) -> QFrame:
        line = QFrame()
        line.setObjectName("separator")
        line.setFrameShape(QFrame.Shape.VLine)
        return line

    # ── Signals ───────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self._clip_w.open_popup.connect(self._show_clipboard)

        self._yt_module.status_changed.connect(self._on_yt_status)
        self._yt_module.error.connect(lambda msg: self._on_yt_status(f"Erro: {msg[:50]}"))
        self._yt_w.btn.clicked.connect(self._show_youtube)

        self._calc_w.btn.clicked.connect(self._open_calc)
        self._notes_w.btn.clicked.connect(self._show_notes)
        self._alarm_w.btn.clicked.connect(self._show_alarm)
        self._quotes_w.btn.clicked.connect(self._show_quotes)
        self._todo_w.btn.clicked.connect(self._show_todo)
        self._photos_w.btn.clicked.connect(self._toggle_slideshow)
        self._hcalc_w.btn.clicked.connect(self._show_hcalc)
        self._pokemon_w.btn.clicked.connect(self._show_pokemon)
        self._stress_w.btn.clicked.connect(self._show_stress)

        self._settings_win.section_toggled.connect(self._on_section_toggled)
        self._settings_win.youtube_connect.connect(self._on_yt_connect)
        self._settings_win.youtube_refresh.connect(self._yt_module.refresh)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _show_clipboard(self):
        btn = self._clip_w.clip_btn
        pos = btn.mapToGlobal(QPoint(0, btn.height() + 6))
        self._clip_popup.show_at(pos)

    def _show_youtube(self):
        btn = self._yt_w.btn
        pos = btn.mapToGlobal(QPoint(btn.width() // 2, btn.height() + 6))
        self._yt_popup.show_at(pos)

    def _open_calc(self):
        try:
            subprocess.Popen(["calc.exe"])
        except FileNotFoundError:
            subprocess.Popen(["gnome-calculator"], stderr=subprocess.DEVNULL)

    def _show_notes(self):
        btn = self._notes_w.btn
        pos = btn.mapToGlobal(QPoint(btn.width() // 2, btn.height() + 6))
        self._notes_popup.show_at(pos)

    def _show_alarm(self):
        btn = self._alarm_w.btn
        pos = btn.mapToGlobal(QPoint(btn.width() // 2, btn.height() + 6))
        self._alarm_popup.show_at(pos)

    def _show_quotes(self):
        btn = self._quotes_w.btn
        pos = btn.mapToGlobal(QPoint(btn.width() // 2, btn.height() + 6))
        self._quotes_popup.show_at(pos)

    def _show_todo(self):
        btn = self._todo_w.btn
        pos = btn.mapToGlobal(QPoint(btn.width() // 2, btn.height() + 6))
        self._todo_popup.show_at(pos)

    def _toggle_slideshow(self):
        if self._slideshow.isVisible():
            self._slideshow.hide()
            return
        btn = self._photos_w.btn
        pos = btn.mapToGlobal(QPoint(0, btn.height() + 6))
        self._slideshow.move(pos)
        self._slideshow.show()
        self._slideshow.raise_()

    def _show_hcalc(self):
        btn = self._hcalc_w.btn
        pos = btn.mapToGlobal(QPoint(btn.width() // 2, btn.height() + 6))
        self._hcalc_popup.show_at(pos)

    def _show_pokemon(self):
        btn = self._pokemon_w.btn
        pos = btn.mapToGlobal(QPoint(btn.width() // 2, btn.height() + 6))
        if self._pokemon_popup.isVisible():
            self._pokemon_popup.hide()
            return
        self._pokemon_popup.show_at(pos)
        self._pokemon_popup.fetch_random()

    def _show_stress(self):
        btn = self._stress_w.btn
        pos = btn.mapToGlobal(QPoint(btn.width() // 2, btn.height() + 6))
        if self._stress_popup.isVisible():
            self._stress_popup.hide()
            return
        self._stress_popup._start_game()
        self._stress_popup.show_at(pos)

    def _show_settings(self):
        if self._settings_win.isVisible():
            self._settings_win.hide()
            return
        preset = next((p for p in COLOR_PRESETS if p[0] == self._current_color), COLOR_PRESETS[0])
        self._settings_win.update_yt_status(self._yt_status)
        self._settings_win.apply_theme(preset[2], preset[3], preset[5])
        screen = QApplication.primaryScreen().geometry()
        self._settings_win.adjustSize()
        sw = self._settings_win.width()
        pill_geo = self.geometry()
        x = max(0, min(pill_geo.center().x() - sw // 2, screen.width() - sw))
        self._settings_win.move(x, pill_geo.bottom() + 8)
        self._settings_win.show()
        self._settings_win.raise_()
        self._settings_win.activateWindow()

    def _on_yt_status(self, msg: str):
        self._yt_status = msg
        self._settings_win.update_yt_status(msg)

    def _on_yt_connect(self, secrets_path: str):
        if secrets_path:
            self._yt_module.set_secrets_path(secrets_path)
        self._yt_module.authenticate()

    def _on_section_toggled(self, key: str, visible: bool):
        self._sections_state[key] = visible
        self._update_separators()
        self._save_settings()

    # ── Section visibility ────────────────────────────────────────────────────

    def _update_separators(self):
        order = [
            "spotify", "pomodoro", "clipboard", "youtube",
            "calc", "notes", "alarm", "quotes", "todo", "photos",
            "hcalc", "pokemon", "stress",
        ]
        seen_visible = False
        for key in order:
            w, sep = self._section_info[key]
            visible = self._sections_state.get(key, True)
            w.setVisible(visible)
            if sep is not None:
                sep.setVisible(visible and seen_visible)
            if visible:
                seen_visible = True
        self._position_top_center()

    # ── Theming ───────────────────────────────────────────────────────────────

    def _load_settings(self):
        if SETTINGS_PATH.exists():
            try:
                data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                self._current_color = data.get("color", "space-gray")
                for k, v in data.get("sections", {}).items():
                    if k in self._sections_state:
                        self._sections_state[k] = v
            except Exception:
                pass
        for key, val in self._sections_state.items():
            if key in self._settings_win._toggles:
                self._settings_win._toggles[key].setChecked(val)
        preset = next((p for p in COLOR_PRESETS if p[0] == self._current_color), COLOR_PRESETS[0])
        self._apply_color(*preset, save=False)
        self._update_separators()

    def _save_settings(self):
        SETTINGS_PATH.write_text(
            json.dumps({"color": self._current_color, "sections": self._sections_state}),
            encoding="utf-8",
        )

    def _apply_color(self, key, _label, bg, border, _accent, mode, icon_rgba, save=True):
        self._current_color = key
        self._current_mode  = mode

        self._pill.setStyleSheet(f"""
            QFrame#pill {{
                background-color: {bg};
                border-top-left-radius:     0px;
                border-top-right-radius:    0px;
                border-bottom-left-radius:  20px;
                border-bottom-right-radius: 20px;
                border-left:   1px solid {border};
                border-right:  1px solid {border};
                border-bottom: 1px solid {border};
                border-top: none;
            }}
        """)

        self.setProperty("mode", mode)
        qss = self.styleSheet()
        self.setStyleSheet("")
        self.setStyleSheet(qss)

        r, g, b, a = icon_rgba
        self._icon_color = QColor(r, g, b, a)
        self._refresh_all_icons()

        for popup in (
            self._clip_popup, self._yt_popup, self._notes_popup,
            self._alarm_popup, self._quotes_popup, self._todo_popup,
            self._hcalc_popup, self._pokemon_popup, self._stress_popup,
            self._settings_win,
        ):
            popup.apply_theme(bg, border, mode)

        self._clip_w.update_label_color(mode)

        if save:
            self._save_settings()

    def _refresh_all_icons(self):
        c = self._icon_color
        self._pomo_w.refresh_icons(c)
        self._clip_w.refresh_icons(c)
        self._spotify_w.refresh_icons(c, is_playing=self._pomo_w.running)
        for w in (
            self._yt_w, self._calc_w, self._notes_w, self._alarm_w,
            self._quotes_w, self._todo_w, self._photos_w, self._hcalc_w,
            self._pokemon_w, self._stress_w,
        ):
            w.refresh_icons(c)

    # ── Context menu ──────────────────────────────────────────────────────────

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(MENU_QSS)

        hdr = QAction("🎨  Cor da barra", self)
        hdr.setEnabled(False)
        menu.addAction(hdr)

        dark_hdr = QAction("   ── Dark ──", self)
        dark_hdr.setEnabled(False)
        menu.addAction(dark_hdr)
        for key, label, bg, border, accent, mode, icon_rgba in COLOR_PRESETS:
            if mode != "dark":
                continue
            mark = "✓  " if key == self._current_color else "    "
            action = QAction(f"{mark}{label}", self)
            action.triggered.connect(
                lambda _, k=key, lb=label, bg_=bg, bd=border, ac=accent, md=mode, ic=icon_rgba:
                    self._apply_color(k, lb, bg_, bd, ac, md, ic)
            )
            menu.addAction(action)

        menu.addSeparator()
        light_hdr = QAction("   ── Light ──", self)
        light_hdr.setEnabled(False)
        menu.addAction(light_hdr)
        for key, label, bg, border, accent, mode, icon_rgba in COLOR_PRESETS:
            if mode != "light":
                continue
            mark = "✓  " if key == self._current_color else "    "
            action = QAction(f"{mark}{label}", self)
            action.triggered.connect(
                lambda _, k=key, lb=label, bg_=bg, bd=border, ac=accent, md=mode, ic=icon_rgba:
                    self._apply_color(k, lb, bg_, bd, ac, md, ic)
            )
            menu.addAction(action)

        menu.addSeparator()
        settings_a = QAction("⚙  Configurações", self)
        settings_a.triggered.connect(self._show_settings)
        menu.addAction(settings_a)

        menu.addSeparator()
        hide_a = QAction("Ocultar barra", self)
        hide_a.triggered.connect(self.hide)
        menu.addAction(hide_a)

        menu.addSeparator()
        quit_a = QAction("Sair do Notch", self)
        quit_a.triggered.connect(QApplication.quit)
        menu.addAction(quit_a)

        menu.exec(event.globalPos())

    # ── Position & styles ─────────────────────────────────────────────────────

    def _position_top_center(self):
        screen = QApplication.primaryScreen().geometry()
        self.adjustSize()
        x = (screen.width() - self.sizeHint().width()) // 2
        self.move(x, 0)

    def _load_styles(self):
        if QSS_PATH.exists():
            self.setStyleSheet(QSS_PATH.read_text(encoding="utf-8"))

    # ── Drag to move ──────────────────────────────────────────────────────────

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── Auto-hide ─────────────────────────────────────────────────────────────

    def _setup_autohide(self):
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(10_000)
        self._hide_timer.timeout.connect(self._slide_out)

        self._peek_poll = QTimer(self)
        self._peek_poll.setInterval(50)
        self._peek_poll.timeout.connect(self._check_peek)

        self._slide_anim = QPropertyAnimation(self, b"pos")
        self._slide_anim.setDuration(300)

        self._hide_timer.start()

    def enterEvent(self, event):
        self._hide_timer.stop()
        if self._is_slid_out:
            self._slide_in()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._is_slid_out and not self._any_popup_visible():
            self._hide_timer.start()
        super().leaveEvent(event)

    def _any_popup_visible(self) -> bool:
        return any(p.isVisible() for p in [
            self._clip_popup, self._yt_popup, self._notes_popup,
            self._alarm_popup, self._quotes_popup, self._todo_popup,
            self._slideshow, self._hcalc_popup, self._pokemon_popup,
            self._stress_popup, self._settings_win,
        ])

    def _slide_out(self):
        if self._is_slid_out or self._any_popup_visible():
            return
        self._is_slid_out = True
        self._slide_anim.stop()
        self._slide_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._slide_anim.setStartValue(self.pos())
        self._slide_anim.setEndValue(QPoint(self.pos().x(), -self.height()))
        self._slide_anim.start()
        self._peek_poll.start()

    def _slide_in(self):
        if not self._is_slid_out:
            return
        self._is_slid_out = False
        self._peek_poll.stop()
        self._slide_anim.stop()
        self._slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._slide_anim.setStartValue(self.pos())
        self._slide_anim.setEndValue(QPoint(self.pos().x(), 0))
        self._slide_anim.start()
        self._hide_timer.start()

    def _check_peek(self):
        if not self._is_slid_out:
            self._peek_poll.stop()
            return
        cursor = QCursor.pos()
        geo = self.geometry()
        if cursor.y() <= 2 and geo.left() <= cursor.x() <= geo.right():
            self._slide_in()

    # ── System tray ───────────────────────────────────────────────────────────

    def _make_tray_icon(self) -> QIcon:
        px = QPixmap(32, 32)
        px.fill(QColor(0, 0, 0, 0))
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor("#e5e5ea")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(2, 10, 28, 12, 6, 6)
        p.end()
        return QIcon(px)

    def _setup_tray(self):
        self._tray = QSystemTrayIcon(self._make_tray_icon(), self)
        self._tray.setToolTip("Notch Win")

        menu = QMenu()
        menu.setStyleSheet(MENU_QSS)
        show_action = QAction("Mostrar / Ocultar", self)
        show_action.triggered.connect(self._toggle_visibility)
        quit_action = QAction("Sair", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(
            lambda reason: self._toggle_visibility()
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None
        )
        self._tray.show()

    def _toggle_visibility(self):
        if self.isVisible() and not self._is_slid_out:
            self.hide()
        else:
            self._is_slid_out = False
            self._peek_poll.stop()
            self._slide_anim.stop()
            self.move(self.pos().x(), 0)
            self.show()
            self.raise_()
            self._hide_timer.start()
