import sys


def get_font_family():
    if sys.platform == 'darwin':
        return 'PingFang SC'
    elif sys.platform == 'win32':
        return 'Microsoft YaHei'
    else:
        return 'Noto Sans CJK SC'


def get_font(size, weight=None):
    from PyQt6.QtGui import QFont
    font = QFont(get_font_family(), size)
    if weight is not None:
        font.setWeight(weight)
    return font


def get_css_font_family():
    family = get_font_family()
    return f"'{family}', sans-serif"
