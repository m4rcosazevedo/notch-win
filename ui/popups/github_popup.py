from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt, QPoint, QUrl, QObject, QEvent
from PyQt6.QtGui import QCursor, QDesktopServices

from modules.github_feed import GitHubFeedModule
from ui.popups.base_popup import BasePopup, popup_show_at


class _NotifClickFilter(QObject):
    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton):
            QDesktopServices.openUrl(QUrl(self._url))
            return True
        return False


class GitHubPopup(BasePopup):
    def __init__(self, github_module: GitHubFeedModule, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._github = github_module
        self._build_ui()
        self._github.updated.connect(self._on_updated)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame(); self._card.setObjectName("gh-popup")
        self._card.setFixedWidth(400)
        v = QVBoxLayout(self._card)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("gh-popup-header")
        hh = QHBoxLayout(hdr); hh.setContentsMargins(14, 10, 10, 10)
        title_lbl = QLabel("🐙  GitHub — Notificações"); title_lbl.setObjectName("gh-popup-title")
        close_btn = QPushButton("✕"); close_btn.setObjectName("gh-popup-close")
        close_btn.setFixedSize(22, 22); close_btn.clicked.connect(self.hide)
        hh.addWidget(title_lbl); hh.addStretch(); hh.addWidget(close_btn)
        v.addWidget(hdr)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setFixedHeight(460)

        self._list_widget = QWidget(); self._list_widget.setObjectName("gh-list")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 4, 0, 4)
        self._list_layout.setSpacing(0)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._list_widget)
        v.addWidget(self._scroll)
        outer.addWidget(self._card)

    def _on_updated(self, notifications):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not notifications:
            lbl = QLabel("Nenhuma notificação.\nConfigure suas contas nas Configurações.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("padding: 24px; color: rgba(128,128,128,0.7); background: transparent;")
            self._list_layout.insertWidget(0, lbl)
            return

        for i, n in enumerate(notifications):
            self._list_layout.insertWidget(i * 2, self._make_notif_row(n))
            if i < len(notifications) - 1:
                sep = QFrame(); sep.setObjectName("gh-row-sep")
                sep.setFrameShape(QFrame.Shape.HLine)
                self._list_layout.insertWidget(i * 2 + 1, sep)

    def _make_notif_row(self, n) -> QFrame:
        row = QFrame(); row.setObjectName("gh-notif-row")
        row.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        h = QHBoxLayout(row); h.setContentsMargins(14, 10, 14, 10); h.setSpacing(12)

        icon_lbl = QLabel(self._get_type_icon(n["type"]))
        icon_lbl.setObjectName("gh-type-icon")
        icon_lbl.setFixedSize(24, 24)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.addWidget(icon_lbl)

        info = QVBoxLayout(); info.setSpacing(2); info.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout(); top.setSpacing(4)
        repo_lbl = QLabel(n["repo"]); repo_lbl.setObjectName("gh-repo")
        acc_lbl = QLabel(f"@{n['account']}"); acc_lbl.setObjectName("gh-acc")
        top.addWidget(repo_lbl, 1); top.addWidget(acc_lbl, 0)
        
        title_lbl = QLabel(n["title"]); title_lbl.setObjectName("gh-notif-title")
        title_lbl.setWordWrap(True)
        
        info.addLayout(top); info.addWidget(title_lbl)
        h.addLayout(info, 1)

        # Click to open via EventFilter
        filt = _NotifClickFilter(f"https://github.com/{n['repo']}", parent=row)
        row.installEventFilter(filt)
        
        return row

    def _get_type_icon(self, n_type):
        mapping = {
            "PullRequest": "⤴️",
            "Issue": "🔴",
            "Release": "📦",
            "Commit": "🔨",
            "CheckSuite": "✅"
        }
        return mapping.get(n_type, "🔔")

    def apply_theme(self, bg: str, border: str, mode: str):
        is_light  = mode == "light"
        text      = "#1c1c1e"              if is_light else "#e5e5ea"
        muted     = "rgba(0,0,0,0.45)"    if is_light else "rgba(255,255,255,0.40)"
        sep_color = "rgba(0,0,0,0.07)"    if is_light else "rgba(255,255,255,0.07)"
        hover_bg  = "rgba(0,0,0,0.04)"    if is_light else "rgba(255,255,255,0.05)"
        close_h   = "rgba(255,80,80,0.15)"
        scroll_h  = "rgba(0,0,0,0.15)"    if is_light else "rgba(255,255,255,0.15)"
        list_bg   = "rgba(0,0,0,0.03)"    if is_light else "rgba(0,0,0,0.15)"

        self._card.setStyleSheet(f"""
            QFrame#gh-popup {{
                background-color: {bg}; border-radius: 16px; border: 1px solid {border};
            }}
            QFrame#gh-popup-header {{
                background: {hover_bg}; border-bottom: 1px solid {sep_color};
                border-top-left-radius: 16px; border-top-right-radius: 16px;
            }}
            QLabel#gh-popup-title {{
                color: {text}; font-size: 13px; font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QPushButton#gh-popup-close {{
                color: {muted}; background: transparent; border: none; border-radius: 11px;
                font-size: 12px; min-width:22px; max-width:22px; min-height:22px; max-height:22px; padding:0px;
            }}
            QPushButton#gh-popup-close:hover {{ background: {close_h}; color: #ff453a; }}
            QScrollArea {{ background: transparent; border: none; }}
            QWidget#gh-list {{ background: {list_bg}; border-bottom-left-radius: 16px; border-bottom-right-radius: 16px; }}
            QFrame#gh-notif-row {{ background: transparent; border: none; }}
            QFrame#gh-notif-row:hover {{ background: {hover_bg}; border-radius: 8px; }}
            QLabel#gh-repo {{
                color: {text}; font-size: 11px; font-weight: 700;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QLabel#gh-acc {{
                color: {muted}; font-size: 10px; font-weight: 600;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QLabel#gh-notif-title {{
                color: {muted}; font-size: 12px;
                font-family: "SF Pro Text","Segoe UI",sans-serif; background: transparent;
            }}
            QLabel#gh-type-icon {{
                background: transparent;
            }}
            QFrame#gh-row-sep {{ color: {sep_color}; max-height: 1px; }}
            QScrollBar:vertical {{ background: transparent; width: 4px; margin: 3px 1px; }}
            QScrollBar::handle:vertical {{
                background: {scroll_h}; border-radius: 2px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

    def show_at(self, pos: QPoint):
        self._on_updated(self._github._fetch_last_notifications if hasattr(self._github, '_fetch_last_notifications') else [])
        # Trigger refresh on show
        self._github.refresh()
        popup_show_at(self, pos)
