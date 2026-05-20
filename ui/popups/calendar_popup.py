from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor, QColor

from modules.calendar_feed import CalendarFeedModule
from ui.popups.base_popup import BasePopup, popup_show_at
from ui.icons import _icon_btn, _refresh_icon, _ic_refresh_action


class CalendarPopup(BasePopup):
    def __init__(self, cal_module: CalendarFeedModule, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._cal = cal_module
        self._icon_color = QColor(200, 200, 200)
        self._build_ui()
        self._cal.updated.connect(self._on_updated)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame(); self._card.setObjectName("cal-popup")
        self._card.setFixedWidth(400)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("cal-popup-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        title_lbl = QLabel("🗓  Calendário — Agenda"); title_lbl.setObjectName("cal-popup-title")
        
        self.refresh_btn = _icon_btn(_ic_refresh_action)
        self.refresh_btn.setObjectName("cal-popup-refresh")
        self.refresh_btn.setFixedSize(22, 22)
        self.refresh_btn.setToolTip("Atualizar agora")
        self.refresh_btn.clicked.connect(self._cal.refresh)

        close_btn = QPushButton("✕"); close_btn.setObjectName("cal-popup-close")
        close_btn.setFixedSize(22, 22); close_btn.clicked.connect(self.hide)
        
        hh.addWidget(title_lbl); hh.addStretch()
        hh.addWidget(self.refresh_btn); hh.addSpacing(4)
        hh.addWidget(close_btn)
        v.addWidget(hdr)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setFixedHeight(460)

        self._list_widget = QWidget(); self._list_widget.setObjectName("cal-list")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 4, 0, 4)
        self._list_layout.setSpacing(0)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._list_widget)
        v.addWidget(self._scroll)
        outer.addWidget(self._card)

    def _on_updated(self, events):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not events:
            lbl = QLabel("Nenhum compromisso para hoje.\nConfigure suas contas nas Configurações.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("padding: 24px; color: rgba(128,128,128,0.7); background: transparent;")
            self._list_layout.insertWidget(0, lbl)
            return

        for i, event in enumerate(events):
            self._list_layout.insertWidget(i * 2, self._make_event_row(event))
            if i < len(events) - 1:
                sep = QFrame(); sep.setObjectName("cal-row-sep")
                sep.setFrameShape(QFrame.Shape.HLine)
                self._list_layout.insertWidget(i * 2 + 1, sep)

    def _make_event_row(self, e) -> QFrame:
        row = QFrame(); row.setObjectName("cal-event-row")
        h = QHBoxLayout(row); h.setContentsMargins(14, 10, 14, 10); h.setSpacing(12)

        time_col = QVBoxLayout(); time_col.setSpacing(0)
        time_lbl = QLabel(e.get("time", "00:00")); time_lbl.setObjectName("cal-time")
        type_lbl = QLabel(e.get("type", "Event")); type_lbl.setObjectName("cal-type")
        time_col.addWidget(time_lbl); time_col.addWidget(type_lbl)
        h.addLayout(time_col)

        info = QVBoxLayout(); info.setSpacing(2); info.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel(e.get("title", "Sem título")); title_lbl.setObjectName("cal-title")
        title_lbl.setWordWrap(True)
        acc_lbl = QLabel(e.get("account", "Agenda")); acc_lbl.setObjectName("cal-acc")
        info.addWidget(title_lbl); info.addWidget(acc_lbl)
        h.addLayout(info, 1)

        return row

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light  = mode == "light"
        text      = "#1c1c1e"              if is_light else "#e5e5ea"
        muted     = "rgba(0,0,0,0.45)"    if is_light else "rgba(255,255,255,0.40)"
        sep_color = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.07)"
        hover_bg  = "rgba(0,0,0,0.04)"    if is_light else "rgba(255,255,255,0.05)"
        close_h   = "rgba(255,80,80,0.15)"
        scroll_h  = "rgba(0,0,0,0.15)"    if is_light else "rgba(255,255,255,0.15)"
        list_bg   = "rgba(0,0,0,0.03)"    if is_light else "rgba(0,0,0,0.15)"

        # Update refresh icon color
        _refresh_icon(self.refresh_btn, _ic_refresh_action, color=QColor(text))

        self._card.setStyleSheet(f"""
            QFrame#cal-popup {{
                background-color: {bg}; border-radius: 16px; border: 1px solid {border};
            }}
            QFrame#cal-popup-header {{
                background: {hover_bg}; border-bottom: 1px solid {sep_color};
                border-top-left-radius: 16px; border-top-right-radius: 16px;
            }}
            QLabel#cal-popup-title {{
                color: {text}; font-size: 13px; font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QPushButton#cal-popup-refresh {{
                background: transparent; border: none; border-radius: 11px;
            }}
            QPushButton#cal-popup-refresh:hover {{ background: {hover_bg}; }}
            
            QPushButton#cal-popup-close {{
                color: {muted}; background: transparent; border: none; border-radius: 11px;
                font-size: 12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#cal-popup-close:hover {{ background: {close_h}; color: #ff453a; }}
            QScrollArea {{ background: transparent; border: none; }}
            QWidget#cal-list {{ background: {list_bg}; border-bottom-left-radius: 16px; border-bottom-right-radius: 16px; }}
            QFrame#cal-event-row {{ background: transparent; border: none; }}
            QLabel#cal-time {{
                color: {text}; font-size: 12px; font-weight: 700;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QLabel#cal-type {{
                color: #0a84ff; font-size: 9px; font-weight: 700; text-transform: uppercase;
                background: transparent;
            }}
            QLabel#cal-title {{
                color: {text}; font-size: 12px; font-weight: 500;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QLabel#cal-acc {{
                color: {muted}; font-size: 10px;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QFrame#cal-row-sep {{ color: {sep_color}; max-height: 1px; }}
            QScrollBar:vertical {{ background: transparent; width: 4px; margin: 3px 1px; }}
            QScrollBar::handle:vertical {{
                background: {scroll_h}; border-radius: 2px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

    def show_at(self, pos: QPoint):
        # Trigger refresh on show
        self._cal.refresh()
        popup_show_at(self, pos)
