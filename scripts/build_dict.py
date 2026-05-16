import sqlite3
import os
import logging
import urllib.request
import gzip
import re
import sys
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CEDICT_URLS = [
    "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz",
]

XINHUA_IDIOM_URLS = [
    "https://cdn.jsdelivr.net/gh/pwxcoo/chinese-xinhua@master/data/idiom.json",
    "https://raw.githubusercontent.com/pwxcoo/chinese-xinhua/master/data/idiom.json",
]
XINHUA_CI_URLS = [
    "https://cdn.jsdelivr.net/gh/pwxcoo/chinese-xinhua@master/data/ci.json",
    "https://raw.githubusercontent.com/pwxcoo/chinese-xinhua/master/data/ci.json",
]


def download_cedict():
    for url in CEDICT_URLS:
        try:
            logger.info(f"Trying to download from: {url}")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=120) as response:
                data = response.read()

            if url.endswith('.gz'):
                data = gzip.decompress(data)

            content = data.decode('utf-8')
            logger.info(f"Successfully downloaded {len(content)} characters")
            return content
        except Exception as e:
            logger.warning(f"Failed to download from {url}: {e}")
            continue

    return None


def download_json(urls):
    if isinstance(urls, str):
        urls = [urls]
    for url in urls:
        try:
            logger.info(f"Downloading JSON from: {url}")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=180) as response:
                data = response.read()
            content = data.decode('utf-8')
            result = json.loads(content)
            logger.info(f"Successfully downloaded {len(result)} entries")
            return result
        except Exception as e:
            logger.warning(f"Failed to download JSON from {url}: {e}")
            continue
    return None


def load_local_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} entries from local file: {filepath}")
            return data
        except Exception as e:
            logger.warning(f"Failed to load local JSON {filepath}: {e}")
    return None


def parse_cedict_line(line):
    match = re.match(r'^(\S+) (\S+) \[(.*?)\] /(.+)/$', line)
    if match:
        traditional = match.group(1)
        simplified = match.group(2)
        pinyin = match.group(3)
        definition = match.group(4).replace('/', '; ')
        return (traditional, simplified, pinyin, definition)
    return None


def parse_cedict(content):
    words = []
    for line in content.strip().split('\n'):
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        parsed = parse_cedict_line(line)
        if parsed:
            words.append(parsed)
    return words


def build_dictionary(db_path, cedict_words, idiom_50k=None, xinhua_idioms=None, xinhua_ci=None, extra_idioms=None, extra_words=None):
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            traditional TEXT NOT NULL,
            simplified TEXT NOT NULL,
            pinyin TEXT NOT NULL,
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

    idiom_map = {}

    if idiom_50k:
        for item in idiom_50k:
            word = item.get('word', '')
            if word:
                idiom_map[word] = {
                    'pinyin': item.get('pinyin', ''),
                    'explanation': item.get('explanation', ''),
                }
        logger.info(f"Built idiom map from idiom_50k with {len(idiom_map)} entries")

    if xinhua_idioms:
        added = 0
        for item in xinhua_idioms:
            word = item.get('word', '')
            if word and word not in idiom_map:
                idiom_map[word] = {
                    'pinyin': item.get('pinyin', ''),
                    'explanation': item.get('explanation', ''),
                }
                added += 1
        logger.info(f"Added {added} idioms from xinhua (not in idiom_50k), total: {len(idiom_map)}")

    if extra_idioms:
        added = 0
        for item in extra_idioms:
            word = item.get('word', '')
            if word and word not in idiom_map:
                idiom_map[word] = {
                    'pinyin': item.get('pinyin', ''),
                    'explanation': item.get('explanation', ''),
                }
                added += 1
        logger.info(f"Added {added} extra idioms, total idiom map: {len(idiom_map)} entries")

    ci_map = {}
    if xinhua_ci:
        for item in xinhua_ci:
            word = item.get('ci', '')
            if word:
                ci_map[word] = item.get('explanation', '')
        logger.info(f"Built ci map with {len(ci_map)} entries")

    cedict_simplified = set()
    for traditional, simplified, pinyin, definition in cedict_words:
        cedict_simplified.add(simplified)
        definition_cn = ''
        if simplified in idiom_map:
            definition_cn = idiom_map[simplified].get('explanation', '')
        elif simplified in ci_map:
            definition_cn = ci_map.get(simplified, '')
        cursor.execute(
            'INSERT INTO words (traditional, simplified, pinyin, definition, definition_cn) VALUES (?, ?, ?, ?, ?)',
            (traditional, simplified, pinyin, definition, definition_cn)
        )

    xinhua_idiom_only = 0
    for word, data in idiom_map.items():
        if word not in cedict_simplified:
            xinhua_idiom_only += 1
            cursor.execute(
                'INSERT INTO words (traditional, simplified, pinyin, definition, definition_cn) VALUES (?, ?, ?, ?, ?)',
                (word, word, data.get('pinyin', ''), '', data.get('explanation', ''))
            )
    logger.info(f"Added {xinhua_idiom_only} idioms from xinhua+extra not in CC-CEDICT")

    xinhua_ci_only = 0
    for word, explanation in ci_map.items():
        if word not in cedict_simplified and word not in idiom_map:
            xinhua_ci_only += 1
            cursor.execute(
                'INSERT INTO words (traditional, simplified, pinyin, definition, definition_cn) VALUES (?, ?, ?, ?, ?)',
                (word, word, '', '', explanation)
            )
    logger.info(f"Added {xinhua_ci_only} words from chinese-xinhua ci not in CC-CEDICT")

    extra_words_count = 0
    if extra_words:
        for item in extra_words:
            word = item.get('word', '')
            pinyin = item.get('pinyin', '')
            explanation = item.get('explanation', '')
            if word:
                cursor.execute(
                    'SELECT id FROM words WHERE simplified = ?',
                    (word,)
                )
                existing = cursor.fetchone()
                if existing:
                    cursor.execute(
                        'UPDATE words SET definition_cn = ? WHERE simplified = ?',
                        (explanation, word)
                    )
                else:
                    extra_words_count += 1
                    cursor.execute(
                        'INSERT INTO words (traditional, simplified, pinyin, definition, definition_cn) VALUES (?, ?, ?, ?, ?)',
                        (word, word, pinyin, '', explanation)
                    )
        logger.info(f"Added/updated {len(extra_words)} extra words ({extra_words_count} new)")

    conn.commit()

    _resolve_cross_references(conn, cursor)

    cursor.execute('SELECT COUNT(*) FROM words')
    count = cursor.fetchone()[0]
    logger.info(f"Successfully created dictionary with {count} entries.")

    cursor.execute('SELECT COUNT(*) FROM words WHERE definition_cn IS NOT NULL AND definition_cn != ""')
    cn_count = cursor.fetchone()[0]
    logger.info(f"Entries with Chinese definitions: {cn_count}")

    conn.close()
    return db_path


