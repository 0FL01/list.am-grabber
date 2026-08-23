import tomllib
from pathlib import Path

from dto import AvitoConfig, ListAmConfig


def load_list_am_config(path: str = "config.toml") -> ListAmConfig:
    with open(path, "rb") as file:
        section = tomllib.load(file)["list_am"]

    config = ListAmConfig(
        search_urls=section.get("search_urls", []),
        max_pages=section.get("max_pages", 1),
        poll_interval_seconds=section.get("poll_interval_seconds", 60),
        database_path=Path(section.get("database_path", "data/listings.db")),
    )
    _validate_list_am_config(config)
    return config


def _validate_list_am_config(config: ListAmConfig) -> None:
    from urllib.parse import urlsplit

    if not config.search_urls:
        raise ValueError("At least one List.am search URL is required")
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


def load_avito_config(path: str = "config.toml") -> AvitoConfig:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return AvitoConfig(**data["avito"])


def save_avito_config(config: dict):
    import tomli_w

    with Path("config.toml").open("wb") as f:
        tomli_w.dump(config, f)
