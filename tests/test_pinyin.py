import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.pinyin import (
    convert_syllable,
    convert_pinyin,
    get_initials,
    pinyin_normalize,
    fuzzy_match_pinyin,
)


class TestConvertSyllable(unittest.TestCase):
    def test_tone_1(self):
        self.assertEqual(convert_syllable('a1'), 'ā')

    def test_tone_2(self):
        self.assertEqual(convert_syllable('a2'), 'á')

    def test_tone_3(self):
        self.assertEqual(convert_syllable('a3'), 'ǎ')

    def test_tone_4(self):
        self.assertEqual(convert_syllable('a4'), 'à')

    def test_tone_5(self):
        self.assertEqual(convert_syllable('a5'), 'a')

    def test_tone_0(self):
        self.assertEqual(convert_syllable('a0'), 'a')

    def test_no_tone(self):
        self.assertEqual(convert_syllable('a'), 'a')

    def test_vowel_priority(self):
        self.assertEqual(convert_syllable('zhong1'), 'zhōng')
        self.assertEqual(convert_syllable('guo2'), 'guó')

    def test_umlaut(self):
        self.assertEqual(convert_syllable('nv3'), 'nǚ')
        self.assertEqual(convert_syllable('lv3'), 'lǚ')

    def test_multi_vowel(self):
        self.assertEqual(convert_syllable('yi1'), 'yī')
        self.assertEqual(convert_syllable('ye4'), 'yè')


class TestConvertPinyin(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(convert_pinyin(''), '')

    def test_none(self):
        self.assertEqual(convert_pinyin(None), '')

    def test_single_syllable(self):
        self.assertEqual(convert_pinyin('yi1'), 'yī')

    def test_multiple_syllables(self):
        self.assertEqual(convert_pinyin('yi1 xin1 yi1 yi4'), 'yī xīn yī yì')

    def test_zhong_guo(self):
        self.assertEqual(convert_pinyin('zhong1 guo2'), 'zhōng guó')

    def test_nv_hai(self):
        self.assertEqual(convert_pinyin('nv3 hai2'), 'nǚ hái')


class TestGetInitials(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(get_initials(''), '')

    def test_none(self):
        self.assertEqual(get_initials(None), '')

    def test_single_syllable(self):
        self.assertEqual(get_initials('yi1'), 'y')

    def test_multiple_syllables(self):
        self.assertEqual(get_initials('yi1 xin1 yi1 yi4'), 'yxyy')

    def test_yi_ma_dang_xian(self):
        self.assertEqual(get_initials('yi1 ma3 dang1 xian1'), 'ymdx')

    def test_uppercase(self):
        self.assertEqual(get_initials('YI1'), 'y')


class TestPinyinNormalize(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(pinyin_normalize(''), '')

    def test_none(self):
        self.assertEqual(pinyin_normalize(None), '')

    def test_lv_to_nv(self):
        self.assertEqual(pinyin_normalize('lv'), 'nv')

    def test_lv3_to_nv3(self):
        self.assertEqual(pinyin_normalize('lv3'), 'nv3')

    def test_nvl_unchanged(self):
        self.assertEqual(pinyin_normalize('nvl'), 'nvl')

    def test_uppercase(self):
        self.assertEqual(pinyin_normalize('LV'), 'nv')

    def test_no_change(self):
        self.assertEqual(pinyin_normalize('zhong1'), 'zhong1')


class TestFuzzyMatchPinyin(unittest.TestCase):
    def test_empty_query(self):
        self.assertFalse(fuzzy_match_pinyin('', 'yi1 xin1'))

    def test_empty_field(self):
        self.assertFalse(fuzzy_match_pinyin('yi', ''))

    def test_none_query(self):
        self.assertFalse(fuzzy_match_pinyin(None, 'yi1 xin1'))

    def test_none_field(self):
        self.assertFalse(fuzzy_match_pinyin('yi', None))

    def test_exact_match(self):
        self.assertTrue(fuzzy_match_pinyin('yixin', 'yi1 xin1'))

    def test_prefix_match(self):
        self.assertTrue(fuzzy_match_pinyin('yi', 'yi1 xin1'))

    def test_syllable_prefix_match(self):
        self.assertTrue(fuzzy_match_pinyin('yi x', 'yi1 xin1'))

    def test_no_match(self):
        self.assertFalse(fuzzy_match_pinyin('abc', 'yi1 xin1'))

    def test_with_tones(self):
        self.assertTrue(fuzzy_match_pinyin('yi1xin1', 'yi1 xin1'))


if __name__ == '__main__':
    unittest.main()
