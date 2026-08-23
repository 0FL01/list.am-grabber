from html import escape

import requests

from models import RentalListing


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        if not bot_token.strip() or not chat_id.strip():
            raise ValueError("Telegram bot token and chat ID are required")
        self.bot_token = bot_token
        self.chat_id = chat_id

    def notify(self, listing: RentalListing) -> None:
        text = format_listing(listing)
        image_urls = listing.image_urls[:10]
        if image_urls:
            try:
                self._send_images(image_urls, text)
                return
            except RuntimeError:
                pass
        self._request(
            "sendMessage",
            {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
            },
        )

    def _send_images(self, image_urls: tuple[str, ...], caption: str) -> None:
        if len(image_urls) == 1:
            self._request(
                "sendPhoto",
                {
                    "chat_id": self.chat_id,
                    "photo": image_urls[0],
                    "caption": caption,
                    "parse_mode": "HTML",
                },
            )
            return

        media = [{"type": "photo", "media": url} for url in image_urls]
        media[0].update({"caption": caption, "parse_mode": "HTML"})
        self._request(
            "sendMediaGroup",
            {"chat_id": self.chat_id, "media": media},
        )

    def _request(self, method: str, payload: dict) -> None:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/{method}",
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            status = error.response.status_code if error.response is not None else None
            suffix = f" with status {status}" if status else ""
            raise RuntimeError(f"Telegram delivery failed{suffix}") from None

        try:
            result = response.json()
        except ValueError:
            raise RuntimeError("Telegram returned an invalid response") from None
        if not result.get("ok"):
            raise RuntimeError("Telegram rejected the alert")


def format_listing(listing: RentalListing) -> str:
    parts = []
    if listing.price_text:
        parts.append(f"<b>{escape(listing.price_text)}</b>")
    parts.append(
        f'<a href="{escape(listing.url, quote=True)}">{escape(listing.title)}</a>'
    )
    if listing.summary:
        parts.append(escape(listing.summary))
    if listing.seller_label:
        parts.append(f"Продавец: {escape(listing.seller_label)}")
    return "\n".join(parts)
