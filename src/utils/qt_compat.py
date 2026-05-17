import sys

USE_PYQT5 = False

try:
    from PyQt6.QtWidgets import QApplication
    USE_PYQT5 = False
except ImportError:
    from PyQt5.QtWidgets import QApplication
    USE_PYQT5 = True


def import_qt(module_name):
    if USE_PYQT5:
        return __import__(f'PyQt5.{module_name}', fromlist=['*'])
    return __import__(f'PyQt6.{module_name}', fromlist=['*'])


QtWidgets = import_qt('QtWidgets')
QtCore = import_qt('QtCore')
QtGui = import_qt('QtGui')

QApplication = QtWidgets.QApplication
QMainWindow = QtWidgets.QMainWindow
QWidget = QtWidgets.QWidget
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QTextEdit = QtWidgets.QTextEdit
QLabel = QtWidgets.QLabel
QSplitter = QtWidgets.QSplitter
QListWidget = QtWidgets.QListWidget
QListWidgetItem = QtWidgets.QListWidgetItem
QPushButton = QtWidgets.QPushButton
QFrame = QtWidgets.QFrame
QScrollArea = QtWidgets.QScrollArea
QLineEdit = QtWidgets.QLineEdit
QMessageBox = QtWidgets.QMessageBox

Qt = QtCore.Qt
pyqtSignal = QtCore.pyqtSignal
QTimer = QtCore.QTimer
QTextCursor = QtGui.QTextCursor
QFont = QtGui.QFont
QKeySequence = QtGui.QKeySequence


def _align_center():
    if USE_PYQT5:
        return Qt.AlignCenter
    return Qt.AlignmentFlag.AlignCenter


def _align_left():
    if USE_PYQT5:
        return Qt.AlignLeft
    return Qt.AlignmentFlag.AlignLeft


def _align_right():
    if USE_PYQT5:
        return Qt.AlignRight
    return Qt.AlignmentFlag.AlignRight


def _font_weight_bold():
    if USE_PYQT5:
        return QFont.Bold
    return QFont.Weight.Bold


def _msg_icon_critical():
    if USE_PYQT5:
        return QMessageBox.Critical
    return QMessageBox.Icon.Critical


def _key_return():
    if USE_PYQT5:
        return Qt.Key_Return
    return Qt.Key.Key_Return


def _key_enter():
    if USE_PYQT5:
        return Qt.Key_Enter
    return Qt.Key.Key_Enter


ALIGN_CENTER = _align_center()
ALIGN_LEFT = _align_left()
ALIGN_RIGHT = _align_right()
FONT_WEIGHT_BOLD = _font_weight_bold()
MSG_ICON_CRITICAL = _msg_icon_critical()
KEY_RETURN = _key_return()
KEY_ENTER = _key_enter()
