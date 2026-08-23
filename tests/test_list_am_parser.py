import unittest
from pathlib import Path

from parser.list_am import normalize_phone, parse_category_page


FIXTURES = Path(__file__).parent / "fixtures"


class CategoryParserTest(unittest.TestCase):
    def test_parses_cards_and_next_page(self):
        html = (FIXTURES / "category.html").read_text(encoding="utf-8")

        page = parse_category_page(
            html,
            "https://www.list.am/ru/category/56?price1=100000&price2=300000",
        )

        self.assertEqual([listing.id for listing in page.listings], ["111", "222"])
        self.assertEqual(page.listings[0].url, "https://www.list.am/ru/item/111")
        self.assertEqual(page.listings[0].price_key, "AMD:250000")
        self.assertEqual(page.listings[0].seller_label, "Агентство")
        self.assertEqual(len(page.listings[0].image_urls), 10)
        self.assertEqual(
            page.listings[0].image_urls[0],
            "https://img.list.am/f/001/101001001.webp",
        )
        self.assertEqual(
            page.listings[0].image_urls[-1],
            "https://img.list.am/f/010/101001010.webp",
        )
        self.assertEqual(page.listings[1].price_key, "USD:700")
        self.assertEqual(
            page.next_url,
            "https://www.list.am/category/56/2?price1=100000&price2=300000",
        )

    def test_normalizes_armenian_phone_for_calling(self):
        self.assertEqual(normalize_phone("tel:093 93-93-19"), "+37493939319")
        self.assertEqual(normalize_phone("+374 (93) 93-93-19"), "+37493939319")
        self.assertEqual(normalize_phone("93939319"), "+37493939319")
        self.assertEqual(normalize_phone("invalid"), "")


if __name__ == "__main__":
    unittest.main()
