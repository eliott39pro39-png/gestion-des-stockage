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

    def test_archived_update_controls_disabled(self):
        source = """class Window:
    pass
if __name__=='__main__': pass
application_id='io.github.gestionstockage.Final'
"""
        patched = prepare_source(source, '27.6.2')
        self.assertIn('Window.updates_page = _archive_updates_page', patched)
        self.assertIn('Window.check_updates = _archive_no_update', patched)
        self.assertIn('Window.download_update = _archive_no_update', patched)
        self.assertIn('Window._start_update_download = _archive_no_update', patched)
        compile(patched, '<archived-app>', 'exec')

    def test_archive_update_page_is_read_only(self):
        source = """class Window:
    def __init__(self): self.messages = []
    def clear(self): pass
    def mark_page(self, value): self.messages.append(value)
    def heading(self, value): self.messages.append(value)
    def info(self, value): self.messages.append(value)
    def dialog(self, title, body): self.messages.append(title)
VERSION='27.6.2'
application_id='io.github.gestionstockage.Final'
if __name__=='__main__': pass
"""
        namespace = {'__name__':'archived_test'}
        exec(compile(prepare_source(source,'27.6.2'),'<archived-app>','exec'), namespace)
        window = namespace['Window']()
        window.updates_page()
        self.assertTrue(any('désactivées' in message for message in window.messages))
        self.assertFalse(any('Télécharger et installer' in message for message in window.messages))
        window.check_updates()
        self.assertIn('Mises à jour désactivées', window.messages)

if __name__ == '__main__':
    unittest.main()
