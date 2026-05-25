import os
import threading
import time
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright
from PyQt6.QtCore import QObject, pyqtSignal

class WhatsAppFeedModule(QObject):
    updated = pyqtSignal(list)
    new_message = pyqtSignal(dict)
    qr_code_ready = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.messages = []
        self._status = 'disconnected'
        self._running = False
        self._thread = None
        self._session_dir = Path.home() / ".notch_win" / "whatsapp_session"
        self._session_dir.mkdir(parents=True, exist_ok=True)

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._run_browser, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run_browser(self):
        try:
            with sync_playwright() as p:
                self.status_changed.emit('logging_in')
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self._session_dir),
                    headless=True,
                    user_agent=user_agent,
                    viewport={'width': 1280, 'height': 800},
                    args=["--disable-blink-features=AutomationControlled"]
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                try:
                    page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)
                except Exception as e:
                    self.status_changed.emit('error')
                    browser.close()
                    return

                while self._running:
                    is_logged = page.query_selector('#side') or page.query_selector('#pane-side') or page.query_selector('div[data-testid="chat-list"]')
                    
                    if is_logged:
                        if self._status != 'ready':
                            print("[WhatsApp] Conectado! Aguardando 5s para carregar chats...")
                            time.sleep(5) # Delay crucial para renderizar a lista
                            self._status = 'ready'
                            self.status_changed.emit('ready')
                        self._scrape_messages(page)
                    else:
                        qr_canvas = page.query_selector('canvas')
                        if qr_canvas:
                            if self._status != 'qr_ready':
                                self._status = 'qr_ready'
                                self.status_changed.emit('qr_ready')
                            try:
                                qr_bytes = qr_canvas.screenshot()
                                qr_b64 = base64.b64encode(qr_bytes).decode('utf-8')
                                self.qr_code_ready.emit(qr_b64)
                            except: pass
                        else:
                            if self._status != 'logging_in':
                                self.status_changed.emit('logging_in')

                    time.sleep(10)

                browser.close()
        except Exception as e:
            self.status_changed.emit('error')

    def _scrape_messages(self, page):
        # Script ultra-detalhado para extrair conversas
        script = """
        () => {
            const results = [];
            // Busca os itens da lista lateral por role ou por TestID do WhatsApp
            let chats = Array.from(document.querySelectorAll('div[role="listitem"]'));
            if (chats.length === 0) {
                chats = Array.from(document.querySelectorAll('div[data-testid^="list-item-"]'));
            }

            chats.forEach((chat) => {
                try {
                    // Nome do contato (span com title)
                    const senderEl = chat.querySelector('span[title]');
                    const sender = senderEl ? senderEl.getAttribute('title') : null;
                    if (!sender || sender === "WhatsApp") return;

                    // Ultima mensagem (procura o span com a classe de preview ou dir=ltr)
                    const spans = Array.from(chat.querySelectorAll('span'));
                    let content = "";
                    // Pega o span que tem texto longo e nao e o nome/hora
                    for (let s of spans) {
                        if (s.innerText && s.innerText !== sender && !s.innerText.includes(':') && s.innerText.length > 2) {
                            content = s.innerText;
                        }
                    }

                    // Hora
                    const timeEl = chat.querySelector('div[style*="grid-area: time"]') || chat.querySelector('span:last-child');
                    const time = (timeEl && timeEl.innerText.length < 10) ? timeEl.innerText : "";

                    // Bolinha de nao lida
                    const unread = !!chat.querySelector('span[aria-label*="unread"], span[aria-label*="não lida"], [class*="unread"]');

                    results.push({ sender, content, time, unread });
                } catch (e) {}
            });
            return results.slice(0, 10);
        }
        """
        try:
            raw_messages = page.evaluate(script)
            if raw_messages:
                print(f"[WhatsApp] {len(raw_messages)} conversas capturadas.")
                if raw_messages != self.messages:
                    self.messages = raw_messages
                    self.updated.emit(self.messages)
            else:
                # Se ainda estiver vazio, tenta forçar um scroll suave para "acordar" a lista
                page.mouse.wheel(0, 500)
                print("[WhatsApp] Tentando acordar a lista de chats...")
        except: pass
