import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

            notify_existing_state = ListingStateStore(
                str(Path(directory) / "notify-existing.db")
            )
            initial_delivery = []
            with patch("parser.pipeline.random.uniform", return_value=1.5), patch(
                "parser.pipeline.time.sleep"
            ) as sleep:
                result = process_listings(
                    [first, second],
                    notify_existing_state,
                    initial_delivery.append,
                    notify_existing_on_first_run=True,
                    delivery_jitter_seconds=(1.0, 2.0),
                )
            self.assertEqual(result.delivered, 2)
            self.assertEqual(
                [listing.id for listing in initial_delivery],
                ["111", "222"],
            )
            sleep.assert_called_once_with(1.5)


if __name__ == "__main__":
    unittest.main()
