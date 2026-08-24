import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from analyst import AnalystClient, AnalystError
from dto import AnalystConfig
from load_config import load_list_am_config
from models import RentalListing


def response(status=200, body=None, headers=None):
    result = Mock()
    result.status_code = status
    result.headers = headers or {}
    result.json.return_value = body if body is not None else {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": "Перспективно"},
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "completion_tokens_details": {"reasoning_tokens": 12},
        },
    }
    return result


class StopEvent:
    def __init__(self, stop_on_wait=False):
        self.stop_on_wait = stop_on_wait
        self.waits = []

    def is_set(self):
        return False

    def wait(self, delay):
        self.waits.append(delay)
        return self.stop_on_wait


class AnalystConfigTest(unittest.TestCase):
    def _load(self, analyst=""):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text(
                f"""
[telegram]
bot_token = "token"
chat_id = "123"

[list_am]
search_urls = ["https://www.list.am/ru/category/56"]

{analyst}
""".strip(),
                encoding="utf-8",
            )
            return load_list_am_config(str(path))

    def test_absent_and_disabled_are_off(self):
        self.assertFalse(self._load().analyst.enabled)
        self.assertFalse(
            self._load('[analyst]\nenabled = false\nbase_url = 7').analyst.enabled
        )

    def test_loads_arbitrary_model_and_effort(self):
        config = self._load(
            """
[analyst]
enabled = true
base_url = "https://llm.example.com/v1"
api_key = "secret"
model = "provider/custom-model"
vision = true
reasoning_effort = "provider-effort"
reply_format = "markdown"
max_images = 2
max_completion_tokens = 4096
retries = 4
prompt = "Проверь лот"
""".strip()
        ).analyst

        self.assertEqual(config.model, "provider/custom-model")
        self.assertEqual(config.reasoning_effort, "provider-effort")
        self.assertEqual(config.reply_format, "markdown")
        self.assertEqual(config.max_images, 2)
        self.assertEqual(config.retries, 4)

    def test_rejects_invalid_enabled_config(self):
        invalid_sections = (
            '[analyst]\nenabled = "true"',
            "[analyst]\nenabled = true",
            '[analyst]\nenabled = true\nbase_url = "https://user@llm.example/v1"\nmodel = "m"\nreasoning_effort = "high"\nprompt = "p"',
            '[analyst]\nenabled = true\nbase_url = "https://llm.example/v1?x=1"\nmodel = "m"\nreasoning_effort = "high"\nprompt = "p"',
            '[analyst]\nenabled = true\nbase_url = "https://llm.example/v1"\nmodel = "m"\nvision = 1\nreasoning_effort = "high"\nprompt = "p"',
            '[analyst]\nenabled = true\nbase_url = "https://llm.example/v1"\nmodel = "m"\nreasoning_effort = "high"\nreply_format = "html"\nprompt = "p"',
            '[analyst]\nenabled = true\nbase_url = "https://llm.example/v1"\nmodel = "m"\nreasoning_effort = "high"\nreply_format = ["markdown"]\nprompt = "p"',
            '[analyst]\nenabled = true\nbase_url = "https://llm.example/v1"\nmodel = "m"\nreasoning_effort = "high"\nmax_images = -1\nprompt = "p"',
        )
        for section in invalid_sections:
            with self.subTest(section=section), self.assertRaises(ValueError):
                self._load(section)


