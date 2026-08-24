from dataclasses import replace

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from models import RentalListing
from parser.list_am import parse_category_page, parse_listing_details


class ScanError(RuntimeError):
    pass


class ListAmScanner:
    def __init__(self, headless: bool = True, proxy_url: str = ""):
        self.headless = headless
        self.proxy_url = proxy_url
        self._playwright_context = None
        self.browser = None
        self.context = None
        self.page = None

    def __enter__(self):
        self._playwright_context = Stealth().use_sync(sync_playwright())
        playwright = self._playwright_context.__enter__()
        launch_options = {
            "headless": self.headless,
            "executable_path": playwright.chromium.executable_path,
            "args": ["--disable-blink-features=AutomationControlled"],
        }
        if self.proxy_url:
            launch_options["proxy"] = {"server": self.proxy_url}
        self.browser = playwright.chromium.launch(**launch_options)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.browser:
            self.browser.close()
        if self._playwright_context:
            self._playwright_context.__exit__(exc_type, exc_value, traceback)

    def scan(self, search_urls: list[str], max_pages: int) -> list[RentalListing]:
        listings = {}
        for search_url in search_urls:
            self.context = self.browser.new_context(locale="ru-RU")
            self.page = self.context.new_page()
            try:
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
                        raise ScanError(
                            f"List.am category content is missing at {current_url}"
                        )

                    parsed_page = parse_category_page(
                        self.page.content(),
                        current_url=self.page.url,
                    )
                    for listing in parsed_page.listings:
                        listings.setdefault(listing.id, listing)

                    if not parsed_page.next_url:
                        break
                    current_url = parsed_page.next_url
            finally:
                self.context.close()
                self.context = None
                self.page = None

        return list(listings.values())

    def add_details(self, listing: RentalListing) -> RentalListing:
        detail_context = self.browser.new_context(locale="ru-RU")
        detail_page = detail_context.new_page()
        try:
            detail_page.goto(
                listing.url,
                wait_until="domcontentloaded",
                timeout=60_000,
            )
            self._wait_for_challenge(detail_page)
            if self._is_challenge(detail_page):
                raise ScanError("List.am blocked detail extraction")

            details = parse_listing_details(detail_page.content())
            return replace(
                listing,
                title=details.title or listing.title,
                price_text=details.price_text or listing.price_text,
                published_text=details.published_text,
                updated_text=details.updated_text,
                description=details.description,
                image_urls=details.image_urls or listing.image_urls,
                detail_attributes=details.detail_attributes,
            )
        finally:
            detail_context.close()

    def _wait_for_challenge(self, page=None) -> None:
        page = page or self.page
        for _ in range(15):
            if not self._is_challenge(page):
                return
            page.wait_for_timeout(1_000)

    def _is_challenge(self, page=None) -> bool:
        page = page or self.page
        title = page.title().casefold()
        return (
            "один момент" in title
            or "just a moment" in title
            or "/cdn-cgi/challenge" in page.url
        )
