import sqlite3
import os
import sys
import re
import random
import json
import urllib.request
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from src.utils.pinyin import convert_pinyin, get_initials, pinyin_normalize, fuzzy_match_pinyin
from src.utils.radicals import get_radical_chars
from src.utils.helpers import get_version, get_remote_version_url
from src.utils.decorators import safe_operation, safe_void_operation, retry_on_error


def get_db_path() -> str:
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


def format_pinyin(pinyin: Optional[str]) -> str:
    if not pinyin:
        return ''
    if any(c.isdigit() for c in pinyin):
        return convert_pinyin(pinyin)
    return pinyin


def _build_fuzzy_pinyin_like(query: str) -> str:
    """Build a LIKE pattern for full pinyin fuzzy match.
    e.g. 'yixin' -> 'y%x%i%x%n%'
    This allows matching 'yi1 xin1' style pinyin fields.
    """
    if not query:
        return '%'
    chars = [c for c in query.lower() if c.isalpha()]
    if not chars:
        return f'%{query}%'
    return '%' + '%'.join(chars) + '%'


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_db_path()
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._fts5_available = False
        self.connect()

    def connect(self) -> None:
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                traditional TEXT NOT NULL,
                simplified TEXT NOT NULL,
                pinyin TEXT NOT NULL,
                definition TEXT NOT NULL,
                definition_cn TEXT,
                examples TEXT,
                frequency TEXT,
                hsk_level INTEGER,
                discrimination TEXT
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

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_word (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                date TEXT NOT NULL UNIQUE,
                FOREIGN KEY (word_id) REFERENCES words(id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS word_book (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL UNIQUE,
                review_count INTEGER DEFAULT 0,
                last_reviewed TIMESTAMP,
                next_review TIMESTAMP,
                ease_factor REAL DEFAULT 2.5,
                interval_days INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (word_id) REFERENCES words(id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                total_words_learned INTEGER DEFAULT 0,
                total_reviews INTEGER DEFAULT 0,
                streak_days INTEGER DEFAULT 0,
                last_study_date TEXT,
                quiz_correct INTEGER DEFAULT 0,
                quiz_total INTEGER DEFAULT 0
            )
        ''')
        self.cursor.execute('''
            INSERT OR IGNORE INTO stats (id) VALUES (1)
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_simplified ON words(simplified)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_traditional ON words(traditional)')

        # Add missing columns with migrations
        self._migrate_columns()

        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_pinyin_initials ON words(pinyin_initials)')

        # Performance optimizations
        self._optimize_sqlite()

        self._ensure_fts5()
        self.conn.commit()

    def _migrate_columns(self) -> None:
        """Add columns that may be missing from older databases."""
        migrations = [
            ('definition_cn', 'TEXT'),
            ('pinyin_initials', 'TEXT'),
            ('examples', 'TEXT'),
            ('frequency', 'TEXT'),
            ('hsk_level', 'INTEGER'),
            ('discrimination', 'TEXT'),
        ]
        for col_name, col_type in migrations:
            try:
                self.cursor.execute(f'SELECT {col_name} FROM words LIMIT 1')
            except sqlite3.OperationalError:
                self.cursor.execute(f'ALTER TABLE words ADD COLUMN {col_name} {col_type}')

    def _optimize_sqlite(self) -> None:
        """Apply SQLite performance optimizations."""
        # Commit any pending transaction before changing PRAGMAs
        self.conn.commit()
        self.cursor.execute('PRAGMA journal_mode = WAL')
        self.cursor.execute('PRAGMA synchronous = NORMAL')
        self.cursor.execute('PRAGMA cache_size = -64000')  # 64MB cache
        self.cursor.execute('PRAGMA temp_store = MEMORY')
        self.cursor.execute('PRAGMA mmap_size = 268435456')  # 256MB memory map

    def _ensure_fts5(self) -> None:
        """Create FTS5 virtual table and triggers if FTS5 is available."""
        self._fts5_available = False
        try:
            self.cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS words_fts USING fts5(simplified, traditional, pinyin, definition, definition_cn, content=words, content_rowid=id)")
            self._fts5_available = True
        except sqlite3.OperationalError:
            self._fts5_available = False
            return

        if self._fts5_available:
            self.cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS words_fts_insert AFTER INSERT ON words BEGIN
                    INSERT INTO words_fts(rowid, simplified, traditional, pinyin, definition, definition_cn)
                    VALUES (new.id, new.simplified, new.traditional, new.pinyin, new.definition, new.definition_cn);
                END
            ''')
            self.cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS words_fts_delete AFTER DELETE ON words BEGIN
                    INSERT INTO words_fts(words_fts, rowid, simplified, traditional, pinyin, definition, definition_cn)
                    VALUES ('delete', old.id, old.simplified, old.traditional, old.pinyin, old.definition, old.definition_cn);
                END
            ''')
            self.cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS words_fts_update AFTER UPDATE ON words BEGIN
                    INSERT INTO words_fts(words_fts, rowid, simplified, traditional, pinyin, definition, definition_cn)
                    VALUES ('delete', old.id, old.simplified, old.traditional, old.pinyin, old.definition, old.definition_cn);
                    INSERT INTO words_fts(rowid, simplified, traditional, pinyin, definition, definition_cn)
                    VALUES (new.id, new.simplified, new.traditional, new.pinyin, new.definition, new.definition_cn);
                END
            ''')

    def rebuild_fts5(self) -> None:
        """Rebuild the FTS5 index. Call this after bulk data import."""
        if not self._fts5_available:
            return
        try:
            self.cursor.execute("INSERT INTO words_fts(words_fts) VALUES ('rebuild')")
            self.conn.commit()
        except Exception as e:
            print(f"FTS5 rebuild failed: {e}")

    def _format_result(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        row_dict['pinyin'] = format_pinyin(row_dict.get('pinyin', ''))
        return row_dict

    def search_exact(self, word: str) -> Optional[Dict[str, Any]]:
        self.cursor.execute(
            'SELECT * FROM words WHERE simplified = ? OR traditional = ? LIMIT 1',
            (word, word)
        )
        row = self.cursor.fetchone()
        if row:
            return self._format_result(dict(row))
        return None

    def search_fts(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search using FTS5 full-text search. Falls back to regular fuzzy search if FTS5 is unavailable."""
        if not query:
            return []
        if not getattr(self, '_fts5_available', False):
            return self.search_fuzzy(query, limit=limit)

        try:
            self.cursor.execute(
                '''SELECT w.* FROM words_fts fts
                   JOIN words w ON w.id = fts.rowid
                   WHERE words_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?''',
                (query, limit)
            )
            rows = self.cursor.fetchall()
            results = [self._format_result(dict(row)) for row in rows]
            if results:
                return results
        except Exception:
            pass
        return self.search_fuzzy(query, limit=limit)

    def search_fuzzy(self, word: str, limit: int = 20) -> List[Dict[str, Any]]:
        if not word:
            return []

        like_pattern = f'%{word}%'
        norm_word = pinyin_normalize(word)
        norm_like = f'%{norm_word}%'
        initials = get_initials(word)
        norm_initials = get_initials(norm_word)

        if initials and len(initials) >= 2:
            self.cursor.execute(
                '''SELECT * FROM words
                   WHERE simplified LIKE ? OR traditional LIKE ?
                      OR pinyin LIKE ? OR pinyin LIKE ?
                      OR pinyin_initials LIKE ? OR pinyin_initials LIKE ?
                   LIMIT ?''',
                (like_pattern, like_pattern, like_pattern, norm_like,
                 f'{initials}%', f'{norm_initials}%', limit * 3)
            )
        else:
            self.cursor.execute(
                '''SELECT * FROM words
                   WHERE simplified LIKE ? OR traditional LIKE ?
                      OR pinyin LIKE ? OR pinyin LIKE ?
                   LIMIT ?''',
                (like_pattern, like_pattern, like_pattern, norm_like, limit * 3)
            )

        rows = self.cursor.fetchall()

        results: List[Dict[str, Any]] = []
        seen: set = set()
        for row in rows:
            rd = dict(row)
            wid = rd.get('id')
            if wid in seen:
                continue
            seen.add(wid)
            rd['pinyin'] = format_pinyin(rd.get('pinyin', ''))
            results.append(rd)

        word_lower = word.lower()
        norm_lower = norm_word.lower()

        def rank_score(r: Dict[str, Any]) -> Tuple[int, int]:
            simp = r.get('simplified', '') or ''
            trad = r.get('traditional', '') or ''
            py_raw = r.get('pinyin', '') or ''
            pi = r.get('pinyin_initials', '') or ''

            if simp == word or trad == word:
                return (0, 0)
            if simp.startswith(word) or trad.startswith(word):
                return (1, 0)
            if word in simp or word in trad:
                return (2, 0)

            py_stripped = re.sub(r'[^a-z]', '', py_raw.lower())
            q_stripped = re.sub(r'[^a-z]', '', word_lower)
            norm_q_stripped = re.sub(r'[^a-z]', '', norm_lower)
            if q_stripped and py_stripped == q_stripped:
                return (3, 0)
            if norm_q_stripped and py_stripped == norm_q_stripped:
                return (3, 0)
            if q_stripped and py_stripped.startswith(q_stripped):
                return (4, 0)
            if norm_q_stripped and py_stripped.startswith(norm_q_stripped):
                return (4, 0)
            if q_stripped and q_stripped in py_stripped:
                return (5, 0)
            if norm_q_stripped and norm_q_stripped in py_stripped:
                return (5, 0)
            if fuzzy_match_pinyin(word, py_raw):
                return (6, 0)
            if fuzzy_match_pinyin(norm_word, py_raw):
                return (6, 0)
            if initials and pi.startswith(initials):
                return (7, 0)
            if norm_initials and pi.startswith(norm_initials):
                return (7, 0)
            return (8, 0)

        results.sort(key=rank_score)
        return results[:limit]

    def get_suggestions(self, prefix: str, limit: int = 10) -> List[Tuple[str, str]]:
        if not prefix:
            return []

        like_pattern = f'{prefix}%'
        norm_prefix = pinyin_normalize(prefix)
        norm_like = f'{norm_prefix}%'
        initials = get_initials(prefix)
        norm_initials = get_initials(norm_prefix)

        if initials and len(initials) >= 2:
            self.cursor.execute(
                '''SELECT DISTINCT simplified, pinyin FROM words
                   WHERE simplified LIKE ? OR pinyin LIKE ? OR pinyin LIKE ?
                      OR pinyin_initials LIKE ? OR pinyin_initials LIKE ?
                   LIMIT ?''',
                (like_pattern, like_pattern, norm_like,
                 f'{initials}%', f'{norm_initials}%', limit)
            )
        else:
            self.cursor.execute(
                '''SELECT DISTINCT simplified, pinyin FROM words
                   WHERE simplified LIKE ? OR pinyin LIKE ? OR pinyin LIKE ?
                   LIMIT ?''',
                (like_pattern, like_pattern, norm_like, limit)
            )

        return [(row[0], format_pinyin(row[1])) for row in self.cursor.fetchall()]

    def search_by_radical(self, radical: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search words by radical using a hardcoded mapping."""
        chars = get_radical_chars(radical)
        if not chars:
            return []

        placeholders = ','.join('?' * len(chars))
        self.cursor.execute(
            f'SELECT * FROM words WHERE simplified IN ({placeholders}) LIMIT ?',
            tuple(chars) + (limit,)
        )
        return [self._format_result(dict(row)) for row in self.cursor.fetchall()]

    def add_favorite(self, word_id: int) -> None:
        self.cursor.execute(
            'INSERT INTO favorites (word_id) VALUES (?)',
            (word_id,)
        )
        self.conn.commit()

    def remove_favorite(self, word_id: int) -> None:
        self.cursor.execute(
            'DELETE FROM favorites WHERE word_id = ?',
            (word_id,)
        )
        self.conn.commit()

    def is_favorite(self, word_id: int) -> bool:
        self.cursor.execute(
            'SELECT COUNT(*) FROM favorites WHERE word_id = ?',
            (word_id,)
        )
        return self.cursor.fetchone()[0] > 0

    def get_favorites(self, limit: int = 50) -> List[Dict[str, Any]]:
        self.cursor.execute(
            '''SELECT w.* FROM words w
               INNER JOIN favorites f ON w.id = f.word_id
               ORDER BY f.created_at DESC
               LIMIT ?''',
            (limit,)
        )
        return [self._format_result(dict(row)) for row in self.cursor.fetchall()]

    def add_search_history(self, word: str) -> None:
        self.cursor.execute(
            'INSERT INTO search_history (word) VALUES (?)',
            (word,)
        )
        self.conn.commit()

    def get_search_history(self, limit: int = 20) -> List[str]:
        """Get search history with time-decay weighting.
        More recent searches and frequently searched words are prioritized.
        """
        self.cursor.execute(
            '''SELECT word,
                       COUNT(*) as freq,
                       MAX(searched_at) as last_searched,
                       JULIANDAY('now') - JULIANDAY(MAX(searched_at)) as days_ago
               FROM search_history
               GROUP BY word
               ORDER BY (freq * 1.0 / (1 + days_ago * 0.1)) DESC, last_searched DESC
               LIMIT ?''',
            (limit,)
        )
        return [row[0] for row in self.cursor.fetchall()]

    def close(self) -> None:
        if self.conn:
            self.conn.close()

    def get_word_count(self) -> int:
        self.cursor.execute('SELECT COUNT(*) FROM words')
        return self.cursor.fetchone()[0]

    def get_daily_word(self) -> Optional[Dict[str, Any]]:
        today = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute(
            'SELECT word_id FROM daily_word WHERE date = ?',
            (today,)
        )
        row = self.cursor.fetchone()
        if row:
            word_id = row[0]
        else:
            count = self.get_word_count()
            if count == 0:
                return None
            seed = int(today.replace('-', ''))
            random.seed(seed)
            offset = random.randint(0, count - 1)
            self.cursor.execute(
                'SELECT id FROM words LIMIT 1 OFFSET ?',
                (offset,)
            )
            word_id = self.cursor.fetchone()[0]
            self.cursor.execute(
                'INSERT INTO daily_word (word_id, date) VALUES (?, ?)',
                (word_id, today)
            )
            self.conn.commit()
        self.cursor.execute('SELECT * FROM words WHERE id = ?', (word_id,))
        row = self.cursor.fetchone()
        if row:
            return self._format_result(dict(row))
        return None

    def add_to_word_book(self, word_id: int) -> None:
        self.cursor.execute(
            '''INSERT OR IGNORE INTO word_book (word_id, next_review)
               VALUES (?, datetime('now'))''',
            (word_id,)
        )
        self.conn.commit()

    def remove_from_word_book(self, word_id: int) -> None:
        self.cursor.execute(
            'DELETE FROM word_book WHERE word_id = ?',
            (word_id,)
        )
        self.conn.commit()

    def is_in_word_book(self, word_id: int) -> bool:
        self.cursor.execute(
            'SELECT COUNT(*) FROM word_book WHERE word_id = ?',
            (word_id,)
        )
        return self.cursor.fetchone()[0] > 0

    def get_due_reviews(self, limit: int = 20) -> List[Dict[str, Any]]:
        self.cursor.execute(
            '''SELECT w.* FROM words w
               INNER JOIN word_book wb ON w.id = wb.word_id
               WHERE wb.next_review IS NULL OR wb.next_review <= datetime('now')
               ORDER BY wb.next_review ASC
               LIMIT ?''',
            (limit,)
        )
        return [self._format_result(dict(row)) for row in self.cursor.fetchall()]

    def review_word(self, word_id: int, quality: int) -> None:
        """Review a word using an enhanced SM-2 algorithm.

        Args:
            word_id: The word ID
            quality: 0-5 rating where:
                0-2 = Incorrect response (reset or reduce interval)
                3 = Correct but difficult
                4 = Correct with hesitation
                5 = Perfect response
        """
        self.cursor.execute(
            'SELECT * FROM word_book WHERE word_id = ?',
            (word_id,)
        )
        row = self.cursor.fetchone()
        if not row:
            return
        data = dict(row)
        ease = data.get('ease_factor', 2.5) or 2.5
        interval = data.get('interval_days', 0) or 0
        reps = data.get('review_count', 0) or 0

        # Enhanced SM-2 algorithm
        if quality < 3:
            # Failed: reset interval but keep some progress
            if reps > 2:
                interval = max(1, interval // 2)
            else:
                interval = 1
            reps = max(0, reps - 1)
        else:
            if reps == 0:
                interval = 1
            elif reps == 1:
                interval = 6
            else:
                interval = int(round(interval * ease))

        # Adjust ease factor based on quality
        ease = ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if ease < 1.3:
            ease = 1.3

        reps += 1
        next_review = datetime.now() + timedelta(days=interval)

        self.cursor.execute(
            '''UPDATE word_book
               SET review_count = ?, last_reviewed = datetime('now'),
                   next_review = ?, ease_factor = ?, interval_days = ?
               WHERE word_id = ?''',
            (reps, next_review.strftime('%Y-%m-%d %H:%M:%S'), ease, interval, word_id)
        )
        self.conn.commit()

        self.cursor.execute(
            '''UPDATE stats SET total_reviews = total_reviews + 1 WHERE id = 1'''
        )
        self.conn.commit()

    def get_word_book_words(self, limit: int = 50) -> List[Dict[str, Any]]:
        self.cursor.execute(
            '''SELECT w.* FROM words w
               INNER JOIN word_book wb ON w.id = wb.word_id
               ORDER BY wb.added_at DESC
               LIMIT ?''',
            (limit,)
        )
        return [self._format_result(dict(row)) for row in self.cursor.fetchall()]

    def get_stats(self) -> Dict[str, int]:
        self.cursor.execute('SELECT * FROM stats WHERE id = 1')
        row = self.cursor.fetchone()
        if not row:
            return {
                'total_words_learned': 0,
                'total_reviews': 0,
                'streak_days': 0,
                'quiz_correct': 0,
                'quiz_total': 0,
            }
        data = dict(row)
        today = datetime.now().strftime('%Y-%m-%d')
        last = data.get('last_study_date')
        streak = data.get('streak_days', 0) or 0
        if last and last != today:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            if last != yesterday:
                streak = 0
        return {
            'total_words_learned': data.get('total_words_learned', 0) or 0,
            'total_reviews': data.get('total_reviews', 0) or 0,
            'streak_days': streak,
            'quiz_correct': data.get('quiz_correct', 0) or 0,
            'quiz_total': data.get('quiz_total', 0) or 0,
        }

    def update_study_streak(self) -> None:
        today = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute('SELECT last_study_date FROM stats WHERE id = 1')
        row = self.cursor.fetchone()
        last = row[0] if row else None
        if last == today:
            return
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        if last == yesterday:
            self.cursor.execute(
                '''UPDATE stats SET streak_days = streak_days + 1, last_study_date = ?
                   WHERE id = 1''',
                (today,)
            )
        else:
            self.cursor.execute(
                '''UPDATE stats SET streak_days = 1, last_study_date = ?
                   WHERE id = 1''',
                (today,)
            )
        self.conn.commit()

    def record_quiz_result(self, correct: int, total: int) -> None:
        self.cursor.execute(
            '''UPDATE stats SET quiz_correct = quiz_correct + ?,
                                quiz_total = quiz_total + ?
               WHERE id = 1''',
            (correct, total)
        )
        self.conn.commit()

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        try:
            self.cursor.execute(
                'SELECT value FROM settings WHERE key = ?',
                (key,)
            )
            row = self.cursor.fetchone()
            return row[0] if row else default
        except Exception:
            return default

    def set_setting(self, key: str, value: str) -> None:
        try:
            self.cursor.execute(
                '''INSERT INTO settings (key, value) VALUES (?, ?)
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value''',
                (key, value)
            )
            self.conn.commit()
        except Exception:
            pass

    def update_check(self) -> Dict[str, Any]:
        """Check if a newer version of the database is available remotely.
        Returns a dict with keys: has_update (bool), remote_version (str), local_version (str), info (str).
        For now this is a framework; network call is best-effort and non-blocking.
        """
        local_version = get_version()
        result: Dict[str, Any] = {
            'has_update': False,
            'remote_version': local_version,
            'local_version': local_version,
            'info': ''
        }
        try:
            url = get_remote_version_url()
            req = urllib.request.Request(url, headers={'User-Agent': 'ChineseDict/' + local_version})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                tag_name = data.get('tag_name', '')
                if tag_name.startswith('v'):
                    tag_name = tag_name[1:]
                result['remote_version'] = tag_name
                if tag_name and tag_name != local_version:
                    result['has_update'] = True
                    result['info'] = data.get('body', '')
        except Exception as e:
            result['info'] = str(e)
        return result

    def export_learning_data(self) -> Dict[str, Any]:
        """Export all learning data for backup/transfer."""
        tables = ['favorites', 'search_history', 'word_book', 'stats', 'settings', 'daily_word']
        data: Dict[str, Any] = {}
        for table in tables:
            try:
                self.cursor.execute(f'SELECT * FROM {table}')
                rows = self.cursor.fetchall()
                columns = [description[0] for description in self.cursor.description]
                data[table] = [dict(zip(columns, row)) for row in rows]
            except Exception:
                data[table] = []
        return {
            'version': get_version(),
            'exported_at': datetime.now().isoformat(),
            'tables': data,
        }

    def import_learning_data(self, data: Dict[str, Any]) -> bool:
        """Import learning data from a backup."""
        try:
            tables = data.get('tables', {})
            for table, rows in tables.items():
                if not rows:
                    continue
                # Clear existing data and import
                self.cursor.execute(f'DELETE FROM {table}')
                columns = list(rows[0].keys())
                placeholders = ','.join('?' * len(columns))
                col_names = ','.join(columns)
                insert_sql = f'INSERT INTO {table} ({col_names}) VALUES ({placeholders})'
                for row in rows:
                    values = [row.get(col) for col in columns]
                    self.cursor.execute(insert_sql, values)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Import failed: {e}")
            self.conn.rollback()
            return False
