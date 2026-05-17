from src.utils.qt_compat import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QSplitter, QListWidget, QListWidgetItem, QPushButton,
    QFrame, QScrollArea, Qt, pyqtSignal, QFont, QTextCursor,
    FONT_WEIGHT_BOLD, ALIGN_CENTER
)
from src.ui.search_bar import SearchBar
from src.utils.font import get_font, get_css_font_family

class SearchResultView(QTextEdit):
    toggle_favorite = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(get_font(11))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        self.setPlaceholderText("输入词汇进行查询...")
        self.current_word_id = None
    
    def mousePressEvent(self, event):
        try:
            cursor = self.cursorForPosition(event.pos())
            cursor.select(QTextCursor.WordUnderCursor)
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("收藏词汇")
        title_label.setFont(get_font(10, FONT_WEIGHT_BOLD))
        title_label.setStyleSheet("padding: 8px; background-color: #e9ecef; border-radius: 4px;")
        layout.addWidget(title_label)
        
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
    
    def _on_item_clicked(self, item):
        self.item_clicked.emit(item.text())
    
    def add_item(self, word):
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).text() == word:
                return
        self.list_widget.addItem(word)
    
    def clear(self):
        self.list_widget.clear()
    
    def get_items(self):
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]

class HistoryListWidget(QWidget):
    item_clicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("搜索历史")
        title_label.setFont(get_font(10, FONT_WEIGHT_BOLD))
        title_label.setStyleSheet("padding: 8px; background-color: #e9ecef; border-radius: 4px;")
        layout.addWidget(title_label)
        
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
    
    def _on_item_clicked(self, item):
        self.item_clicked.emit(item.text())
    
    def add_item(self, word):
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).text() == word:
                return
        self.list_widget.insertItem(0, word)
    
    def clear(self):
        self.list_widget.clear()

class MainWindow(QMainWindow):
    search_requested = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("现代汉语词典")
        self.setMinimumSize(900, 650)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        self.search_bar = SearchBar()
        main_layout.addWidget(self.search_bar)
        self.search_bar.search_requested.connect(self.search_requested.emit)
        
        content_splitter = QHBoxLayout()
        content_splitter.setSpacing(16)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        
        self.search_result_view = SearchResultView()
        left_layout.addWidget(self.search_result_view, stretch=3)
        
        self.favorite_widget = FavoriteListWidget()
        left_layout.addWidget(self.favorite_widget, stretch=1)
        
        content_splitter.addWidget(left_panel, stretch=3)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        
        self.history_widget = HistoryListWidget()
        right_layout.addWidget(self.history_widget)
        
        content_splitter.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_splitter)
        
        self.favorite_widget.item_clicked.connect(self.search_requested.emit)
        self.history_widget.item_clicked.connect(self.search_requested.emit)
    
    def display_result(self, word, pinyin, definition, definition_cn, word_id, is_favorite=False):
        favorite_icon = "☆" if not is_favorite else "★"
        safe_word = word or ""
        safe_pinyin = pinyin or ""
        safe_definition = definition or ""
        safe_definition_cn = definition_cn or ""

        sections = ""

        if safe_definition_cn:
            formatted_cn = safe_definition_cn.replace('\n', '<br/>')
            sections += f"""
            <div style="margin-bottom: 16px;">
                <h3 style="color: #1976d2; font-size: 14px; margin: 0 0 8px 0; padding: 4px 8px; background-color: #e3f2fd; border-radius: 4px;">中文释义</h3>
                <p style="font-size: 14px; line-height: 1.8; color: #333; margin: 0; padding-left: 8px;">
                    {formatted_cn}
                </p>
            </div>
            """

        if safe_definition:
            formatted_en = safe_definition.replace(';', '<br/>• ')
            sections += f"""
            <div style="margin-bottom: 16px;">
                <h3 style="color: #6a1b9a; font-size: 14px; margin: 0 0 8px 0; padding: 4px 8px; background-color: #f3e5f5; border-radius: 4px;">英文释义</h3>
                <p style="font-size: 13px; line-height: 1.8; color: #555; margin: 0; padding-left: 8px;">
                    {formatted_en}
                </p>
            </div>
            """

        if not sections:
            sections = '<p style="font-size: 14px; color: #999;">暂无释义</p>'

        css_font = get_css_font_family()

        html = f"""
        <div style="font-family: {css_font};">
            <h2 style="color: #1976d2; margin: 0;">{safe_word} <span style="font-size: 14px; color: #666;">{safe_pinyin}</span> <span style="float: right; font-size: 18px; cursor: pointer;">{favorite_icon}</span></h2>
            <hr style="border: none; border-top: 2px solid #e0e0e0; margin: 12px 0;">
            {sections}
        </div>
        """
        self.search_result_view.current_word_id = word_id
        self.search_result_view.setHtml(html)
    
    def display_no_result(self, word):
        safe_word = word or ""
        css_font = get_css_font_family()
        html = f"""
        <div style="font-family: {css_font}; text-align: center; padding: 40px;">
            <p style="font-size: 16px; color: #999;">未找到「{safe_word}」的释义</p>
            <p style="font-size: 12px; color: #bbb;">请尝试其他词汇或检查拼写</p>
        </div>
        """
        self.search_result_view.current_word_id = None
        self.search_result_view.setHtml(html)
    
    def clear_result(self):
        self.search_result_view.current_word_id = None
        self.search_result_view.clear()
