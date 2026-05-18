import sys
import os
import json
import base64
import math
import random
import subprocess
import datetime
import webbrowser
import threading
import urllib.request
os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.dbus.*=false")
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QSystemTrayIcon, QMenu,
    QScrollArea, QTextEdit, QLineEdit, QCheckBox,
    QFileDialog, QSpinBox,
)
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, QLineF, QUrl, QEvent, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QIcon, QAction, QCursor, QPixmap, QPainter,
    QColor, QBrush, QPen, QPolygonF, QDesktopServices,
)

from modules.pomodoro import PomodoroModule
from modules.clipboard import ClipboardModule
from modules.spotify import SpotifyModule
from ui.spotify_widget import SpotifyWidget
from modules.youtube_feed import YouTubeFeedModule
from ui.settings_window import SettingsWindow

try:
    from plyer import notification as plyer_notify
    PLYER_OK = True
except Exception:
    PLYER_OK = False

BASE_DIR      = Path(__file__).parent
QSS_PATH      = BASE_DIR / "ui" / "styles.qss"
SETTINGS_PATH = BASE_DIR / ".notch_settings.json"
NOTES_PATH    = BASE_DIR / ".notch_notes.txt"
TODO_PATH     = BASE_DIR / ".notch_todo.json"

try:
    import winsound as _winsound
    _WINSOUND_OK = True
except ImportError:
    _winsound = None
    _WINSOUND_OK = False

# ── Paleta de cores ───────────────────────────────────────────────────────────
# (key, label, pill_bg, border, accent_rgb, mode, icon_rgba)
COLOR_PRESETS = [
    # ── Dark ──────────────────────────────────────────────────────────────────
    ("space-gray", "Space Gray",  "rgba(14,14,14,248)",    "rgba(255,255,255,0.07)", (180,180,180), "dark",  (220,220,220,190)),
    ("graphite",   "Graphite",    "rgba(28,28,30,248)",    "rgba(255,255,255,0.10)", (200,200,200), "dark",  (220,220,220,190)),
    ("midnight",   "Midnight",    "rgba(10,16,38,248)",    "rgba(80,130,255,0.18)",  ( 74,122,255), "dark",  (180,210,255,200)),
    ("ocean",      "Ocean",       "rgba(5,20,35,248)",     "rgba(0,160,230,0.18)",   (  0,170,240), "dark",  (150,220,255,200)),
    ("viridian",   "Viridian",    "rgba(8,26,16,248)",     "rgba(48,210,88,0.18)",   ( 48,209, 88), "dark",  (170,240,190,200)),
    ("forest",     "Forest",      "rgba(5,20,10,248)",     "rgba(50,180,80,0.15)",   ( 50,180, 80), "dark",  (160,230,170,200)),
    ("grape",      "Grape",       "rgba(24,10,44,248)",    "rgba(190,100,255,0.18)", (155, 89,182), "dark",  (210,170,255,200)),
    ("rosewood",   "Rosewood",    "rgba(38,8,14,248)",     "rgba(255,70,90,0.18)",   (255, 69, 58), "dark",  (255,180,180,200)),
    ("ember",      "Ember",       "rgba(30,12,5,248)",     "rgba(255,120,40,0.20)",  (255,120, 40), "dark",  (255,205,155,200)),
    ("obsidian",   "Obsidian",    "rgba(18,18,22,248)",    "rgba(150,150,255,0.12)", (120,120,200), "dark",  (200,200,230,190)),
    # ── Light ─────────────────────────────────────────────────────────────────
    ("arctic",     "Arctic",      "rgba(245,248,252,235)", "rgba(0,0,0,0.12)",       ( 80,120,200), "light", ( 30, 30, 40,200)),
    ("sand",       "Sand",        "rgba(248,242,228,235)", "rgba(0,0,0,0.10)",       (160,120, 60), "light", ( 60, 45, 20,200)),
    ("blossom",    "Blossom",     "rgba(252,236,244,235)", "rgba(200,80,140,0.20)",  (200, 80,140), "light", (100, 20, 60,200)),
    ("sky",        "Sky",         "rgba(228,242,255,235)", "rgba(60,130,230,0.20)",  ( 60,130,230), "light", ( 20, 50,130,200)),
    ("mint",       "Mint",        "rgba(228,248,236,235)", "rgba(40,180,100,0.20)",  ( 40,180,100), "light", ( 10, 80, 40,200)),
    ("lavender",   "Lavender",    "rgba(236,232,252,235)", "rgba(130,100,220,0.20)", (130,100,220), "light", ( 60, 30,130,200)),
    ("cream",      "Cream",       "rgba(252,248,238,235)", "rgba(160,130,60,0.15)",  (160,130, 60), "light", ( 80, 65, 20,200)),
]

# ── Presets de duração do Pomodoro ────────────────────────────────────────────
POMO_PRESETS = [
    ("15 min",  15,  5, 10),
    ("20 min",  20,  5, 10),
    ("25 min",  25,  5, 15),
    ("30 min",  30, 10, 20),
    ("45 min",  45, 15, 25),
    ("60 min",  60, 20, 30),
]

# ── QSS do context menu ───────────────────────────────────────────────────────
MENU_QSS = """
QMenu {
    background-color: rgba(28,28,30,252);
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 12px;
    padding: 6px 4px;
    font-family: "SF Pro Text","Segoe UI",sans-serif;
    font-size: 12px;
    color: #e5e5ea;
}
QMenu::item {
    padding: 7px 20px 7px 14px;
    border-radius: 8px;
    margin: 1px 4px;
    color: #e5e5ea;
}
QMenu::item:selected { background: rgba(255,255,255,0.10); color:#fff; }
QMenu::item:disabled { color: rgba(255,255,255,0.28); }
QMenu::separator     { height:1px; background:rgba(255,255,255,0.10); margin:4px 10px; }
"""


def notify(title: str, message: str):
    if PLYER_OK:
        try:
            plyer_notify.notify(title=title, message=message, app_name="Notch", timeout=4)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# Ícones vetoriais (estilo macOS SF Symbols)
# ══════════════════════════════════════════════════════════════════════════════

from ui.icons import (
    _DEFAULT_DARK, _DEFAULT_LIGHT, _make_icon, _icon_btn, _refresh_icon,
    _ic_prev, _ic_next, _ic_play, _ic_pause,
)


def _ic_reset(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 2.0); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(3, 3, s-6, s-6), 40*16, 290*16)
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    tx, ty = s-4.5, 4.5
    p.drawPolygon(QPolygonF([QPointF(tx-4,ty), QPointF(tx+1,ty+4), QPointF(tx+2,ty-3)]))


def _ic_timer(p: QPainter, s: int, c: QColor):
    cx, cy = s/2, s/2 + 1.5
    r = (s - 9) / 2
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(int(cx)-2, 0, 4, 4, 1.5, 1.5)
    pen = QPen(c, 1.8); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(3, 4, s-6, s-6))
    pen2 = QPen(c, 1.8); pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen2)
    a_m = math.radians(-70)
    p.drawLine(QLineF(cx, cy, cx + r*0.58*math.sin(a_m), cy - r*0.58*math.cos(a_m)))
    a_h = math.radians(90)
    p.drawLine(QLineF(cx, cy, cx + r*0.38*math.sin(a_h), cy - r*0.38*math.cos(a_h)))


def _ic_clip_open(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 2.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    m = s/2
    p.drawPolyline(QPolygonF([QPointF(4, m-2), QPointF(m, m+3), QPointF(s-4, m-2)]))


def _ic_youtube(p: QPainter, s: int, c: QColor):
    # Rounded rect outline (video frame)
    pen = QPen(c, 1.8)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(2, 5, s - 4, s - 10), 3, 3)
    # Play triangle
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    cx, cy = s / 2, s / 2
    p.drawPolygon(QPolygonF([
        QPointF(cx - 3.5, cy - 4),
        QPointF(cx + 4.5, cy),
        QPointF(cx - 3.5, cy + 4),
    ]))


def _ic_calc(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.5); pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(3, 2, s - 6, s - 4), 3, 3)
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    for gx in range(2):
        for gy in range(3):
            p.drawEllipse(QRectF(6 + gx * 8, 6 + gy * 5, 3, 3))


def _ic_notes(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(4, 2, s - 8, s - 4), 3, 3)
    for y in [7, 11, 15]:
        p.drawLine(QLineF(7, y, s - 7, y))


def _ic_alarm(p: QPainter, s: int, c: QColor):
    cx, cy, r = s / 2, s / 2 + 1, (s - 10) / 2
    pen = QPen(c, 1.7); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
    p.drawLine(QLineF(3, 6, 7, 2))
    p.drawLine(QLineF(s - 3, 6, s - 7, 2))
    p.drawLine(QLineF(cx, cy, cx, cy - r * 0.55))
    p.drawLine(QLineF(cx, cy, cx + r * 0.4, cy))


def _ic_quotes(p: QPainter, s: int, c: QColor):
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    for ox in [3, 12]:
        p.drawRoundedRect(QRectF(ox, 4, 3.5, 5), 1.5, 1.5)
        p.drawRoundedRect(QRectF(ox + 4.5, 4, 3.5, 5), 1.5, 1.5)
    pen = QPen(c, 1.4); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.drawLine(QLineF(3, 14, s - 3, 14))
    p.drawLine(QLineF(3, 18, s - 7, 18))


def _ic_todo(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    for i in range(3):
        y = 4 + i * 6
        p.drawRect(QRectF(2, y, 5, 5))
        p.drawLine(QLineF(10, y + 2.5, s - 3, y + 2.5))
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawRect(QRectF(3.5, 5.5, 2, 2))


def _ic_photo(p: QPainter, s: int, c: QColor):
    pen = QPen(c, 1.5); pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(2, 4, s - 4, s - 7), 3, 3)
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(s - 8, 7, 4, 4))
    p.drawPolygon(QPolygonF([QPointF(3, s - 5), QPointF(8, 11), QPointF(13, s - 5)]))
    p.drawPolygon(QPolygonF([QPointF(10, s - 5), QPointF(16, 13), QPointF(s - 3, s - 5)]))


def _ic_hcalc(p: QPainter, s: int, c: QColor):
    # Relógio (lado esquerdo)
    r, cx, cy = (s - 10) / 2, s / 2 - 2, s / 2
    pen = QPen(c, 1.5); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
    p.drawLine(QLineF(cx, cy, cx, cy - r * 0.6))
    p.drawLine(QLineF(cx, cy, cx + r * 0.45, cy))
    # Moeda (canto inferior direito)
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(s - 8, s - 8, 7, 7))
    # R$ (linha vertical + 2 horizontais dentro da moeda)
    pen2 = QPen(QColor(0, 0, 0, 160), 1.2)
    pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen2)
    mx = s - 4.5
    p.drawLine(QLineF(mx, s - 7.5, mx, s - 1.5))
    p.drawLine(QLineF(mx - 2, s - 6,   mx + 1.5, s - 6))
    p.drawLine(QLineF(mx - 2, s - 4.2, mx + 1.5, s - 4.2))


def _ic_pokemon(p: QPainter, s: int, c: QColor):
    # Pokéball: círculo exterior
    r, cx, cy = (s - 4) / 2, s / 2, s / 2
    pen = QPen(c, 1.6); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
    # Metade superior preenchida (semitransparente)
    semi = QColor(c); semi.setAlpha(int(c.alpha() * 0.35))
    p.setBrush(QBrush(semi)); p.setPen(Qt.PenStyle.NoPen)
    p.drawChord(QRectF(cx - r, cy - r, r * 2, r * 2), 0, 180 * 16)
    # Linha horizontal central
    p.setPen(pen)
    p.drawLine(QLineF(cx - r, cy, cx + r, cy))
    # Círculo central
    cr = r * 0.27
    p.setBrush(QBrush(QColor(255, 255, 255, 220))); p.setPen(pen)
    p.drawEllipse(QRectF(cx - cr, cy - cr, cr * 2, cr * 2))


def _ic_stress(p: QPainter, s: int, c: QColor):
    # Caveira com chifres — ícone de desestresse
    cx, cy = s / 2, s / 2 + 1
    r = (s - 6) / 2
    # Chifres
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    horn = [QPointF(cx-r*0.5, cy-r*0.7), QPointF(cx-r*0.25, cy-r*0.7), QPointF(cx-r*0.38, cy-r*1.15)]
    p.drawPolygon(QPolygonF(horn))
    horn2 = [QPointF(cx+r*0.25, cy-r*0.7), QPointF(cx+r*0.5, cy-r*0.7), QPointF(cx+r*0.38, cy-r*1.15)]
    p.drawPolygon(QPolygonF(horn2))
    # Cabeça
    p.drawEllipse(QRectF(cx - r*0.72, cy - r*0.82, r*1.44, r*1.30))
    # Olhos (vazios)
    p.setBrush(QBrush(QColor(0, 0, 0, 0)))
    pen2 = QPen(QColor(0, 0, 0, 200), 1.4); p.setPen(pen2)
    p.setBrush(QBrush(QColor(0, 0, 0, 180)))
    p.drawEllipse(QRectF(cx - r*0.48, cy - r*0.38, r*0.32, r*0.30))
    p.drawEllipse(QRectF(cx + r*0.16, cy - r*0.38, r*0.32, r*0.30))
    # Dentes
    p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
    for i in range(3):
        tx = cx - r*0.28 + i * r*0.28
        p.drawRect(QRectF(tx, cy + r*0.22, r*0.18, r*0.28))


