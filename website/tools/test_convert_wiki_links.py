import unittest

from convert_wiki_links import normalize_markdown_links, normalize_target


class NormalizeLinksTests(unittest.TestCase):
    def test_normalizes_unicode_hyphen_in_markdown_target(self):
        source = '[Power Curve Test \u2010 Site Assessment](/Power-Curve-Test-\u2010-Site-Assessment)'

        result, count = normalize_markdown_links(source, lowercase=True)

        self.assertEqual(
            result,
            '[Power Curve Test \u2010 Site Assessment](/power-curve-test--site-assessment)',
        )
        self.assertEqual(count, 1)

    def test_normalizes_common_unicode_dashes_in_wiki_targets(self):
        for dash in ('\u2010', '\u2011', '\u2012', '\u2013', '\u2014', '\u2212'):
            with self.subTest(dash=dash):
                self.assertEqual(normalize_target(f'one{dash}two'), '/onetwo')


if __name__ == '__main__':
    unittest.main()