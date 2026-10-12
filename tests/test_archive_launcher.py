import unittest
from archive_launcher import prepare_source

class ArchiveLauncherTests(unittest.TestCase):
    def test_unique_application_id(self):
        source = "super().__init__(application_id='io.github.gestionstockage.Final',flags=Gio.ApplicationFlags.FLAGS_NONE)"
        patched = prepare_source(source, '27.6.1')
        self.assertIn("application_id='io.github.gestionstockage.ArchiveV27_6_1'", patched)
        self.assertNotIn("application_id='io.github.gestionstockage.Final'", patched)

    def test_different_versions_get_different_ids(self):
        source = 'application_id="io.github.gestionstockage.Final"'
        self.assertNotEqual(prepare_source(source,'27.5.4'),prepare_source(source,'27.6.0'))

    def test_missing_id_is_reported(self):
        with self.assertRaises(ValueError):
            prepare_source('print("hello")', '27.5.4')

if __name__ == '__main__':
    unittest.main()
