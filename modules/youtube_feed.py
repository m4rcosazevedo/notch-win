"""
YouTube Feed — busca os últimos vídeos dos canais inscritos favoritados via API oficial.
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from config import BASE_DIR, YOUTUBE_ACCS_PATH

CACHE_PATH   = BASE_DIR / ".youtube_subs.json"

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    _GOOGLE_OK = True
except ImportError:
    _GOOGLE_OK = False

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
MAX_FAVORITES = 20
MAX_PER_CHAN  = 3     
MAX_RESULTS   = 25    
FETCH_WORKERS = 10    # API calls são mais pesadas, reduzimos um pouco o paralelismo
FETCH_TIMEOUT = 40    


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
    status_updated = pyqtSignal(str, str) # name, msg
    refresh_started = pyqtSignal()
    error          = pyqtSignal(str)
    favorites_changed = pyqtSignal(list) # list of channel ids

    def __init__(self, refresh_minutes: int = 30):
        super().__init__()
        self._accounts = self._load_accounts()
        self._channels: dict[str, str] = {}   # id → name (aggregated subs)
        self._favorites: list[str] = []       # list of channel ids
        self._videos: list[VideoItem] = []
        self._refresh_min = refresh_minutes
        self._secrets_path = BASE_DIR / "client_secrets.json"
        self._tokens_dir = BASE_DIR / ".tokens"
        self._tokens_dir.mkdir(exist_ok=True)

        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_async)

        self._load_cache()

    # ── Public API ────────────────────────────────────────────────────────────

    def _load_accounts(self):
        if YOUTUBE_ACCS_PATH.exists():
            try:
                return json.loads(YOUTUBE_ACCS_PATH.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def save_accounts(self, accounts):
        self._accounts = accounts
        YOUTUBE_ACCS_PATH.write_text(json.dumps(accounts), encoding="utf-8")

    @property
    def videos(self) -> list:
        return self._videos

    @property
    def favorites(self) -> list:
        return self._favorites

    @property
    def all_channels(self) -> dict:
        return self._channels

    def toggle_favorite(self, channel_id: str):
        if channel_id in self._favorites:
            self._favorites.remove(channel_id)
        else:
            if len(self._favorites) >= MAX_FAVORITES:
                return False # Limit reached
            self._favorites.append(channel_id)
        
        self._save_cache()
        self.favorites_changed.emit(self._favorites)
        self.refresh()
        return True

    def set_bulk_favorites(self, mode: str):
        """Seleciona os primeiros 20 canais ou limpa todos."""
        if mode == "none":
            self._favorites = []
        elif mode == "all":
            self._favorites = list(self._channels.keys())[:MAX_FAVORITES]
        
        self._save_cache()
        self.favorites_changed.emit(self._favorites)
        self.refresh()

    def deps_ok(self) -> tuple[bool, str]:
        if not _GOOGLE_OK:
            return False, "Instale: pip install google-api-python-client google-auth-oauthlib"
        return True, ""

    def set_secrets_path(self, path: str):
        self._secrets_path = Path(path) if path else BASE_DIR / "client_secrets.json"

    def authenticate(self, account_name: str):
        ok, msg = self.deps_ok()
        if not ok:
            self.error.emit(msg); return

        # Validação rigorosa do arquivo de segredos
        if not self._secrets_path or not self._secrets_path.exists() or not self._secrets_path.is_file():
            self.error.emit(f"Selecione um arquivo JSON de credenciais válido.\nCaminho atual: {self._secrets_path}")
            return

        def _thread():
            try:
                self.status_updated.emit(account_name, "Autenticando no browser...")
                flow = InstalledAppFlow.from_client_secrets_file(str(self._secrets_path), SCOPES)
                creds = flow.run_local_server(port=0, open_browser=True)
                
                token_path = self._tokens_dir / f"yt_{account_name}.json"
                token_path.write_text(creds.to_json())
                
                if not any(a["name"] == account_name for a in self._accounts):
                    self._accounts.append({"name": account_name})
                    self.save_accounts(self._accounts)
                
                self.status_updated.emit(account_name, "Conectado!")
                self._fetch_subscriptions_for(account_name, creds)
            except Exception as e:
                self.error.emit(f"Erro na autenticação: {e}")
                self.status_updated.emit(account_name, "Erro de login")

        threading.Thread(target=_thread, daemon=True).start()

    def refresh(self):
        self._refresh_async()

    def start_polling(self):
        self._timer.start(self._refresh_min * 60 * 1000)
        self._refresh_async()

    def stop_polling(self):
        self._timer.stop()

    # ── Subscriptions ─────────────────────────────────────────────────────────

    def _get_creds(self, name):
        token_path = self._tokens_dir / f"yt_{name}.json"
        if not token_path.exists():
            return None
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_path.write_text(creds.to_json())
            return creds
        except Exception:
            return None

    def _fetch_subscriptions_for(self, name, creds):
        try:
            # Discovery safe in threads
            yt = build("youtube", "v3", credentials=creds, static_discovery=False)
            page = None
            found_any = False
            while True:
                resp = yt.subscriptions().list(
                    part="snippet", mine=True, maxResults=50, pageToken=page
                ).execute()
                for item in resp.get("items", []):
                    snip = item["snippet"]
                    self._channels[snip["resourceId"]["channelId"]] = snip["title"]
                    found_any = True
                page = resp.get("nextPageToken")
                if not page:
                    break
            
            if found_any:
                self._save_cache()
                self.status_updated.emit(name, f"Sincronizado ({len(self._channels)} canais)")
                self.favorites_changed.emit(self._favorites)
        except Exception as e:
            print(f"Erro ao buscar canais para {name}: {e}")

    # ── API feed ──────────────────────────────────────────────────────────────

    def _refresh_async(self):
        if not self._accounts:
            return
        self.refresh_started.emit()
        threading.Thread(target=self._fetch_feeds, daemon=True).start()

    def _fetch_feeds(self):
        print(f"[YouTube] Iniciando busca via API para {len(self._favorites)} favoritos...")
        if not self._favorites:
            self._videos = []
            self.videos_updated.emit([])
            return

        # Busca a primeira credencial válida
        creds = None
        for acc in self._accounts:
            creds = self._get_creds(acc["name"])
            if creds: break
        
        if not creds:
            print("[YouTube] Nenhuma credencial válida encontrada.")
            return

        videos: list[VideoItem] = []

        def fetch_one(cid: str) -> list[VideoItem]:
            try:
                # build() inside thread avoids SSL version issues
                yt = build("youtube", "v3", credentials=creds, static_discovery=False)
                uploads_playlist_id = "UU" + cid[2:]
                
                resp = yt.playlistItems().list(
                    part="snippet",
                    playlistId=uploads_playlist_id,
                    maxResults=MAX_PER_CHAN
                ).execute()
                
                items = []
                for item in resp.get("items", []):
                    snip = item["snippet"]
                    vid_id = snip["resourceId"]["videoId"]
                    thumbs = snip.get("thumbnails", {})
                    thumb_url = ""
                    for quality in ["medium", "high", "standard", "default"]:
                        if quality in thumbs:
                            thumb_url = thumbs[quality]["url"]
                            break
                    
                    try:
                        pub_str = snip["publishedAt"].replace("Z", "+00:00")
                        pub = datetime.fromisoformat(pub_str)
                    except Exception:
                        pub = datetime.now(timezone.utc)

                    items.append(VideoItem(
                        title         = snip.get("title", ""),
                        channel       = snip.get("channelTitle", ""),
                        url           = f"https://www.youtube.com/watch?v={vid_id}",
                        published     = pub,
                        video_id      = vid_id,
                        thumbnail_url = thumb_url
                    ))
                
                print(f"  [OK] Canal {cid}: {len(items)} vídeos")
                return items
            except Exception as e:
                print(f"  [ERRO] Canal {cid} via API: {e}")
                return []

        with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
            futures = {pool.submit(fetch_one, cid): cid for cid in self._favorites[:MAX_FAVORITES]}
            for fut in as_completed(futures, timeout=FETCH_TIMEOUT):
                try:
                    res = fut.result()
                    if res: videos.extend(res)
                except Exception as e:
                    print(f"[YouTube] Falha em thread: {e}")

        videos.sort(key=lambda v: v.published, reverse=True)
        self._videos = videos[:MAX_RESULTS]
        print(f"[YouTube] Busca finalizada. Total: {len(self._videos)} vídeos.")
        self.videos_updated.emit(self._videos)

    # ── Cache ─────────────────────────────────────────────────────────────────

    def _load_cache(self):
        if not CACHE_PATH.exists():
            return
        try:
            data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            self._channels = data.get("channels", {})
            self._favorites = data.get("favorites", [])
            print(f"[YouTube] Cache carregado: {len(self._channels)} canais, {len(self._favorites)} favoritos.")
        except Exception as e:
            print(f"[YouTube] Erro ao carregar cache: {e}")

    def _save_cache(self):
        try:
            data = {
                "channels": self._channels,
                "favorites": self._favorites
            }
            CACHE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[YouTube] Cache salvo: {len(self._favorites)} favoritos.")
        except Exception as e:
            print(f"[YouTube] Erro ao salvar cache: {e}")
