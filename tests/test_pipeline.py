import tempfile
import unittest
from dataclasses import replace
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

            def notify(listing):
                delivered.append(listing)
                return int(listing.id)

            result = process_listings([first], state, notify)
            self.assertEqual(result.baselined, 1)
            self.assertEqual(delivered, [])

            result = process_listings([first], state, notify)
            self.assertEqual(result.unchanged, 1)
            self.assertEqual(delivered, [])

            result = process_listings([first, second], state, notify)
            self.assertEqual(result.delivered, 1)
            self.assertEqual([listing.id for listing in delivered], ["222"])

            cheaper_first = RentalListing(
                id=first.id,
                url=first.url,
                title=first.title,
                price_text="230,000 ֏ в месяц",
            )
            result = process_listings([cheaper_first], state, notify)
            self.assertEqual(result.delivered, 1)
            self.assertEqual(state.get_price_key(first.id), "AMD:230000")

            failed = RentalListing(
                id="444",
                url="https://www.list.am/ru/item/444",
                title="Квартира с ошибкой доставки",
            )

            def fail_delivery(_listing):
                raise RuntimeError("Telegram unavailable")

            callbacks = []
            with self.assertRaisesRegex(RuntimeError, "Telegram unavailable"):
                process_listings(
                    [failed],
                    state,
                    fail_delivery,
                    after_delivery=lambda listing, message_id: callbacks.append(
                        (listing, message_id)
                    ),
                )
            self.assertIsNone(state.get_price_key(failed.id))
            self.assertEqual(callbacks, [])

            result = process_listings([failed], state, notify)
            self.assertEqual(result.delivered, 1)
            self.assertEqual(state.get_price_key(failed.id), "NO_PRICE")

            notify_existing_state = ListingStateStore(
                str(Path(directory) / "notify-existing.db")
            )
            initial_delivery = []

            def notify_initial(listing):
                initial_delivery.append(listing)
                return int(listing.id)

            with patch("parser.pipeline.random.uniform", return_value=1.5), patch(
                "parser.pipeline.time.sleep"
            ) as sleep:
                result = process_listings(
                    [first, second],
                    notify_existing_state,
                    notify_initial,
                    enrich=lambda listing: replace(
                        listing,
                        published_text="Размещено 10.12.2023",
                    ),
                    notify_existing_on_first_run=True,
                    delivery_jitter_seconds=(1.0, 2.0),
                )
            self.assertEqual(result.delivered, 2)
            self.assertEqual(
                [listing.id for listing in initial_delivery],
                ["111", "222"],
            )
            self.assertEqual(
                initial_delivery[0].published_text,
                "Размещено 10.12.2023",
            )
            sleep.assert_called_once_with(1.5)

    def test_after_delivery_runs_after_save_and_failure_does_not_stop_batch(self):
        listings = [
            RentalListing(
                id=str(listing_id),
                url=f"https://www.list.am/ru/item/{listing_id}",
                title="Дом",
                price_text=f"{listing_id} $",
            )
            for listing_id in (111, 222)
        ]

        with tempfile.TemporaryDirectory() as directory:
            state = ListingStateStore(str(Path(directory) / "state.db"))
            state.initialize([])
            callbacks = []

            def notify(listing):
                return int(listing.id) + 1000

            def after_delivery(listing, message_id):
                callbacks.append(
                    (
                        listing.id,
                        listing.description,
                        message_id,
                        state.get_price_key(listing.id),
                    )
                )
                if listing.id == "111":
                    raise RuntimeError("callback failed")

            result = process_listings(
                listings,
                state,
                notify,
                enrich=lambda listing: replace(listing, description="details"),
                after_delivery=after_delivery,
            )

        self.assertEqual(result.delivered, 2)
        self.assertEqual(
            callbacks,
            [
                ("111", "details", 1111, "USD:111"),
                ("222", "details", 1222, "USD:222"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
