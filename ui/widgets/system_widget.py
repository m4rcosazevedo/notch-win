from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from modules.system_monitor import SystemMonitorModule
from ui.icons import _DEFAULT_DARK


class SystemWidget(QWidget):
    def __init__(self, monitor: SystemMonitorModule, parent=None):
        super().__init__(parent)
        self.setProperty("class", "section")
        self._monitor = monitor
        self._build_ui()
        self._monitor.stats_updated.connect(self._on_stats_update)

    def _build_ui(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(4, 0, 4, 0)
        h.setSpacing(8)

        self._cpu_label = QLabel("CPU: 0%")
        self._cpu_label.setObjectName("sys-label")
        self._ram_label = QLabel("RAM: 0%")
        self._ram_label.setObjectName("sys-label")
        self._ping_label = QLabel("Ping: 0ms")
        self._ping_label.setObjectName("sys-label")

        for lbl in (self._cpu_label, self._ram_label, self._ping_label):
            lbl.setFixedHeight(30)
            h.addWidget(lbl)

    def _on_stats_update(self, stats):
        self._cpu_label.setText(f"CPU: {int(stats['cpu'])}%")
        self._ram_label.setText(f"RAM: {int(stats['ram'])}%")
        p = stats['ping']
        ping_text = f"{p}ms" if p >= 0 else "Err"
        self._ping_label.setText(f"Ping: {ping_text}")

    def refresh_icons(self, color: QColor):
        # This widget uses text labels, but we can update their color if needed
        # In this project, labels are styled via QSS, but we'll ensure they are visible
        pass
