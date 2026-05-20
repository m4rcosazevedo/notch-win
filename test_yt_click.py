import sys
from PyQt6.QtWidgets import QApplication
from ui.notch_window import NotchWindow

app = QApplication(sys.argv)
win = NotchWindow()
win._settings_win._yt_name_edit.setText("Pessoal")
win._settings_win._on_yt_connect()
print("Done without crash!")
