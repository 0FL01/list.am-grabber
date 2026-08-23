from dataclasses import replace

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from models import RentalListing
from parser.list_am import parse_category_page, parse_listing_dates


class ScanError(RuntimeError):
    pass


class ListAmScanner:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright_context = None
        self.browser = None
        self.context = None
        self.page = None
        self.details_blocked = False

    def __enter__(self):
        self._playwright_context = Stealth().use_sync(sync_playwright())
        playwright = self._playwright_context.__enter__()
        self.browser = playwright.chromium.launch(
            headless=self.headless,
            executable_path=playwright.chromium.executable_path,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.context = self.browser.new_context(locale="ru-RU")
        self.page = self.context.new_page()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.browser:
            self.browser.close()
        if self._playwright_context:
            self._playwright_context.__exit__(exc_type, exc_value, traceback)

    def scan(self, search_urls: list[str], max_pages: int) -> list[RentalListing]:
        listings = {}
        for search_url in search_urls:
            current_url = search_url
            visited_urls = set()

            for _ in range(max_pages):
                if current_url in visited_urls:
                    raise ScanError(f"Pagination loop at {current_url}")
                visited_urls.add(current_url)

                self.page.goto(
                    current_url,
                    wait_until="domcontentloaded",
                    timeout=60_000,
                )
                self._wait_for_challenge()
                if self._is_challenge():
                    raise ScanError("List.am blocked the headless browser")
                if not self.page.locator("h1").count():
                    raise ScanError(f"List.am category content is missing at {current_url}")

                parsed_page = parse_category_page(
                    self.page.content(),
                    current_url=self.page.url,
                )
                for listing in parsed_page.listings:
                    listings.setdefault(listing.id, listing)

                if not parsed_page.next_url:
                    break
                current_url = parsed_page.next_url

        return list(listings.values())

    def add_dates(self, listing: RentalListing) -> RentalListing:
        if self.details_blocked:
            return listing
        self.page.goto(
            listing.url,
            wait_until="domcontentloaded",
            timeout=60_000,
        )
        self._wait_for_challenge()
        if self._is_challenge():
            self.details_blocked = True
            raise ScanError("List.am blocked date extraction")

        published_text, updated_text = parse_listing_dates(self.page.content())
        return replace(
            listing,
            published_text=published_text,
            updated_text=updated_text,
        )

    def _wait_for_challenge(self) -> None:
        for _ in range(15):
            if not self._is_challenge():
                return
            self.page.wait_for_timeout(1_000)

    def _is_challenge(self) -> bool:
        title = self.page.title().casefold()
        return (
            "один момент" in title
            or "just a moment" in title
            or "/cdn-cgi/challenge" in self.page.url
        )
