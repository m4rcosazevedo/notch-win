import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.dbus.*=false")

from dotenv import load_dotenv
load_dotenv()

from PyQt6.QtWidgets import QApplication
from ui.notch_window import NotchWindow


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = NotchWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