class AnalystClientTest(unittest.TestCase):
    def setUp(self):
        self.listing = RentalListing(
            id="123",
            url="https://www.list.am/ru/item/123",
            title="Дом",
            price_text="200,000 ֏",
            description="Тихий дом",
            detail_attributes=("Парковка — Нет",),
            image_urls=(
                "https://s.list.am/f/1.jpg",
                "https://img.list.am/f/2.jpg",
                "https://s.list.am/f/3.jpg",
            ),
        )

    def config(self, **changes):
        values = dict(
            enabled=True,
            base_url="https://llm.example/v1/",
            api_key="",
            model="any-model",
            vision=True,
            reasoning_effort="xhigh",
            max_images=0,
            max_completion_tokens=0,
            retries=3,
            prompt="Проверь",
        )
        values.update(changes)
        return AnalystConfig(**values)

    @patch("analyst.requests.post")
    def test_sends_exact_multimodal_payload_and_parses_usage(self, post):
        post.return_value = response()

        result = AnalystClient(self.config()).analyze(self.listing)

        self.assertEqual(post.call_args.args[0], "https://llm.example/v1/chat/completions")
        request = post.call_args.kwargs
        self.assertEqual(request["headers"], {"Content-Type": "application/json"})
        self.assertEqual(request["timeout"], (10, 300))
        payload = request["json"]
        self.assertEqual(payload["model"], "any-model")
        self.assertFalse(payload["store"])
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["reasoning_effort"], "xhigh")
        self.assertNotIn("max_completion_tokens", payload)
        self.assertEqual(payload["messages"][0], {"role": "developer", "content": "Проверь"})
        self.assertEqual(len(payload["messages"][1]["content"]), 4)
        self.assertIn("Парковка — Нет", payload["messages"][1]["content"][0]["text"])
        self.assertEqual(result.text, "Перспективно")
        self.assertEqual(result.image_count, 3)
        self.assertEqual(result.reasoning_tokens, 12)

    @patch("analyst.requests.post")
    def test_applies_image_and_completion_limits_with_auth(self, post):
        post.return_value = response()
        client = AnalystClient(
            self.config(api_key="secret", max_images=1, max_completion_tokens=4096)
        )

        client.analyze(self.listing)

        request = post.call_args.kwargs
        self.assertEqual(request["headers"]["Authorization"], "Bearer secret")
        self.assertEqual(request["json"]["max_completion_tokens"], 4096)
        self.assertEqual(len(request["json"]["messages"][1]["content"]), 2)

    @patch("analyst.requests.post")
    def test_retries_transient_errors_with_one_global_budget(self, post):
        post.side_effect = [
            requests.exceptions.ConnectionError("private detail"),
            response(408, {"error": {"code": "busy"}}),
            response(429, {"error": {"type": "rate_limit"}}, {"Retry-After": "15"}),
            response(),
        ]
        stop = StopEvent()

        result = AnalystClient(self.config()).analyze(self.listing, stop)

        self.assertEqual(post.call_count, 4)
        self.assertEqual(stop.waits, [5, 10, 20])
        self.assertEqual(result.attempts, 4)

    @patch("analyst.requests.post")
    def test_vision_fallback_consumes_global_attempt(self, post):
        post.side_effect = [
            response(415, {"error": {"code": "unsupported_image"}}),
            response(500, {"error": {"code": "server"}}),
        ]

        with self.assertRaisesRegex(AnalystError, "http_transient"):
            AnalystClient(self.config(retries=1)).analyze(self.listing, StopEvent())

        self.assertEqual(post.call_count, 2)
        second_content = post.call_args_list[1].kwargs["json"]["messages"][1]["content"]
        self.assertEqual(len(second_content), 1)

    @patch("analyst.requests.post")
    def test_retry_wait_is_interruptible(self, post):
        post.return_value = response(500, {"error": {"code": "busy"}})

        with self.assertRaisesRegex(AnalystError, "stopped"):
            AnalystClient(self.config()).analyze(
                self.listing, StopEvent(stop_on_wait=True)
            )

        self.assertEqual(post.call_count, 1)

    @patch("analyst.requests.post")
    def test_read_timeout_and_length_are_terminal(self, post):
        post.side_effect = requests.exceptions.ReadTimeout("private detail")
        with self.assertRaisesRegex(AnalystError, "read_timeout"):
            AnalystClient(self.config()).analyze(self.listing)
        self.assertEqual(post.call_count, 1)

        post.reset_mock()
        post.side_effect = None
        post.return_value = response(
            body={
                "choices": [
                    {"finish_reason": "length", "message": {"content": "partial"}}
                ]
            }
        )
        with self.assertRaisesRegex(AnalystError, "completion_length"):
            AnalystClient(self.config()).analyze(self.listing)
        self.assertEqual(post.call_count, 1)

    @patch("analyst.requests.post")
    def test_malformed_json_retries_only_once(self, post):
        broken_one = response()
        broken_one.json.side_effect = ValueError("secret body")
        broken_two = response()
        broken_two.json.side_effect = ValueError("secret body")
        post.side_effect = [broken_one, broken_two]

        with self.assertRaisesRegex(AnalystError, "malformed_json") as caught:
            AnalystClient(self.config()).analyze(self.listing, StopEvent())

        self.assertEqual(post.call_count, 2)
        self.assertNotIn("secret", str(caught.exception))

    @patch("analyst.requests.post")
    def test_long_retry_after_sets_client_cooldown(self, post):
        post.return_value = response(
            429,
            {"error": {"code": "temporary_rate_limit"}},
            {"Retry-After": "120", "x-request-id": "req\nprivate"},
        )
        client = AnalystClient(self.config())

        with self.assertRaisesRegex(AnalystError, "cooldown") as caught:
            client.analyze(self.listing)
        with self.assertRaisesRegex(AnalystError, "cooldown"):
            client.analyze(self.listing)

        self.assertEqual(post.call_count, 1)
        self.assertEqual(caught.exception.request_id, "reqprivate")

    @patch("analyst.requests.post")
    def test_permanent_quota_error_is_terminal(self, post):
        post.return_value = response(
            429,
            {"error": {"code": "insufficient_quota", "message": "secret body"}},
        )

        with self.assertRaisesRegex(AnalystError, "quota_exhausted") as caught:
            AnalystClient(self.config()).analyze(self.listing)

        self.assertEqual(post.call_count, 1)
        self.assertNotIn("secret", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
