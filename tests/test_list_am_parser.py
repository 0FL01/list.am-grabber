import unittest
from pathlib import Path

from parser.list_am import parse_category_page, parse_listing_details


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
        self.assertEqual(len(page.listings[0].image_urls), 11)
        self.assertEqual(
            page.listings[0].image_urls[0],
            "https://img.list.am/f/001/101001001.webp",
        )
        self.assertEqual(
            page.listings[0].image_urls[-1],
            "https://img.list.am/f/011/101001011.webp",
        )
        self.assertEqual(page.listings[1].price_key, "USD:700")
        self.assertEqual(
            page.next_url,
            "https://www.list.am/category/56/2?price1=100000&price2=300000",
        )

    def test_parses_listing_details(self):
        html = (FIXTURES / "detail.html").read_text(encoding="utf-8")
        details = parse_listing_details(html)

        self.assertEqual(details.title, "2-комн. квартира в Цахкадзоре, 48 кв.м.")
        self.assertEqual(details.price_text, "240,000 ֏ в месяц")
        self.assertEqual(
            (details.published_text, details.updated_text),
            ("Размещено 10.12.2023", "Обновлено 23.08.2026, 01:29"),
        )
        self.assertEqual(
            details.description,
            "По остальным вопросам смело звоните.",
        )
        self.assertEqual(len(details.image_urls), 24)
        self.assertEqual(details.image_urls[0], "https://s.list.am/f/photo-01.webp")
        self.assertEqual(details.image_urls[-1], "https://img.list.am/f/photo-24.webp")
        self.assertEqual(
            details.detail_attributes,
            (
                "Основные параметры — 70 кв.м. Общая площадь",
                "О здании — Новостройка Нет",
                "Парковка — Открытая",
            ),
        )

if __name__ == "__main__":
    unittest.main()
