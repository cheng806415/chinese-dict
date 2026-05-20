import unittest
import sqlite3
import os
import tempfile
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.db_manager import DatabaseManager, format_pinyin


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_initialization(self):
        self.assertIsNotNone(self.db.conn)
        self.assertIsNotNone(self.db.cursor)

    def test_tables_created(self):
        tables = ['words', 'favorites', 'search_history', 'daily_word',
                  'word_book', 'stats', 'settings']
        for table in tables:
            self.db.cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            )
            self.assertIsNotNone(self.db.cursor.fetchone(), f"Table {table} should exist")

    def test_add_and_search_word(self):
        self.db.cursor.execute('''
            INSERT INTO words (traditional, simplified, pinyin, definition)
            VALUES (?, ?, ?, ?)
        ''', ('测试', '测试', 'ce4 shi4', 'test'))
        self.db.conn.commit()

        result = self.db.search_exact('测试')
        self.assertIsNotNone(result)
        self.assertEqual(result['simplified'], '测试')
        self.assertEqual(result['pinyin'], 'cè shì')

    def test_search_no_result(self):
        result = self.db.search_exact('不存在')
        self.assertIsNone(result)

    def test_favorite(self):
        self.db.cursor.execute('''
            INSERT INTO words (traditional, simplified, pinyin, definition)
            VALUES (?, ?, ?, ?)
        ''', ('测试', '测试', 'ce4 shi4', 'test'))
        self.db.conn.commit()
        word_id = self.db.cursor.lastrowid

        self.assertFalse(self.db.is_favorite(word_id))
        self.db.add_favorite(word_id)
        self.assertTrue(self.db.is_favorite(word_id))

        favorites = self.db.get_favorites()
        self.assertEqual(len(favorites), 1)

        self.db.remove_favorite(word_id)
        self.assertFalse(self.db.is_favorite(word_id))

    def test_search_history(self):
        self.db.add_search_history('测试')
        history = self.db.get_search_history()
        self.assertIn('测试', history)

    def test_word_book(self):
        self.db.cursor.execute('''
            INSERT INTO words (traditional, simplified, pinyin, definition)
            VALUES (?, ?, ?, ?)
        ''', ('测试', '测试', 'ce4 shi4', 'test'))
        self.db.conn.commit()
        word_id = self.db.cursor.lastrowid

        self.assertFalse(self.db.is_in_word_book(word_id))
        self.db.add_to_word_book(word_id)
        self.assertTrue(self.db.is_in_word_book(word_id))

        words = self.db.get_word_book_words()
        self.assertEqual(len(words), 1)

        self.db.remove_from_word_book(word_id)
        self.assertFalse(self.db.is_in_word_book(word_id))

    def test_settings(self):
        self.assertIsNone(self.db.get_setting('test_key'))
        self.assertEqual(self.db.get_setting('test_key', 'default'), 'default')

        self.db.set_setting('test_key', 'test_value')
        self.assertEqual(self.db.get_setting('test_key'), 'test_value')

        self.db.set_setting('test_key', 'updated_value')
        self.assertEqual(self.db.get_setting('test_key'), 'updated_value')

    def test_stats(self):
        stats = self.db.get_stats()
        self.assertIn('total_words_learned', stats)
        self.assertIn('total_reviews', stats)
        self.assertIn('streak_days', stats)

    def test_export_import_learning_data(self):
        # Add test data
        self.db.cursor.execute('''
            INSERT INTO words (traditional, simplified, pinyin, definition)
            VALUES (?, ?, ?, ?)
        ''', ('测试', '测试', 'ce4 shi4', 'test'))
        self.db.conn.commit()
        word_id = self.db.cursor.lastrowid

        self.db.add_favorite(word_id)
        self.db.add_search_history('测试')
        self.db.add_to_word_book(word_id)

        # Export
        exported = self.db.export_learning_data()
        self.assertIn('version', exported)
        self.assertIn('exported_at', exported)
        self.assertIn('tables', exported)

        # Clear data
        self.db.cursor.execute('DELETE FROM favorites')
        self.db.cursor.execute('DELETE FROM search_history')
        self.db.cursor.execute('DELETE FROM word_book')
        self.db.conn.commit()

        self.assertEqual(len(self.db.get_favorites()), 0)

        # Import
        success = self.db.import_learning_data(exported)
        self.assertTrue(success)

        self.assertEqual(len(self.db.get_favorites()), 1)

    def test_get_word_count(self):
        initial_count = self.db.get_word_count()
        self.db.cursor.execute('''
            INSERT INTO words (traditional, simplified, pinyin, definition)
            VALUES (?, ?, ?, ?)
        ''', ('测试', '测试', 'ce4 shi4', 'test'))
        self.db.conn.commit()
        self.assertEqual(self.db.get_word_count(), initial_count + 1)


class TestFormatPinyin(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(format_pinyin(''), '')

    def test_none(self):
        self.assertEqual(format_pinyin(None), '')

    def test_no_tone(self):
        self.assertEqual(format_pinyin('zhong guo'), 'zhong guo')

    def test_with_tone(self):
        self.assertEqual(format_pinyin('zhong1 guo2'), 'zhōng guó')


if __name__ == '__main__':
    unittest.main()
