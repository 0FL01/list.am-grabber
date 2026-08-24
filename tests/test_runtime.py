import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from analyst import AnalysisResult, AnalystError
from dto import AnalystConfig
from models import RentalListing
from parser_cls import _run_analyses, run_monitor


class FakeState:
    def __init__(self, events):
        self.events = events
        self.prices = {}

    def is_initialized(self):
        return True

    def get_price_key(self, listing_id):
        return self.prices.get(listing_id)

    def save(self, listing):
        self.events.append(f"save:{listing.id}")
        self.prices[listing.id] = listing.price_key


class FakeScanner:
    def __init__(self, events, listings):
        self.events = events
        self.listings = listings

    def __enter__(self):
        self.events.append("browser:open")
        return self

    def __exit__(self, *_args):
        self.events.append("browser:closed")

    def scan(self, _urls, _max_pages):
        return self.listings

    def add_details(self, listing):
        self.events.append(f"detail:{listing.id}")
        return replace(listing, description="details")


class RuntimeTest(unittest.TestCase):
    def test_sends_all_primary_alerts_and_closes_browser_before_analysis(self):
        events = []
        listings = [
            RentalListing(
                id=str(listing_id),
                url=f"https://www.list.am/ru/item/{listing_id}",
                title="Дом",
            )
            for listing_id in (111, 222)
        ]
        analyst_config = AnalystConfig(
            enabled=True,
            base_url="https://llm.example/v1",
            model="custom-model",
            vision=True,
            reasoning_effort="high",
            prompt="Проверь",
        )
        config = SimpleNamespace(
            telegram_bot_token="token",
            telegram_chat_id="chat",
            database_path=Path("unused.db"),
            search_urls=["https://www.list.am/ru/category/56"],
            max_pages=1,
            notify_existing_on_first_run=False,
            poll_interval_seconds=60,
            analyst=analyst_config,
        )
        notifier = Mock()

        def notify(listing):
            events.append(f"main:{listing.id}")
            return int(listing.id) + 1000

        notifier.notify.side_effect = notify

        analyst = Mock()

        def analyze(listing, _stop_event):
            events.append(f"analysis:{listing.id}")
            self.assertIn("browser:closed", events)
            return AnalysisResult(
                text="Вердикт",
                mode="vision",
                image_count=2,
                attempts=1,
                latency_ms=10,
            )

        analyst.analyze.side_effect = analyze
        notifier.reply.side_effect = lambda message_id, _text, _format: events.append(
            f"reply:{message_id}"
        ) or message_id + 1

        with patch("parser_cls.load_list_am_config", return_value=config), patch(
            "parser_cls.TelegramNotifier", return_value=notifier
        ), patch("parser_cls.ListingStateStore", return_value=FakeState(events)), patch(
            "parser_cls.ListAmScanner",
            side_effect=lambda **_kwargs: FakeScanner(events, listings),
        ), patch("parser_cls.AnalystClient", return_value=analyst), patch(
            "parser_cls.signal.signal"
        ), patch("parser.pipeline.time.sleep"):
            exit_code = run_monitor("config.toml", once=True)

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            events,
            [
                "browser:open",
                "detail:111",
                "main:111",
                "save:111",
                "detail:222",
                "main:222",
                "save:222",
                "browser:closed",
                "analysis:111",
                "reply:1111",
                "analysis:222",
                "reply:1222",
            ],
        )

    def test_analysis_and_reply_failures_do_not_stop_later_jobs(self):
        listings = [
            RentalListing(
                id=str(listing_id),
                url=f"https://www.list.am/ru/item/{listing_id}",
                title="Дом",
            )
            for listing_id in (111, 222, 333)
        ]
        analyst = Mock()
        success = AnalysisResult(
            text="Вердикт",
            mode="text",
            image_count=0,
            attempts=1,
            latency_ms=10,
        )
        analyst.analyze.side_effect = [AnalystError("read_timeout"), success, success]
        notifier = Mock()
        notifier.reply.side_effect = [RuntimeError("Telegram failed"), 44]

        _run_analyses(
            analyst,
            notifier,
            [(listing, index) for index, listing in enumerate(listings, 1)],
            Mock(is_set=Mock(return_value=False)),
            "model",
        )

        self.assertEqual(analyst.analyze.call_count, 3)
        self.assertEqual(notifier.reply.call_count, 2)
        self.assertEqual(notifier.reply.call_args.args, (3, "Вердикт", "plain"))

    def test_disabled_analyst_does_not_create_client(self):
        events = []
        config = SimpleNamespace(
            telegram_bot_token="token",
            telegram_chat_id="chat",
            database_path=Path("unused.db"),
            search_urls=["https://www.list.am/ru/category/56"],
            max_pages=1,
            notify_existing_on_first_run=False,
            poll_interval_seconds=60,
            analyst=AnalystConfig(),
        )

        with patch("parser_cls.load_list_am_config", return_value=config), patch(
            "parser_cls.TelegramNotifier"
        ), patch("parser_cls.ListingStateStore", return_value=FakeState(events)), patch(
            "parser_cls.ListAmScanner",
            side_effect=lambda **_kwargs: FakeScanner(events, []),
        ), patch("parser_cls.AnalystClient") as client, patch(
            "parser_cls.signal.signal"
        ):
            exit_code = run_monitor("config.toml", once=True)

        self.assertEqual(exit_code, 0)
        client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
