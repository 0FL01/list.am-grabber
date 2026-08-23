import json
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from models import RentalListing


CARD_TEST_ID = re.compile(r"^favorite-ad-card-(\d+)$")
CATEGORY_PATH = re.compile(r"^/(?:[a-z]{2}/)?category/(\d+)(?:/(\d+))?/?$")
ITEM_PATH = re.compile(r"^/(?:[a-z]{2}/)?item/(\d+)/?$")


@dataclass(frozen=True)
class CategoryPage:
    listings: list[RentalListing]
    next_url: str | None


@dataclass(frozen=True)
class ListingDetails:
    published_text: str
    updated_text: str
    description: str
    image_urls: tuple[str, ...]


def parse_listing_details(html: str) -> ListingDetails:
    soup = BeautifulSoup(html, "html.parser")
    published_element = soup.select_one('[itemprop="datePosted"]')
    updated_element = (
        published_element.find_next_sibling("span") if published_element else None
    )
    description_element = soup.select_one('[itemprop="description"]')
    if description_element:
        for translation_marker in description_element.select(".trans"):
            translation_marker.decompose()

    return ListingDetails(
        published_text=_text(published_element),
        updated_text=_text(updated_element),
        description=_text(description_element),
        image_urls=_detail_image_urls(soup),
    )


def parse_category_page(html: str, current_url: str) -> CategoryPage:
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    seen_ids = set()

    for card in soup.select('a[data-testid^="favorite-ad-card-"]'):
        test_id = card.get("data-testid", "")
        test_id_match = CARD_TEST_ID.fullmatch(test_id)
        href = card.get("href", "")
        item_match = ITEM_PATH.fullmatch(urlsplit(href).path)
        if not test_id_match or not item_match:
            continue

        listing_id = test_id_match.group(1)
        if listing_id != item_match.group(1) or listing_id in seen_ids:
            continue

        title_element = card.select_one(".l")
        if not title_element:
            continue

        seen_ids.add(listing_id)
        listings.append(
            RentalListing(
                id=listing_id,
                url=f"https://www.list.am/ru/item/{listing_id}",
                title=title_element.get_text(" ", strip=True),
                price_text=_text(card.select_one(".p")),
                summary=_text(card.select_one(".at")),
                seller_label=_text(card.select_one(".po69 .ge4")),
                image_urls=_image_urls(card.get("data-tslider", "")),
            )
        )

    return CategoryPage(
        listings=listings,
        next_url=_find_next_url(soup=soup, current_url=current_url),
    )


def _text(element) -> str:
    return element.get_text(" ", strip=True) if element else ""


def _image_urls(value: str) -> tuple[str, ...]:
    image_ids = [image_id.strip() for image_id in value.split(",")]
    return tuple(
        f"https://img.list.am/f/{image_id[-3:]}/{image_id}.webp"
        for image_id in image_ids[:10]
        if image_id.isdigit()
    )


def _detail_image_urls(soup: BeautifulSoup) -> tuple[str, ...]:
    decoder = json.JSONDecoder()
    for script in soup.find_all("script"):
        content = script.string or script.get_text()
        if "po99.init" not in content:
            continue

        key_position = content.find("img:")
        if key_position == -1:
            continue
        array_position = key_position + len("img:")
        while array_position < len(content) and content[array_position].isspace():
            array_position += 1
        if array_position >= len(content) or content[array_position] != "[":
            continue

        try:
            image_urls, _ = decoder.raw_decode(content, array_position)
        except json.JSONDecodeError:
            continue
        if not isinstance(image_urls, list):
            continue

        return tuple(
            _absolute_image_url(image_url)
            for image_url in image_urls[:10]
            if isinstance(image_url, str) and image_url
        )
    return ()


def _absolute_image_url(image_url: str) -> str:
    if image_url.startswith("//"):
        return f"https:{image_url}"
    return urljoin("https://www.list.am", image_url)


def _find_next_url(soup: BeautifulSoup, current_url: str) -> str | None:
    current_parts = urlsplit(current_url)
    current_match = CATEGORY_PATH.fullmatch(current_parts.path)
    if not current_match:
        return None

    category_id = current_match.group(1)
    current_page = int(current_match.group(2) or 1)
    candidates = []

    for link in soup.select(".dlf a[href]"):
        absolute_url = urljoin(current_url, link.get("href", ""))
        parts = urlsplit(absolute_url)
        match = CATEGORY_PATH.fullmatch(parts.path)
        if (
            parts.netloc != current_parts.netloc
            or not match
            or match.group(1) != category_id
            or not match.group(2)
        ):
            continue

        page_number = int(match.group(2))
        if page_number <= current_page:
            continue

        if not parts.query and current_parts.query:
            absolute_url = urlunsplit(
                (parts.scheme, parts.netloc, parts.path, current_parts.query, parts.fragment)
            )
        candidates.append((page_number, absolute_url))

    return min(candidates, default=(0, None), key=lambda candidate: candidate[0])[1]
