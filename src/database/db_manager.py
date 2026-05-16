import sqlite3
import os
import sys

from src.utils.pinyin import convert_pinyin


def get_db_path():
    if getattr(sys, 'frozen', False):
        if sys.platform == 'darwin':
            app_support = os.path.expanduser('~/Library/Application Support')
            data_dir = os.path.join(app_support, 'ChineseDict')
        else:
            data_dir = os.path.join(os.path.dirname(sys.executable), 'data')
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'dictionary.db')


def format_pinyin(pinyin):
    if not pinyin:
        return ''
    if any(c.isdigit() for c in pinyin):
        return convert_pinyin(pinyin)
    return pinyin


class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or get_db_path()
        self.conn = None
        self.connect()

    def connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._ensure_tables()

    def _ensure_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                traditional TEXT NOT NULL,
                simplified TEXT NOT NULL,
                pinyin TEXT NOT NULL,
                definition TEXT NOT NULL,
                definition_cn TEXT
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (word_id) REFERENCES words(id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_simplified ON words(simplified)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_traditional ON words(traditional)')

        try:
            self.cursor.execute('SELECT definition_cn FROM words LIMIT 1')
        except sqlite3.OperationalError:
            self.cursor.execute('ALTER TABLE words ADD COLUMN definition_cn TEXT')

        self.conn.commit()

    def _format_result(self, row_dict):
        row_dict['pinyin'] = format_pinyin(row_dict.get('pinyin', ''))
        return row_dict

    def search_exact(self, word):
        self.cursor.execute(
            'SELECT * FROM words WHERE simplified = ? OR traditional = ? LIMIT 1',
            (word, word)
        )
        row = self.cursor.fetchone()
        if row:
            return self._format_result(dict(row))
        return None

    def search_fuzzy(self, word, limit=20):
        like_pattern = f'%{word}%'
        self.cursor.execute(
            '''SELECT * FROM words
               WHERE simplified LIKE ? OR traditional LIKE ? OR pinyin LIKE ?
               LIMIT ?''',
            (like_pattern, like_pattern, like_pattern, limit)
        )
        return [self._format_result(dict(row)) for row in self.cursor.fetchall()]

    def get_suggestions(self, prefix, limit=10):
        like_pattern = f'{prefix}%'
        self.cursor.execute(
            '''SELECT simplified, pinyin FROM words
               WHERE simplified LIKE ? OR pinyin LIKE ?
               LIMIT ?''',
            (like_pattern, like_pattern, limit)
        )
        return [(row[0], format_pinyin(row[1])) for row in self.cursor.fetchall()]

    def add_favorite(self, word_id):
        self.cursor.execute(
            'INSERT INTO favorites (word_id) VALUES (?)',
            (word_id,)
        )
        self.conn.commit()

    def remove_favorite(self, word_id):
        self.cursor.execute(
            'DELETE FROM favorites WHERE word_id = ?',
            (word_id,)
        )
        self.conn.commit()

    def is_favorite(self, word_id):
        self.cursor.execute(
            'SELECT COUNT(*) FROM favorites WHERE word_id = ?',
            (word_id,)
        )
        return self.cursor.fetchone()[0] > 0

    def get_favorites(self, limit=50):
        self.cursor.execute(
            '''SELECT w.* FROM words w
               INNER JOIN favorites f ON w.id = f.word_id
               ORDER BY f.created_at DESC
               LIMIT ?''',
            (limit,)
        )
        return [self._format_result(dict(row)) for row in self.cursor.fetchall()]

    def add_search_history(self, word):
        self.cursor.execute(
            'INSERT INTO search_history (word) VALUES (?)',
            (word,)
        )
        self.conn.commit()

    def get_search_history(self, limit=20):
        self.cursor.execute(
            'SELECT DISTINCT word FROM search_history ORDER BY searched_at DESC LIMIT ?',
            (limit,)
        )
        return [row[0] for row in self.cursor.fetchall()]

    def close(self):
        if self.conn:
            self.conn.close()

    def get_word_count(self):
        self.cursor.execute('SELECT COUNT(*) FROM words')
        return self.cursor.fetchone()[0]
