import sys

USE_PYQT5 = sys.platform == 'darwin'

if USE_PYQT5:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTextEdit, QLabel, QSplitter, QListWidget, QListWidgetItem,
        QPushButton, QFrame, QScrollArea, QLineEdit, QMessageBox,
    )
    from PyQt5.QtCore import Qt, pyqtSignal, QTimer
    from PyQt5.QtGui import QFont, QKeySequence, QTextCursor

    ALIGN_CENTER = Qt.AlignCenter
    ALIGN_LEFT = Qt.AlignLeft
    ALIGN_RIGHT = Qt.AlignRight
    FONT_WEIGHT_BOLD = QFont.Bold
    MSG_ICON_CRITICAL = QMessageBox.Critical
    KEY_RETURN = Qt.Key_Return
    KEY_ENTER = Qt.Key_Enter
    WORD_UNDER_CURSOR = QTextCursor.WordUnderCursor
    USER_ROLE = Qt.UserRole
else:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTextEdit, QLabel, QSplitter, QListWidget, QListWidgetItem,
        QPushButton, QFrame, QScrollArea, QLineEdit, QMessageBox,
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QKeySequence, QTextCursor

    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
    ALIGN_LEFT = Qt.AlignmentFlag.AlignLeft
    ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight
    FONT_WEIGHT_BOLD = QFont.Weight.Bold
    MSG_ICON_CRITICAL = QMessageBox.Icon.Critical
    KEY_RETURN = Qt.Key.Key_Return
    KEY_ENTER = Qt.Key.Key_Enter
    WORD_UNDER_CURSOR = QTextCursor.SelectionType.WordUnderCursor
    USER_ROLE = Qt.ItemDataRole.UserRole
