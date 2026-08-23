import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from db_service import ListingStateStore
from models import RentalListing
from parser.pipeline import process_listings


class PipelineTest(unittest.TestCase):
    def test_baseline_dedupe_price_change_and_delivery_failure(self):
        first = RentalListing(
            id="111",
            url="https://www.list.am/ru/item/111",
            title="Квартира",
            price_text="250,000 ֏ в месяц",
        )
        second = RentalListing(
            id="222",
            url="https://www.list.am/ru/item/222",
            title="Дом",
            price_text="$700 в месяц",
        )

        with tempfile.TemporaryDirectory() as directory:
            state = ListingStateStore(str(Path(directory) / "state.db"))
            delivered = []

            result = process_listings([first], state, delivered.append)
            self.assertEqual(result.baselined, 1)
            self.assertEqual(delivered, [])

            result = process_listings([first], state, delivered.append)
            self.assertEqual(result.unchanged, 1)
            self.assertEqual(delivered, [])

            result = process_listings([first, second], state, delivered.append)
            self.assertEqual(result.delivered, 1)
            self.assertEqual([listing.id for listing in delivered], ["222"])

            third = RentalListing(
                id="333",
                url="https://www.list.am/ru/item/333",
                title="Квартира с телефоном",
            )
            result = process_listings(
                [third],
                state,
                delivered.append,
                prepare=lambda listing: replace(listing, phone="+37493939319"),
            )
            self.assertEqual(result.delivered, 1)
            self.assertEqual(delivered[-1].phone, "+37493939319")

            cheaper_first = RentalListing(
                id=first.id,
                url=first.url,
                title=first.title,
                price_text="230,000 ֏ в месяц",
            )
            result = process_listings([cheaper_first], state, delivered.append)
            self.assertEqual(result.delivered, 1)
            self.assertEqual(state.get_price_key(first.id), "AMD:230000")

            failed = RentalListing(
                id="444",
                url="https://www.list.am/ru/item/444",
                title="Квартира с ошибкой доставки",
            )

            def fail_delivery(_listing):
                raise RuntimeError("Telegram unavailable")

            with self.assertRaisesRegex(RuntimeError, "Telegram unavailable"):
                process_listings([failed], state, fail_delivery)
            self.assertIsNone(state.get_price_key(failed.id))

            result = process_listings([failed], state, delivered.append)
            self.assertEqual(result.delivered, 1)
            self.assertEqual(state.get_price_key(failed.id), "NO_PRICE")


if __name__ == "__main__":
    unittest.main()
