import tomllib
from pathlib import Path

from dto import AnalystConfig, AvitoConfig, ListAmConfig


def load_list_am_config(path: str = "config.toml") -> ListAmConfig:
    with open(path, "rb") as file:
        data = tomllib.load(file)
    section = data["list_am"]
    telegram = data["telegram"]

    config = ListAmConfig(
        search_urls=section.get("search_urls", []),
        telegram_bot_token=telegram.get("bot_token", ""),
        telegram_chat_id=str(telegram.get("chat_id", "")),
        notify_existing_on_first_run=section.get(
            "notify_existing_on_first_run", False
        ),
        max_pages=section.get("max_pages", 1),
        poll_interval_seconds=section.get("poll_interval_seconds", 60),
        database_path=Path(section.get("database_path", "data/listings.db")),
        analyst=_load_analyst_config(data.get("analyst")),
    )
    _validate_list_am_config(config)
    return config


def _validate_list_am_config(config: ListAmConfig) -> None:
    from urllib.parse import urlsplit

    if not config.search_urls:
        raise ValueError("At least one List.am search URL is required")
    if not config.telegram_bot_token or not config.telegram_chat_id:
        raise ValueError("Telegram bot token and chat ID are required")
    for url in config.search_urls:
        parts = urlsplit(url)
        if (
            parts.scheme != "https"
            or parts.netloc not in {"list.am", "www.list.am"}
            or "/category/" not in parts.path
        ):
            raise ValueError(f"Unsupported List.am search URL: {url}")
    if config.max_pages < 1:
        raise ValueError("max_pages must be at least 1")
    if config.poll_interval_seconds < 1:
        raise ValueError("poll_interval_seconds must be at least 1")


def _load_analyst_config(section) -> AnalystConfig:
    if section is None:
        return AnalystConfig()
    if not isinstance(section, dict):
        raise ValueError("analyst must be a TOML table")

    enabled = section.get("enabled", False)
    if type(enabled) is not bool:
        raise ValueError("analyst.enabled must be a boolean")
    if not enabled:
        return AnalystConfig()

    string_values = {}
    for name in ("base_url", "api_key", "model", "reasoning_effort", "prompt"):
        value = section.get(name, "")
        if not isinstance(value, str):
            raise ValueError(f"analyst.{name} must be a string")
        string_values[name] = value
    for name in ("base_url", "model", "reasoning_effort", "prompt"):
        if not string_values[name].strip():
            raise ValueError(f"analyst.{name} is required when analyst is enabled")

    vision = section.get("vision", True)
    if type(vision) is not bool:
        raise ValueError("analyst.vision must be a boolean")

    numeric_values = {}
    for name, default in (
        ("max_images", 0),
        ("max_completion_tokens", 0),
        ("retries", 3),
    ):
        value = section.get(name, default)
        if type(value) is not int or value < 0:
            raise ValueError(f"analyst.{name} must be a non-negative integer")
        numeric_values[name] = value

    from urllib.parse import urlsplit

    try:
        parts = urlsplit(string_values["base_url"])
        port = parts.port
    except ValueError as error:
        raise ValueError("analyst.base_url is invalid") from error
    if (
        parts.scheme not in {"http", "https"}
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
        or port is not None and not 1 <= port <= 65535
    ):
        raise ValueError("analyst.base_url must be an absolute HTTP(S) API root")

    return AnalystConfig(
        enabled=True,
        vision=vision,
        **string_values,
        **numeric_values,
    )


def load_avito_config(path: str = "config.toml") -> AvitoConfig:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return AvitoConfig(**data["avito"])


def save_avito_config(config: dict):
    import tomli_w

    with Path("config.toml").open("wb") as f:
        tomli_w.dump(config, f)
