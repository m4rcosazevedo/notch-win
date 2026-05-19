import random

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QWidget
from PyQt6.QtCore import Qt

from ui.popups.base_popup import BasePopup

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


class QuotesPopup(BasePopup):
    def __init__(self, parent=None):
        super().__init__(parent)
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

        next_btn = QPushButton("Próxima frase →"); next_btn.setObjectName("quotes-next-btn")
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

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light = mode == "light"
        text   = "#1c1c1e"              if is_light else "#e5e5ea"
        muted  = "rgba(0,0,0,0.45)"    if is_light else "rgba(255,255,255,0.40)"
        sep    = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.07)"
        sm_bg  = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.09)"
        sm_hov = "rgba(0,0,0,0.12)"    if is_light else "rgba(255,255,255,0.16)"
        self._card.setStyleSheet(f"""
            QFrame#quotes-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#quotes-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#quotes-title {{
                color:{text}; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QPushButton#quotes-close {{
                color:{muted}; background:transparent; border:none; border-radius:11px;
                font-size:12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#quotes-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QWidget#quotes-body {{ background:transparent; }}
            QLabel#quotes-text {{
                color:{text}; font-size:13px; font-style:italic;
                font-family:"Georgia","Times New Roman",serif; background:transparent; line-height:1.5;
            }}
            QPushButton#quotes-next-btn {{
                background:{sm_bg}; color:{text}; border:none; border-radius:9px;
                font-size:12px; font-family:"SF Pro Text","Segoe UI",sans-serif; padding:7px 14px;
            }}
            QPushButton#quotes-next-btn:hover {{ background:{sm_hov}; }}
        """)
