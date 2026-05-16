from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication


MAX_ITEMS = 15
MAX_PREVIEW = 30


class ClipboardModule(QObject):
    history_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._history: list[str] = []
        self._clipboard = QApplication.clipboard()
        self._clipboard.dataChanged.connect(self._on_change)

    def _on_change(self):
        text = self._clipboard.text().strip()
        if not text:
            return
        if self._history and self._history[0] == text:
            return
        if text in self._history:
            self._history.remove(text)
        self._history.insert(0, text)
        if len(self._history) > MAX_ITEMS:
            self._history.pop()
        self.history_changed.emit()

    def get_history(self) -> list[str]:
        return self._history

    def copy(self, index: int):
        if 0 <= index < len(self._history):
            self._clipboard.setText(self._history[index])

    def clear(self):
        self._history.clear()
        self.history_changed.emit()

    def count(self) -> int:
        return len(self._history)

    @staticmethod
    def preview(text: str) -> str:
        text = text.replace("\n", " ")
        return text[:MAX_PREVIEW] + "…" if len(text) > MAX_PREVIEW else text
