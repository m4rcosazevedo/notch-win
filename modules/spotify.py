import os
import threading
from pathlib import Path
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError
    SPOTIPY_AVAILABLE = True
except ImportError:
    SPOTIPY_AVAILABLE = False

SCOPE        = "user-read-playback-state user-modify-playback-state"
POLL_INTERVAL = 3000  # ms
REDIRECT_URI  = "http://127.0.0.1:8888/callback"


class TrackInfo:
    def __init__(self, title="", artist="", is_playing=False):
        self.title     = title
        self.artist    = artist
        self.is_playing = is_playing

    def __eq__(self, other):
        return (self.title, self.artist, self.is_playing) == (other.title, other.artist, other.is_playing)


class SpotifyModule(QObject):
    track_updated  = pyqtSignal(object)  # TrackInfo
    error          = pyqtSignal(str)
    status_changed = pyqtSignal(str)     # human-readable status

    def __init__(self):
        super().__init__()
        self._sp      = None
        self._auth    = None
        self._current = TrackInfo()
        self._poll_timer = QTimer()
        self._poll_timer.setInterval(POLL_INTERVAL)
        self._poll_timer.timeout.connect(self._poll)

        if SPOTIPY_AVAILABLE:
            # Ao iniciar, NÃO abre o browser automaticamente para evitar loops no boot
            self._init_client(open_browser=False)
        else:
            self.status_changed.emit("spotipy não instalado")

    def _init_client(self, open_browser: bool = False):
        client_id     = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
        redirect_uri  = os.getenv("SPOTIFY_REDIRECT_URI", REDIRECT_URI)

        if not client_id or not client_secret:
            self.status_changed.emit("Não configurado")
            return

        try:
            self._auth = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=SCOPE,
                cache_path=".spotify_cache",
                open_browser=open_browser,
            )
            self._sp = spotipy.Spotify(auth_manager=self._auth)
            
            # Verifica se temos um token em cache antes de começar o poll
            # Isso evita disparar o fluxo de auth se não for intencional
            token_info = self._auth.get_cached_token()
            if token_info:
                self._poll_timer.start()
                self.status_changed.emit("Conectando…")
            elif open_browser:
                # Se foi pedido explicitamente para abrir browser (ex: clicou em salvar/conectar)
                self._poll_timer.start()
                self.status_changed.emit("Autorize no navegador…")
            else:
                self.status_changed.emit("Login necessário")

        except Exception as e:
            self.error.emit(f"Spotify: {e}")
            self.status_changed.emit(f"Erro: {str(e)[:60]}")

    def reconfigure(self, client_id: str, client_secret: str):
        """Save new credentials to .env and reinitialize the client."""
        self._poll_timer.stop()
        self._sp = None
        self._auth = None

        env_path = Path(".env")
        _set_env_key(env_path, "SPOTIFY_CLIENT_ID",     client_id)
        _set_env_key(env_path, "SPOTIFY_CLIENT_SECRET",  client_secret)
        _set_env_key(env_path, "SPOTIFY_REDIRECT_URI",   REDIRECT_URI)

        os.environ["SPOTIFY_CLIENT_ID"]     = client_id
        os.environ["SPOTIFY_CLIENT_SECRET"] = client_secret
        os.environ["SPOTIFY_REDIRECT_URI"]  = REDIRECT_URI

        if SPOTIPY_AVAILABLE:
            # Ao reconfigurar via UI, queremos que o browser abra se necessário
            self._init_client(open_browser=True)

    def _poll(self):
        if not self._sp:
            return
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
            if self._current.title:
                self.status_changed.emit(f"▶ {self._current.title[:40]}")
        except SpotifyOauthError:
            self.status_changed.emit("Erro de autenticação")
            self._poll_timer.stop() # Para o poll para não ficar abrindo browser ou dando erro
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


def _set_env_key(path: Path, key: str, value: str):
    """Update or append a KEY=value line in a .env file."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}=") or line.startswith(f"{key} ="):
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
