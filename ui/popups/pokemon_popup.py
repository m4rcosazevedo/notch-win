import json
import random
import threading
import urllib.request

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QWidget,
)
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QPixmap

from ui.popups.base_popup import BasePopup

_TYPE_COLORS = {
    "normal": "#A8A878", "fire": "#F08030", "water": "#6890F0",
    "electric": "#F8D030", "grass": "#78C850", "ice": "#98D8D8",
    "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820",
    "rock": "#B8A038", "ghost": "#705898", "dragon": "#7038F8",
    "dark": "#705848", "steel": "#B8B8D0", "fairy": "#EE99AC",
}


class _PokeLoader(QObject):
    pokemon_loaded = pyqtSignal(dict, bytes)
    load_error     = pyqtSignal(str)

    _HEADERS = {"User-Agent": "Mozilla/5.0 NotchWin/1.0"}

    def fetch(self, pokemon_id: int):
        threading.Thread(target=self._do_fetch, args=(pokemon_id,), daemon=True).start()

    def _do_fetch(self, pokemon_id: int):
        try:
            url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
            req = urllib.request.Request(url, headers=self._HEADERS)
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read())
            img_url  = (data.get("sprites") or {}).get("front_default") or ""
            img_data = b""
            if img_url:
                try:
                    img_req = urllib.request.Request(img_url, headers=self._HEADERS)
                    with urllib.request.urlopen(img_req, timeout=6) as r:
                        img_data = r.read()
                except Exception:
                    pass
            self.pokemon_loaded.emit(data, img_data)
        except Exception as e:
            self.load_error.emit(str(e))


class PokemonPopup(BasePopup):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._loader = _PokeLoader()
        self._loader.pokemon_loaded.connect(self._on_loaded)
        self._loader.load_error.connect(self._on_error)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._card = QFrame(); self._card.setObjectName("poke-card")
        self._card.setFixedWidth(260)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("poke-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        ttl = QLabel("Pokémon Aleatório"); ttl.setObjectName("poke-title")
        cls = QPushButton("✕"); cls.setObjectName("poke-close")
        cls.setFixedSize(22, 22); cls.clicked.connect(self.hide)
        hh.addWidget(ttl); hh.addStretch(); hh.addWidget(cls)
        v.addWidget(hdr)

        body = QWidget(); body.setObjectName("poke-body")
        bv = QVBoxLayout(body); bv.setContentsMargins(16, 16, 16, 16); bv.setSpacing(10)

        self._sprite_lbl = QLabel(); self._sprite_lbl.setObjectName("poke-sprite")
        self._sprite_lbl.setFixedSize(96, 96)
        self._sprite_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv.addWidget(self._sprite_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._name_lbl = QLabel("Carregando…"); self._name_lbl.setObjectName("poke-name")
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv.addWidget(self._name_lbl)

        self._info_lbl = QLabel(""); self._info_lbl.setObjectName("poke-info")
        self._info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv.addWidget(self._info_lbl)

        type_w = QWidget()
        self._types_row = QHBoxLayout(type_w)
        self._types_row.setContentsMargins(0, 0, 0, 0); self._types_row.setSpacing(6)
        self._types_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        bv.addWidget(type_w)

        self._next_btn = QPushButton("🎲  Novo Pokémon"); self._next_btn.setObjectName("poke-btn")
        self._next_btn.clicked.connect(self.fetch_random)
        bv.addWidget(self._next_btn)

        v.addWidget(body)
        outer.addWidget(self._card)

    def fetch_random(self):
        self._name_lbl.setText("Carregando…")
        self._info_lbl.setText("")
        self._sprite_lbl.clear()
        self._next_btn.setEnabled(False)
        while self._types_row.count():
            item = self._types_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._loader.fetch(random.randint(1, 1010))

    def _on_loaded(self, data: dict, img_data: bytes):
        name    = data.get("name", "???").capitalize()
        poke_id = data.get("id", 0)
        weight  = data.get("weight", 0) / 10
        types   = [t["type"]["name"] for t in data.get("types", [])]

        self._name_lbl.setText(name)
        self._info_lbl.setText(f"#{poke_id:04d}  ·  {weight:.1f} kg")

        while self._types_row.count():
            item = self._types_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for t in types:
            color = _TYPE_COLORS.get(t, "#888888")
            pill = QLabel(t.capitalize())
            pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pill.setStyleSheet(
                f"background:{color}; color:#fff; border-radius:8px;"
                f" padding:2px 10px; font-size:11px; font-weight:700;"
                f" font-family:'SF Pro Text','Segoe UI',sans-serif;"
            )
            self._types_row.addWidget(pill)

        if img_data:
            px = QPixmap()
            px.loadFromData(img_data)
            px = px.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
            self._sprite_lbl.setPixmap(px)
        else:
            self._sprite_lbl.setText("?")

        self._next_btn.setEnabled(True)
        self.adjustSize()

    def _on_error(self, msg: str):
        self._name_lbl.setText("Erro ao carregar")
        self._info_lbl.setText(msg[:40])
        self._next_btn.setEnabled(True)

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light = mode == "light"
        text  = "#1c1c1e"             if is_light else "#e5e5ea"
        muted = "rgba(0,0,0,0.45)"   if is_light else "rgba(255,255,255,0.40)"
        sep   = "rgba(0,0,0,0.07)"   if is_light else "rgba(255,255,255,0.07)"
        self._card.setStyleSheet(f"""
            QFrame#poke-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#poke-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#poke-title {{
                color:{text}; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QPushButton#poke-close {{
                color:{muted}; background:transparent; border:none; border-radius:11px;
                font-size:12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#poke-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QWidget#poke-body {{ background:transparent; }}
            QLabel#poke-sprite {{ background:transparent; }}
            QLabel#poke-name {{
                color:{text}; font-size:20px; font-weight:700;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QLabel#poke-info {{
                color:{muted}; font-size:11px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QPushButton#poke-btn {{
                background:#0a84ff; color:#fff; border:none; border-radius:9px;
                font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; padding:9px;
            }}
            QPushButton#poke-btn:hover {{ background:#0070e0; }}
            QPushButton#poke-btn:disabled {{ background:rgba(10,132,255,0.4); }}
        """)
