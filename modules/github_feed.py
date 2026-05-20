import json
import threading
import time
from github import Github
from PyQt6.QtCore import QObject, pyqtSignal
from config import GITHUB_PATH


class GitHubFeedModule(QObject):
    updated = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, interval=300):
        super().__init__()
        self.interval = interval
        self._running = False
        self._tokens = self._load_tokens()
        self._fetch_last_notifications = []

    def _load_tokens(self):
        if GITHUB_PATH.exists():
            try:
                return json.loads(GITHUB_PATH.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def save_tokens(self, tokens):
        self._tokens = tokens
        GITHUB_PATH.write_text(json.dumps(tokens), encoding="utf-8")

    def set_tokens(self, tokens):
        """Atualiza os tokens e dispara um refresh imediato."""
        self.save_tokens(tokens)
        self.refresh()

    def start(self):
        if self._running: return
        self._running = True
        threading.Thread(target=self._run, daemon=True).start()

    def refresh(self):
        threading.Thread(target=self._fetch, daemon=True).start()

    def _run(self):
        while self._running:
            self._fetch()
            time.sleep(self.interval)

    def _fetch(self):
        if not self._tokens:
            self.updated.emit([])
            return

        all_notifications = []
        for token_data in self._tokens:
            try:
                g = Github(token_data["token"])
                user = g.get_user()
                notifs = g.get_user().get_notifications()
                for n in notifs[:10]:
                    all_notifications.append({
                        "account": token_data.get("name", user.login),
                        "title": n.subject.title,
                        "type": n.subject.type,
                        "repo": n.repository.full_name,
                        "url": n.subject.url # Need to convert to browser URL usually
                    })
            except Exception as e:
                self.error.emit(f"GitHub Error ({token_data.get('name')}): {str(e)}")
        
        self._fetch_last_notifications = all_notifications
        self.updated.emit(all_notifications)
