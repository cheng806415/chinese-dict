import sys

from src.utils.qt_compat import (
    QApplication, QPalette, QColor, QMenu, QAction,
    QMessageBox, QPushButton, QSlider, QHBoxLayout,
    QWidget, QLabel, Qt, QFont
)
from src.utils.font import get_font


class ThemeManager:
    LIGHT = "light"
    DARK = "dark"

    def __init__(self, app=None):
        self.app = app or QApplication.instance()
        self.current_theme = self.LIGHT
        self._font_size_offset = 0
        self._pinyin_visible = True
        self._listeners = []

    def add_listener(self, callback):
        self._listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self):
        for cb in self._listeners:
            try:
                cb()
            except Exception:
                pass

    @property
    def font_size_offset(self):
        return self._font_size_offset

    @font_size_offset.setter
    def font_size_offset(self, value):
        self._font_size_offset = max(-4, min(8, int(value)))
        self._notify()

    @property
    def pinyin_visible(self):
        return self._pinyin_visible

    @pinyin_visible.setter
    def pinyin_visible(self, value):
        self._pinyin_visible = bool(value)
        self._notify()

    def get_font_size(self, base_size):
        return base_size + self._font_size_offset

    def get_app_font(self):
        base_size = 10
        if sys.platform == 'darwin':
            base_size = 13
        return get_font(self.get_font_size(base_size))

    def toggle_theme(self):
        self.set_theme(self.DARK if self.current_theme == self.LIGHT else self.LIGHT)

    def set_theme(self, theme):
        self.current_theme = theme
        if theme == self.DARK:
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
        self._notify()

    def _apply_light_theme(self):
        palette = QPalette()
        self.app.setPalette(palette)
        self.app.setStyleSheet(self._light_qss())

    def _apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#2b2b2b"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#2b2b2b"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2b2b2b"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#e0e0e0"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#3c3c3c"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#ff5555"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#1976d2"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        self.app.setPalette(palette)
        self.app.setStyleSheet(self._dark_qss())

    def _light_qss(self):
        return """
        QMainWindow { background-color: #ffffff; }
        QMenuBar { background-color: #f5f5f5; color: #333; }
        QMenuBar::item:selected { background-color: #e3f2fd; color: #000; }
        QMenu { background-color: #ffffff; border: 1px solid #dee2e6; }
        QMenu::item:selected { background-color: #e3f2fd; }
        QPushButton { border-radius: 4px; }
        QSlider::groove:horizontal { height: 6px; background: #dee2e6; border-radius: 3px; }
        QSlider::handle:horizontal { width: 14px; background: #1976d2; border-radius: 7px; }
        """

    def _dark_qss(self):
        return """
        QMainWindow { background-color: #2b2b2b; }
        QMenuBar { background-color: #3c3c3c; color: #e0e0e0; }
        QMenuBar::item:selected { background-color: #505050; color: #fff; }
        QMenu { background-color: #3c3c3c; border: 1px solid #555; color: #e0e0e0; }
        QMenu::item:selected { background-color: #505050; }
        QLineEdit {
            background-color: #1e1e1e;
            color: #e0e0e0;
            border: 2px solid #1976d2;
            border-radius: 6px;
            padding: 10px 14px;
        }
        QLineEdit:focus { background-color: #252525; border: 2px solid #42a5f5; }
        QPushButton {
            background-color: #1976d2;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 6px 16px;
        }
        QPushButton:hover { background-color: #1565c0; }
        QPushButton:pressed { background-color: #0d47a1; }
        QListWidget {
            background-color: #1e1e1e;
            color: #e0e0e0;
            border: 1px solid #444;
            border-radius: 6px;
        }
        QListWidget::item:hover { background-color: #333; }
        QTextEdit {
            background-color: #1e1e1e;
            color: #e0e0e0;
            border: 1px solid #444;
            border-radius: 6px;
        }
        QSlider::groove:horizontal { height: 6px; background: #555; border-radius: 3px; }
        QSlider::handle:horizontal { width: 14px; background: #42a5f5; border-radius: 7px; }
        QLabel { color: #e0e0e0; }
        QSplitter::handle { background-color: #444; }
        """

    def is_dark(self):
        return self.current_theme == self.DARK

    def get_result_bg(self):
        return "#1e1e1e" if self.is_dark() else "#f8f9fa"

    def get_text_color(self):
        return "#e0e0e0" if self.is_dark() else "#333"

    def get_muted_color(self):
        return "#999" if self.is_dark() else "#666"

    def get_card_bg(self):
        return "#2b2b2b" if self.is_dark() else "#ffffff"

    def get_border_color(self):
        return "#444" if self.is_dark() else "#dee2e6"

    def get_section_header_bg(self, section="cn"):
        if self.is_dark():
            return "#1a3a4a" if section == "cn" else "#3a1a4a"
        return "#e3f2fd" if section == "cn" else "#f3e5f5"

    def get_section_header_color(self, section="cn"):
        if self.is_dark():
            return "#90caf9" if section == "cn" else "#ce93d8"
        return "#1976d2" if section == "cn" else "#6a1b9a"


class FontSizeControl(QWidget):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel("字体:")
        label.setFont(get_font(10))
        layout.addWidget(label)

        self.minus_btn = QPushButton("-")
        self.minus_btn.setFixedSize(24, 24)
        self.minus_btn.setFont(get_font(12))
        self.minus_btn.clicked.connect(self._decrease)
        layout.addWidget(self.minus_btn)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(-4, 8)
        self.slider.setValue(self.theme_manager.font_size_offset)
        self.slider.setFixedWidth(80)
        self.slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.slider)

        self.plus_btn = QPushButton("+")
        self.plus_btn.setFixedSize(24, 24)
        self.plus_btn.setFont(get_font(12))
        self.plus_btn.clicked.connect(self._increase)
        layout.addWidget(self.plus_btn)

        self.size_label = QLabel(f"{self.theme_manager.get_font_size(10)}pt")
        self.size_label.setFont(get_font(10))
        layout.addWidget(self.size_label)

        layout.addStretch()

    def _on_slider_changed(self, value):
        self.theme_manager.font_size_offset = value
        self._update_label()

    def _increase(self):
        self.slider.setValue(self.slider.value() + 1)

    def _decrease(self):
        self.slider.setValue(self.slider.value() - 1)

    def _update_label(self):
        self.size_label.setText(f"{self.theme_manager.get_font_size(10)}pt")
