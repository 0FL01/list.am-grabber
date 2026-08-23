import time
from html import escape

import requests
from loguru import logger

from models import RentalListing


MAX_CAPTION_LENGTH = 1024
MAX_MESSAGE_LENGTH = 4096
MIN_SEND_INTERVAL_SECONDS = 1.0


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        if not bot_token.strip() or not chat_id.strip():
            raise ValueError("Telegram bot token and chat ID are required")
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._last_send_at = None

    def notify(self, listing: RentalListing) -> int:
        text = format_listing(listing)
        image_urls = listing.image_urls[:10]
        if image_urls:
            try:
                return self._send_images(image_urls, text)
            except RuntimeError:
                pass
        result = self._request(
            "sendMessage",
            {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
            },
        )
        return _message_id(result)

    def reply(self, message_id: int, text: str) -> int | None:
        if type(message_id) is not int or message_id < 1:
            raise ValueError("Telegram reply message ID must be a positive integer")
        text = text.strip()
        if not text:
            return None
        truncated = truncate_telegram_text(text)
        if truncated != text:
            logger.warning("Telegram analyst reply truncated reply_to={}", message_id)
        result = self._request(
            "sendMessage",
            {
                "chat_id": self.chat_id,
                "text": truncated,
                "reply_parameters": {"message_id": message_id},
            },
        )
        return _message_id(result)

    def _send_images(self, image_urls: tuple[str, ...], caption: str) -> int:
        if len(image_urls) == 1:
            result = self._request(
                "sendPhoto",
                {
                    "chat_id": self.chat_id,
                    "photo": image_urls[0],
                    "caption": caption,
                    "parse_mode": "HTML",
                },
            )
            return _message_id(result)

        media = [{"type": "photo", "media": url} for url in image_urls]
        media[0].update({"caption": caption, "parse_mode": "HTML"})
        result = self._request(
            "sendMediaGroup",
            {"chat_id": self.chat_id, "media": media},
        )
        if not isinstance(result, list) or not result:
            raise RuntimeError("Telegram returned an invalid media group")
        return _message_id(result[0])

    def _request(self, method: str, payload: dict):
        self._wait_for_send_slot()
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
            body = response.json()
        except ValueError:
            raise RuntimeError("Telegram returned an invalid response") from None
        if not isinstance(body, dict) or not body.get("ok"):
            raise RuntimeError("Telegram rejected the alert")
        return body.get("result")

    def _wait_for_send_slot(self) -> None:
        now = time.monotonic()
        if self._last_send_at is not None:
            delay = MIN_SEND_INTERVAL_SECONDS - (now - self._last_send_at)
            if delay > 0:
                time.sleep(delay)
                now = time.monotonic()
        self._last_send_at = now


def format_listing(listing: RentalListing) -> str:
    parts = []
    plain_parts = []
    if listing.price_text:
        parts.append(f"<b>{escape(listing.price_text)}</b>")
        plain_parts.append(listing.price_text)
    parts.append(
        f'<a href="{escape(listing.url, quote=True)}">{escape(listing.title)}</a>'
    )
    plain_parts.append(listing.title)
    if listing.summary:
        parts.append(escape(listing.summary))
        plain_parts.append(listing.summary)
    if listing.seller_label:
        parts.append(f"Продавец: {escape(listing.seller_label)}")
        plain_parts.append(f"Продавец: {listing.seller_label}")
    if listing.published_text:
        parts.append(escape(listing.published_text))
        plain_parts.append(listing.published_text)
    if listing.updated_text:
        parts.append(escape(listing.updated_text))
        plain_parts.append(listing.updated_text)
    if listing.description:
        prefix = "Описание:\n"
        available = (
            MAX_CAPTION_LENGTH
            - len("\n".join(plain_parts))
            - 1
            - len(prefix)
        )
        if available > 0:
            description = _truncate(listing.description, available)
            parts.append(f"{prefix}{escape(description)}")
    return "\n".join(parts)


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    if limit == 1:
        return "…"
    return f"{value[:limit - 1].rstrip()}…"


def truncate_telegram_text(value: str, limit: int = MAX_MESSAGE_LENGTH) -> str:
    if _utf16_length(value) <= limit:
        return value
    remaining = limit - _utf16_length("…")
    characters = []
    for character in value:
        width = _utf16_length(character)
        if width > remaining:
            break
        characters.append(character)
        remaining -= width
    return f"{''.join(characters).rstrip()}…"


def _utf16_length(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def _message_id(result) -> int:
    message_id = result.get("message_id") if isinstance(result, dict) else None
    if type(message_id) is not int or message_id < 1:
        raise RuntimeError("Telegram returned an invalid message ID")
    return message_id
