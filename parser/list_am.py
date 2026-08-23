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


def normalize_phone(value: str) -> str:
    digits = "".join(character for character in value if character.isdigit())
    if len(digits) == 11 and digits.startswith("374"):
        return f"+{digits}"
    if len(digits) == 9 and digits.startswith("0"):
        return f"+374{digits[1:]}"
    if len(digits) == 8:
        return f"+374{digits}"
    return ""


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
            )
        )

    return CategoryPage(
        listings=listings,
        next_url=_find_next_url(soup=soup, current_url=current_url),
    )


def _text(element) -> str:
    return element.get_text(" ", strip=True) if element else ""


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
