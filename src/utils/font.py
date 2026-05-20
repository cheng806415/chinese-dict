import sys
from typing import Optional

from src.utils.qt_compat import QFont


def get_font_family() -> str:
    if sys.platform == 'darwin':
        return 'PingFang SC'
    elif sys.platform == 'win32':
        return 'Microsoft YaHei'
    else:
        return 'Noto Sans CJK SC'


def get_font(size: int, weight: Optional[int] = None) -> QFont:
    font = QFont(get_font_family(), size)
    if weight is not None:
        font.setWeight(weight)
    return font


def get_css_font_family() -> str:
    family = get_font_family()
    return f"'{family}', sans-serif"
