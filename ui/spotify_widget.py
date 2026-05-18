from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from modules.spotify import SpotifyModule
from ui.icons import _icon_btn, _refresh_icon, _ic_prev, _ic_next, _ic_play, _ic_pause, _DEFAULT_DARK


class SpotifyWidget(QWidget):
    def __init__(self, spotify: SpotifyModule, parent=None):
        super().__init__(parent)
        self.setProperty("class", "section")
        self._spotify = spotify
        self._color: QColor = _DEFAULT_DARK
        self._build_ui()
        self._connect()

    def _build_ui(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(4, 0, 4, 0)
        h.setSpacing(6)

        info = QVBoxLayout()
        info.setSpacing(1)

        self._track_title = QLabel("Spotify")
        self._track_title.setObjectName("track-title")
        self._track_title.setFixedHeight(17)
        self._track_title.setMaximumWidth(155)

        self._track_artist = QLabel("Não conectado")
        self._track_artist.setObjectName("track-artist")
        self._track_artist.setFixedHeight(14)
        self._track_artist.setMaximumWidth(155)

        info.addWidget(self._track_title)
        info.addWidget(self._track_artist)

        self.prev_btn = _icon_btn(_ic_prev)
        self.play_btn = _icon_btn(_ic_play)
        self.play_btn.setObjectName("play-btn")
        self.next_btn = _icon_btn(_ic_next)

        h.addLayout(info)
        h.addWidget(self.prev_btn)
        h.addWidget(self.play_btn)
        h.addWidget(self.next_btn)

    def _connect(self):
        self._spotify.track_updated.connect(self._on_track_update)
        self._spotify.error.connect(lambda msg: self._track_artist.setText(msg[:40]))
        self.play_btn.clicked.connect(self._spotify.play_pause)
        self.prev_btn.clicked.connect(self._spotify.prev_track)
        self.next_btn.clicked.connect(self._spotify.next_track)

    def _on_track_update(self, info):
        fm_t = self._track_title.fontMetrics()
        fm_a = self._track_artist.fontMetrics()
        self._track_title.setText(
            fm_t.elidedText(info.title or "Nenhuma música", Qt.TextElideMode.ElideRight, 155)
        )
        self._track_artist.setText(
            fm_a.elidedText(info.artist or "", Qt.TextElideMode.ElideRight, 155)
        )
        _refresh_icon(self.play_btn, _ic_pause if info.is_playing else _ic_play, color=self._color)

    def refresh_icons(self, color: QColor, is_playing: bool = False):
        self._color = color
        _refresh_icon(self.prev_btn, _ic_prev, color=color)
        _refresh_icon(self.next_btn, _ic_next, color=color)
        _refresh_icon(self.play_btn, _ic_pause if is_playing else _ic_play, color=color)
