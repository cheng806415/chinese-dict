TONE_MAP = {
    'a': ['ā', 'á', 'ǎ', 'à', 'a'],
    'e': ['ē', 'é', 'ě', 'è', 'e'],
    'i': ['ī', 'í', 'ǐ', 'ì', 'i'],
    'o': ['ō', 'ó', 'ǒ', 'ò', 'o'],
    'u': ['ū', 'ú', 'ǔ', 'ù', 'u'],
    'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ', 'ü'],
    'v': ['ǖ', 'ǘ', 'ǚ', 'ǜ', 'ü'],
}

def convert_syllable(syllable):
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

def convert_pinyin(pinyin_str):
    if not pinyin_str:
        return ''
    syllables = pinyin_str.strip().split()
    result = []
    for s in syllables:
        result.append(convert_syllable(s))
    return ' '.join(result)


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
