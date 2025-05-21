import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
from src.ui.main_window import MainWindow
import time

def main():
    QCoreApplication.setOrganizationName("Physicshow")
    QCoreApplication.setApplicationName("LectureShow")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()