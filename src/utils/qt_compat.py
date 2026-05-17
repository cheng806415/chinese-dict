import sys

USE_PYQT5 = sys.platform == 'darwin'

if USE_PYQT5:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTextEdit, QLabel, QSplitter, QListWidget, QListWidgetItem,
        QPushButton, QFrame, QScrollArea, QLineEdit, QMessageBox,
        QAction, QMenu, QMenuBar, QSlider, QToolBar, QStatusBar,
        QDialog, QFileDialog, QDialogButtonBox, QComboBox, QCheckBox,
        QGroupBox, QFormLayout, QGridLayout, QProgressDialog,
        QPrintDialog, QProgressBar,
    )
    from PyQt5.QtCore import Qt, pyqtSignal, QTimer
    from PyQt5.QtGui import QFont, QKeySequence, QTextCursor, QPalette, QColor, QClipboard
    from PyQt5.QtPrintSupport import QPrinter

    ALIGN_CENTER = Qt.AlignCenter
    ALIGN_LEFT = Qt.AlignLeft
    ALIGN_RIGHT = Qt.AlignRight
    FONT_WEIGHT_BOLD = QFont.Bold
    MSG_ICON_CRITICAL = QMessageBox.Critical
    MSG_ICON_INFORMATION = QMessageBox.Information
    MSG_ACTION_ROLE = QMessageBox.ActionRole
    MSG_ACCEPT_ROLE = QMessageBox.AcceptRole
    KEY_RETURN = Qt.Key_Return
    KEY_ENTER = Qt.Key_Enter
    WORD_UNDER_CURSOR = QTextCursor.WordUnderCursor
    USER_ROLE = Qt.UserRole
else:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTextEdit, QLabel, QSplitter, QListWidget, QListWidgetItem,
        QPushButton, QFrame, QScrollArea, QLineEdit, QMessageBox,
        QMenu, QMenuBar, QSlider, QToolBar, QStatusBar,
        QDialog, QFileDialog, QDialogButtonBox, QComboBox, QCheckBox,
        QGroupBox, QFormLayout, QGridLayout, QProgressDialog,
        QPrintDialog, QProgressBar,
    )
    from PyQt6.QtGui import QAction, QFont, QKeySequence, QTextCursor, QPalette, QColor, QClipboard, QPrinter
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer

    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
    ALIGN_LEFT = Qt.AlignmentFlag.AlignLeft
    ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight
    FONT_WEIGHT_BOLD = QFont.Weight.Bold
    MSG_ICON_CRITICAL = QMessageBox.Icon.Critical
    MSG_ICON_INFORMATION = QMessageBox.Icon.Information
    MSG_ACTION_ROLE = QMessageBox.ButtonRole.ActionRole
    MSG_ACCEPT_ROLE = QMessageBox.ButtonRole.AcceptRole
    KEY_RETURN = Qt.Key.Key_Return
    KEY_ENTER = Qt.Key.Key_Enter
    WORD_UNDER_CURSOR = QTextCursor.SelectionType.WordUnderCursor
    USER_ROLE = Qt.ItemDataRole.UserRole
