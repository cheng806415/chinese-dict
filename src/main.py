import sys
import os
import traceback

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from src.utils.qt_compat import QApplication, QMessageBox, QFont, MSG_ICON_CRITICAL

from src.database.db_manager import DatabaseManager, get_db_path
from src.database.importer import import_data
from src.ui.main_window import MainWindow


def global_exception_handler(exc_type, exc_value, exc_tb):
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"Unhandled exception:\n{error_msg}")
    try:
        msg = QMessageBox()
        msg.setIcon(MSG_ICON_CRITICAL)
        msg.setWindowTitle("Error")
        msg.setText(str(exc_value))
        msg.setDetailedText(error_msg)
        msg.exec()
    except Exception:
        pass


class DictionaryApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("现代汉语词典")
        self.app.setStyle("Fusion")

        self.db = None
        self.main_window = None

        if sys.platform == 'darwin':
            self.app.setFont(QFont("PingFang SC", 13))
        elif sys.platform == 'win32':
            self.app.setFont(QFont("Microsoft YaHei", 10))
        else:
            self.app.setFont(QFont("Noto Sans CJK SC", 10))

    def initialize_database(self):
        db_path = import_data()
        self.db = DatabaseManager(db_path)
        self.show_main_window()

    def show_main_window(self):
        self.main_window = MainWindow()
        self.main_window.search_requested.connect(self.on_search)
        self.main_window.search_bar.set_suggestions_callback(self.get_suggestions)
        self.main_window.search_bar.search_requested.connect(self.on_search_history_add)
        self.main_window.search_result_view.toggle_favorite.connect(self.on_toggle_favorite)

        self.load_favorites()
        self.load_history()

        self.main_window.show()

    def load_favorites(self):
        try:
            favorites = self.db.get_favorites()
            for fav in favorites:
                self.main_window.favorite_widget.add_item(fav["simplified"])
        except Exception as e:
            print(f"Error loading favorites: {e}")

    def load_history(self):
        try:
            history = self.db.get_search_history()
            for word in history:
                self.main_window.history_widget.add_item(word)
        except Exception as e:
            print(f"Error loading history: {e}")

    def on_search(self, word):
        if not word:
            return

        try:
            result = self.db.search_exact(word)

            if result:
                is_fav = self.db.is_favorite(result["id"])
                self.main_window.display_result(
                    result["simplified"],
                    result["pinyin"],
                    result["definition"],
                    result.get("definition_cn", ""),
                    result["id"],
                    is_fav
                )
                self.on_search_history_add(word)
            else:
                self.main_window.display_no_result(word)
                self.on_search_history_add(word)
        except Exception as e:
            error_msg = f"Search error: {e}\n{traceback.format_exc()}"
            print(error_msg)
            try:
                self.main_window.display_no_result(word)
            except Exception:
                pass

    def on_toggle_favorite(self, word_id):
        try:
            if self.db.is_favorite(word_id):
                self.db.remove_favorite(word_id)
            else:
                self.db.add_favorite(word_id)

            self.load_favorites()

            current_word = self.main_window.search_bar.get_text()
            if current_word:
                self.on_search(current_word)
        except Exception as e:
            print(f"Error toggling favorite: {e}")

    def on_search_history_add(self, word):
        if word:
            try:
                self.db.add_search_history(word)
                self.main_window.history_widget.add_item(word)
            except Exception as e:
                print(f"Error adding history: {e}")

    def get_suggestions(self, prefix):
        if not prefix or len(prefix) < 1:
            return []
        try:
            return self.db.get_suggestions(prefix, limit=10)
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return []

    def run(self):
        try:
            self.initialize_database()
            sys.exit(self.app.exec())
        except Exception as e:
            error_msg = f"Fatal error: {e}\n{traceback.format_exc()}"
            print(error_msg)
            try:
                msg = QMessageBox()
                msg.setIcon(MSG_ICON_CRITICAL)
                msg.setWindowTitle("Fatal Error")
                msg.setText(str(e))
                msg.setDetailedText(error_msg)
                msg.exec()
            except Exception:
                pass
        finally:
            if self.db:
                self.db.close()


def main():
    sys.excepthook = global_exception_handler
    if getattr(sys, 'frozen', False) and sys.platform == 'darwin':
        log_dir = os.path.expanduser('~/Library/Logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'ChineseDict.log')
        sys.stdout = open(log_path, 'a', encoding='utf-8')
        sys.stderr = sys.stdout
        print(f"=== ChineseDict started at {__import__('datetime').datetime.now()} ===")
        print(f"Python: {sys.version}")
        print(f"Executable: {sys.executable}")
        print(f"_MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
        print(f"frozen: {getattr(sys, 'frozen', False)}")
    app = DictionaryApp()
    app.run()


if __name__ == "__main__":
    main()
