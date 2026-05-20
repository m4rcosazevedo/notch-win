import json
import threading
import time
import os
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, pyqtSignal
from config import CALENDAR_PATH, BASE_DIR

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

class CalendarFeedModule(QObject):
    updated = pyqtSignal(list)
    status_updated = pyqtSignal(str, str) # account_name, status_msg
    error = pyqtSignal(str)

    def __init__(self, interval=600):
        super().__init__()
        self.interval = interval
        self._running = False
        self._configs = self._load_configs()
        self._tokens_dir = BASE_DIR / ".tokens"
        self._tokens_dir.mkdir(exist_ok=True)

    def _load_configs(self):
        if CALENDAR_PATH.exists():
            try:
                return json.loads(CALENDAR_PATH.read_text(encoding="utf-8"))
            except Exception:
                return {"google": [], "outlook": []}
        return {"google": [], "outlook": []}

    def save_configs(self, configs):
        self._configs = configs
        CALENDAR_PATH.write_text(json.dumps(configs), encoding="utf-8")

    def authenticate_google(self, account_name: str, secrets_path: str):
        """Inicia o fluxo OAuth2 para uma conta Google."""
        # Tenta o caminho padrão se o fornecido for vazio
        if not secrets_path:
            default_secrets = BASE_DIR / "client_secrets.json"
            if default_secrets.exists():
                secrets_path = str(default_secrets)
        
        if not secrets_path or not os.path.exists(secrets_path):
            self.error.emit("Arquivo JSON de credenciais não encontrado. Selecione-o na aba YouTube.")
            return

        def _thread():
            try:
                self.status_updated.emit(account_name, "Autenticando no browser...")
                flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
                creds = flow.run_local_server(port=0)
                
                # Save token
                token_path = self._tokens_dir / f"gcal_{account_name}.json"
                token_path.write_text(creds.to_json())
                
                # Update config
                configs = self._load_configs()
                if "google" not in configs: configs["google"] = []
                if not any(acc["name"] == account_name for acc in configs["google"]):
                    configs["google"].append({"name": account_name})
                
                self.save_configs(configs)
                self.status_updated.emit(account_name, "Conectado com sucesso!")
                self.refresh()
            except Exception as e:
                self.error.emit(f"Erro ao autenticar {account_name}: {str(e)}")
                self.status_updated.emit(account_name, "Falha na conexão")

        threading.Thread(target=_thread, daemon=True).start()

    def authenticate_outlook(self, account_name: str, client_id: str):
        """Inicia o fluxo OAuth2 para uma conta Outlook/Office 365."""
        def _thread():
            try:
                import msal
                import webbrowser
                authority = "https://login.microsoftonline.com/common"
                scopes = ["Calendars.Read"]
                
                app = msal.PublicClientApplication(client_id, authority=authority)
                
                # Inicia o fluxo de autorização
                self.status_updated.emit(account_name, "Autenticando no browser...")
                result = app.acquire_token_interactive(scopes=scopes)
                
                if "access_token" in result:
                    # Save token
                    token_path = self._tokens_dir / f"outlook_{account_name}.json"
                    token_path.write_text(json.dumps(result))
                    
                    configs = self._load_configs()
                    if "outlook" not in configs: configs["outlook"] = []
                    if not any(acc["name"] == account_name for acc in configs["outlook"]):
                        configs["outlook"].append({"name": account_name, "client_id": client_id})
                    
                    self.save_configs(configs)
                    self.status_updated.emit(account_name, "Conectado com sucesso!")
                    self.refresh()
                else:
                    self.error.emit(f"Falha na autenticação Outlook: {result.get('error_description')}")
            except Exception as e:
                self.error.emit(f"Erro Outlook: {str(e)}")

        threading.Thread(target=_thread, daemon=True).start()

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

    def _get_google_creds(self, account_name):
        token_path = self._tokens_dir / f"gcal_{account_name}.json"
        if not token_path.exists():
            return None
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
        return creds

    def _fetch(self):
        all_events = []
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        # Busca eventos para os próximos 7 dias para garantir uma agenda cheia
        time_max = (now + timedelta(days=7)).isoformat() + 'Z'

        # 1. Google
        for g_acc in self._configs.get("google", []):
            name = g_acc["name"]
            try:
                creds = self._get_google_creds(name)
                if not creds:
                    self.status_updated.emit(name, "Token ausente - reconecte")
                    continue
                
                service = build('calendar', 'v3', credentials=creds)
                
                # Fetch all calendars (primary, holidays, shared, etc.)
                cal_list = service.calendarList().list().execute()
                for cal in cal_list.get('items', []):
                    # Só busca se a agenda estiver visível/selecionada no Google
                    if not cal.get('selected', True) and cal.get('id') != 'primary':
                        continue

                    # Fetch top 10 events for each calendar
                    events_result = service.events().list(
                        calendarId=cal['id'], timeMin=time_min, timeMax=time_max,
                        singleEvents=True, orderBy='startTime', maxResults=10
                    ).execute()
                    
                    for e in events_result.get('items', []):
                        start = e['start'].get('dateTime', e['start'].get('date'))
                        # Parse time and date
                        dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        
                        # Formata data se não for hoje
                        if dt.date() == datetime.now().date():
                            time_str = dt.strftime("%H:%M")
                        else:
                            time_str = dt.strftime("%d/%m %H:%M")
                        
                        all_events.append({
                            "time": time_str,
                            "title": e.get('summary', 'Sem título'),
                            "account": f"{name} ({cal.get('summary')})",
                            "type": "Google",
                            "start": start
                        })
                self.status_updated.emit(name, "Sincronizado")
            except Exception as e:
                print(f"Erro ao buscar agenda Google {name}: {e}")
                self.status_updated.emit(name, "Erro de sincronização")

        # 2. Outlook Placeholder
        for o_acc in self._configs.get("outlook", []):
             pass

        # Sort events by start time
        all_events.sort(key=lambda x: x.get("start", ""))
        self.updated.emit(all_events)
