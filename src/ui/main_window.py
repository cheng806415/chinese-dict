from typing import Optional, List, Dict, Any

from src.utils.qt_compat import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QSplitter, QListWidget, QListWidgetItem, QPushButton,
    QFrame, QScrollArea, Qt, pyqtSignal, QFont, QTextCursor,
    FONT_WEIGHT_BOLD, ALIGN_CENTER, WORD_UNDER_CURSOR,
    QAction, QMenu, QClipboard, QApplication, QMessageBox,
    QTimer, QProgressBar, MSG_ICON_INFORMATION, MSG_ACTION_ROLE, MSG_ACCEPT_ROLE,
    QKeySequence, QShortcut,
)
from src.ui.search_bar import SearchBar
from src.utils.font import get_font, get_css_font_family
from src.utils.theme import ThemeManager, FontSizeControl


class SearchResultView(QTextEdit):
    toggle_favorite = pyqtSignal(int)
    copy_requested = pyqtSignal(str, str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(get_font(11))
        self._update_style(False)
        self.setPlaceholderText("输入词汇进行查询...")
        self.current_word_id: Optional[int] = None
        self._word = ""
        self._pinyin = ""
        self._definition = ""

    def _update_style(self, is_dark: bool) -> None:
        if is_dark:
            self.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    border: 1px solid #444;
                    border-radius: 6px;
                    padding: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    color: #333;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 12px;
                }
            """)

    def set_content(self, word: str, pinyin: str, definition: str) -> None:
        self._word = word or ""
        self._pinyin = pinyin or ""
        self._definition = definition or ""

    def contextMenuEvent(self, event) -> None:
        menu = self.createStandardContextMenu()
        menu.addSeparator()

        copy_word_action = QAction("复制词语", self)
        copy_word_action.triggered.connect(lambda: self.copy_requested.emit("word", self._word))
        menu.addAction(copy_word_action)

        copy_pinyin_action = QAction("复制拼音", self)
        copy_pinyin_action.triggered.connect(lambda: self.copy_requested.emit("pinyin", self._pinyin))
        menu.addAction(copy_pinyin_action)

        copy_def_action = QAction("复制释义", self)
        copy_def_action.triggered.connect(lambda: self.copy_requested.emit("definition", self._definition))
        menu.addAction(copy_def_action)

        menu.exec(event.globalPos())

    def mousePressEvent(self, event) -> None:
        try:
            cursor = self.cursorForPosition(event.pos())
            cursor.select(WORD_UNDER_CURSOR)
            word = cursor.selectedText()
            if word in ("☆", "★"):
                if self.current_word_id is not None:
                    self.toggle_favorite.emit(self.current_word_id)
            else:
                super().mousePressEvent(event)
        except Exception:
            super().mousePressEvent(event)


class FavoriteListWidget(QWidget):
    item_clicked = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("收藏词汇")
        title_label.setFont(get_font(10, FONT_WEIGHT_BOLD))
        title_label.setStyleSheet("padding: 8px; background-color: #e9ecef; border-radius: 4px;")
        layout.addWidget(title_label)
        self.title_label = title_label

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        self.list_widget.itemDoubleClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        self.item_clicked.emit(item.text())

    def add_item(self, word: str) -> None:
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).text() == word:
                return
        self.list_widget.addItem(word)

    def clear(self) -> None:
        self.list_widget.clear()

    def get_items(self) -> List[str]:
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def update_theme(self, theme_manager: ThemeManager) -> None:
        if theme_manager.is_dark():
            self.title_label.setStyleSheet(
                "padding: 8px; background-color: #3c3c3c; border-radius: 4px; color: #e0e0e0;"
            )
            self.list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    border: 1px solid #444;
                    border-radius: 6px;
                    padding: 4px;
                }
                QListWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #333;
                }
                QListWidget::item:hover {
                    background-color: #333;
                }
            """)
        else:
            self.title_label.setStyleSheet(
                "padding: 8px; background-color: #e9ecef; border-radius: 4px; color: #333;"
            )
            self.list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #ffffff;
                    color: #333;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 4px;
                }
                QListWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #f0f0f0;
                }
                QListWidget::item:hover {
                    background-color: #e3f2fd;
                }
            """)


class HistoryListWidget(QWidget):
    item_clicked = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("搜索历史")
        title_label.setFont(get_font(10, FONT_WEIGHT_BOLD))
        title_label.setStyleSheet("padding: 8px; background-color: #e9ecef; border-radius: 4px;")
        layout.addWidget(title_label)
        self.title_label = title_label

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #fff3e0;
            }
        """)
        self.list_widget.itemDoubleClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        self.item_clicked.emit(item.text())

    def add_item(self, word: str) -> None:
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).text() == word:
                return
        self.list_widget.insertItem(0, word)

    def clear(self) -> None:
        self.list_widget.clear()

    def update_theme(self, theme_manager: ThemeManager) -> None:
        if theme_manager.is_dark():
            self.title_label.setStyleSheet(
                "padding: 8px; background-color: #3c3c3c; border-radius: 4px; color: #e0e0e0;"
            )
            self.list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    border: 1px solid #444;
                    border-radius: 6px;
                    padding: 4px;
                }
                QListWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #333;
                }
                QListWidget::item:hover {
                    background-color: #333;
                }
            """)
        else:
            self.title_label.setStyleSheet(
                "padding: 8px; background-color: #e9ecef; border-radius: 4px; color: #333;"
            )
            self.list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #ffffff;
                    color: #333;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 4px;
                }
                QListWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #f0f0f0;
                }
                QListWidget::item:hover {
                    background-color: #fff3e0;
                }
            """)


