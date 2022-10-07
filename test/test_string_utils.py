import unittest

from flathunter.string_utils import remove_prefix


class StringUtilsTest(unittest.TestCase):

    def test_remove_prefix(self):
        self.assertEqual(remove_prefix("abcdef", "abc"), "def")
        self.assertEqual(remove_prefix("acdef", "abc"), "acdef")
        self.assertEqual(remove_prefix("abcdef", ""), "abcdef")
        self.assertEqual(remove_prefix("abc", "abc"), "")
        self.assertEqual(remove_prefix("abc", "abcd"), "abc")
        self.assertEqual(remove_prefix("", "abc"), "")
        self.assertEqual(remove_prefix("", ""), "")
        self.assertEqual(remove_prefix(None, "foo"), None)
