from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from modules.github_feed import GitHubFeedModule
from ui.icons import _icon_btn, _refresh_icon, _ic_github


class GitHubWidget(QWidget):
    open_popup = pyqtSignal()

    def __init__(self, github: GitHubFeedModule, parent=None):
        super().__init__(parent)
        self.setProperty("class", "section")
        self._github = github
        self._build_ui()
        self._github.updated.connect(self._on_updated)

    def _build_ui(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(4, 0, 4, 0)
        h.setSpacing(4)

        self.btn = _icon_btn(_ic_github)
        self.btn.setToolTip("GitHub Feed")
        h.addWidget(self.btn)

        self.count_lbl = QLabel("0")
        self.count_lbl.setStyleSheet("font-weight: bold; color: #ffd60a; font-size: 10px;")
        h.addWidget(self.count_lbl)

        self.btn.clicked.connect(self.open_popup.emit)

    def _on_updated(self, notifications):
        self.count_lbl.setText(str(len(notifications)))

    def refresh_icons(self, color: QColor):
        _refresh_icon(self.btn, _ic_github, color=color)