class MainWindow(QMainWindow):
    search_requested = pyqtSignal(str)
    daily_word_requested = pyqtSignal()
    quiz_requested = pyqtSignal()
    review_requested = pyqtSignal()
    word_book_toggle_requested = pyqtSignal(int)
    export_requested = pyqtSignal()
    print_requested = pyqtSignal()
    backup_requested = pyqtSignal()
    restore_requested = pyqtSignal()

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        self.theme_manager = theme_manager or ThemeManager()
        self.theme_manager.add_listener(self._on_theme_changed)

        self.setWindowTitle("现代汉语词典")
        self.setMinimumSize(900, 650)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
        """)

        self._build_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        top_bar = QHBoxLayout()
        self.font_control = FontSizeControl(self.theme_manager)
        top_bar.addWidget(self.font_control)
        top_bar.addStretch()

        self.daily_word_btn = QPushButton("每日一词")
        self.daily_word_btn.setFont(get_font(10, FONT_WEIGHT_BOLD))
        self.daily_word_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
            QPushButton:pressed {
                background-color: #e65100;
            }
        """)
        self.daily_word_btn.clicked.connect(self.daily_word_requested.emit)
        top_bar.addWidget(self.daily_word_btn)

        self.quiz_btn = QPushButton("测验模式")
        self.quiz_btn.setFont(get_font(10, FONT_WEIGHT_BOLD))
        self.quiz_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43a047;
            }
            QPushButton:pressed {
                background-color: #2e7d32;
            }
        """)
        self.quiz_btn.clicked.connect(self.quiz_requested.emit)
        top_bar.addWidget(self.quiz_btn)

        self.review_btn = QPushButton("复习")
        self.review_btn.setFont(get_font(10, FONT_WEIGHT_BOLD))
        self.review_btn.setStyleSheet("""
            QPushButton {
                background-color: #9c27b0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e24aa;
            }
            QPushButton:pressed {
                background-color: #6a1b9a;
            }
        """)
        self.review_btn.clicked.connect(self.review_requested.emit)
        top_bar.addWidget(self.review_btn)

        self.pinyin_toggle_btn = QPushButton("隐藏拼音")
        self.pinyin_toggle_btn.setCheckable(True)
        self.pinyin_toggle_btn.setChecked(not self.theme_manager.pinyin_visible)
        self.pinyin_toggle_btn.setFont(get_font(10))
        self.pinyin_toggle_btn.clicked.connect(self._toggle_pinyin)
        top_bar.addWidget(self.pinyin_toggle_btn)

        self.theme_btn = QPushButton("深色模式")
        self.theme_btn.setCheckable(True)
        self.theme_btn.setChecked(self.theme_manager.is_dark())
        self.theme_btn.setFont(get_font(10))
        self.theme_btn.clicked.connect(self._toggle_theme)
        top_bar.addWidget(self.theme_btn)

        main_layout.addLayout(top_bar)

        self.search_bar = SearchBar()
        main_layout.addWidget(self.search_bar)
        self.search_bar.search_requested.connect(self.search_requested.emit)

        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setMaximumHeight(4)
        self.loading_bar.setStyleSheet("QProgressBar { border: none; background: transparent; } QProgressBar::chunk { background-color: #1976d2; }")
        self.loading_bar.hide()
        main_layout.addWidget(self.loading_bar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        self.search_result_view = SearchResultView()
        left_layout.addWidget(self.search_result_view, stretch=3)

        copy_bar = QHBoxLayout()
        self.copy_word_btn = QPushButton("复制词语")
        self.copy_word_btn.setFont(get_font(10))
        self.copy_word_btn.clicked.connect(lambda: self._copy_field("word"))
        copy_bar.addWidget(self.copy_word_btn)

        self.copy_pinyin_btn = QPushButton("复制拼音")
        self.copy_pinyin_btn.setFont(get_font(10))
        self.copy_pinyin_btn.clicked.connect(lambda: self._copy_field("pinyin"))
        copy_bar.addWidget(self.copy_pinyin_btn)

        self.copy_def_btn = QPushButton("复制释义")
        self.copy_def_btn.setFont(get_font(10))
        self.copy_def_btn.clicked.connect(lambda: self._copy_field("definition"))
        copy_bar.addWidget(self.copy_def_btn)

        self.share_btn = QPushButton("分享")
        self.share_btn.setFont(get_font(10))
        self.share_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.share_btn.clicked.connect(self._share_current_word)
        copy_bar.addWidget(self.share_btn)

        copy_bar.addStretch()
        left_layout.addLayout(copy_bar)

        self.favorite_widget = FavoriteListWidget()
        left_layout.addWidget(self.favorite_widget, stretch=1)

        self.splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        self.history_widget = HistoryListWidget()
        right_layout.addWidget(self.history_widget)

        self.word_book_widget = FavoriteListWidget()
        self.word_book_widget.set_title("单词本")
        right_layout.addWidget(self.word_book_widget)

        self.splitter.addWidget(right_panel)
        self.splitter.setSizes([650, 250])

        main_layout.addWidget(self.splitter, stretch=1)

        self._setup_shortcuts()

        self.favorite_widget.item_clicked.connect(self.search_requested.emit)
        self.history_widget.item_clicked.connect(self.search_requested.emit)
        self.word_book_widget.item_clicked.connect(self.search_requested.emit)
        self.search_result_view.copy_requested.connect(self._on_copy_requested)

        self._current_word = ""
        self._current_pinyin = ""
        self._current_definition = ""
        self._current_definition_cn = ""
        self._current_examples: Optional[str] = None
        self._current_frequency: Optional[str] = None
        self._current_hsk_level: Optional[int] = None
        self._current_discrimination: Optional[str] = None

    def _build_menu_bar(self) -> None:
        menubar = self.menuBar()

        view_menu = menubar.addMenu("视图")

        self.theme_action = QAction("深色模式", self, checkable=True)
        self.theme_action.setChecked(self.theme_manager.is_dark())
        self.theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(self.theme_action)

        self.pinyin_action = QAction("显示拼音", self, checkable=True)
        self.pinyin_action.setChecked(self.theme_manager.pinyin_visible)
        self.pinyin_action.triggered.connect(self._toggle_pinyin_from_menu)
        view_menu.addAction(self.pinyin_action)

        view_menu.addSeparator()

        increase_font_action = QAction("增大字体", self)
        increase_font_action.setShortcut(QKeySequence("Ctrl++"))
        increase_font_action.triggered.connect(self._increase_font)
        view_menu.addAction(increase_font_action)

        decrease_font_action = QAction("减小字体", self)
        decrease_font_action.setShortcut(QKeySequence("Ctrl+-"))
        decrease_font_action.triggered.connect(self._decrease_font)
        view_menu.addAction(decrease_font_action)

        edit_menu = menubar.addMenu("编辑")

        copy_word_action = QAction("复制词语", self)
        copy_word_action.setShortcut(QKeySequence("Ctrl+Shift+W"))
        copy_word_action.triggered.connect(lambda: self._copy_field("word"))
        edit_menu.addAction(copy_word_action)

        copy_pinyin_action = QAction("复制拼音", self)
        copy_pinyin_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        copy_pinyin_action.triggered.connect(lambda: self._copy_field("pinyin"))
        edit_menu.addAction(copy_pinyin_action)

        copy_def_action = QAction("复制释义", self)
        copy_def_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
        copy_def_action.triggered.connect(lambda: self._copy_field("definition"))
        edit_menu.addAction(copy_def_action)

        file_menu = menubar.addMenu("文件")

        export_action = QAction("导出...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_requested.emit)
        file_menu.addAction(export_action)

        print_action = QAction("打印...", self)
        print_action.setShortcut(QKeySequence("Ctrl+P"))
        print_action.triggered.connect(self.print_requested.emit)
        file_menu.addAction(print_action)

        file_menu.addSeparator()

        backup_action = QAction("备份学习数据...", self)
        backup_action.setShortcut(QKeySequence("Ctrl+B"))
        backup_action.triggered.connect(self.backup_requested.emit)
        file_menu.addAction(backup_action)

        restore_action = QAction("恢复学习数据...", self)
        restore_action.setShortcut(QKeySequence("Ctrl+R"))
        restore_action.triggered.connect(self.restore_requested.emit)
        file_menu.addAction(restore_action)

        file_menu.addSeparator()

        share_action = QAction("分享当前词语", self)
        share_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        share_action.triggered.connect(self._share_current_word)
        file_menu.addAction(share_action)

        learn_menu = menubar.addMenu("学习")

        daily_word_action = QAction("每日一词", self)
        daily_word_action.setShortcut(QKeySequence("Ctrl+D"))
        daily_word_action.triggered.connect(self.daily_word_requested.emit)
        learn_menu.addAction(daily_word_action)

        quiz_action = QAction("测验模式", self)
        quiz_action.setShortcut(QKeySequence("Ctrl+Q"))
        quiz_action.triggered.connect(self.quiz_requested.emit)
        learn_menu.addAction(quiz_action)

        review_action = QAction("复习", self)
        review_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        review_action.triggered.connect(self.review_requested.emit)
        learn_menu.addAction(review_action)

    def _setup_shortcuts(self) -> None:
        """Setup global keyboard shortcuts."""
        # Ctrl+F - Focus search
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.search_bar.focus_search)

        # Esc - Clear search
        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self._on_esc_pressed)

        # Ctrl+S - Toggle favorite
        self.fav_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.fav_shortcut.activated.connect(self._toggle_favorite_shortcut)

        # Ctrl+T - Toggle theme
        self.theme_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        self.theme_shortcut.activated.connect(self._toggle_theme)

        # Ctrl+Shift+C - Copy all
        self.copy_all_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        self.copy_all_shortcut.activated.connect(self._copy_all)

    def _on_esc_pressed(self) -> None:
        """Handle Esc key - clear search if focused, otherwise clear result."""
        if self.search_bar.search_input.hasFocus():
            self.search_bar.clear()
        else:
            self.clear_result()

    def _toggle_favorite_shortcut(self) -> None:
        """Toggle favorite for current word via shortcut."""
        word_id = getattr(self, '_current_word_id', None)
        if word_id is not None:
            self.search_result_view.toggle_favorite.emit(word_id)

    def _copy_all(self) -> None:
        """Copy all current word info to clipboard."""
        if not self._current_word:
            return
        parts = []
        parts.append(f"词语：{self._current_word}")
        if self._current_pinyin:
            parts.append(f"拼音：{self._current_pinyin}")
        if self._current_definition_cn:
            parts.append(f"中文释义：{self._current_definition_cn}")
        if self._current_definition:
            parts.append(f"英文释义：{self._current_definition}")
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(parts))
        self._show_toast("已复制全部信息")

    def _toggle_theme(self) -> None:
        self.theme_manager.toggle_theme()

    def _toggle_pinyin(self) -> None:
        self.theme_manager.pinyin_visible = not self.theme_manager.pinyin_visible
        self.pinyin_toggle_btn.setText("显示拼音" if not self.theme_manager.pinyin_visible else "隐藏拼音")
        self.pinyin_action.setChecked(self.theme_manager.pinyin_visible)
        self.refresh_display()

    def _toggle_pinyin_from_menu(self, checked: bool) -> None:
        self.theme_manager.pinyin_visible = checked
        self.pinyin_toggle_btn.setText("显示拼音" if not checked else "隐藏拼音")
        self.pinyin_toggle_btn.setChecked(not checked)
        self.refresh_display()

    def _increase_font(self) -> None:
        self.font_control.slider.setValue(self.font_control.slider.value() + 1)

    def _decrease_font(self) -> None:
        self.font_control.slider.setValue(self.font_control.slider.value() - 1)

    def _on_theme_changed(self) -> None:
        is_dark = self.theme_manager.is_dark()
        self.theme_btn.setText("浅色模式" if is_dark else "深色模式")
        self.theme_btn.setChecked(is_dark)
        self.theme_action.setChecked(is_dark)

        # Update main window background
        if is_dark:
            self.setStyleSheet("QMainWindow { background-color: #2b2b2b; }")
        else:
            self.setStyleSheet("QMainWindow { background-color: #ffffff; }")

        self.favorite_widget.update_theme(self.theme_manager)
        self.history_widget.update_theme(self.theme_manager)
        self.word_book_widget.update_theme(self.theme_manager)
        self.search_bar.setStyleSheet(self._search_bar_qss())
        self.search_result_view._update_style(is_dark)
        self._update_all_fonts()
        self.refresh_display()

    def _update_all_fonts(self) -> None:
        tm = self.theme_manager
        self.setFont(get_font(tm.get_font_size(11)))
        self.search_bar.search_input.setFont(get_font(tm.get_font_size(12)))
        self.search_bar.search_button.setFont(get_font(tm.get_font_size(12), FONT_WEIGHT_BOLD))
        self.daily_word_btn.setFont(get_font(tm.get_font_size(10), FONT_WEIGHT_BOLD))
        self.quiz_btn.setFont(get_font(tm.get_font_size(10), FONT_WEIGHT_BOLD))
        self.review_btn.setFont(get_font(tm.get_font_size(10), FONT_WEIGHT_BOLD))
        self.pinyin_toggle_btn.setFont(get_font(tm.get_font_size(10)))
        self.theme_btn.setFont(get_font(tm.get_font_size(10)))
        self.copy_word_btn.setFont(get_font(tm.get_font_size(10)))
        self.copy_pinyin_btn.setFont(get_font(tm.get_font_size(10)))
        self.copy_def_btn.setFont(get_font(tm.get_font_size(10)))
        self.share_btn.setFont(get_font(tm.get_font_size(10)))
        self.search_result_view.setFont(get_font(tm.get_font_size(11)))

    def show_daily_word(self, word_data: Optional[Dict[str, Any]]) -> None:
        if not word_data:
            QMessageBox.information(self, "每日一词", "暂无每日词汇")
            return
        word = word_data.get("simplified", "")
        pinyin = word_data.get("pinyin", "")
        definition = word_data.get("definition_cn", "") or word_data.get("definition", "")
        QMessageBox.information(
            self, "每日一词",
            f"<h2>{word} <span style='font-size:14px;color:#666;'>{pinyin}</span></h2>"
            f"<p>{definition}</p>"
        )

    def show_review_list(self, words: List[Dict[str, Any]]) -> None:
        if not words:
            QMessageBox.information(self, "复习", "暂无待复习的单词")
            return
        items = [f"{w['simplified']} ({w['pinyin']})" for w in words[:10]]
        text = "<h3>待复习单词:</h3><ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
        QMessageBox.information(self, "复习", text)

    def _search_bar_qss(self) -> str:
        if self.theme_manager.is_dark():
            return """
                QLineEdit {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    border: 2px solid #1976d2;
                    border-radius: 6px;
                    padding: 10px 14px;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border: 2px solid #42a5f5;
                    background-color: #252525;
                }
                QPushButton {
                    background-color: #1976d2;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 24px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #1565c0; }
                QPushButton:pressed { background-color: #0d47a1; }
                QListWidget {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    border: 1px solid #444;
                    border-top: none;
                    border-radius: 0 0 6px 6px;
                }
                QListWidget::item:selected {
                    background-color: #333;
                    color: #e0e0e0;
                }
            """
        return """
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
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1565c0; }
            QPushButton:pressed { background-color: #0d47a1; }
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-top: none;
                border-radius: 0 0 6px 6px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #333;
            }
        """

    def _result_view_qss(self) -> str:
        bg = self.theme_manager.get_result_bg()
        border = self.theme_manager.get_border_color()
        return f"""
            QTextEdit {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 12px;
            }}
        """

    def refresh_display(self) -> None:
        if self._current_word:
            self.display_result(
                self._current_word,
                self._current_pinyin,
                self._current_definition,
                self._current_definition_cn,
                getattr(self, '_current_word_id', None),
                getattr(self, '_current_is_favorite', False),
                getattr(self, '_current_examples', None),
                getattr(self, '_current_frequency', None),
                getattr(self, '_current_hsk_level', None),
                getattr(self, '_current_discrimination', None),
            )

    def display_result(self, word: str, pinyin: str, definition: str, definition_cn: str,
                       word_id: Optional[int], is_favorite: bool = False,
                       examples: Optional[str] = None, frequency: Optional[str] = None,
                       hsk_level: Optional[int] = None, discrimination: Optional[str] = None) -> None:
        self._current_word = word or ""
        self._current_pinyin = pinyin or ""
        self._current_definition = definition or ""
        self._current_definition_cn = definition_cn or ""
        self._current_word_id = word_id
        self._current_is_favorite = is_favorite
        self._current_examples = examples
        self._current_frequency = frequency
        self._current_hsk_level = hsk_level
        self._current_discrimination = discrimination

        self.search_result_view.set_content(self._current_word, self._current_pinyin, self._current_definition)

        favorite_icon = "★" if is_favorite else "☆"
        safe_word = self._current_word
        safe_pinyin = self._current_pinyin if self.theme_manager.pinyin_visible else ""
        safe_definition = self._current_definition
        safe_definition_cn = self._current_definition_cn

        tm = self.theme_manager
        text_color = tm.get_text_color()
        muted = tm.get_muted_color()
        card_bg = tm.get_card_bg()
        border = tm.get_border_color()
        cn_header_bg = tm.get_section_header_bg("cn")
        cn_header_color = tm.get_section_header_color("cn")
        en_header_bg = tm.get_section_header_bg("en")
        en_header_color = tm.get_section_header_color("en")
        font_size = tm.get_font_size(14)
        line_size = tm.get_font_size(13)
        header_size = tm.get_font_size(14)

        sections = ""

        badge_html = ""
        if frequency:
            freq_labels = {"common": "常用", "moderate": "一般", "rare": "生僻"}
            freq_colors = {"common": "#4caf50", "moderate": "#ff9800", "rare": "#9e9e9e"}
            label = freq_labels.get(frequency, frequency)
            color = freq_colors.get(frequency, "#666")
            badge_html += f'<span style="display: inline-block; margin-left: 8px; padding: 2px 8px; background-color: {color}; color: white; border-radius: 12px; font-size: {tm.get_font_size(11)}px;">{label}</span>'
        if hsk_level:
            badge_html += f'<span style="display: inline-block; margin-left: 8px; padding: 2px 8px; background-color: #e53935; color: white; border-radius: 12px; font-size: {tm.get_font_size(11)}px;">HSK {hsk_level}</span>'

        if safe_definition_cn:
            formatted_cn = safe_definition_cn.replace('\n', '<br/>')
            sections += f"""
            <div style="margin-bottom: 16px;">
                <h3 style="color: {cn_header_color}; font-size: {header_size}px; margin: 0 0 8px 0; padding: 4px 8px; background-color: {cn_header_bg}; border-radius: 4px;">中文释义</h3>
                <p style="font-size: {font_size}px; line-height: 1.8; color: {text_color}; margin: 0; padding-left: 8px;">
                    {formatted_cn}
                </p>
            </div>
            """

        if safe_definition:
            formatted_en = safe_definition.replace(';', '<br/>• ')
            sections += f"""
            <div style="margin-bottom: 16px;">
                <h3 style="color: {en_header_color}; font-size: {header_size}px; margin: 0 0 8px 0; padding: 4px 8px; background-color: {en_header_bg}; border-radius: 4px;">英文释义</h3>
                <p style="font-size: {line_size}px; line-height: 1.8; color: {text_color}; margin: 0; padding-left: 8px;">
                    {formatted_en}
                </p>
            </div>
            """

        if examples:
            try:
                import json
                example_list = json.loads(examples) if isinstance(examples, str) else examples
                if isinstance(example_list, list) and example_list:
                    example_items = "<br/>".join(f"<li>{ex}</li>" for ex in example_list if ex)
                    sections += f"""
                    <div style="margin-bottom: 16px;">
                        <h3 style="color: {cn_header_color}; font-size: {header_size}px; margin: 0 0 8px 0; padding: 4px 8px; background-color: {cn_header_bg}; border-radius: 4px;">例句</h3>
                        <ul style="font-size: {font_size}px; line-height: 1.8; color: {text_color}; margin: 0; padding-left: 24px;">
                            {example_items}
                        </ul>
                    </div>
                    """
            except Exception:
                pass

        if discrimination:
            disc_html = discrimination.replace('\n', '<br/>')
            sections += f"""
            <div style="margin-bottom: 16px;">
                <h3 style="color: {en_header_color}; font-size: {header_size}px; margin: 0 0 8px 0; padding: 4px 8px; background-color: {en_header_bg}; border-radius: 4px;">词语辨析</h3>
                <p style="font-size: {font_size}px; line-height: 1.8; color: {text_color}; margin: 0; padding-left: 8px;">
                    {disc_html}
                </p>
            </div>
            """

        if not sections:
            sections = f'<p style="font-size: {font_size}px; color: {muted};">暂无释义</p>'

        css_font = get_css_font_family()
        pinyin_html = f' <span style="font-size: {tm.get_font_size(14)}px; color: {muted};">{safe_pinyin}</span>' if safe_pinyin else ""

        html = f"""
        <div style="font-family: {css_font}; background-color: {card_bg}; color: {text_color};">
            <h2 style="color: {cn_header_color}; margin: 0;">{safe_word}{pinyin_html}{badge_html} <span style="float: right; font-size: 18px; cursor: pointer;">{favorite_icon}</span></h2>
            <hr style="border: none; border-top: 2px solid {border}; margin: 12px 0;">
            {sections}
        </div>
        """
        self.search_result_view.current_word_id = word_id
        self.search_result_view.setHtml(html)

    def display_no_result(self, word: str) -> None:
        safe_word = word or ""
        css_font = get_css_font_family()
        tm = self.theme_manager
        text_color = tm.get_text_color()
        muted = tm.get_muted_color()
        font_size = tm.get_font_size(16)
        small_size = tm.get_font_size(12)

        html = f"""
        <div style="font-family: {css_font}; text-align: center; padding: 40px; color: {text_color};">
            <p style="font-size: {font_size}px; color: {muted};">未找到「{safe_word}」的释义</p>
            <p style="font-size: {small_size}px; color: {muted};">请尝试其他词汇或检查拼写</p>
        </div>
        """
        self.search_result_view.current_word_id = None
        self.search_result_view.setHtml(html)
        self._current_word = ""
        self._current_pinyin = ""
        self._current_definition = ""
        self._current_definition_cn = ""
        self._current_examples = None
        self._current_frequency = None
        self._current_hsk_level = None
        self._current_discrimination = None
        self.search_result_view.set_content("", "", "")

    def clear_result(self) -> None:
        self.search_result_view.current_word_id = None
        self.search_result_view.clear()
        self._current_word = ""
        self._current_pinyin = ""
        self._current_definition = ""
        self._current_definition_cn = ""
        self._current_examples = None
        self._current_frequency = None
        self._current_hsk_level = None
        self._current_discrimination = None
        self.search_result_view.set_content("", "", "")

    def _copy_field(self, field: str) -> None:
        text = ""
        if field == "word":
            text = self._current_word
        elif field == "pinyin":
            text = self._current_pinyin
        elif field == "definition":
            parts = []
            if self._current_definition_cn:
                parts.append(self._current_definition_cn)
            if self._current_definition:
                parts.append(self._current_definition)
            text = "\n".join(parts)
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

    def _on_copy_requested(self, field: str, text: str) -> None:
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

    def _share_current_word(self) -> None:
        word = self._current_word
        if not word:
            QMessageBox.information(self, "分享", "请先查询一个词语")
            return
        pinyin = self._current_pinyin or ""
        definition_cn = self._current_definition_cn or ""
        definition = self._current_definition or ""
        share_text = f"词语：{word}\n拼音：{pinyin}\n释义：{definition_cn}\n英文：{definition}"
        clipboard = QApplication.clipboard()
        clipboard.setText(share_text)
        self._show_toast("已复制到剪贴板，可直接粘贴分享")

    def _show_toast(self, message: str, duration: int = 2000) -> None:
        toast = QLabel(message, self)
        toast.setFont(get_font(11))
        toast.setStyleSheet("""
            QLabel {
                background-color: #323232;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
            }
        """)
        toast.adjustSize()
        x = (self.width() - toast.width()) // 2
        y = self.height() - toast.height() - 60
        toast.move(x, y)
        toast.show()
        QTimer.singleShot(duration, toast.close)

    def set_loading(self, loading: bool) -> None:
        if loading:
            self.loading_bar.show()
        else:
            self.loading_bar.hide()

    def show_update_notification(self, remote_version: str, info: str = "") -> None:
        msg = QMessageBox(self)
        msg.setWindowTitle("发现新版本")
        msg.setText(f"检测到新版本 v{remote_version}，当前版本较旧。")
        if info:
            msg.setDetailedText(info)
        msg.setIcon(MSG_ICON_INFORMATION)
        copy_btn = msg.addButton("复制详情", MSG_ACTION_ROLE)
        ok_btn = msg.addButton("稍后提醒", MSG_ACCEPT_ROLE)
        msg.exec()
        if msg.clickedButton() == copy_btn:
            clipboard = QApplication.clipboard()
            clipboard.setText(f"新版本: v{remote_version}\n\n{info}")
