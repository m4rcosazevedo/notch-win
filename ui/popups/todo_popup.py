import json

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QCheckBox, QLineEdit, QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt

from config import TODO_PATH
from ui.popups.base_popup import BasePopup


class TodoPopup(BasePopup):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[dict] = []
        self._load()
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self._card = QFrame(); self._card.setObjectName("todo-card")
        self._card.setFixedWidth(320)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("todo-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        ttl = QLabel("☑  Tarefas"); ttl.setObjectName("todo-title")
        cls = QPushButton("✕"); cls.setObjectName("todo-close")
        cls.setFixedSize(22, 22); cls.clicked.connect(self.hide)
        hh.addWidget(ttl); hh.addStretch(); hh.addWidget(cls)
        v.addWidget(hdr)

        inp_row = QWidget(); inp_row.setObjectName("todo-input-row")
        ih = QHBoxLayout(inp_row); ih.setContentsMargins(14, 10, 14, 10); ih.setSpacing(8)
        self._inp = QLineEdit(); self._inp.setObjectName("todo-input")
        self._inp.setPlaceholderText("Nova tarefa…")
        self._inp.returnPressed.connect(self._add_item)
        add_btn = QPushButton("+"); add_btn.setObjectName("todo-add-btn")
        add_btn.setFixedSize(28, 28); add_btn.clicked.connect(self._add_item)
        ih.addWidget(self._inp, 1); ih.addWidget(add_btn)
        v.addWidget(inp_row)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setMinimumHeight(80)
        self._scroll.setMaximumHeight(360)

        self._list_widget = QWidget(); self._list_widget.setObjectName("todo-list")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 4, 0, 4); self._list_layout.setSpacing(0)
        self._list_layout.addStretch()
        self._scroll.setWidget(self._list_widget)
        v.addWidget(self._scroll)
        outer.addWidget(self._card)
        self._refresh_list()

    def _add_item(self):
        text = self._inp.text().strip()
        if not text:
            return
        self._items.append({"text": text, "done": False})
        self._inp.clear()
        self._refresh_list()
        self._save()

    def _toggle_item(self, idx: int, done: bool):
        if 0 <= idx < len(self._items):
            self._items[idx]["done"] = done
            self._refresh_list()
            self._save()

    def _remove_item(self, idx: int):
        if 0 <= idx < len(self._items):
            del self._items[idx]
            self._refresh_list()
            self._save()

    def _refresh_list(self):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self._items:
            lbl = QLabel("Nenhuma tarefa ainda"); lbl.setObjectName("todo-empty")
            lbl.setContentsMargins(14, 12, 14, 12)
            self._list_layout.insertWidget(0, lbl)
            return
        for i, item in enumerate(self._items):
            row = QFrame(); row.setObjectName("todo-item")
            rh = QHBoxLayout(row); rh.setContentsMargins(14, 7, 14, 7); rh.setSpacing(8)
            chk = QCheckBox(); chk.setObjectName("todo-chk")
            chk.setChecked(item["done"])
            chk.toggled.connect(lambda v, ix=i: self._toggle_item(ix, v))
            lbl = QLabel(item["text"])
            lbl.setObjectName("todo-item-lbl-done" if item["done"] else "todo-item-lbl")
            lbl.setWordWrap(True)
            rm = QPushButton("✕"); rm.setObjectName("todo-rm-btn")
            rm.setFixedSize(18, 18); rm.clicked.connect(lambda _, ix=i: self._remove_item(ix))
            rh.addWidget(chk); rh.addWidget(lbl, 1); rh.addWidget(rm)
            self._list_layout.insertWidget(i, row)
        self.adjustSize()

    def _save(self):
        TODO_PATH.write_text(json.dumps(self._items, ensure_ascii=False), encoding="utf-8")

    def _load(self):
        if TODO_PATH.exists():
            try:
                self._items = json.loads(TODO_PATH.read_text(encoding="utf-8"))
            except Exception:
                self._items = []

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light  = mode == "light"
        text      = "#1c1c1e"              if is_light else "#e5e5ea"
        done_text = "rgba(0,0,0,0.35)"    if is_light else "rgba(255,255,255,0.30)"
        muted     = "rgba(0,0,0,0.45)"    if is_light else "rgba(255,255,255,0.40)"
        sep       = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.07)"
        inp_bg    = "rgba(0,0,0,0.05)"    if is_light else "rgba(255,255,255,0.07)"
        scroll_h  = "rgba(0,0,0,0.15)"    if is_light else "rgba(255,255,255,0.15)"
        self._card.setStyleSheet(f"""
            QFrame#todo-card {{ background:{bg}; border-radius:16px; border:1px solid {border}; }}
            QFrame#todo-header {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#todo-title {{
                color:{text}; font-size:13px; font-weight:600;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QPushButton#todo-close {{
                color:{muted}; background:transparent; border:none; border-radius:11px;
                font-size:12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#todo-close:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QWidget#todo-input-row {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLineEdit#todo-input {{
                background:{inp_bg}; color:{text}; border:1px solid {sep}; border-radius:8px;
                font-size:12px; font-family:"SF Pro Text","Segoe UI",sans-serif; padding:5px 10px;
            }}
            QPushButton#todo-add-btn {{ background:#0a84ff; color:#fff; border:none; border-radius:8px; font-size:16px; font-weight:bold; }}
            QPushButton#todo-add-btn:hover {{ background:#0070e0; }}
            QScrollArea {{ background:transparent; border:none; }}
            QWidget#todo-list {{ background:transparent; }}
            QFrame#todo-item {{ background:transparent; border-bottom:1px solid {sep}; }}
            QLabel#todo-item-lbl {{
                color:{text}; font-size:12px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QLabel#todo-item-lbl-done {{
                color:{done_text}; font-size:12px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
                text-decoration:line-through;
            }}
            QPushButton#todo-rm-btn {{
                color:{muted}; background:transparent; border:none; border-radius:9px; font-size:10px;
            }}
            QPushButton#todo-rm-btn:hover {{ background:rgba(255,80,80,0.15); color:#ff453a; }}
            QLabel#todo-empty {{
                color:{muted}; font-size:12px;
                font-family:"SF Pro Text","Segoe UI",sans-serif; background:transparent;
            }}
            QScrollBar:vertical {{ background:transparent; width:4px; margin:3px 1px; }}
            QScrollBar::handle:vertical {{ background:{scroll_h}; border-radius:2px; min-height:20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0px; }}
        """)
        self._refresh_list()

    def show_at(self, pos):
        self._refresh_list()
        super().show_at(pos)
