"""
YouTube Feed — busca os últimos vídeos dos canais inscritos.

Fluxo:
  1. Usuário fornece client_secrets.json (Google Cloud → YouTube Data API v3)
  2. authenticate() abre OAuth no browser; token fica em .youtube_token.json
  3. Lista de canais é cacheada em .youtube_subs.json (válida por 24 h)
  4. RSS público de cada canal é buscado em paralelo (sem quota)
  5. Top 20 vídeos mais recentes são emitidos via sinal videos_updated
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

BASE_DIR     = Path(__file__).parent.parent
TOKEN_PATH   = BASE_DIR / ".youtube_token.json"
CACHE_PATH   = BASE_DIR / ".youtube_subs.json"
SECRETS_PATH = BASE_DIR / "client_secrets.json"
FEED_URL     = "https://www.youtube.com/feeds/videos.xml?channel_id={}"

try:
    import feedparser
    _FEED_OK = True
except ImportError:
    _FEED_OK = False

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    _GOOGLE_OK = True
except ImportError:
    _GOOGLE_OK = False

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
MAX_CHANNELS  = 150   # máximo de canais para buscar RSS
MAX_PER_CHAN  = 3     # vídeos por canal
MAX_RESULTS   = 20    # total no feed
FETCH_WORKERS = 25    # threads paralelas para RSS
FETCH_TIMEOUT = 18    # segundos


@dataclass
class VideoItem:
    title:         str
    channel:       str
    url:           str
    published:     datetime
    video_id:      str = ""
    thumbnail_url: str = ""

    def time_ago(self) -> str:
        delta = int((datetime.now(timezone.utc) - self.published).total_seconds())
        if delta < 60:        return "agora"
        if delta < 3600:      return f"{delta//60}min"
        if delta < 86400:     return f"{delta//3600}h atrás"
        if delta < 86400 * 7: return f"{delta//86400}d atrás"
        return self.published.strftime("%d/%m")


class YouTubeFeedModule(QObject):
    videos_updated = pyqtSignal(list)   # list[VideoItem]
    status_changed = pyqtSignal(str)    # mensagem de status
    error          = pyqtSignal(str)

    def __init__(self, refresh_minutes: int = 30):
        super().__init__()
        self._creds: Optional[Credentials] = None
        self._channels: dict[str, str] = {}   # id → name
        self._videos: list[VideoItem] = []
        self._refresh_min = refresh_minutes
        self._secrets_path = SECRETS_PATH

        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_async)

        self._load_cache()
        self._try_load_token()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def videos(self) -> list:
        return self._videos

    def is_authenticated(self) -> bool:
        return self._creds is not None and self._creds.valid

    def has_channels(self) -> bool:
        return bool(self._channels)

    def deps_ok(self) -> tuple[bool, str]:
        if not _GOOGLE_OK:
            return False, "Instale: pip install google-api-python-client google-auth-oauthlib"
        if not _FEED_OK:
            return False, "Instale: pip install feedparser"
        return True, ""

    def set_secrets_path(self, path: str):
        self._secrets_path = Path(path) if path else SECRETS_PATH

    def authenticate(self):
        ok, msg = self.deps_ok()
        if not ok:
            self.error.emit(msg); return
        if not self._secrets_path.exists():
            self.error.emit(f"Arquivo não encontrado:\n{self._secrets_path}"); return
        threading.Thread(target=self._do_auth, daemon=True).start()

    def refresh(self):
        self._refresh_async()

    def start_polling(self):
        if self._channels:
            self._refresh_async()
        self._timer.start(self._refresh_min * 60 * 1000)

    def stop_polling(self):
        self._timer.stop()

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _try_load_token(self):
        if not _GOOGLE_OK or not TOKEN_PATH.exists():
            return
        try:
            data  = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
            creds = Credentials.from_authorized_user_info(data, SCOPES)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
            self._creds = creds
            self.status_changed.emit(f"Conectado · {len(self._channels)} canais")
        except Exception:
            self._creds = None

    def _do_auth(self):
        try:
            self.status_changed.emit("Abrindo browser para autenticação…")
            flow   = InstalledAppFlow.from_client_secrets_file(str(self._secrets_path), SCOPES)
            creds  = flow.run_local_server(port=0, open_browser=True)
            self._creds = creds
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
            self.status_changed.emit("Autenticado! Buscando canais inscritos…")
            self._fetch_subscriptions()
        except Exception as e:
            self.error.emit(f"Erro na autenticação: {e}")

    # ── Subscriptions ─────────────────────────────────────────────────────────

    def _fetch_subscriptions(self):
        try:
            yt      = build("youtube", "v3", credentials=self._creds)
            channels: dict[str, str] = {}
            page    = None
            while True:
                resp = yt.subscriptions().list(
                    part="snippet", mine=True, maxResults=50, pageToken=page
                ).execute()
                for item in resp.get("items", []):
                    snip = item["snippet"]
                    channels[snip["resourceId"]["channelId"]] = snip["title"]
                page = resp.get("nextPageToken")
                if not page:
                    break
            self._channels = channels
            self._save_cache()
            self.status_changed.emit(f"Conectado · {len(channels)} canais")
            self._refresh_async()
        except Exception as e:
            self.error.emit(f"Erro ao buscar canais: {e}")

    # ── RSS feed ──────────────────────────────────────────────────────────────

    def _refresh_async(self):
        if not self._channels or not _FEED_OK:
            return
        threading.Thread(target=self._fetch_feeds, daemon=True).start()

    def _fetch_feeds(self):
        ids    = list(self._channels.keys())[:MAX_CHANNELS]
        videos: list[VideoItem] = []

        def fetch_one(cid: str) -> list[VideoItem]:
            try:
                feed = feedparser.parse(FEED_URL.format(cid))
                name = self._channels.get(cid) or feed.feed.get("title", cid)
                items = []
                for entry in feed.entries:
                    if len(items) >= MAX_PER_CHAN:
                        break
                    link = entry.get("link", "")
                    if "/shorts/" in link:      # ignora YouTube Shorts
                        continue
                    try:
                        pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    except Exception:
                        pub = datetime.now(timezone.utc)
                    video_id = entry.get("yt_videoid", "")
                    thumb = ""
                    try:
                        mt = getattr(entry, "media_thumbnail", None)
                        if mt:
                            thumb = mt[0].get("url", "")
                    except Exception:
                        pass
                    if not thumb and video_id:
                        thumb = f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"
                    items.append(VideoItem(
                        title         = entry.get("title", ""),
                        channel       = name,
                        url           = link,
                        published     = pub,
                        video_id      = video_id,
                        thumbnail_url = thumb,
                    ))
                return items
            except Exception:
                return []

        with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
            futures = {pool.submit(fetch_one, cid): cid for cid in ids}
            for fut in as_completed(futures, timeout=FETCH_TIMEOUT):
                try:
                    videos.extend(fut.result())
                except Exception:
                    pass

        videos.sort(key=lambda v: v.published, reverse=True)
        self._videos = videos[:MAX_RESULTS]
        self.videos_updated.emit(self._videos)

    # ── Cache ─────────────────────────────────────────────────────────────────

    def _load_cache(self):
        if not CACHE_PATH.exists():
            return
        try:
            data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            self._channels = data.get("channels", {})
        except Exception:
            pass

    def _save_cache(self):
        CACHE_PATH.write_text(
            json.dumps({"channels": self._channels}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
