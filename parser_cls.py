import argparse
import signal
from pathlib import Path
from threading import Event

from loguru import logger

from db_service import ListingStateStore
from integrations.notifications.list_am_telegram import TelegramNotifier
from load_config import load_list_am_config
from parser.browser import ListAmScanner
from parser.pipeline import process_listings


def run_monitor(config_path: str, once: bool = False) -> int:
    config = load_list_am_config(config_path)
    notifier = TelegramNotifier(
        bot_token=config.telegram_bot_token,
        chat_id=config.telegram_chat_id,
    )
    state = ListingStateStore(str(config.database_path))
    stop_event = Event()

    def request_stop(_signal_number, _frame):
        stop_event.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    with ListAmScanner() as scanner:
        while not stop_event.is_set():
            try:
                listings = scanner.scan(config.search_urls, config.max_pages)

                def add_phone(listing):
                    try:
                        return scanner.add_phone(listing)
                    except Exception as error:
                        logger.warning(
                            "phone extraction failed for listing {}: {}",
                            listing.id,
                            error,
                        )
                        return listing

                result = process_listings(
                    listings,
                    state,
                    notifier.notify,
                    prepare=add_phone,
                )
                logger.info(
                    "scan parsed={} baselined={} delivered={} unchanged={}",
                    len(listings),
                    result.baselined,
                    result.delivered,
                    result.unchanged,
                )
            except Exception as error:
                logger.error("scan failed: {}", error)
                if once:
                    return 1

            if once:
                return 0
            stop_event.wait(config.poll_interval_seconds)

    return 0


def main() -> int:
    argument_parser = argparse.ArgumentParser(description="List.am rental monitor")
    argument_parser.add_argument(
        "--config",
        default="config.toml",
        help="Path to the List.am TOML config",
    )
    argument_parser.add_argument(
        "--once",
        action="store_true",
        help="Run one scan and exit",
    )
    arguments = argument_parser.parse_args()

    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/app.log", rotation="5 MB", retention="5 days")

    try:
        return run_monitor(config_path=arguments.config, once=arguments.once)
    except Exception as error:
        logger.error("startup failed: {}", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
