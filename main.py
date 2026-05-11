# main.py
"""Application entry point."""
import sys
import warnings
warnings.filterwarnings('ignore')

from PySide6.QtWidgets import QApplication

from auth import AuthDialog, init_db
from ui_main import MainWindow


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    auth = AuthDialog()
    if auth.exec() != AuthDialog.Accepted:
        sys.exit(0)

    win = MainWindow()
    win.show()

    win._current_user = auth.username()
    win.log(f'欢迎 {auth.username()}！', 'success')

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
