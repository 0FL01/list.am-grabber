import argparse
import signal
from pathlib import Path
from threading import Event

from loguru import logger

from analyst import AnalysisResult, AnalystClient, AnalystError
from db_service import ListingStateStore
from integrations.notifications.list_am_telegram import (
    TelegramNotifier,
    truncate_telegram_text,
)
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
    analyst = AnalystClient(config.analyst) if config.analyst.enabled else None
    if analyst:
        logger.info(
            "analyst enabled model={} vision={} reply_format={} max_images={} max_completion_tokens={} retries={}",
            config.analyst.model,
            config.analyst.vision,
            config.analyst.reply_format,
            config.analyst.max_images or "all",
            config.analyst.max_completion_tokens or "provider-default",
            config.analyst.retries,
        )

    def request_stop(_signal_number, _frame):
        stop_event.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    while not stop_event.is_set():
        try:
            analysis_jobs = []
            with ListAmScanner() as scanner:
                listings = scanner.scan(config.search_urls, config.max_pages)

                def add_details(listing):
                    try:
                        return scanner.add_details(listing)
                    except Exception as error:
                        logger.warning(
                            "detail extraction failed for listing {}: {}",
                            listing.id,
                            error,
                        )
                        return listing

                def queue_analysis(listing, message_id):
                    analysis_jobs.append((listing, message_id))

                result = process_listings(
                    listings,
                    state,
                    notifier.notify,
                    enrich=add_details,
                    after_delivery=queue_analysis if analyst else None,
                    notify_existing_on_first_run=config.notify_existing_on_first_run,
                    delivery_jitter_seconds=(1.0, 2.0),
                )
            logger.info(
                "scan parsed={} baselined={} delivered={} unchanged={}",
                len(listings),
                result.baselined,
                result.delivered,
                result.unchanged,
            )
            if analyst:
                _run_analyses(
                    analyst,
                    notifier,
                    analysis_jobs,
                    stop_event,
                    config.analyst.model,
                    config.analyst.reply_format,
                )
        except Exception as error:
            logger.error("scan failed: {}", error)
            if once:
                return 1

        if once:
            return 0
        stop_event.wait(config.poll_interval_seconds)

    return 0


def _run_analyses(
    analyst: AnalystClient,
    notifier: TelegramNotifier,
    jobs: list[tuple],
    stop_event: Event,
    model: str,
    reply_format: str = "plain",
) -> None:
    for listing, message_id in jobs:
        if stop_event.is_set():
            return
        try:
            result = analyst.analyze(listing, stop_event)
        except AnalystError as error:
            logger.warning(
                "analyst failed listing={} reason={} status={} provider_code={} request_id={}",
                listing.id,
                error.reason,
                error.status,
                error.provider_code,
                error.request_id,
            )
            continue
        except Exception as error:
            logger.warning(
                "analyst failed listing={} reason=unexpected error_type={}",
                listing.id,
                type(error).__name__,
            )
            continue

        try:
            reply_id = notifier.reply(message_id, result.text, reply_format)
        except Exception as error:
            logger.warning(
                "analyst reply failed listing={} reply_to={} error_type={}",
                listing.id,
                message_id,
                type(error).__name__,
            )
            continue
        reply_text = truncate_telegram_text(result.text)
        _log_analysis_success(listing.id, message_id, reply_id, model, result, reply_text)


def _log_analysis_success(
    listing_id: str,
    message_id: int,
    reply_id: int | None,
    model: str,
    result: AnalysisResult,
    reply_text: str,
) -> None:
    logger.info(
        "analyst delivered listing={} model={} mode={} images={} attempts={} latency_ms={} prompt_tokens={} completion_tokens={} reasoning_tokens={} visible_chars={} reply_to={} reply_id={}",
        listing_id,
        model,
        result.mode,
        result.image_count,
        result.attempts,
        result.latency_ms,
        result.prompt_tokens,
        result.completion_tokens,
        result.reasoning_tokens,
        len(reply_text),
        message_id,
        reply_id,
    )


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
