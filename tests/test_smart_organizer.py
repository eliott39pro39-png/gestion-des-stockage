import tempfile
import unittest
from pathlib import Path
import smart_organizer

class OrganizerTests(unittest.TestCase):
    def test_preview_move_and_undo(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'photo.PNG').write_bytes(b'image')
            (root / 'notes.pdf').write_bytes(b'doc')
            (root / 'other.unknown').write_bytes(b'other')
            moves = smart_organizer.plan(root)
            self.assertEqual(len(moves), 2)
            self.assertTrue((root / 'photo.PNG').exists())
            done = smart_organizer.execute(moves)
            self.assertEqual(len(done), 2)
            self.assertTrue((root / 'Images/photo.PNG').exists())
            self.assertTrue((root / 'Documents/notes.pdf').exists())
            self.assertEqual(len(smart_organizer.undo(done)), 2)
            self.assertTrue((root / 'photo.PNG').exists())
            self.assertTrue((root / 'other.unknown').exists())

    def test_collision_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'Images').mkdir()
            (root / 'Images/photo.jpg').write_text('existing')
            (root / 'photo.jpg').write_text('original')
            self.assertEqual(smart_organizer.plan(root), [])

if __name__ == '__main__':
    unittest.main()
