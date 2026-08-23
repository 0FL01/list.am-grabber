from urllib.parse import urlsplit

from bs4 import BeautifulSoup, NavigableString
from markdown_it import MarkdownIt


_MARKDOWN = MarkdownIt(
    "commonmark",
    {"html": False, "linkify": False},
)
_ALLOWED_TAGS = {"a", "b", "code", "i", "pre"}


def render_telegram_markdown(value: str) -> tuple[str, str]:
    soup = BeautifulSoup(_MARKDOWN.render(value), "html.parser")
    for whitespace in soup.find_all(string=lambda text: not text.strip()):
        if not whitespace.find_parent("pre"):
            whitespace.extract()

    for element in soup.find_all("strong"):
        element.name = "b"
    for element in soup.find_all("em"):
        element.name = "i"
    for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        element.name = "b"
        element.insert_after(NavigableString("\n\n"))

    for list_element in reversed(soup.find_all(["ul", "ol"])):
        ordered = list_element.name == "ol"
        for index, item in enumerate(
            list_element.find_all("li", recursive=False),
            start=1,
        ):
            prefix = f"{index}. " if ordered else "• "
            item.insert(0, NavigableString(prefix))
            item.append(NavigableString("\n"))
            item.unwrap()
        list_element.insert_after(NavigableString("\n"))
        list_element.unwrap()

    for paragraph in soup.find_all("p"):
        paragraph.insert_after(NavigableString("\n\n"))
        paragraph.unwrap()
    for quote in soup.find_all("blockquote"):
        lines = quote.get_text().strip().splitlines()
        quote.replace_with(
            NavigableString("\n".join(f"> {line}" for line in lines) + "\n\n")
        )
    for line_break in soup.find_all("br"):
        next_element = line_break.next_sibling
        if isinstance(next_element, NavigableString) and next_element.startswith("\n"):
            next_element.replace_with(NavigableString(next_element[1:]))
        line_break.replace_with(NavigableString("\n"))
    for horizontal_rule in soup.find_all("hr"):
        horizontal_rule.replace_with(NavigableString("——\n"))
    for image in soup.find_all("img"):
        image.replace_with(NavigableString(image.get("alt", "")))

    for link in soup.find_all("a"):
        if not _safe_link(link.get("href", "")):
            link.unwrap()
        else:
            link.attrs = {"href": link["href"]}
    for element in soup.find_all(True):
        if element.name not in _ALLOWED_TAGS:
            element.unwrap()
        elif element.name != "a":
            element.attrs = {}

    plain_text = soup.get_text().strip()
    rendered = soup.decode().strip()
    return rendered, plain_text


def _safe_link(value: str) -> bool:
    try:
        parts = urlsplit(value)
        parts.port
    except ValueError:
        return False
    return (
        parts.scheme in {"http", "https"}
        and bool(parts.hostname)
        and parts.username is None
        and parts.password is None
    )
