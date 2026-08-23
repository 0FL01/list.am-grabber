import tempfile
import unittest
from pathlib import Path

from load_config import load_list_am_config


class ConfigTest(unittest.TestCase):
    def test_loads_minimal_list_am_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text(
                """
[list_am]
search_urls = ["https://www.list.am/ru/category/56?price1=100000"]
max_pages = 2
poll_interval_seconds = 30
database_path = "data/test.db"
""".strip(),
                encoding="utf-8",
            )

            config = load_list_am_config(str(path))

        self.assertEqual(config.max_pages, 2)
        self.assertEqual(config.poll_interval_seconds, 30)
        self.assertEqual(config.database_path, Path("data/test.db"))

    def test_rejects_non_list_am_url(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text(
                '[list_am]\nsearch_urls = ["https://example.com/category/56"]',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Unsupported List.am"):
                load_list_am_config(str(path))


if __name__ == "__main__":
    unittest.main()
