from typing import Optional, Callable, List, Tuple

from src.utils.qt_compat import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QListWidget,
    QListWidgetItem, QVBoxLayout, QFrame, QLabel,
    Qt, pyqtSignal, QTimer, QFont, QKeySequence,
    FONT_WEIGHT_BOLD, KEY_RETURN, KEY_ENTER, USER_ROLE
)
from src.utils.font import get_font


class SearchBar(QWidget):
    search_requested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("SearchBar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入中文词汇、拼音或英文... (Ctrl+F)")
        self.search_input.setFont(get_font(12))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.returnPressed.connect(self._on_search)
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px;
                border: 2px solid #1976d2;
                border-radius: 6px;
                background-color: #ffffff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #0d47a1;
                background-color: #e3f2fd;
            }
        """)
        input_layout.addWidget(self.search_input)

        self.search_button = QPushButton("查询")
        self.search_button.setFont(get_font(12, FONT_WEIGHT_BOLD))
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.search_button.clicked.connect(self._on_search)
        input_layout.addWidget(self.search_button)

        layout.addLayout(input_layout)

        self.suggestion_list = QListWidget()
        self.suggestion_list.setVisible(False)
        self.suggestion_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-top: none;
                border-radius: 0 0 6px 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #333;
            }
        """)
        self.suggestion_list.itemClicked.connect(self._on_suggestion_selected)
        layout.addWidget(self.suggestion_list)

        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._request_suggestions)
        self._last_suggestions: List[Tuple[str, str]] = []

        self.suggestions_callback: Optional[Callable[[str], List[Tuple[str, str]]]] = None

    def set_suggestions_callback(self, callback: Callable[[str], List[Tuple[str, str]]]) -> None:
        self.suggestions_callback = callback

    def _on_text_changed(self, text: str) -> None:
        if text.strip():
            self.debounce_timer.start(150)
        else:
            self.suggestion_list.setVisible(False)

    def _request_suggestions(self) -> None:
        text = self.search_input.text().strip()
        if text and self.suggestions_callback:
            suggestions = self.suggestions_callback(text)
            self._update_suggestions(suggestions)

    def _update_suggestions(self, suggestions: List[Tuple[str, str]]) -> None:
        # Avoid redundant UI updates if suggestions haven't changed
        if suggestions == self._last_suggestions:
            return
        self._last_suggestions = suggestions

        self.suggestion_list.clear()
        if suggestions:
            for item in suggestions:
                word = item[0] if isinstance(item, (list, tuple)) else item
                pinyin = item[1] if isinstance(item, (list, tuple)) and len(item) > 1 else ""
                display_text = f"{word}  ({pinyin})" if pinyin else word
                list_item = QListWidgetItem(display_text)
                list_item.setData(USER_ROLE, word)
                self.suggestion_list.addItem(list_item)
            self.suggestion_list.setVisible(True)
            self.suggestion_list.setMaximumHeight(min(len(suggestions) * 40, 200))
        else:
            self.suggestion_list.setVisible(False)

    def _on_suggestion_selected(self, item: QListWidgetItem) -> None:
        word = item.data(USER_ROLE)
        if word:
            self.search_input.setText(word)
            self.suggestion_list.setVisible(False)
            self.search_requested.emit(word)

    def _on_search(self) -> None:
        word = self.search_input.text().strip()
        if word:
            self.suggestion_list.setVisible(False)
            self.search_requested.emit(word)

    def get_text(self) -> str:
        return self.search_input.text().strip()

    def set_text(self, text: str) -> None:
        self.search_input.setText(text)

    def clear(self) -> None:
        self.search_input.clear()
        self.suggestion_list.setVisible(False)

    def focus_search(self) -> None:
        """Focus the search input and select all text."""
        self.search_input.setFocus()
        self.search_input.selectAll()