# ══════════════════════════════════════════════════════════════════════════════
# Clipboard popup
# ══════════════════════════════════════════════════════════════════════════════

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

        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setObjectName("clip-popup-header")
        hh = QHBoxLayout(hdr)
        hh.setContentsMargins(14, 10, 10, 10)
        title = QLabel("⊞  Histórico")
        title.setObjectName("clip-popup-title")
        close_btn = QPushButton("✕")
        close_btn.setObjectName("clip-popup-close")
        close_btn.setFixedSize(22, 22)
        close_btn.clicked.connect(self.close)
        hh.addWidget(title)
        hh.addStretch()
        hh.addWidget(close_btn)
        v.addWidget(hdr)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setMaximumHeight(430)

        self._items_widget = QWidget()
        self._items_widget.setObjectName("clip-items")
        self._list_layout = QVBoxLayout(self._items_widget)
        self._list_layout.setContentsMargins(0, 4, 0, 4)
        self._list_layout.setSpacing(0)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._items_widget)
        v.addWidget(self._scroll)

        # Rodapé limpar
        self._clear_btn = QPushButton("Limpar histórico")
        self._clear_btn.setObjectName("clip-clear-btn")
        self._clear_btn.setFixedHeight(32)
        self._clear_btn.clicked.connect(self._clip.clear)
        v.addWidget(self._clear_btn)

        outer.addWidget(self._card)

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light    = mode == "light"
        text        = "#1c1c1e"             if is_light else "#e5e5ea"
        muted       = "rgba(0,0,0,0.45)"   if is_light else "rgba(255,255,255,0.40)"
        sep_color   = "rgba(0,0,0,0.07)"   if is_light else "rgba(255,255,255,0.07)"
        hover_bg    = "rgba(0,0,0,0.04)"   if is_light else "rgba(255,255,255,0.05)"
        close_h     = "rgba(255,80,80,0.15)"
        clear_color = "#880000"             if is_light else "rgba(255,80,80,0.70)"
        clear_hover = "#550000"             if is_light else "#ff453a"
        scroll_h    = "rgba(0,0,0,0.15)"   if is_light else "rgba(255,255,255,0.15)"

        self._card.setStyleSheet(f"""
            QFrame#clip-popup {{
                background-color: {bg};
                border-radius: 16px;
                border: 1px solid {border};
            }}
            QFrame#clip-popup-header {{
                background: transparent;
                border-bottom: 1px solid {sep_color};
            }}
            QLabel#clip-popup-title {{
                color: {text};
                font-size: 13px;
                font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                background: transparent;
            }}
            QPushButton#clip-popup-close {{
                color: {muted};
                background: transparent;
                border: none;
                border-radius: 11px;
                font-size: 12px;
                min-width:22px; max-width:22px;
                min-height:22px; max-height:22px;
                padding:0px;
            }}
            QPushButton#clip-popup-close:hover {{
                background: {close_h};
                color: #ff453a;
            }}
            QScrollArea {{ background: transparent; border: none; }}
            QWidget#clip-items {{ background: transparent; }}
            QFrame#clip-item-row {{
                background: transparent;
                border: none;
            }}
            QFrame#clip-item-row:hover {{
                background: {hover_bg};
                border-radius: 8px;
            }}
            QLabel#clip-item-lbl {{
                color: {text};
                font-size: 12px;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                background: transparent;
            }}
            QLabel#clip-empty {{
                color: {muted};
                font-size: 12px;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                background: transparent;
            }}
            QFrame#clip-row-sep {{
                color: {sep_color};
                max-height: 1px;
            }}
            QPushButton#clip-clear-btn {{
                color: {clear_color};
                font-size: 11px;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                border-top: 1px solid {sep_color};
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                background: transparent;
                min-width: 0px;
                max-width: 32767px;
            }}
            QPushButton#clip-clear-btn:hover {{
                color: {clear_hover};
                background: {hover_bg};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 4px;
                margin: 3px 1px;
            }}
            QScrollBar::handle:vertical {{
                background: {scroll_h};
                border-radius: 2px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

    def _make_item_row(self, text: str, index: int) -> QFrame:
        row = QFrame()
        row.setObjectName("clip-item-row")
        row.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        h = QHBoxLayout(row)
        h.setContentsMargins(14, 8, 14, 8)
        lbl = QLabel(self._clip.preview(text))
        lbl.setObjectName("clip-item-lbl")
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
            lbl = QLabel("Nada copiado ainda")
            lbl.setObjectName("clip-empty")
            lbl.setContentsMargins(14, 12, 14, 12)
            self._list_layout.insertWidget(0, lbl)
            return
        for i, text in enumerate(history):
            self._list_layout.insertWidget(i * 2, self._make_item_row(text, i))
            if i < len(history) - 1:
                sep = QFrame()
                sep.setObjectName("clip-row-sep")
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


# ══════════════════════════════════════════════════════════════════════════════
# Thumbnail loader (download assíncrono, thread-safe)
# ══════════════════════════════════════════════════════════════════════════════

from PyQt6.QtCore import QObject, pyqtSignal as _Signal

class ThumbnailLoader(QObject):
    loaded = _Signal(str, bytes)   # url, raw bytes (vazio em erro)

    def __init__(self):
        super().__init__()
        self._cache: dict[str, bytes] = {}

    def load(self, url: str):
        if url in self._cache:
            self.loaded.emit(url, self._cache[url])
            return
        threading.Thread(target=self._fetch, args=(url,), daemon=True).start()

    def _fetch(self, url: str):
        try:
            with urllib.request.urlopen(url, timeout=6) as r:
                data = r.read()
        except Exception:
            data = b""
        self._cache[url] = data
        self.loaded.emit(url, data)


class _VideoClickFilter(QObject):
    """Event filter that opens a URL on left-click and consumes the event."""
    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            QDesktopServices.openUrl(QUrl(self._url))
            return True   # consume — prevents propagation to parent windows
        return False


# ══════════════════════════════════════════════════════════════════════════════
# YouTube popup
# ══════════════════════════════════════════════════════════════════════════════

class YouTubePopup(QWidget):
    def __init__(self, yt_module: YouTubeFeedModule, parent=None):
        super().__init__(parent,
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._yt = yt_module
        self._thumb_labels: dict[str, QLabel] = {}
        self._thumb_loader = ThumbnailLoader()
        self._thumb_loader.loaded.connect(self._on_thumb_loaded)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame()
        self._card.setObjectName("yt-popup")
        self._card.setFixedWidth(400)

        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setObjectName("yt-popup-header")
        hh = QHBoxLayout(hdr)
        hh.setContentsMargins(14, 10, 10, 10)
        title_lbl = QLabel("▶  YouTube — Inscrições")
        title_lbl.setObjectName("yt-popup-title")
        close_btn = QPushButton("✕")
        close_btn.setObjectName("yt-popup-close")
        close_btn.setFixedSize(22, 22)
        close_btn.clicked.connect(self.hide)
        hh.addWidget(title_lbl)
        hh.addStretch()
        hh.addWidget(close_btn)
        v.addWidget(hdr)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setFixedHeight(460)

        self._list_widget = QWidget()
        self._list_widget.setObjectName("yt-list")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 4, 0, 4)
        self._list_layout.setSpacing(0)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._list_widget)
        v.addWidget(self._scroll)

        outer.addWidget(self._card)

    def _on_thumb_loaded(self, url: str, data: bytes):
        lbl = self._thumb_labels.get(url)
        if not lbl or not data:
            return
        px = QPixmap()
        px.loadFromData(data)
        if px.isNull():
            return
        # Escala e corta para exatamente 107×60 (16:9)
        px = px.scaled(107, 60, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                       Qt.TransformationMode.SmoothTransformation)
        if px.width() > 107:
            px = px.copy((px.width() - 107) // 2, 0, 107, px.height())
        if px.height() > 60:
            px = px.copy(0, (px.height() - 60) // 2, px.width(), 60)
        lbl.setPixmap(px)

    def _refresh(self, videos: list = None):
        if videos is None:
            videos = self._yt.videos

        self._thumb_labels.clear()

        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not videos:
            lbl = QLabel("Nenhum vídeo disponível.\nConecte ao YouTube nas Configurações.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("padding: 24px; color: rgba(128,128,128,0.7); background: transparent;")
            self._list_layout.insertWidget(0, lbl)
            return

        for i, video in enumerate(videos):
            self._list_layout.insertWidget(i * 2, self._make_video_row(video))
            if i < len(videos) - 1:
                sep = QFrame()
                sep.setObjectName("yt-row-sep")
                sep.setFrameShape(QFrame.Shape.HLine)
                self._list_layout.insertWidget(i * 2 + 1, sep)

    def _make_video_row(self, video) -> QFrame:
        row = QFrame()
        row.setObjectName("yt-video-row")
        row.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        h = QHBoxLayout(row)
        h.setContentsMargins(10, 8, 14, 8)
        h.setSpacing(10)

        # Thumbnail 107×60
        thumb_lbl = QLabel()
        thumb_lbl.setObjectName("yt-thumb")
        thumb_lbl.setFixedSize(107, 60)
        thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder = QPixmap(107, 60)
        placeholder.fill(QColor(40, 40, 46))
        thumb_lbl.setPixmap(placeholder)

        if video.thumbnail_url:
            self._thumb_labels[video.thumbnail_url] = thumb_lbl
            self._thumb_loader.load(video.thumbnail_url)

        h.addWidget(thumb_lbl)

        # Texto: canal + tempo + título
        info = QVBoxLayout()
        info.setSpacing(3)
        info.setContentsMargins(0, 0, 0, 0)

        top = QHBoxLayout()
        top.setSpacing(4)
        ch = video.channel[:22] if len(video.channel) > 22 else video.channel
        channel_lbl = QLabel(ch)
        channel_lbl.setObjectName("yt-channel")
        time_lbl = QLabel(video.time_ago())
        time_lbl.setObjectName("yt-time")
        top.addWidget(channel_lbl, 1)
        top.addWidget(time_lbl, 0)

        title_lbl = QLabel(video.title)
        title_lbl.setObjectName("yt-title")
        title_lbl.setWordWrap(True)
        title_lbl.setToolTip(video.title)

        info.addLayout(top)
        info.addWidget(title_lbl)
        info.addStretch()
        h.addLayout(info, 1)

        url = video.url
        filt = _VideoClickFilter(url, parent=row)
        row.installEventFilter(filt)
        return row

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light   = mode == "light"
        text       = "#1c1c1e"             if is_light else "#e5e5ea"
        muted      = "rgba(0,0,0,0.45)"   if is_light else "rgba(255,255,255,0.40)"
        sep_color  = "rgba(0,0,0,0.07)"   if is_light else "rgba(255,255,255,0.07)"
        hover_bg   = "rgba(0,0,0,0.04)"   if is_light else "rgba(255,255,255,0.05)"
        close_h    = "rgba(255,80,80,0.15)"
        scroll_h   = "rgba(0,0,0,0.15)"   if is_light else "rgba(255,255,255,0.15)"

        self._card.setStyleSheet(f"""
            QFrame#yt-popup {{
                background-color: {bg};
                border-radius: 16px;
                border: 1px solid {border};
            }}
            QFrame#yt-popup-header {{
                background: transparent;
                border-bottom: 1px solid {sep_color};
            }}
            QLabel#yt-popup-title {{
                color: {text};
                font-size: 13px;
                font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                background: transparent;
            }}
            QPushButton#yt-popup-close {{
                color: {muted};
                background: transparent;
                border: none;
                border-radius: 11px;
                font-size: 12px;
                min-width:22px; max-width:22px;
                min-height:22px; max-height:22px;
                padding:0px;
            }}
            QPushButton#yt-popup-close:hover {{
                background: {close_h};
                color: #ff453a;
            }}
            QScrollArea {{ background: transparent; border: none; }}
            QWidget#yt-list {{ background: transparent; }}
            QFrame#yt-video-row {{
                background: transparent;
                border: none;
            }}
            QFrame#yt-video-row:hover {{
                background: {hover_bg};
                border-radius: 8px;
            }}
            QLabel#yt-channel {{
                color: {muted};
                font-size: 10px;
                font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                background: transparent;
            }}
            QLabel#yt-time {{
                color: {muted};
                font-size: 10px;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                background: transparent;
            }}
            QLabel#yt-title {{
                color: {text};
                font-size: 12px;
                font-family: "SF Pro Text","Segoe UI",sans-serif;
                background: transparent;
            }}
            QLabel#yt-thumb {{
                border-radius: 4px;
                background: {"rgba(0,0,0,0.08)" if is_light else "rgba(255,255,255,0.06)"};
            }}
            QFrame#yt-row-sep {{
                color: {sep_color};
                max-height: 1px;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 4px;
                margin: 3px 1px;
            }}
            QScrollBar::handle:vertical {{
                background: {scroll_h};
                border-radius: 2px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

    def show_at(self, pos: QPoint):
        self._refresh(self._yt.videos)
        _popup_show_at(self, pos)


_QUOTES = [
    "O sucesso é a soma de pequenos esforços repetidos dia após dia.",
    "Acredite em si mesmo — chegará o dia em que os outros não terão escolha senão acreditar com você.",
    "Não é sobre ter tempo, é sobre fazer tempo.",
    "A persistência é o caminho do êxito.",
    "Você é mais forte do que pensa e mais capaz do que imagina.",
    "Grandes conquistas começam com pequenos passos corajosos.",
    "O fracasso é apenas a oportunidade de começar novamente com mais inteligência.",
    "A diferença entre o ordinário e o extraordinário é aquele pequeno 'extra'.",
    "Seja a mudança que você deseja ver no mundo.",
    "O único lugar onde o sucesso vem antes do trabalho é no dicionário.",
    "Não espere pela oportunidade certa. Crie-a.",
    "Cada dia é uma nova oportunidade de melhorar.",
    "Você não pode mudar o começo, mas pode recomeçar agora.",
    "O segredo do sucesso é começar.",
    "Sonhe grande, trabalhe duro, mantenha o foco.",
    "A vida começa no fim da sua zona de conforto.",
    "Quem tem um porquê para viver suporta quase qualquer como.",
    "Sua única limitação é aquela que você define em sua própria mente.",
    "O melhor momento para plantar uma árvore foi há 20 anos. O segundo melhor é agora.",
    "Quanto mais você aprende, mais lugares você irá.",
]


# ══════════════════════════════════════════════════════════════════════════════
# _popup_card — fábrica de card comum para popups Tool-window
# ══════════════════════════════════════════════════════════════════════════════

def _tool_popup(parent=None) -> "QWidget":
    w = QWidget(parent,
        Qt.WindowType.Tool |
        Qt.WindowType.FramelessWindowHint |
        Qt.WindowType.WindowStaysOnTopHint)
    w.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    return w


def _popup_show_at(popup: "QWidget", pos: QPoint):
    popup.adjustSize()
    screen = QApplication.primaryScreen().geometry()
    x = max(0, min(pos.x() - popup.width() // 2, screen.width() - popup.width()))
    popup.move(x, pos.y())
    if popup.isVisible():
        popup.hide()
    else:
        popup.show(); popup.raise_()


# ══════════════════════════════════════════════════════════════════════════════
# NotesPopup
# ══════════════════════════════════════════════════════════════════════════════

from PyQt6.QtCore import QTimer as _QTimer

class NotesPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent,
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._save_timer = _QTimer(singleShot=True)
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

    def apply_theme(self, bg, border, mode):
        is_light = mode == "light"
        text   = "#1c1c1e"           if is_light else "#e5e5ea"
        muted  = "rgba(0,0,0,0.45)" if is_light else "rgba(255,255,255,0.40)"
        sep    = "rgba(0,0,0,0.07)" if is_light else "rgba(255,255,255,0.07)"
        ed_bg  = "rgba(0,0,0,0.03)" if is_light else "rgba(0,0,0,0.25)"
        self._card.setStyleSheet(f"""
            QFrame#notes-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#notes-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#notes-title {{ color:{text}; font-size:13px; font-weight:600; font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QPushButton#notes-close {{ color:{muted}; background:transparent; border:none; border-radius:11px; font-size:12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px; }}
            QPushButton#notes-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QTextEdit#notes-editor {{ background:{ed_bg}; color:{text}; border:none; font-size:12px; font-family:"SF Pro Text","Segoe UI",sans-serif; padding:10px 14px; border-bottom-left-radius:16px; border-bottom-right-radius:16px; }}
        """)

    def show_at(self, pos: QPoint):
        _popup_show_at(self, pos)


# ── Spinner ±1 sem QSpinBox (evita conflitos de estilo) ──────────────────────

class _SpinBox(QFrame):
    """Spinner compacto com botões − e + totalmente estilizável via CSS."""

    def __init__(self, lo: int, hi: int, val: int, parent=None):
        super().__init__(parent)
        self.setObjectName("alarm-spin-box")
        self._lo, self._hi, self._val = lo, hi, val
        h = QHBoxLayout(self)
        h.setContentsMargins(2, 2, 2, 2)
        h.setSpacing(0)

        self._btn_m = QPushButton("−")
        self._btn_m.setObjectName("alarm-spin-side-btn")
        self._btn_m.setFixedSize(26, 30)
        self._btn_m.clicked.connect(self._dec)

        self._val_lbl = QLabel(f"{val:02d}")
        self._val_lbl.setObjectName("alarm-spin-val")
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._val_lbl.setFixedWidth(34)

        self._btn_p = QPushButton("+")
        self._btn_p.setObjectName("alarm-spin-side-btn")
        self._btn_p.setFixedSize(26, 30)
        self._btn_p.clicked.connect(self._inc)

        h.addWidget(self._btn_m)
        h.addWidget(self._val_lbl)
        h.addWidget(self._btn_p)

    def value(self) -> int:
        return self._val

    def setValue(self, v: int):
        self._val = self._lo if v > self._hi else (self._hi if v < self._lo else v)
        self._val_lbl.setText(f"{self._val:02d}")

    def _inc(self):
        self.setValue(self._lo if self._val >= self._hi else self._val + 1)

    def _dec(self):
        self.setValue(self._hi if self._val <= self._lo else self._val - 1)


# ══════════════════════════════════════════════════════════════════════════════
# AlarmPopup
# ══════════════════════════════════════════════════════════════════════════════

class AlarmPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent,
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._alarms: list[dict] = []   # {h, m, label, fired_date}
        self._build_ui()
        self._ticker = _QTimer()
        self._ticker.timeout.connect(self._check)
        self._ticker.start(15_000)      # check every 15 s

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._card = QFrame(); self._card.setObjectName("alarm-card")
        self._card.setFixedWidth(280)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("alarm-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        ttl = QLabel("⏰  Despertador"); ttl.setObjectName("alarm-title")
        cls = QPushButton("✕"); cls.setObjectName("alarm-close")
        cls.setFixedSize(22, 22); cls.clicked.connect(self.hide)
        hh.addWidget(ttl); hh.addStretch(); hh.addWidget(cls)
        v.addWidget(hdr)

        # Add-alarm row
        add_row = QWidget(); add_row.setObjectName("alarm-add-row")
        ah = QHBoxLayout(add_row); ah.setContentsMargins(14, 10, 14, 10); ah.setSpacing(6)

        self._spin_h = _SpinBox(0, 23, datetime.datetime.now().hour)
        colon = QLabel(":"); colon.setObjectName("alarm-colon")
        colon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spin_m = _SpinBox(0, 59, 0)

        add_btn = QPushButton("Adicionar"); add_btn.setObjectName("alarm-add-btn")
        add_btn.clicked.connect(self._add_alarm)

        ah.addWidget(self._spin_h); ah.addWidget(colon)
        ah.addWidget(self._spin_m); ah.addStretch(); ah.addWidget(add_btn)
        v.addWidget(add_row)

        # List
        self._list_widget = QWidget(); self._list_widget.setObjectName("alarm-list")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0); self._list_layout.setSpacing(0)
        v.addWidget(self._list_widget)

        outer.addWidget(self._card)

    def _add_alarm(self):
        h, m = self._spin_h.value(), self._spin_m.value()
        self._alarms.append({"h": h, "m": m, "fired_date": ""})
        self._alarms.sort(key=lambda a: (a["h"], a["m"]))
        self._refresh_list()

    def _refresh_list(self):
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if not self._alarms:
            empty = QLabel("Nenhum alarme definido")
            empty.setObjectName("alarm-empty")
            empty.setContentsMargins(14, 10, 14, 10)
            self._list_layout.addWidget(empty)
            return
        for i, a in enumerate(self._alarms):
            row = QFrame(); row.setObjectName("alarm-item")
            rh = QHBoxLayout(row); rh.setContentsMargins(14, 8, 14, 8)
            lbl = QLabel(f"{a['h']:02d}:{a['m']:02d}"); lbl.setObjectName("alarm-item-time")
            rm = QPushButton("✕"); rm.setObjectName("alarm-rm-btn")
            rm.setFixedSize(20, 20)
            rm.clicked.connect(lambda _, ix=i: self._remove(ix))
            rh.addWidget(lbl); rh.addStretch(); rh.addWidget(rm)
            self._list_layout.addWidget(row)
        self.adjustSize()

    def _remove(self, idx: int):
        if 0 <= idx < len(self._alarms):
            del self._alarms[idx]
            self._refresh_list()

    def _check(self):
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        for a in self._alarms:
            if f"{a['h']:02d}:{a['m']:02d}" == time_str and a.get("fired_date") != today:
                a["fired_date"] = today
                self._fire(time_str)

    def _fire(self, time_str: str):
        notify("⏰ Despertador", f"Alarme das {time_str}!")
        if _WINSOUND_OK:
            threading.Thread(target=self._beep, daemon=True).start()

    @staticmethod
    def _beep():
        for _ in range(5):
            _winsound.Beep(880, 350)
            import time; time.sleep(0.15)

    def apply_theme(self, bg, border, mode):
        is_light = mode == "light"
        text   = "#1c1c1e"              if is_light else "#e5e5ea"
        muted  = "rgba(0,0,0,0.45)"    if is_light else "rgba(255,255,255,0.40)"
        sep    = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.07)"
        sm_hov = "rgba(0,0,0,0.12)"    if is_light else "rgba(255,255,255,0.14)"
        sp_bg  = "rgba(0,0,0,0.06)"    if is_light else "rgba(255,255,255,0.09)"
        sp_brd = "rgba(0,0,0,0.14)"    if is_light else "rgba(255,255,255,0.18)"
        self._card.setStyleSheet(f"""
            QFrame#alarm-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#alarm-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#alarm-title {{ color:{text}; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QPushButton#alarm-close {{ color:{muted}; background:transparent; border:none;
                border-radius:11px; font-size:12px;
                min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px; }}
            QPushButton#alarm-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QWidget#alarm-add-row {{ background:transparent; border-bottom:1px solid {sep}; }}
            QFrame#alarm-spin-box {{
                background:{sp_bg}; border:1px solid {sp_brd}; border-radius:9px; }}
            QPushButton#alarm-spin-side-btn {{
                color:{text}; background:transparent; border:none; border-radius:5px;
                font-size:16px; font-weight:bold;
                font-family:"SF Pro Text","Segoe UI",sans-serif; }}
            QPushButton#alarm-spin-side-btn:hover {{ background:{sm_hov}; }}
            QLabel#alarm-spin-val {{
                color:{text}; font-size:17px; font-weight:700;
                font-family:"Consolas","Cascadia Code",monospace; background:transparent; }}
            QLabel#alarm-colon {{
                color:{text}; font-size:18px; font-weight:bold;
                font-family:"Segoe UI",sans-serif; background:transparent; }}
            QPushButton#alarm-add-btn {{
                background:#0a84ff; color:#fff; border:none; border-radius:8px;
                font-size:11px; font-family:"SF Pro Text","Segoe UI",sans-serif;
                padding:5px 12px; }}
            QPushButton#alarm-add-btn:hover {{ background:#0070e0; }}
            QWidget#alarm-list {{ background:transparent; }}
            QFrame#alarm-item {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#alarm-item-time {{
                color:{text}; font-size:18px; font-weight:700;
                font-family:"Consolas","Cascadia Code",monospace; background:transparent; }}
            QPushButton#alarm-rm-btn {{
                color:{muted}; background:transparent; border:none; border-radius:10px;
                font-size:11px; }}
            QPushButton#alarm-rm-btn:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QLabel#alarm-empty {{
                color:{muted}; font-size:12px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
        """)
        self._refresh_list()

    def show_at(self, pos: QPoint):
        self._refresh_list()
        _popup_show_at(self, pos)


# ══════════════════════════════════════════════════════════════════════════════
# QuotesPopup
# ══════════════════════════════════════════════════════════════════════════════

class QuotesPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent,
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._idx = random.randint(0, len(_QUOTES) - 1)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._card = QFrame(); self._card.setObjectName("quotes-card")
        self._card.setFixedWidth(340)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("quotes-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        ttl = QLabel("❝  Motivação"); ttl.setObjectName("quotes-title")
        cls = QPushButton("✕"); cls.setObjectName("quotes-close")
        cls.setFixedSize(22, 22); cls.clicked.connect(self.hide)
        hh.addWidget(ttl); hh.addStretch(); hh.addWidget(cls)
        v.addWidget(hdr)

        body = QWidget(); body.setObjectName("quotes-body")
        bv = QVBoxLayout(body); bv.setContentsMargins(18, 16, 18, 16); bv.setSpacing(14)

        self._quote_lbl = QLabel()
        self._quote_lbl.setObjectName("quotes-text")
        self._quote_lbl.setWordWrap(True)
        self._quote_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv.addWidget(self._quote_lbl)

        next_btn = QPushButton("Próxima frase →")
        next_btn.setObjectName("quotes-next-btn")
        next_btn.clicked.connect(self._next)
        bv.addWidget(next_btn)
        v.addWidget(body)
        outer.addWidget(self._card)
        self._show_current()

    def _show_current(self):
        self._quote_lbl.setText(f'"{_QUOTES[self._idx]}"')

    def _next(self):
        self._idx = (self._idx + 1) % len(_QUOTES)
        self._show_current()

    def apply_theme(self, bg, border, mode):
        is_light = mode == "light"
        text   = "#1c1c1e"              if is_light else "#e5e5ea"
        muted  = "rgba(0,0,0,0.45)"    if is_light else "rgba(255,255,255,0.40)"
        sep    = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.07)"
        sm_bg  = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.09)"
        sm_hov = "rgba(0,0,0,0.12)"    if is_light else "rgba(255,255,255,0.16)"
        self._card.setStyleSheet(f"""
            QFrame#quotes-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#quotes-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#quotes-title {{ color:{text}; font-size:13px; font-weight:600; font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QPushButton#quotes-close {{ color:{muted}; background:transparent; border:none; border-radius:11px; font-size:12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px; }}
            QPushButton#quotes-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QWidget#quotes-body {{ background:transparent; }}
            QLabel#quotes-text {{ color:{text}; font-size:13px; font-style:italic; font-family:"Georgia","Times New Roman",serif; background:transparent; line-height:1.5; }}
            QPushButton#quotes-next-btn {{ background:{sm_bg}; color:{text}; border:none; border-radius:9px; font-size:12px; font-family:"SF Pro Text","Segoe UI",sans-serif; padding:7px 14px; }}
            QPushButton#quotes-next-btn:hover {{ background:{sm_hov}; }}
        """)

    def show_at(self, pos: QPoint):
        _popup_show_at(self, pos)


# ══════════════════════════════════════════════════════════════════════════════
# TodoPopup
# ══════════════════════════════════════════════════════════════════════════════

class TodoPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent,
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._items: list[dict] = []
        self._load()
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._card = QFrame(); self._card.setObjectName("todo-card")
        self._card.setFixedWidth(320)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("todo-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        ttl = QLabel("☑  Tarefas"); ttl.setObjectName("todo-title")
        cls = QPushButton("✕"); cls.setObjectName("todo-close")
        cls.setFixedSize(22, 22); cls.clicked.connect(self.hide)
        hh.addWidget(ttl); hh.addStretch(); hh.addWidget(cls)
        v.addWidget(hdr)

        # Input row
        inp_row = QWidget(); inp_row.setObjectName("todo-input-row")
        ih = QHBoxLayout(inp_row); ih.setContentsMargins(14, 10, 14, 10); ih.setSpacing(8)
        self._inp = QLineEdit(); self._inp.setObjectName("todo-input")
        self._inp.setPlaceholderText("Nova tarefa…")
        self._inp.returnPressed.connect(self._add_item)
        add_btn = QPushButton("+"); add_btn.setObjectName("todo-add-btn")
        add_btn.setFixedSize(28, 28); add_btn.clicked.connect(self._add_item)
        ih.addWidget(self._inp, 1); ih.addWidget(add_btn)
        v.addWidget(inp_row)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setMaximumHeight(360)

        self._list_widget = QWidget(); self._list_widget.setObjectName("todo-list")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 4, 0, 4); self._list_layout.setSpacing(0)
        self._list_layout.addStretch()
        self._scroll.setWidget(self._list_widget)
        v.addWidget(self._scroll)

        outer.addWidget(self._card)
        self._refresh_list()

    def _add_item(self):
        text = self._inp.text().strip()
        if not text: return
        self._items.append({"text": text, "done": False})
        self._inp.clear()
        self._refresh_list()
        self._save()

    def _toggle_item(self, idx: int, done: bool):
        if 0 <= idx < len(self._items):
            self._items[idx]["done"] = done
            self._refresh_list()
            self._save()

    def _remove_item(self, idx: int):
        if 0 <= idx < len(self._items):
            del self._items[idx]
            self._refresh_list()
            self._save()

    def _refresh_list(self):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if not self._items:
            lbl = QLabel("Nenhuma tarefa ainda")
            lbl.setObjectName("todo-empty")
            lbl.setContentsMargins(14, 12, 14, 12)
            self._list_layout.insertWidget(0, lbl)
            return
        for i, item in enumerate(self._items):
            row = QFrame(); row.setObjectName("todo-item")
            rh = QHBoxLayout(row); rh.setContentsMargins(14, 7, 14, 7); rh.setSpacing(8)
            chk = QCheckBox(); chk.setObjectName("todo-chk")
            chk.setChecked(item["done"])
            chk.toggled.connect(lambda v, ix=i: self._toggle_item(ix, v))
            lbl = QLabel(item["text"]); lbl.setObjectName("todo-item-lbl")
            lbl.setWordWrap(True)
            if item["done"]:
                lbl.setObjectName("todo-item-lbl-done")
            rm = QPushButton("✕"); rm.setObjectName("todo-rm-btn")
            rm.setFixedSize(18, 18)
            rm.clicked.connect(lambda _, ix=i: self._remove_item(ix))
            rh.addWidget(chk); rh.addWidget(lbl, 1); rh.addWidget(rm)
            self._list_layout.insertWidget(i, row)
        self.adjustSize()

    def _save(self):
        TODO_PATH.write_text(
            json.dumps(self._items, ensure_ascii=False), encoding="utf-8"
        )

    def _load(self):
        if TODO_PATH.exists():
            try:
                self._items = json.loads(TODO_PATH.read_text(encoding="utf-8"))
            except Exception:
                self._items = []

    def apply_theme(self, bg, border, mode):
        is_light  = mode == "light"
        text      = "#1c1c1e"              if is_light else "#e5e5ea"
        done_text = "rgba(0,0,0,0.35)"    if is_light else "rgba(255,255,255,0.30)"
        muted     = "rgba(0,0,0,0.45)"    if is_light else "rgba(255,255,255,0.40)"
        sep       = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.07)"
        inp_bg    = "rgba(0,0,0,0.05)"    if is_light else "rgba(255,255,255,0.07)"
        scroll_h  = "rgba(0,0,0,0.15)"    if is_light else "rgba(255,255,255,0.15)"
        self._card.setStyleSheet(f"""
            QFrame#todo-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#todo-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#todo-title {{ color:{text}; font-size:13px; font-weight:600; font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QPushButton#todo-close {{ color:{muted}; background:transparent; border:none; border-radius:11px; font-size:12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px; }}
            QPushButton#todo-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QWidget#todo-input-row {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLineEdit#todo-input {{ background:{inp_bg}; color:{text}; border:1px solid {sep}; border-radius:8px; font-size:12px; font-family:"SF Pro Text","Segoe UI",sans-serif; padding:5px 10px; }}
            QPushButton#todo-add-btn {{ background:#0a84ff; color:#fff; border:none; border-radius:8px; font-size:16px; font-weight:bold; }}
            QPushButton#todo-add-btn:hover {{ background:#0070e0; }}
            QScrollArea {{ background:transparent; border:none; }}
            QWidget#todo-list {{ background:transparent; }}
            QFrame#todo-item {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#todo-item-lbl {{ color:{text}; font-size:12px; font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QLabel#todo-item-lbl-done {{ color:{done_text}; font-size:12px; font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; text-decoration:line-through; }}
            QPushButton#todo-rm-btn {{ color:{muted}; background:transparent; border:none; border-radius:9px; font-size:10px; }}
            QPushButton#todo-rm-btn:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QLabel#todo-empty {{ color:{muted}; font-size:12px; font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QScrollBar:vertical {{ background:transparent; width:4px; margin:3px 1px; }}
            QScrollBar::handle:vertical {{ background:{scroll_h}; border-radius:2px; min-height:20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0px; }}
        """)
        self._refresh_list()

    def show_at(self, pos: QPoint):
        self._refresh_list()
        _popup_show_at(self, pos)


# ══════════════════════════════════════════════════════════════════════════════
# PhotoSlideshow — janela flutuante arrastável, sempre à frente
# ══════════════════════════════════════════════════════════════════════════════

class PhotoSlideshow(QWidget):
    def __init__(self):
        super().__init__(None,
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._photos: list[Path] = []
        self._idx = 0
        self._drag_pos: QPoint | None = None
        self._playing = True

        self._timer = _QTimer()
        self._timer.timeout.connect(self._next)
        self._timer.start(5_000)

        self._build_ui()

    _W, _H = 140, 180

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)

        # Card
        self._card = QFrame(); self._card.setObjectName("slide-card")
        self._card.setFixedSize(self._W + 2, self._H + 30)
        cv = QVBoxLayout(self._card)
        cv.setContentsMargins(1, 1, 1, 0); cv.setSpacing(0)

        # Image label
        self._img_lbl = QLabel()
        self._img_lbl.setObjectName("slide-img")
        self._img_lbl.setFixedSize(self._W, self._H)
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self._set_placeholder()
        cv.addWidget(self._img_lbl)

        # Controls strip
        ctrl = QFrame(); ctrl.setObjectName("slide-ctrl")
        ch = QHBoxLayout(ctrl); ch.setContentsMargins(4, 2, 4, 2); ch.setSpacing(2)

        def _small_btn(text, slot):
            b = QPushButton(text); b.setObjectName("slide-btn")
            b.setFixedSize(24, 22); b.clicked.connect(slot)
            return b

        ch.addWidget(_small_btn("←", self._prev))
        ch.addWidget(_small_btn("▶", self._toggle_play))
        ch.addWidget(_small_btn("→", self._next))
        ch.addStretch()
        ch.addWidget(_small_btn("📁", self._pick_folder))
        ch.addWidget(_small_btn("✕", self.hide))
        cv.addWidget(ctrl)

        outer.addWidget(self._card)

        self._card.setStyleSheet("""
            QFrame#slide-card { background: rgba(20,20,22,220); border-radius: 12px; border: 1px solid rgba(255,255,255,0.12); }
            QLabel#slide-img { border-top-left-radius: 11px; border-top-right-radius: 11px; background: rgba(0,0,0,0.4); }
            QFrame#slide-ctrl { background: transparent; border-top: 1px solid rgba(255,255,255,0.08); }
            QPushButton#slide-btn { background: transparent; color: rgba(255,255,255,0.65); border: none; border-radius: 5px; font-size: 11px; }
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
        self._photos = sorted(
            p for p in Path(folder).iterdir()
            if p.suffix.lower() in exts
        )
        self._idx = 0
        self._show_current()

    def _show_current(self):
        if not self._photos: return
        path = self._photos[self._idx % len(self._photos)]
        px = QPixmap(str(path))
        if px.isNull(): return
        px = px.scaled(self._W, self._H,
                       Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                       Qt.TransformationMode.SmoothTransformation)
        if px.width() > self._W:
            px = px.copy((px.width() - self._W) // 2, 0, self._W, self._H)
        if px.height() > self._H:
            px = px.copy(0, (px.height() - self._H) // 2, self._W, self._H)
        self._img_lbl.setPixmap(px)

    def _next(self):
        if not self._photos: return
        self._idx = (self._idx + 1) % len(self._photos)
        self._show_current()

    def _prev(self):
        if not self._photos: return
        self._idx = (self._idx - 1) % len(self._photos)
        self._show_current()

    def _toggle_play(self):
        self._playing = not self._playing
        if self._playing: self._timer.start(5_000)
        else: self._timer.stop()

    def _pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Escolher pasta de fotos")
        if folder:
            self.set_folder(folder)
            return folder
        return ""

    # Drag to move
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None


# ══════════════════════════════════════════════════════════════════════════════
# HoursCalcPopup
# ══════════════════════════════════════════════════════════════════════════════

class HoursCalcPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent,
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._card = QFrame(); self._card.setObjectName("hcalc-card")
        self._card.setFixedWidth(300)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        # Header
        hdr = QFrame(); hdr.setObjectName("hcalc-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        ttl = QLabel("⏱  Calculadora de Horas"); ttl.setObjectName("hcalc-title")
        cls = QPushButton("✕"); cls.setObjectName("hcalc-close")
        cls.setFixedSize(22, 22); cls.clicked.connect(self.hide)
        hh.addWidget(ttl); hh.addStretch(); hh.addWidget(cls)
        v.addWidget(hdr)

        # Body
        body = QWidget(); body.setObjectName("hcalc-body")
        bv = QVBoxLayout(body)
        bv.setContentsMargins(16, 14, 16, 14); bv.setSpacing(10)

        # Horas + Minutos (lado a lado)
        time_row = QWidget()
        tr = QHBoxLayout(time_row); tr.setContentsMargins(0, 0, 0, 0); tr.setSpacing(10)

        for attr, lbl_text, ph in [
            ("_inp_h", "HORAS",   "0"),
            ("_inp_m", "MINUTOS", "0"),
        ]:
            col = QVBoxLayout(); col.setSpacing(4)
            lbl = QLabel(lbl_text); lbl.setObjectName("hcalc-field-lbl")
            inp = QLineEdit(); inp.setObjectName("hcalc-input")
            inp.setPlaceholderText(ph)
            inp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            inp.returnPressed.connect(self._calc)
            setattr(self, attr, inp)
            col.addWidget(lbl); col.addWidget(inp)
            tr.addLayout(col)

        bv.addWidget(time_row)

        # Valor por hora
        rate_lbl = QLabel("VALOR POR HORA  (R$)"); rate_lbl.setObjectName("hcalc-field-lbl")
        self._inp_rate = QLineEdit(); self._inp_rate.setObjectName("hcalc-input")
        self._inp_rate.setPlaceholderText("0,00")
        self._inp_rate.returnPressed.connect(self._calc)
        bv.addWidget(rate_lbl); bv.addWidget(self._inp_rate)

        # Botão calcular
        calc_btn = QPushButton("Calcular →"); calc_btn.setObjectName("hcalc-btn")
        calc_btn.clicked.connect(self._calc)
        bv.addWidget(calc_btn)

        # Resultado (oculto até calcular)
        self._result_frame = QFrame(); self._result_frame.setObjectName("hcalc-result-frame")
        self._result_frame.setVisible(False)
        rv = QVBoxLayout(self._result_frame)
        rv.setContentsMargins(14, 12, 14, 12); rv.setSpacing(4)

        lbl_receberá = QLabel("Você receberá:"); lbl_receberá.setObjectName("hcalc-result-label")
        lbl_receberá.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_main = QLabel()
        self._result_main.setObjectName("hcalc-result-main")
        self._result_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_sub = QLabel()
        self._result_sub.setObjectName("hcalc-result-sub")
        self._result_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rv.addWidget(lbl_receberá)
        rv.addWidget(self._result_main)
        rv.addWidget(self._result_sub)
        bv.addWidget(self._result_frame)

        v.addWidget(body)
        outer.addWidget(self._card)

    # ── Lógica ────────────────────────────────────────────────────────────────

    def _calc(self):
        try:
            h = int(self._inp_h.text().strip() or 0)
            m = int(self._inp_m.text().strip() or 0)
            if not (0 <= m <= 59):
                raise ValueError
            rate_str = self._inp_rate.text().strip().replace(',', '.')
            rate = float(rate_str or 0)
        except ValueError:
            self._result_main.setText("⚠  Verifique os valores")
            self._result_sub.setText("Minutos: 0–59 · Valores numéricos")
            self._result_frame.setVisible(True)
            self.adjustSize()
            return

        total_h = h + m / 60
        total   = total_h * rate
        self._result_main.setText(self._fmt(total))
        self._result_sub.setText(f"{h}h {m:02d}min  ×  {self._fmt(rate)}/h")
        self._result_frame.setVisible(True)
        self.adjustSize()

    @staticmethod
    def _fmt(v: float) -> str:
        return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # ── Tema ──────────────────────────────────────────────────────────────────

    def apply_theme(self, bg, border, mode):
        is_light  = mode == "light"
        text      = "#1c1c1e"              if is_light else "#e5e5ea"
        muted     = "rgba(0,0,0,0.45)"    if is_light else "rgba(255,255,255,0.40)"
        sep       = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.07)"
        inp_bg    = "rgba(0,0,0,0.05)"    if is_light else "rgba(255,255,255,0.07)"
        inp_brd   = "rgba(0,0,0,0.12)"    if is_light else "rgba(255,255,255,0.14)"
        res_bg    = "rgba(48,209,88,0.10)"
        green     = "#1a7a3a"             if is_light else "#30d158"
        self._card.setStyleSheet(f"""
            QFrame#hcalc-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#hcalc-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#hcalc-title {{ color:{text}; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QPushButton#hcalc-close {{ color:{muted}; background:transparent; border:none;
                border-radius:11px; font-size:12px;
                min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px; }}
            QPushButton#hcalc-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QWidget#hcalc-body {{ background:transparent; }}
            QLabel#hcalc-field-lbl {{ color:{muted}; font-size:10px; font-weight:700;
                font-family:"SF Pro Text","Segoe UI",sans-serif;
                background:transparent; letter-spacing:0.6px; }}
            QLineEdit#hcalc-input {{ background:{inp_bg}; color:{text};
                border:1px solid {inp_brd}; border-radius:8px;
                font-size:16px; font-weight:600;
                font-family:"Consolas","Cascadia Code",monospace;
                padding:6px 8px; selection-background-color:#0a84ff; }}
            QLineEdit#hcalc-input:focus {{ border:1px solid rgba(10,132,255,0.55); }}
            QPushButton#hcalc-btn {{ background:#0a84ff; color:#fff; border:none;
                border-radius:9px; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; padding:9px; }}
            QPushButton#hcalc-btn:hover {{ background:#0070e0; }}
            QFrame#hcalc-result-frame {{ background:{res_bg}; border-radius:10px;
                border:1px solid rgba(48,209,88,0.20); }}
            QLabel#hcalc-result-label {{ color:{muted}; font-size:10px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif;
                background:transparent; letter-spacing:0.5px; }}
            QLabel#hcalc-result-main {{ color:{green}; font-size:24px; font-weight:700;
                font-family:"Consolas","Cascadia Code",monospace; background:transparent; }}
            QLabel#hcalc-result-sub {{ color:{muted}; font-size:11px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
        """)

    def show_at(self, pos: QPoint):
        _popup_show_at(self, pos)


# ══════════════════════════════════════════════════════════════════════════════
# Pokémon popup
# ══════════════════════════════════════════════════════════════════════════════

_TYPE_COLORS = {
    "normal": "#A8A878", "fire": "#F08030", "water": "#6890F0",
    "electric": "#F8D030", "grass": "#78C850", "ice": "#98D8D8",
    "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820",
    "rock": "#B8A038", "ghost": "#705898", "dragon": "#7038F8",
    "dark": "#705848", "steel": "#B8B8D0", "fairy": "#EE99AC",
}

from PyQt6.QtCore import pyqtSignal as _PokeSignal

class _PokeLoader(QObject):
    pokemon_loaded = _PokeSignal(dict, bytes)
    load_error     = _PokeSignal(str)

    def fetch(self, pokemon_id: int):
        threading.Thread(target=self._do_fetch, args=(pokemon_id,), daemon=True).start()

    _HEADERS = {"User-Agent": "Mozilla/5.0 NotchWin/1.0"}

    def _do_fetch(self, pokemon_id: int):
        try:
            url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
            req = urllib.request.Request(url, headers=self._HEADERS)
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            img_url  = (data.get("sprites") or {}).get("front_default") or ""
            img_data = b""
            if img_url:
                try:
                    img_req = urllib.request.Request(img_url, headers=self._HEADERS)
                    with urllib.request.urlopen(img_req, timeout=6) as r:
                        img_data = r.read()
                except Exception:
                    pass
            self.pokemon_loaded.emit(data, img_data)
        except Exception as e:
            self.load_error.emit(str(e))


class PokemonPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent,
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._loader = _PokeLoader()
        self._loader.pokemon_loaded.connect(self._on_loaded)
        self._loader.load_error.connect(self._on_error)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame(); self._card.setObjectName("poke-card")
        self._card.setFixedWidth(260)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        # Header
        hdr = QFrame(); hdr.setObjectName("poke-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        ttl = QLabel("Pokémon Aleatório"); ttl.setObjectName("poke-title")
        cls = QPushButton("✕"); cls.setObjectName("poke-close")
        cls.setFixedSize(22, 22); cls.clicked.connect(self.hide)
        hh.addWidget(ttl); hh.addStretch(); hh.addWidget(cls)
        v.addWidget(hdr)

        # Body
        body = QWidget(); body.setObjectName("poke-body")
        bv = QVBoxLayout(body)
        bv.setContentsMargins(16, 16, 16, 16); bv.setSpacing(10)

        # Sprite
        self._sprite_lbl = QLabel()
        self._sprite_lbl.setObjectName("poke-sprite")
        self._sprite_lbl.setFixedSize(96, 96)
        self._sprite_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv.addWidget(self._sprite_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Name
        self._name_lbl = QLabel("Carregando…")
        self._name_lbl.setObjectName("poke-name")
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv.addWidget(self._name_lbl)

        # ID + weight
        self._info_lbl = QLabel("")
        self._info_lbl.setObjectName("poke-info")
        self._info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv.addWidget(self._info_lbl)

        # Type pills row
        type_w = QWidget()
        self._types_row = QHBoxLayout(type_w)
        self._types_row.setContentsMargins(0, 0, 0, 0); self._types_row.setSpacing(6)
        self._types_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        bv.addWidget(type_w)

        # Button
        self._next_btn = QPushButton("🎲  Novo Pokémon")
        self._next_btn.setObjectName("poke-btn")
        self._next_btn.clicked.connect(self._fetch_random)
        bv.addWidget(self._next_btn)

        v.addWidget(body)
        outer.addWidget(self._card)

    def _fetch_random(self):
        self._name_lbl.setText("Carregando…")
        self._info_lbl.setText("")
        self._sprite_lbl.clear()
        self._next_btn.setEnabled(False)
        while self._types_row.count():
            item = self._types_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._loader.fetch(random.randint(1, 1010))

    def _on_loaded(self, data: dict, img_data: bytes):
        name    = data.get("name", "???").capitalize()
        poke_id = data.get("id", 0)
        weight  = data.get("weight", 0) / 10
        types   = [t["type"]["name"] for t in data.get("types", [])]

        self._name_lbl.setText(name)
        self._info_lbl.setText(f"#{poke_id:04d}  ·  {weight:.1f} kg")

        while self._types_row.count():
            item = self._types_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for t in types:
            color = _TYPE_COLORS.get(t, "#888888")
            pill = QLabel(t.capitalize())
            pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pill.setStyleSheet(
                f"background:{color}; color:#fff; border-radius:8px;"
                f" padding:2px 10px; font-size:11px; font-weight:700;"
                f" font-family:'SF Pro Text','Segoe UI',sans-serif;"
            )
            self._types_row.addWidget(pill)

        if img_data:
            px = QPixmap()
            px.loadFromData(img_data)
            px = px.scaled(96, 96,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            self._sprite_lbl.setPixmap(px)
        else:
            self._sprite_lbl.setText("?")

        self._next_btn.setEnabled(True)
        self.adjustSize()

    def _on_error(self, msg: str):
        self._name_lbl.setText("Erro ao carregar")
        self._info_lbl.setText(msg[:40])
        self._next_btn.setEnabled(True)

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light = mode == "light"
        text  = "#1c1c1e"             if is_light else "#e5e5ea"
        muted = "rgba(0,0,0,0.45)"   if is_light else "rgba(255,255,255,0.40)"
        sep   = "rgba(0,0,0,0.07)"   if is_light else "rgba(255,255,255,0.07)"
        self._card.setStyleSheet(f"""
            QFrame#poke-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#poke-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#poke-title {{ color:{text}; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QPushButton#poke-close {{ color:{muted}; background:transparent; border:none;
                border-radius:11px; font-size:12px;
                min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px; }}
            QPushButton#poke-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QWidget#poke-body {{ background:transparent; }}
            QLabel#poke-sprite {{ background:transparent; }}
            QLabel#poke-name {{ color:{text}; font-size:20px; font-weight:700;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QLabel#poke-info {{ color:{muted}; font-size:11px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QPushButton#poke-btn {{ background:#0a84ff; color:#fff; border:none;
                border-radius:9px; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; padding:9px; }}
            QPushButton#poke-btn:hover {{ background:#0070e0; }}
            QPushButton#poke-btn:disabled {{ background:rgba(10,132,255,0.4); }}
        """)

    def show_at(self, pos: QPoint):
        _popup_show_at(self, pos)


# ══════════════════════════════════════════════════════════════════════════════
# Stress Relief — Monster Basher
# ══════════════════════════════════════════════════════════════════════════════

_STRESS_MONSTERS = [
    {"name": "Slime",           "hp": 12, "time":  8, "color": (50,  200,  80), "kind": "slime"},
    {"name": "Morcego",         "hp": 15, "time":  9, "color": (110,  60, 160), "kind": "bat"},
    {"name": "Esqueleto",       "hp": 18, "time": 10, "color": (210, 200, 175), "kind": "skeleton"},
    {"name": "Fantasma",        "hp": 16, "time":  9, "color": (150, 180, 230), "kind": "ghost"},
    {"name": "Goblin",          "hp": 20, "time": 11, "color": ( 60, 160,  50), "kind": "goblin"},
    {"name": "Aranha",          "hp": 18, "time": 10, "color": ( 50,  35,  65), "kind": "spider"},
    {"name": "Orc",             "hp": 25, "time": 12, "color": (100, 140,  70), "kind": "orc"},
    {"name": "Dragão",          "hp": 30, "time": 13, "color": (160,  50, 190), "kind": "dragon"},
    {"name": "Demônio",         "hp": 35, "time": 14, "color": (210,  30,  30), "kind": "demon"},
    {"name": "Cavaleiro Negro", "hp": 40, "time": 16, "color": ( 25,  25,  40), "kind": "knight"},
]

_STRESS_LOSE_MSGS = [
    "O monstro venceu! Você estava devagar demais...\nDescanse um pouco e tente de novo!",
    "Derrota! O monstro riu na sua cara.\nVingança é um prato servido frio — e rápido.",
    "Você ficou paraliso de medo!\nO monstro aproveitou e foi embora vitorioso.",
    "Tempo esgotado! O monstro escapou.\nPróxima vez clique mais rápido, guerreiro!",
    "O monstro foi rápido demais para você desta vez.\nMas você vai melhorar — acredito em você!",
]

_STRESS_WIN_MSGS = [
    "Parabéns, guerreiro! Você destruiu todos os monstros!\nSua sanidade agradece — por enquanto.\nEles já estão se reagrupando nas sombras...",
    "10 monstros eliminados!\nInfelizmente seu chefe, sua ex e sua conta bancária\nainda estão vivos, mas foi uma boa tentativa.",
    "Vitória total! Os monstros fugiram!\nAs reuniões de segunda-feira de manhã continuam intactas, porém.",
    "Incrível! Você é imparável!\nPelo menos aqui no mundo virtual.\nQuer mais uma rodada?",
    "Os 10 monstros foram derrotados com maestria!\nO médico recomenda esta técnica — provavelmente.",
]


class _HPBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(14)
        self._ratio = 1.0

    def set_ratio(self, r: float):
        self._ratio = max(0.0, min(1.0, r))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setBrush(QBrush(QColor(0, 0, 0, 55))); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, w, h, h // 2, h // 2)
        if self._ratio > 0:
            fw = max(h, int(w * self._ratio))
            if self._ratio > 0.5:   clr = QColor(48, 209, 88)
            elif self._ratio > 0.25: clr = QColor(255, 190, 0)
            else:                   clr = QColor(255, 60, 60)
            p.setBrush(QBrush(clr))
            p.drawRoundedRect(0, 0, fw, h, h // 2, h // 2)
        p.end()


class _TimeBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self._ratio = 1.0

    def set_ratio(self, r: float):
        self._ratio = max(0.0, min(1.0, r))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setBrush(QBrush(QColor(0, 0, 0, 55))); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, w, h, h // 2, h // 2)
        if self._ratio > 0:
            fw = max(h, int(w * self._ratio))
            if self._ratio > 0.5:    clr = QColor(10, 132, 255)
            elif self._ratio > 0.25: clr = QColor(255, 149, 0)
            else:                    clr = QColor(255, 59, 48)
            p.setBrush(QBrush(clr))
            p.drawRoundedRect(0, 0, fw, h, h // 2, h // 2)
        p.end()


# Sprites embutidos como base64 — sem dependência de arquivo em disco
_MONSTER_B64 = {
    "slime":    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAAY1BMVEUAAAAAAAAkAgAsAQA0AAA6AABBAABSAABgAABuAAB4AACGAQCcAQCnAQGsAQG4AQHCAgHH+GfUAgHwAgL+ly/+qlj+vH3+xo7/BAL/PAP/SQT/UQX/ZAf/awj/cwn/fQr/ihyunus5AAAAAXRSTlMAQObYZgAAAUNJREFUeNrl0tFu2zAMBdBwTExSokRBsjc6lef+/1dOcRc0bdrnPYyC4Id7cCFDOv2HA2/zfRxNs0T6hoCWvixzFiOCL3Pvy68hWrb4hQD2fV7mfe/ri+uzAK7X3q/X9ffr6lt/6gAy31bzZVvdWyuh0Q/4AKw005zrvHsrliM7Pwpgr57VS4hazF9aydH4EWhKtXjJgYg4lL6ZRn0/Bpwt1lo9pBQp0hRKC9bkTHAHpO4pCJHElIRFqLCt76cAUSGmCyIhURLCPKjtZYJ7QTi/5YQoQyE1V+H1J8EBtJq0dBm5DHLMhX1TWvtNgFyNmyCjIsZIPJYgAu2JaocTmDdjAFaVITj56+45MgJShluBj3g45Co4BiZ19blHvD+dv1+Yaj1uEYICkPsQny50ii2HW+exqUZ4fpHh+PPH4idz+gfzBz6fE7yXT1dQAAAAAElFTkSuQmCC",
    "bat":      "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAASFBMVEUAAAAAAAARDAknIR4sIRs0NDRGPTtHODBOTk5cS0RfSDtnWlNvUld0cLh5+v+Hd2uMjIySblubdWGieWSiemWpf2izh2+3t7cQtBvaAAAAAXRSTlMAQObYZgAAARlJREFUeNqlUwFuhDAMm8ldDpacRhjt/v/TmcBUiUOg01yKktiyahU+rgHijEFMZcAhP5QpVkUdcMRX8llZhOKF1zkMW20Wew8MYclvFnXnAeWoCWL63izAtRmUCLQ0IoIsl4fIAfHnMJf4vJH03JzcghGjncGsxANUAsjojxLWDklFTKKLwHsPkFeZovEkZjETWA2PahBlN1PZMi2cdj36J3enVsLQkkNhEVW6atKL1U4YkQptMTUIky8Z8cO3ZavtmsGRmYr7HXd3UWVPtgELzbkD8KwMu6tT6UTNx+fotpT76wUFHDu4lFXjWxCAFnk4AQ6+D6SNOjey2wH5Wi8x20NAIdwXv8AZn97/AlYccy+4Upy7vJPzF627DIIFXqo1AAAAAElFTkSuQmCC",
    "skeleton": "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAATlBMVEUAAAAAAAAPDw8fHx8rJh03MCVCKQ5FPDFPT09TSj9jXFFvb29ybGJ0SRx/f3+Pj4+fn5+lZye9AAC/v7/Pz8/QhzrQrjzf39/v7+////8Yt6vyAAAAAXRSTlMAQObYZgAAARdJREFUeNp9k+1ygyAURF1vCaD1xuSSou//ol2/aicSDiPDuIcFf9i8AdJUQOj7gErem1nFQD9NU7KKMLUptKmvCM/UPqtHpJD6O5rPRp7Hkfk3al8pQPfBgEoQ0YePZQNZcw4qw5d30aEg2LI/mw6P18+AQgHUsqjwHIjgX4L9BmCDsEHRgNO5c8KW85ln2zYjnYKykhi4Zr8K9sK/Bgu8vq7CLfCQG9bXZ8XOshyYy3AIF+A8v/DlHRoERSHvfEfiIkgoCLGLzDkvDYZL7qMnMUZPQTMKN3DORw7HDIUTRODWFgolENhMKG6LizBiFwPIVYHtDRjHkoA542DMFwGA4cQW4227YQZZ3Qy7XGDlsDnqPznHzi8AJQwpG8sSCAAAAABJRU5ErkJggg==",
    "ghost":    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAAFVBMVEUAAABQUFCQkJCgoKCwsLDAAADAwMCxxeeXAAAAAXRSTlMAQObYZgAAAIZJREFUeNrNkkEOgEAIA9dF9v9PFp0YDli8eJB6m6YNi+PT2ccKNRy13BrHDDJbx3bJdId7fJ0jqDstLx3W8deEKR3r3FLylZzXfLiBDYOj8sZwkmqCwaGkCB5N4h6ZgLtmsF+qbjqzi5bCM4Ntq+PuGvq/gZMlb2bkkaI5HpGBAw/Tuf4xB/HmAjlBXRorAAAAAElFTkSuQmCC",
    "goblin":   "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAApVBMVEUAAAAAAAALCwsODg4ZGRkdHR0fGRUfHx8jIiAsKSgsKigvKCQ1MjE1NDM7NzY8Mi49OTg/NzJCPj1GPThIPjxMEgxQUFBRR0FcFg1eXl5fX19pGQ5wXVV5HRF7e3uFhYWIHxGIIhWJiYmKioqUJBaWJheXJxmYmJicKx2kKBmkpKSpi36wMSCzLBu1tbXDw8PFMR3FNSHNzc3p6en+tlX+v2j///+x7O0pAAAAAXRSTlMAQObYZgAAATZJREFUeNrdkuFWgkAQRvskU5Etqx13hF0LgdKUWqje/9Wa7Uemrj1AwOHA3LvfDJy9+I8HgL+51QpnoVxma7UODzHuAaW3xkgGNogJrSItAY5U+xgTnC98Y1TpXctFtIejT9aKPogY8SkLanxbChYeFSSjLMkVQx1VMEy4HwxeXaJTm+KU31+p5PntZVWMlNWWcSKwEaNtXGJGRnHNOOalCkaSmNTc1exr/KYAe0cwUzuyqZ1yeGfsedV7Jxw7Mw3nDS5w0AMNN0xSXXcqVWm5E4Sa903Qc4lQXD11Xbdbz3NI7SACCPfJ4mFZ5fMqz0SofI/jD13cLrMqy7NsjOjewnU2m+STSxoT4v+aZk5QQUUQYgmbRgQxNowzxjdH4xAXJCEg0SjO35uKEEapuI9N+bPocPUXYJAbG2C0BSUAAAAASUVORK5CYII=",
    "spider":   "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAABelBMVEUAAACARjSXV0MAAAACAgAJBAMT/y8dDwcjEgkjEwknFAkrFA8wFRAzGw00GBA3GRE8IBA9GxU+IhE/IxFCIBZCIxJCJhJDJRNFJhNHIRlHJxNHKhNHKhlHKxNJIxlJKBlKIxpKKBRLKxVQMRxSMRZVMBdYLxhYOyJZNR9ZNiFdNBlfMxlfNRlkOBpmPyhpNwtpOCptPR1wQR5zOx90QiB5QjF+SSKBTCGMUBqPUj+ZUzubTgWcUwqoWRKuXgCwaAK0WgK1XQO2XgC4WwC4XwDAaADEYQDGZgDGcADGdADIYwDKZADLfgXNdxvSdwDTdw/aewDakADccgDcgQDckQDebgDgeQDgmQDidQDkgQDkhgDudgDwgwLwrwDymgDzph/4ngL6gQD/hAH/hQP/kQ//kgX/khH/lBX/mQf/mhf/oAv/pw//rAv/rA3/rBv/rR3/rwP/sh3/tBP/tx3/uA3/uB//yCH/1kf/3lv/3mv/32H/4GX/4VP////1MlzfAAAAA3RSTlMAAAD6dsTeAAAB+klEQVR4AXWS/ZtKQRiG8Si8SyanqPUR4V1il93sECaxG0M+1Ma22mV3Ea2PhOgsf7yZqVzF6fzQnOu973meOVezY9wDAGOh5ftmWWA8xsLKJ30lM2LAzvuvvLCWl8t1OZyBFKCqgONLawnOtEpzkxjiqkrFZIxh+FOdmE7kWxfmBgkAiIqpFIxGEKvf8tOcb7+Upybg8O5K7HsBiBRTxvvQXly9dXaEz0+pSJEjgEfotkv5Z+8eHO+s6PqsmAAMz00BQMQYRNtassz8/rFoF8vR+7ad5jeiCD+XpZAvfq1z85qY7HFXssuuSJFsGf58q86iqYXlAwHxL3cJoJYJrr1nPnmiIw72OSz/evVh/CJBNFl235oQ5u4xwlDAUhyIK2qx9LeYJYta1VNUaAwCNmOwNaR5/bHl8p6vyfMqR70eT56zHAiLsBQsmNX2I1dwRr1xQs7ysq9LIhsW/Oqz/5FIeTPngUoB7gRW8MuMrBC6U75znwDyzG6g92c6S5s6mIQDRDD7gcIMANVwxl+Ls7xXsTVeA4eOAMnc6JUqXxc9+KQQCt3ewL8GfM0WAhA3QxCHAUQxzMvaICEA3Gj0DzBaYQ9aa8ImJIDoPILuezpthUsbNj6H/7nahF322G5EA4TTaSfsd/EBvN+LywHpjvfnCOCj82AePP8DsJ5VcL/hY14AAAAASUVORK5CYII=",
    "orc":      "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAAQlBMVEX///8AAAAEAgAiMTkuQUsvLy81NTU7U2BQUFBfAABiRzpiiJ1tbW1+WUh/AQCYsb6kdV7JjnLW4OXf39/koYL/AwKl5AhJAAAAAXRSTlMAQObYZgAAAUhJREFUeNp9k42OpDAMg89TJu5iuimZ3fd/1UvnhMQUdAZVivxhU37+fAhDp3kW6CLxHz9EFeLeBVpzslC8a8LPz/71K379Pp19z+lC9Naf3J/P7mytA9eOV9/3/bXv7K3d3MYjie/Uq/eWl+PiRxI9q/t3W9N3zID747H2nvFrIeIGYKHW9e0vIScmX4WeUFkoLpI7poRSyPDhkMWkSwmqUREhcoGZ2+xvdTN6kFlTkqgbPvyo24hwLnkbAHIUTu/J5dXGKlIlHZz2AY1gGUgPl1iSABkHgXBSBIs4SLIgiZAOgBIAqvjIMh/EZwfepaW6B2UmDQvTs0RutHrIquWJNK++bTUPey+YPjsEahIYGkRgIqAYwf9Ua0gz4E4zHES4rh0UDtFDk58dIg6JY5h2QZ0jyNkPd/JIBcM5AdLpIrjkuP74t9Nf7hsQmDWiu9YAAAAASUVORK5CYII=",
    "dragon":   "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAAKlBMVEUAAAAAAAAEQUEHeH0Jo6US7+8kyNApMCxEST9naFOKhnGtp5rZ0s78/PyK4ufiAAAAAXRSTlMAQObYZgAAAaZJREFUeAFlk4GOwygQQ9eBK/bY8/+/e9BkozvtNICm78klGvXnLuCs+9nbn0JtYkD76PRfBz7kFtJJ/H8HNtCBiN3EXGUH/+EB0+BaR5C1lmK8vJPulry8gJO31mK9BjYGLfvjjwDIXNR6DXTzMxNNzVFDqDaLtWz8Cum9CKzSGDzdMVh4eEc0KZFz2p20VNoLh6cTtUCOqmz7sxVDLPortKUAYGnG7c9WZhsgvgkxvE2IcjydTk1skYa2AXwXVGt4fv65xizH44oiFt5hlVCJP8730nOIyq+wEQVMjznHjnDlumC29QixFoCKx0nIGQRKzsNlnptcw3VdQ+V85jFKeIal729dQHno+xprx6qDe1bGO7gtUR77aOiQky8d8zFgkjFhUNEWglCNm0KkE9ECEJ6ERgPGl1YslotOm2gEJ3MZOKbjOpp1toZRwDf4zrd8PFxjncN4wPuPCYPdLK4t3O1jQDhP01sbU8R93b4zAIrjCCqAGgt3KY+gCyDHirFpCU85PgK4joXFBCXiLcR3AL7z8P686Of96hiniSJGDzwFh4ryL0eUFWV1tdszAAAAAElFTkSuQmCC",
    "demon":    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAANlBMVEUAAAAAAABAAABgAACAAACAQACgoKCwsLDAAADAoEDBjqLgAADgqADg4OD/AAD/wAD//wD////sfaFGAAAAAXRSTlMAQObYZgAAAT5JREFUeAFVzQF2wyAMA1BjC5q8kdDd/7ITYqaplvWF6NtYptZqdttx82d/skfdqrE9+GzCb7sXwHEDEPkCfYza+If7YC8y+hD4iNEawPmIMdO1IAFFpwnc6jujS7TWkvbhwfjoEeBluiDFpA2gcP1S4Gf2D8DiHe548z8WwQaVNUtHPi7BJ8F8d5TfwgcLiDAC7IMbisKeCRmEAOk8OFZ8R0sI1LuWKMHsN4LVT6B41jYFCFbfcsOOtSVMTW3tASJScFjACGzt31eEVhBEAjNVSjDWtEIbikDs4ZUnoCiAhAB0+AZg1AvoZAuwJwAzayXB6XH+gxxnioT8dVYzOIHOamcWiOt6vU6CnA/VKVS7MaBQrT7BrOeEMfyg+gFUa8RSuPKpPT+k2EB1njGBBCIHVDMIhUAJRr2iS1fM/gDXsg2T75gWiwAAAABJRU5ErkJggg==",
    "knight":   "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAAQlBMVEX///8AAAAwMDBQUFBwcHCAgICQkJCwsLDQ0NDg4OCA//9gAADAAAC1gID1qJz/6uoAAAAVFBsiIzE2N0tIS2ZTYXstz8lrAAAAAXRSTlMAQObYZgAAAUpJREFUeAF9kYGK4zAMRPdFxka7SYrt5P9/9TSIu6ThtkOg4HmekdyvN8HXR3Ec8AliHuc5xu8EY57nGTG/BkCEHO8RwOV/w/d8VLCu/C2gWCuM/xCQhLVqjON8Et50Qhju2uQ5JdUdzXAOmCPEI8Jb1GjJY8rX72MRy0GQOfVaxyB0Lwnih8VYSrUFvcZx35dW+YmQJTwrhYUe4iKozmIKobkbmC0ibhFeDIWEZaAceweaoYMIKUgt/H8NQC9dypCQyyeJcGO79DuYCK9jhJsV4cvIz2ota/Pax7yeU4ZoEdVqobW19zlVkBFykymV0NJi1ujtkIC+pLwQyoW79PhLmiMhLAm4+3jTAVgDVLNtvCVUzyaRqCb8RwcprLDv27pyeXdt++v12jfgAnR2U1w3uGVL27aHXntepmTfnfDiBilvXpB/iafS/ANBCRIvUo+WlQAAAABJRU5ErkJggg==",
}


def _load_monster_pixmap(kind: str) -> "QPixmap | None":
    """Decodifica base64 embutido → QPixmap 192×192. Sem acesso a disco."""
    b64 = _MONSTER_B64.get(kind)
    if b64 is None:
        return None
    pm = QPixmap()
    pm.loadFromData(base64.b64decode(b64), "PNG")
    if pm.isNull():
        return None
    return pm.scaled(
        pm.width() * 6, pm.height() * 6,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.FastTransformation,
    )


class _MonsterCanvas(QLabel):
    """
    Exibe sprites de monstro via QLabel.setPixmap() — forma nativa e garantida
    do Qt de renderizar imagens. paintEvent só trata overlays (flash, dano).
    """
    clicked_at   = _Signal(int, int)
    _cache: dict = {}          # class-level: kind → QPixmap | None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(252, 216)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setStyleSheet("background: rgb(26, 22, 36);")
        self._kind       = "slime"
        self._dead       = False
        self._flash      = False
        self._has_sprite = False
        self._dmg_pos: tuple | None = None
        self._flash_t = _QTimer(self); self._flash_t.setSingleShot(True); self._flash_t.timeout.connect(self._end_flash)
        self._dmg_t   = _QTimer(self); self._dmg_t.setSingleShot(True);   self._dmg_t.timeout.connect(self._end_dmg)

    # ── sprite cache ──────────────────────────────────────────────────────────

    @classmethod
    def _sprite(cls, kind: str):
        if kind not in cls._cache:
            cls._cache[kind] = _load_monster_pixmap(kind)
        return cls._cache[kind]

    # ── public API ────────────────────────────────────────────────────────────

    def set_monster(self, kind: str, color: tuple, dead: bool = False):
        self._kind       = kind
        self._dead       = dead
        self._flash      = False
        pm = self._sprite(kind)
        if pm is not None:
            self.setPixmap(pm)        # QLabel.setPixmap — exibição nativa garantida
            self._has_sprite = True
        else:
            self.setPixmap(QPixmap())
            self._has_sprite = False
        self.update()

    def do_hit(self, x: int, y: int):
        self._flash = True; self._dmg_pos = (x, y)
        self._flash_t.start(110); self._dmg_t.start(480)
        self.update()

    # ── Qt events ─────────────────────────────────────────────────────────────

    def _end_flash(self): self._flash = False; self.update()
    def _end_dmg(self):   self._dmg_pos = None; self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked_at.emit(int(e.position().x()), int(e.position().y()))

    def paintEvent(self, event):
        if self._has_sprite:
            super().paintEvent(event)       # QLabel renderiza o pixmap
            p = QPainter(self)
            if self._dead:
                p.fillRect(self.rect(), QColor(26, 22, 36, 170))   # escurece morto
            elif self._flash:
                p.fillRect(self.rect(), QColor(255, 30, 30, 80))   # flash vermelho
            if self._dmg_pos:
                x, y = self._dmg_pos
                p.setPen(QPen(QColor(255, 55, 55)))
                f = p.font(); f.setPixelSize(19); f.setBold(True); p.setFont(f)
                p.drawText(x - 8, max(22, y - 8), "−1")
            p.end()
        else:
            # fallback: monstros QPainter originais
            p = QPainter(self)
            p.fillRect(self.rect(), QColor(26, 22, 36))
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            cx, cy = self.width() // 2, self.height() // 2 + 14
            if self._dead:
                self._draw_dead(p, cx, cy)
            else:
                getattr(self, f"_draw_{self._kind}", self._draw_slime)(p, cx, cy)
                if self._flash:
                    p.fillRect(self.rect(), QColor(255, 0, 0, 52))
            if self._dmg_pos:
                x, y = self._dmg_pos
                p.setPen(QPen(QColor(255, 55, 55)))
                f = p.font(); f.setPixelSize(19); f.setBold(True); p.setFont(f)
                p.drawText(x - 8, max(22, y - 8), "−1")
            p.end()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _eye(self, p, cx, cy, r=6, col=QColor(255,255,255)):
        p.setBrush(QBrush(col)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-r, cy-r, r*2, r*2))
        p.setBrush(QBrush(QColor(18, 18, 18)))
        p.drawEllipse(QRectF(cx-r*.45, cy-r*.45, r*.9, r*.9))

    def _star(self, p, cx, cy, r):
        p.setPen(QPen(QColor(255, 220, 0), 2))
        for i in range(4):
            a = math.radians(i * 45)
            p.drawLine(int(cx+math.cos(a)*r), int(cy+math.sin(a)*r),
                       int(cx-math.cos(a)*r), int(cy-math.sin(a)*r))

    def _draw_dead(self, p, cx, cy):
        # Corpo acinzentado
        p.setBrush(QBrush(QColor(155, 155, 155))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-42, cy-52, 84, 78))
        # Olhos X
        pen = QPen(QColor(55, 55, 55), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        for ox in (-18, 14):
            p.drawLine(int(cx+ox-9), int(cy-24), int(cx+ox+9), int(cy-8))
            p.drawLine(int(cx+ox+9), int(cy-24), int(cx+ox-9), int(cy-8))
        # Língua
        p.setBrush(QBrush(QColor(220, 55, 80))); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(cx-8, cy+6, 16, 20), 8, 8)
        # Estrelinhas
        for dx, dy in [(-50, -42), (50, -38), (2, -72)]:
            self._star(p, cx+dx, cy+dy, 9)

    # ── 10 monstros estilo Castlevania ───────────────────────────────────────

    def _draw_slime(self, p, cx, cy):
        # Gelatin tóxico (Castlevania blob)
        p.setBrush(QBrush(QColor(0,80,0,55))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-50, cy+34, 100, 18))
        body = QColor(28, 138, 18)
        p.setBrush(QBrush(body))
        # Tendrils/pingos ácidos na base
        for dx,w,h in [(-36,13,28),(-16,15,36),(6,14,32),(26,12,24)]:
            p.drawRoundedRect(QRectF(cx+dx, cy+20, w, h), 5, 8)
        # Corpo blob principal
        p.drawEllipse(QRectF(cx-52, cy-44, 104, 76))
        # Bumps irregulares no topo
        for ox,r in [(-30,20),(-4,26),(22,18),(36,14)]:
            p.drawEllipse(QRectF(cx+ox-r, cy-58, r*2, r*2))
        # Highlight ácido
        p.setBrush(QBrush(QColor(100, 240, 40, 65)))
        p.drawEllipse(QRectF(cx-34, cy-38, 28, 18))
        # Olhos reptilianos com fenda vertical (slit pupils)
        for ox in (-17, 16):
            p.setBrush(QBrush(QColor(140, 255, 0, 80))); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(cx+ox-10, cy-22, 20, 20))
            p.setBrush(QBrush(QColor(210, 255, 30)))
            p.drawEllipse(QRectF(cx+ox-7, cy-19, 14, 14))
            p.setBrush(QBrush(QColor(8,8,8)))
            p.drawRect(QRectF(cx+ox-2, cy-18, 4, 12))
        # Boca com dentes serrilhados
        p.setBrush(QBrush(QColor(8,55,5)))
        p.drawRoundedRect(QRectF(cx-16, cy+4, 32, 13), 4, 4)
        p.setBrush(QBrush(QColor(200,225,170)))
        for i in range(4):
            p.drawPolygon(QPolygonF([QPointF(cx-12+i*8,cy+4),QPointF(cx-8+i*8,cy+4),QPointF(cx-10+i*8,cy+13)]))

    def _draw_bat(self, p, cx, cy):
        # Morcego clássico de Castlevania
        body_c = QColor(62, 22, 102)
        dark    = QColor(35, 10, 62)
        p.setPen(Qt.PenStyle.NoPen)
        # Membranas das asas (couro escuro)
        mem = QColor(48, 18, 82, 225)
        p.setBrush(QBrush(mem))
        p.drawPolygon(QPolygonF([QPointF(cx-6,cy-18),QPointF(cx-104,cy-62),QPointF(cx-86,cy-6),QPointF(cx-48,cy+10),QPointF(cx-16,cy+6)]))
        p.drawPolygon(QPolygonF([QPointF(cx+6,cy-18),QPointF(cx+104,cy-62),QPointF(cx+86,cy-6),QPointF(cx+48,cy+10),QPointF(cx+16,cy+6)]))
        # Nervuras das asas
        pen = QPen(QColor(88, 38, 138), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        for tx,ty in [(-68,-50),(-46,-18),(-84,-12)]:
            p.drawLine(int(cx), int(cy-14), int(cx+tx), int(cy+ty))
        for tx,ty in [(68,-50),(46,-18),(84,-12)]:
            p.drawLine(int(cx), int(cy-14), int(cx+tx), int(cy+ty))
        p.setPen(Qt.PenStyle.NoPen)
        # Corpo
        p.setBrush(QBrush(body_c))
        p.drawEllipse(QRectF(cx-18, cy-26, 36, 46))
        # Cabeça
        p.drawEllipse(QRectF(cx-17, cy-54, 34, 32))
        # Orelhas pontiagudas
        p.setBrush(QBrush(dark))
        p.drawPolygon(QPolygonF([QPointF(cx-17,cy-50),QPointF(cx-9,cy-50),QPointF(cx-15,cy-82)]))
        p.drawPolygon(QPolygonF([QPointF(cx+9,cy-50),QPointF(cx+17,cy-50),QPointF(cx+15,cy-82)]))
        p.setBrush(QBrush(QColor(195, 75, 135)))
        p.drawPolygon(QPolygonF([QPointF(cx-15,cy-52),QPointF(cx-10,cy-52),QPointF(cx-14,cy-75)]))
        p.drawPolygon(QPolygonF([QPointF(cx+10,cy-52),QPointF(cx+15,cy-52),QPointF(cx+14,cy-75)]))
        # Olhos vermelhos brilhantes
        for ox in (-8, 8):
            p.setBrush(QBrush(QColor(255,60,20,100)))
            p.drawEllipse(QRectF(cx+ox-7, cy-44, 14, 12))
            p.setBrush(QBrush(QColor(255,85,20)))
            p.drawEllipse(QRectF(cx+ox-5, cy-42, 10, 9))
            p.setBrush(QBrush(QColor(8,3,3)))
            p.drawEllipse(QRectF(cx+ox-3, cy-41, 6, 7))
        # Presas
        p.setBrush(QBrush(QColor(238,228,215)))
        p.drawPolygon(QPolygonF([QPointF(cx-7,cy-24),QPointF(cx-3,cy-24),QPointF(cx-5,cy-11)]))
        p.drawPolygon(QPolygonF([QPointF(cx+3,cy-24),QPointF(cx+7,cy-24),QPointF(cx+5,cy-11)]))
        # Garras penduradas
        p.setBrush(QBrush(dark))
        for dx in (-12, 0, 12):
            p.drawPolygon(QPolygonF([QPointF(cx+dx-3,cy+18),QPointF(cx+dx+3,cy+18),QPointF(cx+dx,cy+32)]))

    def _draw_skeleton(self, p, cx, cy):
        # Guerreiro Esqueleto (Castlevania Skeleton Warrior)
        bone  = QColor(222, 212, 180)
        shade = QColor(165, 155, 122)
        p.setPen(Qt.PenStyle.NoPen)
        # Crânio
        p.setBrush(QBrush(bone))
        p.drawEllipse(QRectF(cx-26, cy-76, 52, 50))
        p.fillRect(int(cx-18), int(cy-32), 36, 14, bone)
        # Órbitas oculares fundas com brilho vermelho
        p.setBrush(QBrush(QColor(8,6,4)))
        p.drawEllipse(QRectF(cx-20,cy-62,16,15)); p.drawEllipse(QRectF(cx+4,cy-62,16,15))
        p.setBrush(QBrush(QColor(190,25,25,170)))
        p.drawEllipse(QRectF(cx-17,cy-59,10,9)); p.drawEllipse(QRectF(cx+7,cy-59,10,9))
        # Nariz
        p.setBrush(QBrush(QColor(8,6,4)))
        p.drawEllipse(QRectF(cx-5,cy-44,10,8))
        # Dentes
        p.setBrush(QBrush(bone))
        for i in range(5): p.fillRect(int(cx-14+i*7),int(cy-28),5,10,bone)
        p.setBrush(QBrush(QColor(8,6,4)))
        for i in range(4): p.fillRect(int(cx-11+i*7),int(cy-30),2,3,QColor(8,6,4))
        # Vértebras
        for i in range(5):
            p.setBrush(QBrush(bone if i%2==0 else shade))
            p.drawEllipse(QRectF(cx-8, cy-14+i*13, 16, 11))
        # Costelas
        pen = QPen(bone, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        for j in range(3):
            y0 = cy-10+j*13
            p.drawArc(QRectF(cx-34,y0,34,18), 0, 160*16)
            p.drawArc(QRectF(cx,y0,34,18), 180*16,-160*16)
        # Braço esquerdo segurando maça-osso
        pen2 = QPen(bone, 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen2)
        p.drawLine(int(cx-8),int(cy-12), int(cx-40),int(cy-2))
        p.drawLine(int(cx-40),int(cy-2), int(cx-52),int(cy+30))
        # Maça (cabo + bola)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(shade))
        p.fillRect(int(cx-62),int(cy-48), 7, 52, shade)
        p.setBrush(QBrush(bone))
        p.drawEllipse(QRectF(cx-67, cy-56, 18, 18))
        for a in range(0,360,60):  # pontas da maça
            ax = cx-58 + math.cos(math.radians(a))*12
            ay = cy-48 + math.sin(math.radians(a))*12
            p.drawEllipse(QRectF(ax-4, ay-4, 8, 8))
        # Braço direito
        p.setPen(pen2)
        p.drawLine(int(cx+8),int(cy-12), int(cx+42),int(cy+6))
        p.drawLine(int(cx+42),int(cy+6), int(cx+50),int(cy+34))
        # Dedos
        pen3 = QPen(bone, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen3)
        for dx in (-2,5,12): p.drawLine(int(cx+50),int(cy+34), int(cx+48+dx),int(cy+48))
        # Pernas
        pen4 = QPen(bone, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen4)
        p.drawLine(int(cx-6),int(cy+54), int(cx-18),int(cy+94))
        p.drawLine(int(cx+6),int(cy+54), int(cx+18),int(cy+94))
        # Trapo de roupa
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(55,35,22,155)))
        p.drawPolygon(QPolygonF([QPointF(cx-14,cy+50),QPointF(cx+14,cy+50),QPointF(cx+10,cy+74),QPointF(cx,cy+68),QPointF(cx-10,cy+74)]))

    def _draw_ghost(self, p, cx, cy):
        # Specter / Fantasma encapuzado (Castlevania)
        p.setBrush(QBrush(QColor(70,110,210,45))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-64, cy-84, 128, 148))
        # Manto flutuante
        shroud = [
            QPointF(cx-42,cy-64), QPointF(cx-26,cy-84), QPointF(cx,cy-90),
            QPointF(cx+26,cy-84), QPointF(cx+42,cy-64),
            QPointF(cx+50,cy+8),  QPointF(cx+40,cy+44),
            QPointF(cx+24,cy+24), QPointF(cx+12,cy+50),
            QPointF(cx,cy+30),    QPointF(cx-12,cy+50),
            QPointF(cx-24,cy+24), QPointF(cx-40,cy+44),
            QPointF(cx-50,cy+8),
        ]
        p.setBrush(QBrush(QColor(128, 168, 238, 215)))
        p.drawPolygon(QPolygonF(shroud))
        # Interior escuro do capuz
        p.setBrush(QBrush(QColor(6,8,30,210)))
        p.drawEllipse(QRectF(cx-30,cy-80,60,56))
        # Olhos com brilho azul-gelo
        for ox in (-14, 14):
            p.setBrush(QBrush(QColor(30,70,190,80)))
            p.drawEllipse(QRectF(cx+ox-10, cy-64, 20, 18))
            p.setBrush(QBrush(QColor(155, 198, 255, 230)))
            p.drawEllipse(QRectF(cx+ox-7, cy-61, 14, 13))
            p.setBrush(QBrush(QColor(4,4,26)))
            p.drawEllipse(QRectF(cx+ox-4, cy-59, 8, 9))
        # Boca gritando (oval escuro)
        p.setBrush(QBrush(QColor(4,6,24,220)))
        p.drawEllipse(QRectF(cx-10, cy-40, 20, 16))
        # Braços esqueléticos estendidos
        arm = QColor(155, 188, 235, 205)
        p.setBrush(QBrush(arm))
        p.drawEllipse(QRectF(cx-70,cy-28,30,14))
        p.drawEllipse(QRectF(cx+40,cy-28,30,14))
        pen = QPen(arm, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        for dx in (-74,-66,-58): p.drawLine(int(cx+dx),int(cy-22), int(cx+dx-6),int(cy-8))
        for dx in (48,56,64):    p.drawLine(int(cx+dx),int(cy-22), int(cx+dx+6),int(cy-8))

    def _draw_goblin(self, p, cx, cy):
        # Axe Man encurvado (Castlevania)
        skin  = QColor(88, 148, 58)
        dark  = QColor(55, 100, 35)
        p.setPen(Qt.PenStyle.NoPen)
        # Corpo encurvado para frente
        p.setBrush(QBrush(skin))
        p.drawEllipse(QRectF(cx-24, cy-10, 48, 58))
        p.drawEllipse(QRectF(cx-20, cy-30, 40, 38))
        # Cabeça com testa projetada
        p.drawEllipse(QRectF(cx-22, cy-58, 44, 38))
        p.setBrush(QBrush(dark))
        p.drawPolygon(QPolygonF([QPointF(cx-22,cy-46),QPointF(cx+22,cy-46),QPointF(cx+20,cy-38),QPointF(cx-20,cy-38)]))
        # Olhos amarelos afundados
        p.setBrush(QBrush(QColor(240,195,10)))
        p.drawEllipse(QRectF(cx-17,cy-46,12,10))
        p.drawEllipse(QRectF(cx+5,cy-46,12,10))
        p.setBrush(QBrush(QColor(8,6,4)))
        p.drawEllipse(QRectF(cx-14,cy-44,6,6)); p.drawEllipse(QRectF(cx+8,cy-44,6,6))
        # Orelhas de morcego
        p.setBrush(QBrush(skin))
        p.drawPolygon(QPolygonF([QPointF(cx-22,cy-52),QPointF(cx-34,cy-76),QPointF(cx-14,cy-52)]))
        p.drawPolygon(QPolygonF([QPointF(cx+22,cy-52),QPointF(cx+34,cy-76),QPointF(cx+14,cy-52)]))
        # Nariz e boca
        p.setBrush(QBrush(QColor(30,18,8)))
        p.drawRoundedRect(QRectF(cx-13,cy-26,26,11), 3, 3)
        p.setBrush(QBrush(QColor(225,210,158)))
        for i in range(3):
            p.drawPolygon(QPolygonF([QPointF(cx-9+i*9,cy-26),QPointF(cx-5+i*9,cy-26),QPointF(cx-7+i*9,cy-17)]))
        # Braço com machado levantado
        p.setBrush(QBrush(skin)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx+20,cy-22,20,44)); p.drawEllipse(QRectF(cx+36,cy-38,18,28))
        # Machado gótico
        axe_p = QPen(QColor(72,50,22),5,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap); p.setPen(axe_p)
        p.drawLine(int(cx+46),int(cy-46), int(cx+54),int(cy+22))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(155,155,178)))
        p.drawPolygon(QPolygonF([QPointF(cx+38,cy-62),QPointF(cx+62,cy-56),QPointF(cx+56,cy-34),QPointF(cx+42,cy-38)]))
        p.setBrush(QBrush(QColor(205,205,228)))
        p.drawPolygon(QPolygonF([QPointF(cx+40,cy-58),QPointF(cx+58,cy-53),QPointF(cx+52,cy-38),QPointF(cx+42,cy-42)]))
        # Braço esquerdo pendurado com garras
        p.setBrush(QBrush(skin))
        p.drawEllipse(QRectF(cx-40,cy-18,20,44))
        pen = QPen(dark, 2); p.setPen(pen)
        for dx in (-38,-30,-22): p.drawLine(int(cx+dx),int(cy+26),int(cx+dx-5),int(cy+40))
        # Pernas curtas
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(dark))
        p.drawEllipse(QRectF(cx-20,cy+44,18,28)); p.drawEllipse(QRectF(cx+2,cy+44,18,28))

    def _draw_spider(self, p, cx, cy):
        # Cabeça de Medusa — inimigo icônico de Castlevania
        gold  = QColor(210, 172, 38)
        skin  = QColor(222, 192, 138)
        snake = QColor(38, 148, 38)
        dark_s= QColor(18, 92, 18)
        p.setPen(Qt.PenStyle.NoPen)
        # Cobras no cabelo (11 serpentes radiando)
        for ang in range(0, 360, 33):
            a = math.radians(ang)
            dist = 50
            sx = cx + math.cos(a)*dist; sy = cy-12 + math.sin(a)*dist
            pen = QPen(snake, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            mid_x = cx + math.cos(a)*dist*0.5 + math.cos(a+1.2)*10
            mid_y = cy-12 + math.sin(a)*dist*0.5 + math.sin(a+1.2)*10
            p.drawLine(int(cx+math.cos(a)*20), int(cy-12+math.sin(a)*20), int(mid_x), int(mid_y))
            p.drawLine(int(mid_x),int(mid_y), int(sx),int(sy))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(dark_s))
            p.drawEllipse(QRectF(sx-5,sy-5,10,8))
            p.setBrush(QBrush(QColor(255,200,0)))
            p.drawEllipse(QRectF(sx-4,sy-4,3,3)); p.drawEllipse(QRectF(sx+1,sy-4,3,3))
        # Rosto
        p.setBrush(QBrush(skin)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-36, cy-50, 72, 72))
        # Coroa dourada
        p.setBrush(QBrush(gold))
        crown = [QPointF(cx-38,cy-28),QPointF(cx-38,cy-38),QPointF(cx-26,cy-48),QPointF(cx-14,cy-56),
                 QPointF(cx,cy-60),QPointF(cx+14,cy-56),QPointF(cx+26,cy-48),QPointF(cx+38,cy-38),QPointF(cx+38,cy-28)]
        p.drawPolygon(QPolygonF(crown))
        p.setBrush(QBrush(QColor(220,35,35)))
        p.drawEllipse(QRectF(cx-5,cy-60,10,10))
        p.setBrush(QBrush(QColor(38,182,222)))
        p.drawEllipse(QRectF(cx-22,cy-54,8,8)); p.drawEllipse(QRectF(cx+14,cy-54,8,8))
        # Rosto (segundo pass sobre cobras)
        p.setBrush(QBrush(skin))
        p.drawEllipse(QRectF(cx-34, cy-46, 68, 68))
        # Olhos de serpente — íris dourada com pupila fendida
        for ox in (-14, 14):
            p.setBrush(QBrush(QColor(220,178,18))); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(cx+ox-10, cy-22, 20, 18))
            p.setBrush(QBrush(QColor(8,8,8)))
            p.drawRect(QRectF(cx+ox-2, cy-21, 4, 15))
        # Nariz e boca sedutora
        p.setBrush(QBrush(QColor(178,148,98)))
        p.drawEllipse(QRectF(cx-8,cy-2,8,5)); p.drawEllipse(QRectF(cx,cy-2,8,5))
        p.setBrush(QBrush(QColor(185,58,58)))
        p.drawEllipse(QRectF(cx-14,cy+8,28,12))
        p.setBrush(QBrush(QColor(222,88,88)))
        p.drawEllipse(QRectF(cx-10,cy+10,20,7))
        # Brincos de ouro
        p.setBrush(QBrush(gold))
        p.drawEllipse(QRectF(cx-42,cy-12,10,10)); p.drawEllipse(QRectF(cx+32,cy-12,10,10))

    def _draw_orc(self, p, cx, cy):
        # Cavaleiro do Machado — Axe Knight (Castlevania)
        armor   = QColor(72, 72, 96)
        metal   = QColor(118, 118, 148)
        dark    = QColor(28, 28, 42)
        accent  = QColor(185, 28, 28)
        p.setPen(Qt.PenStyle.NoPen)
        # Machado levantado
        p.setBrush(QBrush(QColor(52, 38, 18)))
        p.fillRect(int(cx+30),int(cy-88),8,98, QColor(52,38,18))
        p.setBrush(QBrush(metal))
        p.drawPolygon(QPolygonF([QPointF(cx+18,cy-92),QPointF(cx+62,cy-84),QPointF(cx+54,cy-54),QPointF(cx+24,cy-60)]))
        p.setBrush(QBrush(QColor(200,205,230)))
        p.drawPolygon(QPolygonF([QPointF(cx+22,cy-88),QPointF(cx+56,cy-82),QPointF(cx+50,cy-58),QPointF(cx+26,cy-64)]))
        pen = QPen(QColor(240,242,255),2); p.setPen(pen)
        p.drawLine(int(cx+18),int(cy-92),int(cx+62),int(cy-84))
        p.setPen(Qt.PenStyle.NoPen)
        # Corpo com armadura
        p.setBrush(QBrush(armor))
        p.drawEllipse(QRectF(cx-40,cy-16,80,78))
        # Peitoral
        p.setBrush(QBrush(metal))
        p.drawPolygon(QPolygonF([QPointF(cx-28,cy-14),QPointF(cx+28,cy-14),QPointF(cx+24,cy+38),QPointF(cx,cy+48),QPointF(cx-24,cy+38)]))
        # Emblema (cruz)
        p.setBrush(QBrush(accent))
        p.drawEllipse(QRectF(cx-11,cy+8,22,22))
        pen = QPen(QColor(218,178,28),2); p.setPen(pen)
        p.drawLine(int(cx-7),int(cy+19),int(cx+7),int(cy+19))
        p.drawLine(int(cx),int(cy+12),int(cx),int(cy+26))
        p.setPen(Qt.PenStyle.NoPen)
        # Ombreiras
        p.setBrush(QBrush(armor))
        p.drawEllipse(QRectF(cx-64,cy-24,34,30)); p.drawEllipse(QRectF(cx+30,cy-24,34,30))
        p.setBrush(QBrush(metal))
        p.drawEllipse(QRectF(cx-60,cy-22,26,24)); p.drawEllipse(QRectF(cx+34,cy-22,26,24))
        # Braço direito (segurando machado)
        p.setBrush(QBrush(armor))
        p.drawEllipse(QRectF(cx+20,cy-10,22,50)); p.drawEllipse(QRectF(cx+20,cy+36,22,22))
        # Escudo esquerdo
        p.setBrush(QBrush(dark))
        p.drawPolygon(QPolygonF([QPointF(cx-65,cy-10),QPointF(cx-40,cy-10),QPointF(cx-40,cy+34),QPointF(cx-52,cy+56),QPointF(cx-65,cy+34)]))
        p.setBrush(QBrush(accent))
        p.drawPolygon(QPolygonF([QPointF(cx-60,cy-2),QPointF(cx-46,cy-2),QPointF(cx-46,cy+28),QPointF(cx-54,cy+42),QPointF(cx-60,cy+28)]))
        p.setBrush(QBrush(QColor(218,178,28)))
        p.drawEllipse(QRectF(cx-57,cy+10,10,10))
        # Elmo
        p.setBrush(QBrush(armor))
        p.drawEllipse(QRectF(cx-32,cy-70,64,60))
        p.fillRect(int(cx-34),int(cy-34),68,10,armor)
        p.setBrush(QBrush(dark)); p.fillRect(int(cx-26),int(cy-32),52,7,dark)
        # Olhos ardentes na fresta
        p.setBrush(QBrush(accent))
        p.drawEllipse(QRectF(cx-20,cy-31,14,5)); p.drawEllipse(QRectF(cx+6,cy-31,14,5))
        # Crista do elmo
        p.setBrush(QBrush(accent))
        p.drawPolygon(QPolygonF([QPointF(cx-7,cy-70),QPointF(cx+7,cy-70),QPointF(cx+5,cy-98),QPointF(cx,cy-104),QPointF(cx-5,cy-98)]))
        # Pernas
        p.setBrush(QBrush(metal))
        p.fillRect(int(cx-28),int(cy+58),24,44,metal); p.fillRect(int(cx+4),int(cy+58),24,44,metal)
        p.setBrush(QBrush(armor))
        p.fillRect(int(cx-30),int(cy+94),28,14,armor); p.fillRect(int(cx+2),int(cy+94),28,14,armor)

    def _draw_dragon(self, p, cx, cy):
        # Dragão Ósseo (Bone Dragon — Castlevania)
        bone  = QColor(218, 208, 174)
        shade = QColor(155, 145, 112)
        glow  = QColor(148, 228, 78)
        p.setPen(Qt.PenStyle.NoPen)
        # Cauda
        tp = QPen(bone,14,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap); p.setPen(tp)
        p.drawLine(int(cx+30),int(cy+38),int(cx+72),int(cy+70))
        tp.setWidth(9); p.setPen(tp); p.drawLine(int(cx+72),int(cy+70),int(cx+92),int(cy+50))
        tp.setWidth(6); p.setPen(tp); p.drawLine(int(cx+92),int(cy+50),int(cx+104),int(cy+62))
        p.setPen(Qt.PenStyle.NoPen)
        # Vértebras com protuberâncias
        for i in range(6):
            rs = 9 - i*0.5
            p.setBrush(QBrush(bone if i%2==0 else shade))
            p.drawEllipse(QRectF(cx-rs, cy-14+i*14, rs*2, rs*1.4))
            if i < 4:
                p.setBrush(QBrush(shade))
                p.drawPolygon(QPolygonF([QPointF(cx-5,cy-14+i*14),QPointF(cx+5,cy-14+i*14),QPointF(cx,cy-28+i*14)]))
        # Ossos das asas
        wp = QPen(bone,6,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap); p.setPen(wp)
        p.drawLine(int(cx-8),int(cy-12),int(cx-84),int(cy-62))
        p.drawLine(int(cx-8),int(cy),   int(cx-72),int(cy-28))
        p.drawLine(int(cx-8),int(cy+12),int(cx-60),int(cy+6))
        p.setPen(Qt.PenStyle.NoPen)
        # Membrana óssea translúcida
        p.setBrush(QBrush(QColor(200,190,152,95)))
        p.drawPolygon(QPolygonF([QPointF(cx-8,cy-12),QPointF(cx-84,cy-62),QPointF(cx-72,cy-28),QPointF(cx-60,cy+6),QPointF(cx-8,cy+12)]))
        # Pescoço
        np_ = QPen(bone,16,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap); p.setPen(np_)
        p.drawLine(int(cx),int(cy-18),int(cx-28),int(cy-52))
        p.drawLine(int(cx-28),int(cy-52),int(cx-18),int(cy-82))
        p.setPen(Qt.PenStyle.NoPen)
        # Crânio grande e ameaçador
        p.setBrush(QBrush(bone))
        p.drawEllipse(QRectF(cx-54,cy-108,66,54))
        p.fillRect(int(cx-36),int(cy-78),38,24,bone)
        # Espinhos no crânio
        for i,(sx,sh) in enumerate([(-46,14),(-28,20),(-10,16)]):
            p.setBrush(QBrush(shade if i%2==0 else bone))
            p.drawPolygon(QPolygonF([QPointF(cx+sx,cy-106),QPointF(cx+sx+9,cy-106),QPointF(cx+sx+4,cy-122)]))
        # Órbitas com brilho verde
        p.setBrush(QBrush(QColor(8,8,8)))
        p.drawEllipse(QRectF(cx-52,cy-102,19,17)); p.drawEllipse(QRectF(cx-26,cy-102,19,17))
        p.setBrush(QBrush(glow))
        p.drawEllipse(QRectF(cx-49,cy-99,13,11)); p.drawEllipse(QRectF(cx-23,cy-99,13,11))
        p.setBrush(QBrush(QColor(228,255,128,185)))
        p.drawEllipse(QRectF(cx-46,cy-98,7,7)); p.drawEllipse(QRectF(cx-20,cy-98,7,7))
        # Dentes serrilhados
        p.setBrush(QBrush(shade))
        for i in range(6):
            p.drawPolygon(QPolygonF([QPointF(cx-34+i*7,cy-78),QPointF(cx-30+i*7,cy-78),QPointF(cx-32+i*7,cy-64)]))
        p.setBrush(QBrush(bone))
        for i in range(5):
            p.drawPolygon(QPolygonF([QPointF(cx-31+i*7,cy-56),QPointF(cx-27+i*7,cy-56),QPointF(cx-29+i*7,cy-68)]))

    def _draw_demon(self, p, cx, cy):
        skin  = QColor(115, 155, 90)
        coat  = QColor(22, 32, 20)
        bolt  = QColor(180, 180, 200)
        glow  = QColor(230, 225, 60)
        black = QColor(12, 12, 12)
        # Shadow
        p.setBrush(QBrush(QColor(0,0,0,90))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-40, cy+82, 80, 14))
        # Legs and boots
        p.setBrush(QBrush(coat))
        p.fillRect(int(cx-28), int(cy+50), 22, 36, coat)
        p.fillRect(int(cx+6),  int(cy+50), 22, 36, coat)
        p.fillRect(int(cx-30), int(cy+82), 26, 14, QColor(30,18,8))
        p.fillRect(int(cx+4),  int(cy+82), 26, 14, QColor(30,18,8))
        # Coat body
        p.setBrush(QBrush(coat)); p.setPen(Qt.PenStyle.NoPen)
        p.drawPolygon(QPolygonF([
            QPointF(cx-44, cy-10), QPointF(cx+44, cy-10),
            QPointF(cx+50, cy+54), QPointF(cx-50, cy+54),
        ]))
        # Coat lapels
        p.setBrush(QBrush(QColor(35,46,32)))
        p.drawPolygon(QPolygonF([QPointF(cx-20,cy-10),QPointF(cx,cy+12),QPointF(cx-32,cy+28),QPointF(cx-40,cy+10)]))
        p.drawPolygon(QPolygonF([QPointF(cx+20,cy-10),QPointF(cx,cy+12),QPointF(cx+32,cy+28),QPointF(cx+40,cy+10)]))
        # Arms raised up-left and up-right
        p.setBrush(QBrush(skin))
        p.drawPolygon(QPolygonF([
            QPointF(cx-44,cy-10), QPointF(cx-56,cy-8),
            QPointF(cx-88,cy-56), QPointF(cx-76,cy-62),
        ]))
        p.drawPolygon(QPolygonF([
            QPointF(cx+44,cy-10), QPointF(cx+56,cy-8),
            QPointF(cx+88,cy-56), QPointF(cx+76,cy-62),
        ]))
        # Fists
        p.drawEllipse(QRectF(cx-98, cy-72, 30, 26))
        p.drawEllipse(QRectF(cx+68, cy-72, 30, 26))
        # Knuckles
        for i in range(4):
            p.drawEllipse(QRectF(cx-94+i*7, cy-80, 8, 8))
            p.drawEllipse(QRectF(cx+68+i*7, cy-80, 8, 8))
        # Neck (thick)
        p.fillRect(int(cx-14), int(cy-22), 28, 18, skin)
        # Neck bolts
        p.setBrush(QBrush(bolt))
        p.fillRect(int(cx-26), int(cy-20), 14, 8, bolt)
        p.fillRect(int(cx+12), int(cy-20), 14, 8, bolt)
        p.drawEllipse(QRectF(cx-28, cy-24, 10, 10))
        p.drawEllipse(QRectF(cx+18, cy-24, 10, 10))
        # Lightning from bolts
        for pts in [
            [(cx-22,cy-26),(cx-35,cy-44),(cx-25,cy-50),(cx-37,cy-64)],
            [(cx+22,cy-26),(cx+35,cy-44),(cx+25,cy-50),(cx+37,cy-64)],
        ]:
            pen = QPen(QColor(255,255,140,220), 2)
            p.setPen(pen)
            for i in range(len(pts)-1):
                p.drawLine(int(pts[i][0]),int(pts[i][1]),int(pts[i+1][0]),int(pts[i+1][1]))
        p.setPen(Qt.PenStyle.NoPen)
        # Head (square flat-top)
        p.setBrush(QBrush(skin))
        p.drawPolygon(QPolygonF([
            QPointF(cx-28, cy-22), QPointF(cx+28, cy-22),
            QPointF(cx+26, cy-72), QPointF(cx-26, cy-72),
        ]))
        # Flat-top hair block
        p.setBrush(QBrush(black))
        p.fillRect(int(cx-28), int(cy-78), 56, 14, black)
        # Forehead stitches scar
        pen = QPen(QColor(50,90,40), 2)
        p.setPen(pen)
        p.drawLine(int(cx-14), int(cy-57), int(cx+14), int(cy-57))
        for sx in [-12,-6,0,6,12]:
            p.drawLine(int(cx+sx), int(cy-62), int(cx+sx), int(cy-52))
        p.setPen(Qt.PenStyle.NoPen)
        # Eye sockets (sunken dark)
        p.setBrush(QBrush(QColor(40,20,10)))
        p.drawEllipse(QRectF(cx-18, cy-52, 14, 12))
        p.drawEllipse(QRectF(cx+4,  cy-52, 14, 12))
        # Eye glow (yellow)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QRectF(cx-15, cy-50, 8, 8))
        p.drawEllipse(QRectF(cx+7,  cy-50, 8, 8))
        # Grimacing mouth
        p.setBrush(QBrush(black))
        p.drawPolygon(QPolygonF([
            QPointF(cx-14,cy-36), QPointF(cx+14,cy-36),
            QPointF(cx+12,cy-28), QPointF(cx-12,cy-28),
        ]))
        p.setBrush(QBrush(QColor(220,215,195)))
        for tx in [-10,-5,0,5]:
            p.drawRect(QRectF(cx+tx, cy-35, 4, 6))

    def _draw_knight(self, p, cx, cy):
        robe  = QColor(18, 12, 30)
        bone  = QColor(198, 188, 155)
        blade = QColor(140, 210, 255)
        eye_c = QColor(140, 0, 210)
        # Floating shadow pool
        p.setBrush(QBrush(QColor(60,0,90,110))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-38, cy+80, 76, 14))
        # Robe body (wide trapezoid — floats, no legs)
        p.setBrush(QBrush(robe))
        p.drawPolygon(QPolygonF([
            QPointF(cx-30, cy-18), QPointF(cx+30, cy-18),
            QPointF(cx+55, cy+76), QPointF(cx-55, cy+76),
        ]))
        # Robe creases
        pen = QPen(QColor(10,6,20), 2)
        p.setPen(pen)
        for ox in [-14, 0, 14]:
            p.drawLine(int(cx+ox), int(cy-10), int(cx+ox*2), int(cy+68))
        p.setPen(Qt.PenStyle.NoPen)
        # Pointed hem fringe
        p.setBrush(QBrush(QColor(26,17,44)))
        for i, ox in enumerate(range(-44, 56, 16)):
            tip = cy + 76 + (8 if i % 2 == 0 else 16)
            p.drawPolygon(QPolygonF([
                QPointF(cx+ox-8, cy+72),
                QPointF(cx+ox+8, cy+72),
                QPointF(cx+ox,   tip),
            ]))
        # Hood (large dark oval)
        p.setBrush(QBrush(robe)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx-38, cy-86, 76, 74))
        # Hood deep shadow interior
        p.setBrush(QBrush(QColor(8,4,16)))
        p.drawEllipse(QRectF(cx-26, cy-80, 52, 62))
        # Skull face
        p.setBrush(QBrush(bone))
        p.drawEllipse(QRectF(cx-18, cy-74, 36, 40))
        # Skull jaw
        p.drawPolygon(QPolygonF([
            QPointF(cx-14,cy-40), QPointF(cx+14,cy-40),
            QPointF(cx+16,cy-28), QPointF(cx-16,cy-28),
        ]))
        # Eye sockets (dark + purple glow)
        p.setBrush(QBrush(QColor(10,5,20)))
        p.drawEllipse(QRectF(cx-14, cy-66, 13, 13))
        p.drawEllipse(QRectF(cx+1,  cy-66, 13, 13))
        p.setBrush(QBrush(eye_c))
        p.drawEllipse(QRectF(cx-11, cy-63, 7, 7))
        p.drawEllipse(QRectF(cx+4,  cy-63, 7, 7))
        # Nose cavity
        p.setBrush(QBrush(QColor(12,6,22)))
        p.drawPolygon(QPolygonF([QPointF(cx-3,cy-48),QPointF(cx+3,cy-48),QPointF(cx,cy-42)]))
        # Teeth gap and teeth
        p.fillRect(int(cx-14), int(cy-36), 28, 3, QColor(12,6,22))
        p.setBrush(QBrush(bone))
        for tx in [-12,-7,-2,3,8]:
            p.drawRect(QRectF(cx+tx, cy-36, 4, 8))
        # Left skeletal hand (gripping scythe)
        p.setBrush(QBrush(bone))
        p.drawEllipse(QRectF(cx-36, cy-10, 14, 16))
        for fdx, fdy in [(-38,-20),(-33,-22),(-27,-22),(-22,-14)]:
            p.drawEllipse(QRectF(cx+fdx, cy+fdy, 7, 10))
        # Right skeletal hand (raised toward blade)
        p.drawEllipse(QRectF(cx+22, cy-10, 14, 16))
        for fdx, fdy in [(22,-20),(28,-22),(34,-22),(38,-14)]:
            p.drawEllipse(QRectF(cx+fdx, cy+fdy, 7, 10))
        # Scythe handle (dark diagonal pole)
        pen = QPen(QColor(55,38,18), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(int(cx-30), int(cy+10), int(cx+52), int(cy-76))
        p.setPen(Qt.PenStyle.NoPen)
        # Scythe blade fill (icy blue-white)
        p.setBrush(QBrush(QColor(100,175,240,150)))
        p.drawPolygon(QPolygonF([
            QPointF(cx+52, cy-76),
            QPointF(cx+16, cy-100),
            QPointF(cx-18, cy-82),
            QPointF(cx+2,  cy-66),
            QPointF(cx+44, cy-72),
        ]))
        # Blade edge highlight
        pen = QPen(blade, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(int(cx+52), int(cy-76), int(cx+16), int(cy-100))
        p.drawLine(int(cx+16), int(cy-100), int(cx-18), int(cy-82))
        p.drawLine(int(cx-18), int(cy-82), int(cx+2),   int(cy-66))
        p.setPen(Qt.PenStyle.NoPen)
        # Blade glow halo
        p.setBrush(QBrush(QColor(120,190,255,40)))
        p.drawEllipse(QRectF(cx-24, cy-108, 84, 40))


class StressPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent,
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._order: list[int] = []
        self._cur       = 0
        self._hp        = 0
        self._maxhp     = 0
        self._kills     = 0
        self._dead      = False
        self._time_left = 0   # unidades de 100 ms
        self._time_max  = 0
        self._time_tick = _QTimer(self)
        self._time_tick.setInterval(100)
        self._time_tick.timeout.connect(self._tick_time)
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._card = QFrame(); self._card.setObjectName("stress-card")
        self._card.setFixedWidth(292)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        # Header
        hdr = QFrame(); hdr.setObjectName("stress-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        self._title_lbl = QLabel("💢  Zona Anti-Stress"); self._title_lbl.setObjectName("stress-title")
        cls = QPushButton("✕"); cls.setObjectName("stress-close")
        cls.setFixedSize(22, 22); cls.clicked.connect(self.hide)
        hh.addWidget(self._title_lbl); hh.addStretch(); hh.addWidget(cls)
        v.addWidget(hdr)

        # ── Battle frame ──────────────────────────────────────────────────────
        self._battle_frame = QWidget(); self._battle_frame.setObjectName("stress-body")
        bv = QVBoxLayout(self._battle_frame)
        bv.setContentsMargins(14, 10, 14, 14); bv.setSpacing(8)

        # Counter dots
        self._counter_lbl = QLabel()
        self._counter_lbl.setObjectName("stress-counter")
        self._counter_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv.addWidget(self._counter_lbl)

        # Time bar
        time_row = QHBoxLayout(); time_row.setSpacing(6)
        self._time_bar = _TimeBar()
        self._time_lbl = QLabel(); self._time_lbl.setObjectName("stress-timelbl")
        self._time_lbl.setFixedWidth(28)
        self._time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        time_row.addWidget(self._time_bar)
        time_row.addWidget(self._time_lbl)
        bv.addLayout(time_row)

        # Canvas
        self._canvas = _MonsterCanvas()
        self._canvas.clicked_at.connect(self._on_hit)
        bv.addWidget(self._canvas, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Monster name + HP
        row = QHBoxLayout(); row.setSpacing(10)
        self._mon_name = QLabel(); self._mon_name.setObjectName("stress-monname")
        self._hp_lbl   = QLabel(); self._hp_lbl.setObjectName("stress-hplbl")
        row.addWidget(self._mon_name); row.addStretch(); row.addWidget(self._hp_lbl)
        bv.addLayout(row)

        self._hp_bar = _HPBar()
        bv.addWidget(self._hp_bar)

        hint = QLabel("⚔  Clique para atacar!"); hint.setObjectName("stress-hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv.addWidget(hint)

        v.addWidget(self._battle_frame)

        # ── Victory frame ─────────────────────────────────────────────────────
        self._victory_frame = QWidget(); self._victory_frame.setObjectName("stress-body")
        vv = QVBoxLayout(self._victory_frame)
        vv.setContentsMargins(14, 20, 14, 20); vv.setSpacing(14)

        trophy = QLabel("🏆"); trophy.setObjectName("stress-trophy")
        trophy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vv.addWidget(trophy)

        self._win_lbl = QLabel(); self._win_lbl.setObjectName("stress-winmsg")
        self._win_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._win_lbl.setWordWrap(True)
        vv.addWidget(self._win_lbl)

        restart = QPushButton("🔄  Nova Rodada"); restart.setObjectName("stress-btn")
        restart.clicked.connect(self._start_game)
        vv.addWidget(restart)

        self._victory_frame.setVisible(False)
        v.addWidget(self._victory_frame)

        # ── Defeat frame ──────────────────────────────────────────────────────
        self._defeat_frame = QWidget(); self._defeat_frame.setObjectName("stress-body")
        dv = QVBoxLayout(self._defeat_frame)
        dv.setContentsMargins(14, 20, 14, 20); dv.setSpacing(14)

        skull = QLabel("💀"); skull.setObjectName("stress-trophy")
        skull.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dv.addWidget(skull)

        self._lose_lbl = QLabel(); self._lose_lbl.setObjectName("stress-winmsg")
        self._lose_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lose_lbl.setWordWrap(True)
        dv.addWidget(self._lose_lbl)

        retry = QPushButton("🔄  Tentar Novamente"); retry.setObjectName("stress-btn")
        retry.clicked.connect(self._start_game)
        dv.addWidget(retry)

        self._defeat_frame.setVisible(False)
        v.addWidget(self._defeat_frame)

        outer.addWidget(self._card)

    # ── Game logic ────────────────────────────────────────────────────────────

    def _start_game(self):
        self._time_tick.stop()
        self._order = random.sample(range(len(_STRESS_MONSTERS)), len(_STRESS_MONSTERS))
        self._cur   = 0
        self._kills = 0
        self._dead  = False
        self._victory_frame.setVisible(False)
        self._defeat_frame.setVisible(False)
        self._battle_frame.setVisible(True)
        self._title_lbl.setText("💢  Zona Anti-Stress")
        self._load_monster()
        self.adjustSize()

    def _load_monster(self):
        m = _STRESS_MONSTERS[self._order[self._cur]]
        self._hp = self._maxhp = m["hp"]
        self._time_left = self._time_max = m["time"] * 10  # unidades 100 ms
        self._canvas.set_monster(m["kind"], m["color"])
        self._mon_name.setText(m["name"])
        self._update_counter()
        self._update_hp()
        self._update_time()
        self._time_tick.start()

    def _on_hit(self, x: int, y: int):
        if self._dead or self._hp <= 0:
            return
        self._hp -= 1
        self._canvas.do_hit(x, y)
        self._update_hp()
        if self._hp <= 0:
            self._kill_monster()

    def _kill_monster(self):
        self._time_tick.stop()
        self._dead = True
        m = _STRESS_MONSTERS[self._order[self._cur]]
        self._canvas.set_monster(m["kind"], m["color"], dead=True)
        self._kills += 1
        self._update_counter()
        if self._kills >= len(_STRESS_MONSTERS):
            _QTimer.singleShot(900, self._show_victory)
        else:
            self._cur += 1
            self._dead = False
            _QTimer.singleShot(950, self._load_monster)

    def _tick_time(self):
        if self._dead or self._hp <= 0:
            return
        self._time_left -= 1
        self._update_time()
        if self._time_left <= 0:
            self._time_tick.stop()
            self._monster_wins()

    def _monster_wins(self):
        self._dead = True
        m = _STRESS_MONSTERS[self._order[self._cur]]
        self._canvas.set_monster(m["kind"], m["color"], dead=False)
        _QTimer.singleShot(400, self._show_defeat)

    def _show_victory(self):
        self._battle_frame.setVisible(False)
        self._victory_frame.setVisible(True)
        self._title_lbl.setText("🏆  Vitória!")
        self._win_lbl.setText(random.choice(_STRESS_WIN_MSGS))
        self.adjustSize()

    def _show_defeat(self):
        self._battle_frame.setVisible(False)
        self._defeat_frame.setVisible(True)
        self._title_lbl.setText("💀  Derrota!")
        self._lose_lbl.setText(random.choice(_STRESS_LOSE_MSGS))
        self.adjustSize()

    def _update_hp(self):
        ratio = self._hp / self._maxhp if self._maxhp else 0
        self._hp_bar.set_ratio(ratio)
        self._hp_lbl.setText(f"{self._hp} / {self._maxhp}")

    def _update_time(self):
        ratio = self._time_left / self._time_max if self._time_max else 0
        self._time_bar.set_ratio(ratio)
        secs = math.ceil(self._time_left / 10)
        self._time_lbl.setText(f"{secs}s")

    def _update_counter(self):
        parts = []
        for i in range(len(_STRESS_MONSTERS)):
            if i < self._kills:     parts.append("☠")
            elif i == self._cur:    parts.append("⚔")
            else:                   parts.append("○")
        self._counter_lbl.setText("  ".join(parts))

    # ── Tema ──────────────────────────────────────────────────────────────────

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light = mode == "light"
        text  = "#1c1c1e"            if is_light else "#e5e5ea"
        muted = "rgba(0,0,0,0.45)"  if is_light else "rgba(255,255,255,0.40)"
        sep   = "rgba(0,0,0,0.07)"  if is_light else "rgba(255,255,255,0.07)"
        canvas_bg = "rgba(0,0,0,0.06)" if is_light else "rgba(255,255,255,0.04)"
        self._card.setStyleSheet(f"""
            QFrame#stress-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#stress-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#stress-title {{ color:{text}; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QPushButton#stress-close {{ color:{muted}; background:transparent; border:none;
                border-radius:11px; font-size:12px;
                min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px; }}
            QPushButton#stress-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QWidget#stress-body {{ background:transparent; }}
            QLabel#stress-counter {{ color:{muted}; font-size:14px; letter-spacing:2px;
                background:transparent; font-family:"SF Pro Text","Segoe UI",sans-serif; }}
            QLabel#stress-monname {{ color:{text}; font-size:14px; font-weight:700;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QLabel#stress-hplbl {{ color:{muted}; font-size:12px;
                font-family:"Consolas","Cascadia Code",monospace; background:transparent; }}
            QLabel#stress-hint {{ color:{muted}; font-size:11px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QLabel#stress-timelbl {{ color:{muted}; font-size:10px;
                font-family:"Consolas","Cascadia Code",monospace; background:transparent; }}
            QLabel#stress-trophy {{ font-size:52px; background:transparent; }}
            QLabel#stress-winmsg {{ color:{text}; font-size:12px; line-height:1.5;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent; }}
            QPushButton#stress-btn {{ background:#0a84ff; color:#fff; border:none;
                border-radius:9px; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; padding:10px; }}
            QPushButton#stress-btn:hover {{ background:#0070e0; }}
        """)

    def show_at(self, pos: QPoint):
        _popup_show_at(self, pos)


# ══════════════════════════════════════════════════════════════════════════════
# Main pill window
# ══════════════════════════════════════════════════════════════════════════════

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

        self._pomodoro  = PomodoroModule()
        self._clipboard = ClipboardModule()
        self._spotify   = SpotifyModule()
        self._spotify_w = SpotifyWidget(self._spotify)
        self._yt_module = YouTubeFeedModule()

        self._clip_popup   = ClipboardPopup(self._clipboard)
        self._yt_popup     = YouTubePopup(self._yt_module)
        self._notes_popup  = NotesPopup()
        self._alarm_popup  = AlarmPopup()
        self._quotes_popup = QuotesPopup()
        self._todo_popup   = TodoPopup()
        self._slideshow    = PhotoSlideshow()
        self._hcalc_popup  = HoursCalcPopup()
        self._pokemon_popup = PokemonPopup()
        self._stress_popup  = StressPopup()
        self._settings_win = SettingsWindow(self._sections_state)

        self._build_ui()
        self._connect_signals()
        self._load_styles()
        self._load_settings()
        self._position_top_center()
        self._setup_tray()

        self._pomodoro_label.setText(self._pomodoro.display())
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

        spotify_w   = self._spotify_w
        sep1        = self._vline()
        pomodoro_w  = self._build_pomodoro_section()
        sep2        = self._vline()
        clipboard_w = self._build_clipboard_section()
        sep3        = self._vline()
        youtube_w   = self._build_youtube_section()
        sep4        = self._vline()
        calc_w      = self._build_calc_section()
        sep5        = self._vline()
        notes_w     = self._build_notes_section()
        sep6        = self._vline()
        alarm_w     = self._build_alarm_section()
        sep7        = self._vline()
        quotes_w    = self._build_quotes_section()
        sep8        = self._vline()
        todo_w      = self._build_todo_section()
        sep9        = self._vline()
        photos_w    = self._build_photos_section()
        sep10       = self._vline()
        hcalc_w     = self._build_hcalc_section()
        sep11       = self._vline()
        pokemon_w   = self._build_pokemon_section()
        sep12       = self._vline()
        stress_w    = self._build_stress_section()

        for w in (spotify_w, sep1, pomodoro_w, sep2, clipboard_w, sep3, youtube_w,
                  sep4, calc_w, sep5, notes_w, sep6, alarm_w, sep7, quotes_w,
                  sep8, todo_w, sep9, photos_w, sep10, hcalc_w, sep11, pokemon_w,
                  sep12, stress_w):
            row.addWidget(w)

        self._section_info: dict[str, tuple] = {
            "spotify":   (spotify_w,   None),
            "pomodoro":  (pomodoro_w,  sep1),
            "clipboard": (clipboard_w, sep2),
            "youtube":   (youtube_w,   sep3),
            "calc":      (calc_w,      sep4),
            "notes":     (notes_w,     sep5),
            "alarm":     (alarm_w,     sep6),
            "quotes":    (quotes_w,    sep7),
            "todo":      (todo_w,      sep8),
            "photos":    (photos_w,    sep9),
            "hcalc":     (hcalc_w,    sep10),
            "pokemon":   (pokemon_w,  sep11),
            "stress":    (stress_w,   sep12),
        }

        root.addWidget(self._pill)

    def _vline(self) -> QFrame:
        line = QFrame()
        line.setObjectName("separator")
        line.setFrameShape(QFrame.Shape.VLine)
        return line

    def _build_pomodoro_section(self) -> QWidget:
        w = QWidget(); w.setProperty("class", "section")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0); h.setSpacing(6)

        self._pomo_icon_btn = _icon_btn(_ic_timer)
        self._pomo_icon_btn.setToolTip("Alterar duração do Pomodoro")
        self._pomo_icon_btn.clicked.connect(self._show_pomo_picker)

        self._pomodoro_label = QLabel("25:00")
        self._pomodoro_label.setObjectName("pomodoro-time")
        self._pomodoro_label.setFixedWidth(48)

        self._pomo_toggle = _icon_btn(_ic_play)
        self._pomo_reset  = _icon_btn(_ic_reset)

        h.addWidget(self._pomo_icon_btn)
        h.addWidget(self._pomodoro_label)
        h.addWidget(self._pomo_toggle)
        h.addWidget(self._pomo_reset)
        return w

    def _build_clipboard_section(self) -> QWidget:
        w = QWidget(); w.setProperty("class", "section")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0); h.setSpacing(6)

        clip_icon = QLabel("⊞")
        clip_icon.setFixedWidth(16)
        clip_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clip_icon.setStyleSheet("font-size:15px; color: rgba(255,255,255,0.45);")

        self._clip_count = QLabel("0")
        self._clip_count.setObjectName("clip-count")
        self._clip_count.setFixedWidth(18)

        self._clip_btn = _icon_btn(_ic_clip_open)

        h.addWidget(clip_icon)
        h.addWidget(self._clip_count)
        h.addWidget(self._clip_btn)
        return w

    def _build_youtube_section(self) -> QWidget:
        w = QWidget(); w.setProperty("class", "section")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0); h.setSpacing(6)

        self._yt_btn = _icon_btn(_ic_youtube)
        self._yt_btn.setToolTip("YouTube Feed")

        h.addWidget(self._yt_btn)
        return w

    def _build_calc_section(self) -> QWidget:
        w = QWidget(); w.setProperty("class", "section")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0); h.setSpacing(6)
        self._calc_btn = _icon_btn(_ic_calc)
        self._calc_btn.setToolTip("Calculadora")
        h.addWidget(self._calc_btn)
        return w

    def _build_notes_section(self) -> QWidget:
        w = QWidget(); w.setProperty("class", "section")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0); h.setSpacing(6)
        self._notes_btn = _icon_btn(_ic_notes)
        self._notes_btn.setToolTip("Notas")
        h.addWidget(self._notes_btn)
        return w

    def _build_alarm_section(self) -> QWidget:
        w = QWidget(); w.setProperty("class", "section")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0); h.setSpacing(6)
        self._alarm_btn = _icon_btn(_ic_alarm)
        self._alarm_btn.setToolTip("Despertador")
        h.addWidget(self._alarm_btn)
        return w

    def _build_quotes_section(self) -> QWidget:
        w = QWidget(); w.setProperty("class", "section")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0); h.setSpacing(6)
        self._quotes_btn = _icon_btn(_ic_quotes)
        self._quotes_btn.setToolTip("Motivação")
        h.addWidget(self._quotes_btn)
        return w

    def _build_todo_section(self) -> QWidget:
        w = QWidget(); w.setProperty("class", "section")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0); h.setSpacing(6)
        self._todo_btn = _icon_btn(_ic_todo)
        self._todo_btn.setToolTip("Tarefas")
        h.addWidget(self._todo_btn)
        return w

    def _build_photos_section(self) -> QWidget:
        w = QWidget(); w.setProperty("class", "section")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0); h.setSpacing(6)
        self._photos_btn = _icon_btn(_ic_photo)
        self._photos_btn.setToolTip("Fotos")
        h.addWidget(self._photos_btn)
        return w

    def _build_hcalc_section(self) -> QWidget:
        w = QWidget(); w.setProperty("class", "section")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0); h.setSpacing(6)
        self._hcalc_btn = _icon_btn(_ic_hcalc)
        self._hcalc_btn.setToolTip("Calculadora de Horas")
        h.addWidget(self._hcalc_btn)
        return w

    def _build_pokemon_section(self) -> QWidget:
        w = QWidget(); w.setProperty("class", "section")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0); h.setSpacing(6)
        self._pokemon_btn = _icon_btn(_ic_pokemon)
        self._pokemon_btn.setToolTip("Pokémon Aleatório")
        h.addWidget(self._pokemon_btn)
        return w

    def _build_stress_section(self) -> QWidget:
        w = QWidget(); w.setProperty("class", "section")
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0); h.setSpacing(6)
        self._stress_btn = _icon_btn(_ic_stress)
        self._stress_btn.setToolTip("Zona Anti-Stress")
        h.addWidget(self._stress_btn)
        return w

    # ── Signals ───────────────────────────────────────────────────────────────

    def _connect_signals(self):
        # Pomodoro
        self._pomodoro.tick.connect(self._on_pomo_tick)
        self._pomodoro.mode_changed.connect(self._on_pomo_mode)
        self._pomodoro.session_done.connect(lambda msg: notify("Pomodoro", msg))
        self._pomo_toggle.clicked.connect(self._toggle_pomodoro)
        self._pomo_reset.clicked.connect(self._pomodoro.reset)

        # Clipboard
        self._clipboard.history_changed.connect(
            lambda: self._clip_count.setText(str(self._clipboard.count()))
        )
        self._clip_btn.clicked.connect(self._show_clipboard)

        # YouTube
        self._yt_module.status_changed.connect(self._on_yt_status)
        self._yt_module.error.connect(lambda msg: self._on_yt_status(f"Erro: {msg[:50]}"))
        self._yt_btn.clicked.connect(self._show_youtube)

        # New sections
        self._calc_btn.clicked.connect(self._open_calc)
        self._notes_btn.clicked.connect(self._show_notes)
        self._alarm_btn.clicked.connect(self._show_alarm)
        self._quotes_btn.clicked.connect(self._show_quotes)
        self._todo_btn.clicked.connect(self._show_todo)
        self._photos_btn.clicked.connect(self._toggle_slideshow)
        self._hcalc_btn.clicked.connect(self._show_hcalc)
        self._pokemon_btn.clicked.connect(self._show_pokemon)
        self._stress_btn.clicked.connect(self._show_stress)

        # Settings
        self._settings_win.section_toggled.connect(self._on_section_toggled)
        self._settings_win.youtube_connect.connect(self._on_yt_connect)
        self._settings_win.youtube_refresh.connect(self._yt_module.refresh)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_pomo_tick(self, text: str):
        self._pomodoro_label.setText(text)

    def _on_pomo_mode(self, mode: str):
        self._pomodoro_label.setProperty("mode", mode)
        self._pomodoro_label.style().unpolish(self._pomodoro_label)
        self._pomodoro_label.style().polish(self._pomodoro_label)
        if not self._pomodoro.running:
            _refresh_icon(self._pomo_toggle, _ic_play, color=self._icon_color)
            self._pomo_toggle.setObjectName("")
            self._pomo_toggle.style().unpolish(self._pomo_toggle)
            self._pomo_toggle.style().polish(self._pomo_toggle)

    def _toggle_pomodoro(self):
        self._pomodoro.toggle()
        if self._pomodoro.running:
            _refresh_icon(self._pomo_toggle, _ic_pause, color=self._icon_color)
            self._pomo_toggle.setObjectName("pomo-btn-active")
        else:
            _refresh_icon(self._pomo_toggle, _ic_play, color=self._icon_color)
            self._pomo_toggle.setObjectName("")
        self._pomo_toggle.style().unpolish(self._pomo_toggle)
        self._pomo_toggle.style().polish(self._pomo_toggle)

    def _show_clipboard(self):
        pos = self._clip_btn.mapToGlobal(QPoint(0, self._clip_btn.height() + 6))
        self._clip_popup.show_at(pos)

    def _show_youtube(self):
        pos = self._yt_btn.mapToGlobal(
            QPoint(self._yt_btn.width() // 2, self._yt_btn.height() + 6)
        )
        self._yt_popup.show_at(pos)

    def _open_calc(self):
        try:
            subprocess.Popen(["calc.exe"])
        except FileNotFoundError:
            subprocess.Popen(["gnome-calculator"], stderr=subprocess.DEVNULL)

    def _show_notes(self):
        pos = self._notes_btn.mapToGlobal(
            QPoint(self._notes_btn.width() // 2, self._notes_btn.height() + 6))
        self._notes_popup.show_at(pos)

    def _show_alarm(self):
        pos = self._alarm_btn.mapToGlobal(
            QPoint(self._alarm_btn.width() // 2, self._alarm_btn.height() + 6))
        self._alarm_popup.show_at(pos)

    def _show_quotes(self):
        pos = self._quotes_btn.mapToGlobal(
            QPoint(self._quotes_btn.width() // 2, self._quotes_btn.height() + 6))
        self._quotes_popup.show_at(pos)

    def _show_todo(self):
        pos = self._todo_btn.mapToGlobal(
            QPoint(self._todo_btn.width() // 2, self._todo_btn.height() + 6))
        self._todo_popup.show_at(pos)

    def _toggle_slideshow(self):
        if self._slideshow.isVisible():
            self._slideshow.hide()
        else:
            pos = self._photos_btn.mapToGlobal(QPoint(0, self._photos_btn.height() + 6))
            self._slideshow.move(pos)
            self._slideshow.show()
            self._slideshow.raise_()

    def _show_hcalc(self):
        pos = self._hcalc_btn.mapToGlobal(
            QPoint(self._hcalc_btn.width() // 2, self._hcalc_btn.height() + 6))
        self._hcalc_popup.show_at(pos)

    def _show_pokemon(self):
        pos = self._pokemon_btn.mapToGlobal(
            QPoint(self._pokemon_btn.width() // 2, self._pokemon_btn.height() + 6))
        if self._pokemon_popup.isVisible():
            self._pokemon_popup.hide()
            return
        self._pokemon_popup.show_at(pos)
        self._pokemon_popup._fetch_random()

    def _show_stress(self):
        pos = self._stress_btn.mapToGlobal(
            QPoint(self._stress_btn.width() // 2, self._stress_btn.height() + 6))
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
        x = pill_geo.center().x() - sw // 2
        x = max(0, min(x, screen.width() - sw))
        y = pill_geo.bottom() + 8
        self._settings_win.move(x, y)
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
        order = ["spotify", "pomodoro", "clipboard", "youtube",
                 "calc", "notes", "alarm", "quotes", "todo", "photos", "hcalc", "pokemon", "stress"]
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

    # ── Pomodoro time picker ──────────────────────────────────────────────────

    def _show_pomo_picker(self):
        menu = QMenu(self)
        menu.setStyleSheet(MENU_QSS)

        header = QAction("⏱  Duração do Pomodoro", self)
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()

        current_work = self._pomodoro.work_minutes()
        for label, work, brk, long_brk in POMO_PRESETS:
            mark = "✓  " if work == current_work else "    "
            action = QAction(f"{mark}{label}", self)
            action.setToolTip(f"Foco: {work}min · Pausa: {brk}min · Pausa longa: {long_brk}min")
            action.triggered.connect(
                lambda _, w=work, b=brk, lb=long_brk: self._set_pomo_duration(w, b, lb)
            )
            menu.addAction(action)

        btn_pos = self._pomo_icon_btn.mapToGlobal(
            QPoint(self._pomo_icon_btn.width() // 2, self._pomo_icon_btn.height() + 4)
        )
        menu.exec(btn_pos)

    def _set_pomo_duration(self, work: int, brk: int, long_brk: int):
        self._pomodoro.set_durations(work, brk, long_brk)
        if self._pomodoro.running:
            self._pomodoro.reset()
            _refresh_icon(self._pomo_toggle, _ic_play, color=self._icon_color)
            self._pomo_toggle.setObjectName("")
            self._pomo_toggle.style().unpolish(self._pomo_toggle)
            self._pomo_toggle.style().polish(self._pomo_toggle)

    # ── Cor da barra ──────────────────────────────────────────────────────────

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
        # Sync toggle states in settings window to loaded values
        for key, val in self._sections_state.items():
            if key in self._settings_win._toggles:
                self._settings_win._toggles[key].setChecked(val)
        preset = next((p for p in COLOR_PRESETS if p[0] == self._current_color), COLOR_PRESETS[0])
        self._apply_color(*preset, save=False)
        self._update_separators()

    def _save_settings(self):
        SETTINGS_PATH.write_text(
            json.dumps({"color": self._current_color, "sections": self._sections_state}),
            encoding="utf-8"
        )

    def _apply_color(self, key, _label, bg, border, _accent, mode, icon_rgba, save=True):
        self._current_color = key
        self._current_mode  = mode

        self._pill.setStyleSheet(f"""
            QFrame#pill {{
                background-color: {bg};
                border-top-left-radius:    0px;
                border-top-right-radius:   0px;
                border-bottom-left-radius: 20px;
                border-bottom-right-radius:20px;
                border-left:   1px solid {border};
                border-right:  1px solid {border};
                border-bottom: 1px solid {border};
                border-top: none;
            }}
        """)

        self.setProperty("mode", mode)
        # Limpar e re-aplicar força Qt a re-avaliar seletores de propriedade em todos os filhos
        qss = self.styleSheet()
        self.setStyleSheet("")
        self.setStyleSheet(qss)

        r, g, b, a = icon_rgba
        self._icon_color = QColor(r, g, b, a)
        self._refresh_all_icons()

        self._clip_popup.apply_theme(bg, border, mode)
        self._yt_popup.apply_theme(bg, border, mode)
        self._notes_popup.apply_theme(bg, border, mode)
        self._alarm_popup.apply_theme(bg, border, mode)
        self._quotes_popup.apply_theme(bg, border, mode)
        self._todo_popup.apply_theme(bg, border, mode)
        self._hcalc_popup.apply_theme(bg, border, mode)
        self._pokemon_popup.apply_theme(bg, border, mode)
        self._stress_popup.apply_theme(bg, border, mode)
        self._settings_win.apply_theme(bg, border, mode)

        clip_lbl_color = "rgba(0,0,0,0.40)" if mode == "light" else "rgba(255,255,255,0.45)"
        for child in self.findChildren(QLabel):
            if child.text() == "⊞":
                child.setStyleSheet(f"font-size:15px; color: {clip_lbl_color};")

        if save:
            self._save_settings()

    def _refresh_all_icons(self):
        c = self._icon_color
        fn = _ic_pause if self._pomodoro.running else _ic_play
        self._spotify_w.refresh_icons(c, is_playing=self._pomodoro.running)
        _refresh_icon(self._pomo_icon_btn, _ic_timer,     color=c)
        _refresh_icon(self._pomo_reset,    _ic_reset,     color=c)
        _refresh_icon(self._clip_btn,      _ic_clip_open, color=c)
        _refresh_icon(self._yt_btn,        _ic_youtube,   color=c)
        _refresh_icon(self._calc_btn,      _ic_calc,      color=c)
        _refresh_icon(self._notes_btn,     _ic_notes,     color=c)
        _refresh_icon(self._alarm_btn,     _ic_alarm,     color=c)
        _refresh_icon(self._quotes_btn,    _ic_quotes,    color=c)
        _refresh_icon(self._todo_btn,      _ic_todo,      color=c)
        _refresh_icon(self._photos_btn,    _ic_photo,     color=c)
        _refresh_icon(self._hcalc_btn,     _ic_hcalc,    color=c)
        _refresh_icon(self._pokemon_btn,   _ic_pokemon,  color=c)
        _refresh_icon(self._stress_btn,    _ic_stress,   color=c)
        _refresh_icon(self._pomo_toggle,   fn,            color=c)

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

    # ── Posição e estilos ─────────────────────────────────────────────────────

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
        event.ignore()   # never let Qt destroy the window; hide instead
        self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── Auto-hide (estilo macOS Dock) ─────────────────────────────────────────

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


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = NotchWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
