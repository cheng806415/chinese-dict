import os
import sys
import sqlite3
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BUNDLED_DB_VERSION = "cedict_xinhua_v4"


def get_project_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_data_dir():
    if getattr(sys, 'frozen', False):
        if sys.platform == 'darwin':
            app_support = os.path.expanduser('~/Library/Application Support')
            data_dir = os.path.join(app_support, 'ChineseDict')
        else:
            data_dir = os.path.join(os.path.dirname(sys.executable), 'data')
    else:
        data_dir = os.path.join(get_project_root(), 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_db_path():
    data_dir = get_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "dictionary.db")


def get_version_file():
    return os.path.join(get_data_dir(), ".db_version")


def get_bundled_db_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        db_path = os.path.join(base_path, "data", "dictionary.db")
        if os.path.exists(db_path):
            return db_path
        if sys.platform == 'darwin':
            exe_dir = os.path.dirname(sys.executable)
            alt_path = os.path.join(exe_dir, "data", "dictionary.db")
            if os.path.exists(alt_path):
                return alt_path
            resources_dir = os.path.join(os.path.dirname(exe_dir), "Resources")
            alt_path2 = os.path.join(resources_dir, "data", "dictionary.db")
            if os.path.exists(alt_path2):
                return alt_path2
        return db_path
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, "data", "dictionary.db")


def _has_chinese_definitions(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM words WHERE definition_cn IS NOT NULL AND definition_cn != ''")
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False


def init_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            traditional TEXT NOT NULL,
            simplified TEXT NOT NULL,
            pinyin TEXT NOT NULL,
            pinyin_initials TEXT,
            definition TEXT NOT NULL,
            definition_cn TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (word_id) REFERENCES words(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_simplified ON words(simplified)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_traditional ON words(traditional)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pinyin ON words(pinyin)')

    try:
        cursor.execute('SELECT definition_cn FROM words LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE words ADD COLUMN definition_cn TEXT')

    try:
        cursor.execute('SELECT pinyin_initials FROM words LIMIT 1')
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE words ADD COLUMN pinyin_initials TEXT')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pinyin_initials ON words(pinyin_initials)')

    conn.commit()
    return conn


def import_data():
    db_path = get_db_path()
    version_file = get_version_file()

    if os.path.exists(db_path) and os.path.exists(version_file):
        try:
            with open(version_file, 'r') as f:
                local_version = f.read().strip()
            if local_version == BUNDLED_DB_VERSION and _has_chinese_definitions(db_path):
                logger.info(f"Database up-to-date (v{local_version}). Skipping import.")
                return db_path
        except Exception:
            pass

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM words")
            count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM words WHERE definition_cn IS NOT NULL AND definition_cn != ''")
            cn_count = cursor.fetchone()[0]
            conn.close()
            if count >= 100000 and cn_count >= 20000:
                with open(version_file, 'w') as f:
                    f.write(BUNDLED_DB_VERSION)
                logger.info(f"Database already has {count} entries ({cn_count} with CN def). Skipping import.")
                return db_path
        except Exception as e:
            logger.warning(f"Error checking database: {e}")

    bundled_db = get_bundled_db_path()
    if os.path.exists(bundled_db):
        try:
            shutil.copy2(bundled_db, db_path)
            with open(version_file, 'w') as f:
                f.write(BUNDLED_DB_VERSION)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM words")
            count = cursor.fetchone()[0]
            logger.info(f"Copied bundled dictionary with {count} entries.")
            conn.close()
            return db_path
        except Exception as e:
            logger.error(f"Failed to copy bundled database: {e}")

    logger.warning("No bundled database found. Creating empty database.")
    conn = init_database(db_path)
    conn.close()
    return db_path


if __name__ == "__main__":
    import_data()
