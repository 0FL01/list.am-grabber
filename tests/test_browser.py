import unittest
from unittest.mock import MagicMock, patch

from parser.browser import ListAmScanner


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


if __name__ == "__main__":
    unittest.main()
