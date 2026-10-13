"""Additional automated safety checks for the local assistant."""
import pathlib
import tempfile
import threading
import unittest
from unittest import mock

import assistant_tools


class AssistantSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        (self.root / "documents").mkdir()
        (self.root / "documents" / "résumé.txt").write_text("original", encoding="utf-8")
        (self.root / "notes.txt").write_text("notes", encoding="utf-8")

    def test_accent_insensitive_search(self):
        results, incomplete = assistant_tools.search_items(self.root, "resume")
        self.assertFalse(incomplete)
        self.assertEqual([p.name for p in results], ["résumé.txt"])

    def test_no_results(self):
        results, incomplete = assistant_tools.search_items(self.root, "nonexistent")
        self.assertEqual(results, [])
        self.assertFalse(incomplete)

    def test_invalid_query(self):
        for query in ("", "trouve", "find my files"):
            with self.subTest(query=query):
                with self.assertRaises(ValueError):
                    assistant_tools.search_items(self.root, query)

    def test_invalid_limits(self):
        for kwargs in ({"limit": 0}, {"limit": -1}, {"max_entries": 0},
                       {"max_entries": -2}, {"limit": 1.5}, {"max_entries": 1.2}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    assistant_tools.search_items(self.root, "notes", **kwargs)

    def test_cancelled(self):
        event = threading.Event()
        event.set()
        results, incomplete = assistant_tools.search_items(self.root, "notes", cancel=event)
        self.assertEqual(results, [])
        self.assertTrue(incomplete)

    def test_progress(self):
        updates = []
        assistant_tools.search_items(self.root, "missing", progress=lambda n, p: updates.append(n))
        self.assertTrue(updates)
        self.assertGreater(updates[-1], 0)

    def test_directory_rename_rejected(self):
        with self.assertRaises(ValueError):
            assistant_tools.preview_rename(self.root / "documents", "renamed")

    def test_existing_destination_is_preserved(self):
        before = (self.root / "notes.txt").read_text(encoding="utf-8")
        with self.assertRaises(FileExistsError):
            assistant_tools.preview_rename(self.root / "documents" / "résumé.txt", "notes.txt") if False else assistant_tools.preview_rename(self.root / "notes.txt", "documents")
        self.assertEqual((self.root / "notes.txt").read_text(encoding="utf-8"), before)

    def test_rename_rollback_on_unlink_failure(self):
        source = self.root / "notes.txt"
        original_unlink = pathlib.Path.unlink
        def failing_unlink(path, *args, **kwargs):
            if path == source:
                raise PermissionError("simulated")
            return original_unlink(path, *args, **kwargs)
        src, target = assistant_tools.preview_rename(source, "new.txt")
        with mock.patch.object(pathlib.Path, "unlink", failing_unlink):
            with self.assertRaises(PermissionError):
                assistant_tools.confirm_rename(src, target)
        self.assertTrue(source.exists())
        self.assertFalse(target.exists())

    def test_symlink_not_followed(self):
        link = self.root / "shortcut"
        try:
            link.symlink_to(self.root / "documents", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        results, _ = assistant_tools.search_items(self.root, "shortcut")
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
