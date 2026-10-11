import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import assistant_history

class HistoryTests(unittest.TestCase):
    def test_round_trip_and_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'history.json'
            with patch.object(assistant_history, 'HISTORY_PATH', path):
                assistant_history.save_history([{'user': True, 'message': 'Trouve War Thunder'}, {'user': False, 'message': '🎉 Trouvé !'}])
                self.assertEqual(len(assistant_history.load_history()), 2)
                assistant_history.clear_history()
                self.assertEqual(assistant_history.load_history(), [])

if __name__ == '__main__':
    unittest.main()
