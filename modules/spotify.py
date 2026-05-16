import os
import threading
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    SPOTIPY_AVAILABLE = True
except ImportError:
    SPOTIPY_AVAILABLE = False

SCOPE = "user-read-playback-state user-modify-playback-state"
POLL_INTERVAL = 3000  # ms


class TrackInfo:
    def __init__(self, title="", artist="", is_playing=False):
        self.title = title
        self.artist = artist
        self.is_playing = is_playing

    def __eq__(self, other):
        return (self.title, self.artist, self.is_playing) == (other.title, other.artist, other.is_playing)


class SpotifyModule(QObject):
    track_updated = pyqtSignal(object)   # TrackInfo
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._sp = None
        self._current = TrackInfo()
        self._poll_timer = QTimer()
        self._poll_timer.setInterval(POLL_INTERVAL)
        self._poll_timer.timeout.connect(self._poll)

        if SPOTIPY_AVAILABLE:
            self._init_client()

    def _init_client(self):
        client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

        if not client_id or not client_secret:
            self.error.emit("Configure SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET no .env")
            return

        try:
            auth = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=SCOPE,
                cache_path=".spotify_cache",
                open_browser=True,
            )
            self._sp = spotipy.Spotify(auth_manager=auth)
            self._poll_timer.start()
        except Exception as e:
            self.error.emit(f"Spotify: {e}")

    def _poll(self):
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        if not self._sp:
            return
        try:
            pb = self._sp.current_playback()
            if pb and pb.get("item"):
                item = pb["item"]
                info = TrackInfo(
                    title=item["name"],
                    artist=", ".join(a["name"] for a in item["artists"]),
                    is_playing=pb["is_playing"],
                )
            else:
                info = TrackInfo()
            if info != self._current:
                self._current = info
                self.track_updated.emit(info)
        except Exception:
            pass

    def play_pause(self):
        if not self._sp:
            return
        threading.Thread(target=self._toggle_play, daemon=True).start()

    def _toggle_play(self):
        try:
            pb = self._sp.current_playback()
            if pb and pb["is_playing"]:
                self._sp.pause_playback()
            else:
                self._sp.start_playback()
        except Exception:
            pass

    def next_track(self):
        if not self._sp:
            return
        threading.Thread(target=self._sp.next_track, daemon=True).start()

    def prev_track(self):
        if not self._sp:
            return
        threading.Thread(target=self._sp.previous_track, daemon=True).start()

    @property
    def current(self) -> TrackInfo:
        return self._current

    @property
    def available(self) -> bool:
        return SPOTIPY_AVAILABLE and self._sp is not None
