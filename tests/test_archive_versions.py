import pathlib
import re
import unittest

from packaging.archive_versions import VERSION_PATTERN

class ArchiveVersionTests(unittest.TestCase):
    def test_version_detection(self):
        self.assertEqual(VERSION_PATTERN.search("VERSION='27.6.0'").group(1), '27.6.0')
        self.assertEqual(VERSION_PATTERN.search("VERSION='27.5.4'").group(1), '27.5.4')

    def test_archive_directory_matching(self):
        pattern = r'[0-9]+(?:\.[0-9]+)*'
        for name in ('27.5.4', '27.6.0', '26.9', '1.0'):
            self.assertIsNotNone(re.fullmatch(pattern, name))
        for name in ('foo', '../27.5.4', '27x5x4'):
            self.assertIsNone(re.fullmatch(pattern, name))

if __name__ == '__main__':
    unittest.main()
