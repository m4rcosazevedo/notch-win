import threading
import urllib.request

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt, QPoint, QObject, QEvent, QUrl, pyqtSignal
from PyQt6.QtGui import QCursor, QPixmap, QColor, QDesktopServices

from modules.youtube_feed import YouTubeFeedModule
from ui.popups.base_popup import BasePopup, popup_show_at


class ThumbnailLoader(QObject):
    loaded = pyqtSignal(str, bytes)

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
    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton):
            QDesktopServices.openUrl(QUrl(self._url))
            return True
        return False


class YouTubePopup(BasePopup):
    def __init__(self, yt_module: YouTubeFeedModule, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._yt = yt_module
        self._thumb_labels: dict[str, QLabel] = {}
        self._thumb_loader = ThumbnailLoader()
        self._thumb_loader.loaded.connect(self._on_thumb_loaded)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame(); self._card.setObjectName("yt-popup")
        self._card.setFixedWidth(400)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("yt-popup-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        title_lbl = QLabel("▶  YouTube — Inscrições"); title_lbl.setObjectName("yt-popup-title")
        close_btn = QPushButton("✕"); close_btn.setObjectName("yt-popup-close")
        close_btn.setFixedSize(22, 22); close_btn.clicked.connect(self.hide)
        hh.addWidget(title_lbl); hh.addStretch(); hh.addWidget(close_btn)
        v.addWidget(hdr)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setFixedHeight(460)

        self._list_widget = QWidget(); self._list_widget.setObjectName("yt-list")
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
                sep = QFrame(); sep.setObjectName("yt-row-sep")
                sep.setFrameShape(QFrame.Shape.HLine)
                self._list_layout.insertWidget(i * 2 + 1, sep)

    def _make_video_row(self, video) -> QFrame:
        row = QFrame(); row.setObjectName("yt-video-row")
        row.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        h = QHBoxLayout(row); h.setContentsMargins(10, 8, 14, 8); h.setSpacing(10)

        thumb_lbl = QLabel(); thumb_lbl.setObjectName("yt-thumb")
        thumb_lbl.setFixedSize(107, 60)
        thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder = QPixmap(107, 60); placeholder.fill(QColor(40, 40, 46))
        thumb_lbl.setPixmap(placeholder)
        if video.thumbnail_url:
            self._thumb_labels[video.thumbnail_url] = thumb_lbl
            self._thumb_loader.load(video.thumbnail_url)
        h.addWidget(thumb_lbl)

        info = QVBoxLayout(); info.setSpacing(3); info.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout(); top.setSpacing(4)
        ch = video.channel[:22] if len(video.channel) > 22 else video.channel
        channel_lbl = QLabel(ch); channel_lbl.setObjectName("yt-channel")
        time_lbl = QLabel(video.time_ago()); time_lbl.setObjectName("yt-time")
        top.addWidget(channel_lbl, 1); top.addWidget(time_lbl, 0)
        title_lbl = QLabel(video.title); title_lbl.setObjectName("yt-title")
        title_lbl.setWordWrap(True); title_lbl.setToolTip(video.title)
        info.addLayout(top); info.addWidget(title_lbl); info.addStretch()
        h.addLayout(info, 1)

        filt = _VideoClickFilter(video.url, parent=row)
        row.installEventFilter(filt)
        return row

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light  = mode == "light"
        text      = "#1c1c1e"              if is_light else "#e5e5ea"
        muted     = "rgba(0,0,0,0.45)"    if is_light else "rgba(255,255,255,0.40)"
        sep_color = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.07)"
        hover_bg  = "rgba(0,0,0,0.04)"    if is_light else "rgba(255,255,255,0.05)"
        close_h   = "rgba(255,80,80,0.15)"
        scroll_h  = "rgba(0,0,0,0.15)"    if is_light else "rgba(255,255,255,0.15)"
        thumb_bg  = "rgba(0,0,0,0.08)"    if is_light else "rgba(255,255,255,0.06)"

        self._card.setStyleSheet(f"""
            QFrame#yt-popup {{
                background-color: {bg}; border-radius: 16px; border: 1px solid {border};
            }}
            QFrame#yt-popup-header {{
                background: transparent; border-bottom: 1px solid {sep_color};
            }}
            QLabel#yt-popup-title {{
                color: {text}; font-size: 13px; font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QPushButton#yt-popup-close {{
                color: {muted}; background: transparent; border: none; border-radius: 11px;
                font-size: 12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#yt-popup-close:hover {{ background: {close_h}; color: #ff453a; }}
            QScrollArea {{ background: transparent; border: none; }}
            QWidget#yt-list {{ background: transparent; }}
            QFrame#yt-video-row {{ background: transparent; border: none; }}
            QFrame#yt-video-row:hover {{ background: {hover_bg}; border-radius: 8px; }}
            QLabel#yt-channel {{
                color: {muted}; font-size: 10px; font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QLabel#yt-time {{
                color: {muted}; font-size: 10px;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QLabel#yt-title {{
                color: {text}; font-size: 12px;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QLabel#yt-thumb {{ border-radius: 4px; background: {thumb_bg}; }}
            QFrame#yt-row-sep {{ color: {sep_color}; max-height: 1px; }}
            QScrollBar:vertical {{ background: transparent; width: 4px; margin: 3px 1px; }}
            QScrollBar::handle:vertical {{
                background: {scroll_h}; border-radius: 2px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

    def show_at(self, pos: QPoint):
        self._refresh(self._yt.videos)
        popup_show_at(self, pos)
