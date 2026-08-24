import unittest
from unittest.mock import MagicMock, patch

from parser.browser import ListAmScanner
from parser.list_am import CategoryPage


class BrowserTest(unittest.TestCase):
    @patch("parser.browser.Stealth")
    @patch("parser.browser.sync_playwright")
    def test_launches_chromium_with_configured_proxy(self, sync_playwright, stealth):
        playwright_context = MagicMock()
        playwright = playwright_context.__enter__.return_value
        stealth.return_value.use_sync.return_value = playwright_context

        with ListAmScanner(proxy_url="socks5://172.25.0.1:40000"):
            pass

        sync_playwright.assert_called_once_with()
        launch_options = playwright.chromium.launch.call_args.kwargs
        self.assertEqual(
            launch_options["proxy"],
            {"server": "socks5://172.25.0.1:40000"},
        )

    @patch("parser.browser.parse_category_page")
    @patch("parser.browser.Stealth")
    @patch("parser.browser.sync_playwright")
    def test_uses_a_fresh_context_for_each_search_url(
        self,
        sync_playwright,
        stealth,
        parse_category_page,
    ):
        playwright_context = MagicMock()
        playwright = playwright_context.__enter__.return_value
        stealth.return_value.use_sync.return_value = playwright_context
        browser = playwright.chromium.launch.return_value
        contexts = [MagicMock(), MagicMock()]
        pages = [context.new_page.return_value for context in contexts]
        browser.new_context.side_effect = contexts
        for page, url in zip(pages, ("https://first", "https://second")):
            page.url = url
            page.locator.return_value.count.return_value = 1
        parse_category_page.return_value = CategoryPage([], None, is_empty=True)

        with ListAmScanner() as scanner, patch.object(
            scanner,
            "_wait_for_challenge",
        ), patch.object(scanner, "_is_challenge", return_value=False):
            listings = scanner.scan(["https://first", "https://second"], 1)

        self.assertEqual(listings, [])
        self.assertEqual(browser.new_context.call_count, 2)
        pages[0].goto.assert_called_once_with(
            "https://first",
            wait_until="domcontentloaded",
            timeout=60_000,
        )
        pages[1].goto.assert_called_once_with(
            "https://second",
            wait_until="domcontentloaded",
            timeout=60_000,
        )
        for context in contexts:
            context.close.assert_called_once_with()

    @patch("parser.browser.parse_category_page")
    @patch("parser.browser.Stealth")
    @patch("parser.browser.sync_playwright")
    def test_rejects_a_page_without_cards_or_empty_state(
        self,
        sync_playwright,
        stealth,
        parse_category_page,
    ):
        playwright_context = MagicMock()
        playwright = playwright_context.__enter__.return_value
        stealth.return_value.use_sync.return_value = playwright_context
        browser = playwright.chromium.launch.return_value
        context = browser.new_context.return_value
        page = context.new_page.return_value
        page.url = "https://www.list.am/"
        page.locator.return_value.count.return_value = 1
        parse_category_page.return_value = CategoryPage([], None)

        with ListAmScanner() as scanner, patch.object(
            scanner,
            "_wait_for_challenge",
        ), patch.object(scanner, "_is_challenge", return_value=False):
            with self.assertRaisesRegex(
                RuntimeError,
                "category listings are missing.*final URL",
            ):
                scanner.scan(["https://category"], 1)

        context.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
