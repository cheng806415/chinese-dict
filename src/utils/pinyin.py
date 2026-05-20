import re
from typing import List, Optional

TONE_MAP = {
    'a': ['ā', 'á', 'ǎ', 'à', 'a'],
    'e': ['ē', 'é', 'ě', 'è', 'e'],
    'i': ['ī', 'í', 'ǐ', 'ì', 'i'],
    'o': ['ō', 'ó', 'ǒ', 'ò', 'o'],
    'u': ['ū', 'ú', 'ǔ', 'ù', 'u'],
    'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ', 'ü'],
    'v': ['ǖ', 'ǘ', 'ǚ', 'ǜ', 'ü'],
}

PINYIN_NORMALIZE_MAP = {
    'lv': 'lv',
    'nv': 'nv',
}


def convert_syllable(syllable: str) -> str:
    tone_num = 5
    for ch in syllable:
        if ch.isdigit():
            tone_num = int(ch)
            syllable = syllable.replace(ch, '')
            break

    if tone_num == 5 or tone_num == 0:
        return syllable

    tone_index = tone_num - 1

    if 'ü' in syllable or 'v' in syllable:
        syllable = syllable.replace('v', 'ü')
        if 'ü' in syllable:
            return syllable.replace('ü', TONE_MAP['ü'][tone_index])

    vowels = 'aeiou'
    for i, ch in enumerate(syllable):
        if ch in vowels:
            if i + 1 < len(syllable) and syllable[i + 1] in vowels:
                if ch in 'ae' and syllable[i + 1] in 'iou':
                    return syllable[:i] + TONE_MAP[ch][tone_index] + syllable[i + 1:]
                else:
                    return syllable[:i + 1] + TONE_MAP[syllable[i + 1]][tone_index] + syllable[i + 2:]
            else:
                return syllable[:i] + TONE_MAP[ch][tone_index] + syllable[i + 1:]

    return syllable


def convert_pinyin(pinyin_str: Optional[str]) -> str:
    if not pinyin_str:
        return ''
    syllables = pinyin_str.strip().split()
    result: List[str] = []
    for s in syllables:
        result.append(convert_syllable(s))
    return ' '.join(result)


def get_initials(pinyin_str: Optional[str]) -> str:
    """Extract first letter of each pinyin syllable.
    e.g. 'yi1 xin1 yi1 yi4' -> 'yxyy'
    e.g. 'yi1 ma3 dang1 xian1' -> 'ymdx'
    """
    if not pinyin_str:
        return ''
    syllables = pinyin_str.strip().split()
    initials: List[str] = []
    for s in syllables:
        s = s.lower()
        for ch in s:
            if ch.isalpha():
                initials.append(ch)
                break
    return ''.join(initials)


def pinyin_normalize(pinyin_str: Optional[str]) -> str:
    """Normalize pinyin input for fault-tolerant search.
    Maps common alternative spellings:
      - nv <-> lv (both map to nv for matching)
      - Also handles tone numbers.
    Returns normalized lowercase string.
    """
    if not pinyin_str:
        return ''
    s = pinyin_str.lower().strip()

    def replace_lv(match: re.Match) -> str:
        return 'nv' + match.group(1)
    s = re.sub(r'lv(\d?)', replace_lv, s)
    return s


def fuzzy_match_pinyin(query: Optional[str], pinyin_field: Optional[str]) -> bool:
    """Check if query fuzzy-matches a pinyin field.
    Supports:
      - Full pinyin without tones (e.g. 'yixin' matches 'yi1 xin1')
      - Full pinyin with tones (e.g. 'yi1xin1' matches 'yi1 xin1')
    Returns True if match, False otherwise.
    """
    if not query or not pinyin_field:
        return False
    query = query.lower().strip()
    pinyin_field = pinyin_field.lower().strip()

    def strip_pinyin(p: str) -> str:
        return ''.join(ch for ch in p if ch.isalpha())
    query_stripped = strip_pinyin(query)
    field_stripped = strip_pinyin(pinyin_field)
    if not query_stripped:
        return False

    if query_stripped in field_stripped:
        return True

    query_syllables = query.split()
    field_syllables = pinyin_field.split()
    if len(query_syllables) <= len(field_syllables):
        for qs, fs in zip(query_syllables, field_syllables):
            qs = strip_pinyin(qs)
            fs = strip_pinyin(fs)
            if not fs.startswith(qs):
                return False
        return True
    return False


if __name__ == '__main__':
    tests = [
        ('yi1 xin1 yi1 yi4', 'yī xīn yī yì'),
        ('yi1 ma3 dang1 xian1', 'yī mǎ dāng xiān'),
        ('zhong1 guo2', 'zhōng guó'),
        ('nv3 hai2', 'nǚ hái'),
        ('lu:e4', 'lǜe'),
        ('a1', 'ā'),
        ('e4', 'è'),
    ]
    for inp, expected in tests:
        result = convert_pinyin(inp)
        status = 'OK' if result == expected else f'FAIL (got {result})'
        print(f'{inp} -> {result}  {status}')

    norm_tests = [
        ('lv', 'nv'),
        ('lv3', 'nv3'),
        ('nvl', 'nvl'),
        ('LV', 'nv'),
    ]
    for inp, expected in norm_tests:
        result = pinyin_normalize(inp)
        status = 'OK' if result == expected else f'FAIL (got {result})'
        print(f'normalize({inp}) -> {result}  {status}')