def _resolve_cross_references(conn, cursor):
    cross_ref_patterns = [
        re.compile(r'^[\d]+[.、]\s*见[\u201c\u300c\u300e"\u00ab\u300a\u3014](.+?)[\u201d\u300d\u300f"\u00bb\u300b\u3015]'),
        re.compile(r'^见[\u201c\u300c\u300e"\u00ab\u300a\u3014](.+?)[\u201d\u300d\u300f"\u00bb\u300b\u3015]'),
        re.compile(r'^同[\u201c\u300c\u300e\u2018"\u00ab\u300a\u3014](.+?)[\u201d\u300d\u300f\u2019"\u00bb\u300b\u3015]'),
    ]

    cursor.execute('SELECT id, simplified, definition_cn FROM words WHERE definition_cn LIKE "见%" OR definition_cn LIKE "同%" OR definition_cn LIKE "%见%" OR definition_cn LIKE "%同%"')
    rows = cursor.fetchall()

    resolved = 0
    circular = 0
    for row_id, simplified, definition_cn in rows:
        if not definition_cn:
            continue

        ref_word = None
        for pattern in cross_ref_patterns:
            m = pattern.match(definition_cn)
            if m:
                ref_word = m.group(1).strip()
                break

        if not ref_word:
            continue

        if ref_word == simplified:
            cursor.execute('UPDATE words SET definition_cn = "" WHERE id = ?', (row_id,))
            circular += 1
            continue

        cursor.execute('SELECT definition_cn FROM words WHERE simplified = ? AND definition_cn IS NOT NULL AND definition_cn != "" LIMIT 1', (ref_word,))
        ref_row = cursor.fetchone()
        if ref_row and ref_row[0] and not ref_row[0].startswith('见') and not ref_row[0].startswith('同') and not re.match(r'^[\d]+[.、]\s*见', ref_row[0]):
            cursor.execute('UPDATE words SET definition_cn = ? WHERE id = ?', (ref_row[0], row_id))
            resolved += 1

    conn.commit()
    logger.info(f"Cross-reference resolution: {resolved} resolved, {circular} circular cleared")


def main():
    content = download_cedict()
    if not content:
        logger.error("Failed to download CC-CEDICT from all sources")
        sys.exit(1)

    cedict_words = parse_cedict(content)
    logger.info(f"Parsed {len(cedict_words)} words from CC-CEDICT")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")

    local_idiom_path = os.path.join(data_dir, "idiom.json")
    local_ci_path = os.path.join(data_dir, "ci.json")
    extra_idiom_path = os.path.join(data_dir, "extra_idioms.json")
    idiom_50k_path = os.path.join(data_dir, "idiom_50k.json")

    idiom_50k = load_local_json(idiom_50k_path)
    if idiom_50k:
        logger.info(f"Loaded idiom_50k with {len(idiom_50k)} entries")

    xinhua_idioms = load_local_json(local_idiom_path)
    if not xinhua_idioms:
        xinhua_idioms = download_json(XINHUA_IDIOM_URLS)

    xinhua_ci = load_local_json(local_ci_path)
    if not xinhua_ci:
        xinhua_ci = download_json(XINHUA_CI_URLS)

    extra_idioms = load_local_json(extra_idiom_path)

    extra_word_path = os.path.join(data_dir, "extra_words.json")
    extra_words = load_local_json(extra_word_path)

    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "dictionary.db")

    build_dictionary(db_path, cedict_words, idiom_50k, xinhua_idioms, xinhua_ci, extra_idioms, extra_words)


if __name__ == "__main__":
    main()
