import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from visitor_counter import count_visitors


class VisitorCounterTests(unittest.TestCase):
    def test_repeat_visits_and_new_browser(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "visitors.sqlite3"
            browser = str(uuid4())
            self.assertEqual(count_visitors(browser, database), 1)
            self.assertEqual(count_visitors(browser, database), 1)
            self.assertEqual(count_visitors(None, database), 1)
            self.assertEqual(count_visitors("invalid", database), 1)
            self.assertEqual(count_visitors(str(uuid4()), database), 2)

    def test_concurrent_repeats_are_counted_once(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "visitors.sqlite3"
            browsers = [str(uuid4()) for _ in range(5)]
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda identity: count_visitors(identity, database), browsers * 4))
            self.assertEqual(count_visitors(None, database), 5)


if __name__ == "__main__":
    unittest.main()
