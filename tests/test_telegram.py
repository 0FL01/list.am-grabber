import unittest
from unittest.mock import Mock, patch

import requests
from bs4 import BeautifulSoup

from integrations.notifications.list_am_telegram import TelegramNotifier, format_listing
from models import RentalListing


def telegram_response(result):
    response = Mock()
    response.json.return_value = {"ok": True, "result": result}
    return response


class TelegramNotifierTest(unittest.TestCase):
    def setUp(self):
        self.listing = RentalListing(
            id="111",
            url="https://www.list.am/ru/item/111",
            title="Квартира <центр>",
            price_text="250,000 ֏ в месяц",
            summary="2 комнаты & кабинет",
            seller_label="Собственник",
            published_text="Размещено 10.12.2023",
            updated_text="Обновлено 23.08.2026, 01:29",
            description="Очень подробное описание <&> " * 100,
            detail_attributes=("Парковка — Открытая",),
            image_urls=tuple(
                f"https://img.list.am/f/{index:03d}/101001{index:03d}.webp"
                for index in range(1, 12)
            ),
        )

    def test_sends_one_trimmed_album_with_caption(self):
        response = telegram_response(
            [{"message_id": 101}, {"message_id": 102}]
        )

        with patch(
            "integrations.notifications.list_am_telegram.requests.post",
            return_value=response,
        ) as post:
            message_id = TelegramNotifier("token", "chat").notify(self.listing)

        self.assertEqual(message_id, 101)
        self.assertEqual(post.call_count, 1)
        self.assertTrue(post.call_args.args[0].endswith("/sendMediaGroup"))
        payload = post.call_args.kwargs["json"]
        self.assertEqual(len(payload["media"]), 10)
        self.assertIn("https://www.list.am/ru/item/111", payload["media"][0]["caption"])
        self.assertIn("Квартира &lt;центр&gt;", payload["media"][0]["caption"])
        self.assertIn("2 комнаты &amp; кабинет", payload["media"][0]["caption"])
        self.assertIn("Размещено 10.12.2023", payload["media"][0]["caption"])
        self.assertIn("Обновлено 23.08.2026, 01:29", payload["media"][0]["caption"])
        self.assertIn("Описание:", payload["media"][0]["caption"])
        self.assertTrue(payload["media"][0]["caption"].endswith("…"))
        caption_text = BeautifulSoup(
            payload["media"][0]["caption"], "html.parser"
        ).get_text()
        self.assertLessEqual(len(caption_text), 1024)
        self.assertNotIn("Парковка", payload["media"][0]["caption"])
        self.assertNotIn("caption", payload["media"][1])
        response.raise_for_status.assert_called_once_with()

    def test_sanitizes_transport_failure(self):
        listing = RentalListing(
            id="333", url="https://www.list.am/ru/item/333", title="Дом"
        )
        with patch(
            "integrations.notifications.list_am_telegram.requests.post",
            side_effect=requests.Timeout("https://api.telegram.org/botsecret/sendMessage"),
        ):
            with self.assertRaisesRegex(RuntimeError, "Telegram delivery failed") as error:
                TelegramNotifier("secret", "chat").notify(listing)

        self.assertNotIn("secret", str(error.exception))

    def test_formatter_omits_missing_optional_fields(self):
        listing = RentalListing(id="222", url="https://www.list.am/ru/item/222", title="Дом")
        self.assertEqual(
            format_listing(listing),
            '<a href="https://www.list.am/ru/item/222">Дом</a>',
        )

    def test_sends_one_photo_without_extra_text_message(self):
        response = telegram_response({"message_id": 201})
        listing = RentalListing(
            id="222",
            url="https://www.list.am/ru/item/222",
            title="Дом",
            image_urls=("https://img.list.am/f/001/101001001.webp",),
        )

        with patch(
            "integrations.notifications.list_am_telegram.requests.post",
            return_value=response,
        ) as post:
            message_id = TelegramNotifier("token", "chat").notify(listing)

        self.assertEqual(message_id, 201)
        self.assertEqual(post.call_count, 1)
        self.assertTrue(post.call_args.args[0].endswith("/sendPhoto"))
        self.assertIn("caption", post.call_args.kwargs["json"])

    def test_falls_back_to_one_text_alert_when_album_is_rejected(self):
        rejected = Mock()
        rejected.json.return_value = {"ok": False}
        accepted = telegram_response({"message_id": 301})

        with patch(
            "integrations.notifications.list_am_telegram.requests.post",
            side_effect=[rejected, accepted],
        ) as post, patch(
            "integrations.notifications.list_am_telegram.time.sleep"
        ):
            message_id = TelegramNotifier("token", "chat").notify(self.listing)

        self.assertEqual(message_id, 301)
        self.assertEqual(post.call_count, 2)
        self.assertTrue(post.call_args_list[0].args[0].endswith("/sendMediaGroup"))
        self.assertTrue(post.call_args_list[1].args[0].endswith("/sendMessage"))

    def test_text_alert_returns_message_id(self):
        listing = RentalListing(
            id="333", url="https://www.list.am/ru/item/333", title="Дом"
        )
        with patch(
            "integrations.notifications.list_am_telegram.requests.post",
            return_value=telegram_response({"message_id": 401}),
        ):
            self.assertEqual(TelegramNotifier("token", "chat").notify(listing), 401)

    def test_reply_is_plain_utf16_limited_and_rate_gated(self):
        notifier = TelegramNotifier("token", "chat")
        long_text = "😀" * 3000
        responses = [
            telegram_response({"message_id": 501}),
            telegram_response({"message_id": 502}),
        ]
        listing = RentalListing(
            id="333", url="https://www.list.am/ru/item/333", title="Дом"
        )

        with patch(
            "integrations.notifications.list_am_telegram.requests.post",
            side_effect=responses,
        ) as post, patch(
            "integrations.notifications.list_am_telegram.time.monotonic",
            side_effect=[100.0, 100.25, 101.0],
        ), patch(
            "integrations.notifications.list_am_telegram.time.sleep"
        ) as sleep:
            notifier.notify(listing)
            reply_id = notifier.reply(501, long_text)

        self.assertEqual(reply_id, 502)
        sleep.assert_called_once_with(0.75)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["reply_parameters"], {"message_id": 501})
        self.assertNotIn("parse_mode", payload)
        self.assertNotIn("allow_sending_without_reply", payload["reply_parameters"])
        self.assertTrue(payload["text"].endswith("…"))
        self.assertLessEqual(
            len(payload["text"].encode("utf-16-le")) // 2,
            4096,
        )


if __name__ == "__main__":
    unittest.main()
