import unittest
from unittest.mock import Mock, patch

import requests

from integrations.notifications.list_am_telegram import TelegramNotifier, format_listing
from models import RentalListing


class TelegramNotifierTest(unittest.TestCase):
    def setUp(self):
        self.listing = RentalListing(
            id="111",
            url="https://www.list.am/ru/item/111",
            title="Квартира <центр>",
            price_text="250,000 ֏ в месяц",
            summary="2 комнаты & кабинет",
            seller_label="Собственник",
        )

    def test_formats_and_sends_text_alert(self):
        response = Mock()
        response.json.return_value = {"ok": True}

        with patch(
            "integrations.notifications.list_am_telegram.requests.post",
            return_value=response,
        ) as post:
            TelegramNotifier("token", "chat").notify(self.listing)

        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["parse_mode"], "HTML")
        self.assertIn("https://www.list.am/ru/item/111", payload["text"])
        self.assertIn("Квартира &lt;центр&gt;", payload["text"])
        self.assertIn("2 комнаты &amp; кабинет", payload["text"])
        response.raise_for_status.assert_called_once_with()

    def test_sanitizes_transport_failure(self):
        with patch(
            "integrations.notifications.list_am_telegram.requests.post",
            side_effect=requests.Timeout("https://api.telegram.org/botsecret/sendMessage"),
        ):
            with self.assertRaisesRegex(RuntimeError, "Telegram delivery failed") as error:
                TelegramNotifier("secret", "chat").notify(self.listing)

        self.assertNotIn("secret", str(error.exception))

    def test_formatter_omits_missing_optional_fields(self):
        listing = RentalListing(id="222", url="https://www.list.am/ru/item/222", title="Дом")
        self.assertEqual(
            format_listing(listing),
            '<a href="https://www.list.am/ru/item/222">Дом</a>',
        )


if __name__ == "__main__":
    unittest.main()
