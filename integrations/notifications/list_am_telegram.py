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
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": format_listing(listing),
                    "parse_mode": "HTML",
                },
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
