import sys
import os
import traceback
import datetime
import json
from typing import Optional

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from src.utils.qt_compat import (
    QApplication, QMessageBox, QFont, MSG_ICON_CRITICAL, QTimer,
    MSG_ACTION_ROLE, MSG_ACCEPT_ROLE, QFileDialog
)

from src.database.db_manager import DatabaseManager, get_db_path
from src.database.importer import import_data
from src.ui.main_window import MainWindow
from src.ui.quiz_dialog import QuizDialog
from src.ui.export_dialog import ExportManager
from src.utils.theme import ThemeManager
from src.utils.helpers import get_version, get_crash_log_dir, get_platform_info


def _write_crash_log(error_msg: str) -> Optional[str]:
    try:
        crash_dir = get_crash_log_dir()
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        crash_file = os.path.join(crash_dir, f'crash_{timestamp}.log')
        with open(crash_file, 'w', encoding='utf-8') as f:
            f.write(f"App Version: {get_version()}\n")
            f.write(f"Time: {datetime.datetime.now().isoformat()}\n")
            for k, v in get_platform_info().items():
                f.write(f"{k}: {v}\n")
            f.write("\n--- Stack Trace ---\n")
            f.write(error_msg)
        return crash_file
    except Exception:
        return None


def _show_crash_dialog(error_msg: str, crash_file: Optional[str] = None) -> None:
    try:
        msg = QMessageBox()
        msg.setIcon(MSG_ICON_CRITICAL)
        msg.setWindowTitle("程序出现错误")
        msg.setText("很抱歉，程序遇到了一个错误。")
        detailed = error_msg
        if crash_file:
            detailed += f"\n\n崩溃日志已保存到:\n{crash_file}"
        msg.setDetailedText(detailed)
        copy_btn = msg.addButton("复制错误信息", MSG_ACTION_ROLE)
        msg.addButton("确定", MSG_ACCEPT_ROLE)
        msg.exec()
        if msg.clickedButton() == copy_btn:
            from src.utils.qt_compat import QClipboard, QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(detailed)
    except Exception:
        pass


def global_exception_handler(exc_type, exc_value, exc_tb) -> None:
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"Unhandled exception:\n{error_msg}")
    crash_file = _write_crash_log(error_msg)
    _show_crash_dialog(error_msg, crash_file)


class DictionaryApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("现代汉语词典")
        self.app.setStyle("Fusion")

        self.db: Optional[DatabaseManager] = None
        self.main_window: Optional[MainWindow] = None
        self.theme_manager = ThemeManager(self.app)
        self.export_manager: Optional[ExportManager] = None

        if sys.platform == 'darwin':
            self.app.setFont(QFont("PingFang SC", 13))
        elif sys.platform == 'win32':
            self.app.setFont(QFont("Microsoft YaHei", 10))
        else:
            self.app.setFont(QFont("Noto Sans CJK SC", 10))

    def initialize_database(self) -> None:
        db_path = import_data()
        self.db = DatabaseManager(db_path)
        self._load_settings()
        self._setup_main_window_connections()
        self.load_favorites()
        self.load_history()
        self.load_word_book()
        self.main_window.set_loading(False)
        self._check_update()

    def _load_settings(self) -> None:
        try:
            theme = self.db.get_setting("theme", "light")
            if theme == "dark":
                self.theme_manager.set_theme(ThemeManager.DARK)
            font_offset = self.db.get_setting("font_size_offset", "0")
            try:
                self.theme_manager.font_size_offset = int(font_offset)
            except ValueError:
                pass
            pinyin = self.db.get_setting("pinyin_visible", "1")
            self.theme_manager.pinyin_visible = pinyin == "1"
        except Exception as e:
            print(f"Error loading settings: {e}")

    def _save_settings(self) -> None:
        try:
            self.db.set_setting("theme", self.theme_manager.current_theme)
            self.db.set_setting("font_size_offset", str(self.theme_manager.font_size_offset))
            self.db.set_setting("pinyin_visible", "1" if self.theme_manager.pinyin_visible else "0")
        except Exception as e:
            print(f"Error saving settings: {e}")

    def _setup_main_window_connections(self) -> None:
        self.main_window.search_requested.connect(self.on_search)
        self.main_window.search_bar.set_suggestions_callback(self.get_suggestions)
        self.main_window.search_result_view.toggle_favorite.connect(self.on_toggle_favorite)
        self.main_window.daily_word_requested.connect(self.on_daily_word)
        self.main_window.quiz_requested.connect(self.on_quiz)
        self.main_window.review_requested.connect(self.on_review)
        self.main_window.word_book_toggle_requested.connect(self.on_toggle_word_book)
        self.main_window.export_requested.connect(self.on_export)
        self.main_window.print_requested.connect(self.on_print)
        self.main_window.backup_requested.connect(self.on_backup)
        self.main_window.restore_requested.connect(self.on_restore)

    def _delayed_init(self) -> None:
        self.main_window.set_loading(True)
        try:
            self.initialize_database()
        except Exception as e:
            error_msg = f"Initialization error: {e}\n{traceback.format_exc()}"
            print(error_msg)
            crash_file = _write_crash_log(error_msg)
            _show_crash_dialog(error_msg, crash_file)

    def _check_update(self) -> None:
        try:
            result = self.db.update_check()
            if result.get('has_update'):
                self.main_window.show_update_notification(
                    result.get('remote_version', ''),
                    result.get('info', '')
                )
        except Exception as e:
            print(f"Update check error: {e}")

    def load_favorites(self) -> None:
        try:
            favorites = self.db.get_favorites()
            for fav in favorites:
                self.main_window.favorite_widget.add_item(fav["simplified"])
        except Exception as e:
            print(f"Error loading favorites: {e}")

    def load_history(self) -> None:
        try:
            history = self.db.get_search_history()
            for word in history:
                self.main_window.history_widget.add_item(word)
        except Exception as e:
            print(f"Error loading history: {e}")

    def load_word_book(self) -> None:
        try:
            words = self.db.get_word_book_words()
            for w in words:
                self.main_window.word_book_widget.add_item(w["simplified"])
        except Exception as e:
            print(f"Error loading word book: {e}")

    def on_search(self, word: str) -> None:
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
                    is_fav,
                    result.get("examples"),
                    result.get("frequency"),
                    result.get("hsk_level"),
                    result.get("discrimination"),
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

    def on_toggle_favorite(self, word_id: int) -> None:
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

    def on_search_history_add(self, word: str) -> None:
        if word:
            try:
                self.db.add_search_history(word)
                self.main_window.history_widget.add_item(word)
            except Exception as e:
                print(f"Error adding history: {e}")

    def get_suggestions(self, prefix: str) -> list:
        if not prefix or len(prefix) < 1:
            return []
        try:
            return self.db.get_suggestions(prefix, limit=10)
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return []

    def on_daily_word(self) -> None:
        try:
            word = self.db.get_daily_word()
            self.main_window.show_daily_word(word)
            if word:
                self.db.update_study_streak()
        except Exception as e:
            print(f"Error getting daily word: {e}")

    def on_quiz(self) -> None:
        try:
            dialog = QuizDialog(self.db, parent=self.main_window)
            dialog.quiz_finished.connect(self._on_quiz_finished)
            dialog.exec()
        except Exception as e:
            print(f"Error starting quiz: {e}")

    def _on_quiz_finished(self, score: int, total: int) -> None:
        try:
            self.db.record_quiz_result(score, total)
            self.db.update_study_streak()
        except Exception as e:
            print(f"Error recording quiz result: {e}")

    def on_review(self) -> None:
        try:
            words = self.db.get_due_reviews()
            self.main_window.show_review_list(words)
            if words:
                self.db.update_study_streak()
        except Exception as e:
            print(f"Error getting reviews: {e}")

    def on_toggle_word_book(self, word_id: int) -> None:
        try:
            if self.db.is_in_word_book(word_id):
                self.db.remove_from_word_book(word_id)
            else:
                self.db.add_to_word_book(word_id)
            self.load_word_book()
        except Exception as e:
            print(f"Error toggling word book: {e}")

    def run(self) -> None:
        try:
            self.main_window = MainWindow(self.theme_manager)
            self._setup_main_window_connections()

            self.export_manager = ExportManager(self.db, self.main_window)

            self.main_window.show()
            QTimer.singleShot(100, self._delayed_init)

            exit_code = self.app.exec()
            self._save_settings()
            sys.exit(exit_code)
        except Exception as e:
            error_msg = f"Fatal error: {e}\n{traceback.format_exc()}"
            print(error_msg)
            crash_file = _write_crash_log(error_msg)
            _show_crash_dialog(error_msg, crash_file)
        finally:
            if self.db:
                self.db.close()

    def on_export(self) -> None:
        try:
            self.export_manager.show_export_dialog()
        except Exception as e:
            print(f"Error exporting: {e}")

    def on_print(self) -> None:
        try:
            mw = self.main_window
            if not mw._current_word:
                QMessageBox.information(mw, "打印", "请先查询一个词语")
                return
            self.export_manager.print_current(
                mw._current_word,
                mw._current_pinyin,
                mw._current_definition,
                mw._current_definition_cn,
            )
        except Exception as e:
            print(f"Error printing: {e}")

    def on_backup(self) -> None:
        """Backup learning data to a JSON file."""
        try:
            data = self.db.export_learning_data()
            file_path, _ = QFileDialog.getSaveFileName(
                self.main_window,
                "备份学习数据",
                f"ChineseDict_backup_{datetime.datetime.now().strftime('%Y%m%d')}.json",
                "JSON Files (*.json);;All Files (*)"
            )
            if not file_path:
                return
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(
                self.main_window,
                "备份成功",
                f"学习数据已备份到:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                "备份失败",
                f"备份过程中出现错误:\n{str(e)}"
            )

    def on_restore(self) -> None:
        """Restore learning data from a JSON file."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self.main_window,
                "恢复学习数据",
                "",
                "JSON Files (*.json);;All Files (*)"
            )
            if not file_path:
                return
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Confirm restore
            reply = QMessageBox.question(
                self.main_window,
                "确认恢复",
                "恢复学习数据将覆盖当前的学习记录（收藏、单词本、学习统计等）。\n"
                "词典词汇数据不会受到影响。\n\n是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            success = self.db.import_learning_data(data)
            if success:
                # Reload UI
                self.main_window.favorite_widget.clear()
                self.main_window.history_widget.clear()
                self.main_window.word_book_widget.clear()
                self.load_favorites()
                self.load_history()
                self.load_word_book()
                QMessageBox.information(
                    self.main_window,
                    "恢复成功",
                    "学习数据已成功恢复。"
                )
            else:
                QMessageBox.warning(
                    self.main_window,
                    "恢复失败",
                    "数据恢复失败，请检查备份文件是否有效。"
                )
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                "恢复失败",
                f"恢复过程中出现错误:\n{str(e)}"
            )


def main() -> None:
    sys.excepthook = global_exception_handler
    if getattr(sys, 'frozen', False) and sys.platform == 'darwin':
        log_dir = os.path.expanduser('~/Library/Logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'ChineseDict.log')
        sys.stdout = open(log_path, 'a', encoding='utf-8')
        sys.stderr = sys.stdout
        print(f"=== ChineseDict started at {datetime.datetime.now()} ===")
        print(f"Python: {sys.version}")
        print(f"Executable: {sys.executable}")
        print(f"_MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
        print(f"frozen: {getattr(sys, 'frozen', False)}")
    app = DictionaryApp()
    app.run()


if __name__ == "__main__":
    main()
