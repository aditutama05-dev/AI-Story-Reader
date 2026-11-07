from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

from bs4 import BeautifulSoup


NOISE_TOKEN = re.compile(
    r"(^|[-_\s])(advertisement|advert|ads|comment|comments|related|recommendations|"
    r"recommended|sidebar|breadcrumb|pagination|social|share|navigation|navbar|menu)([-_\s]|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ExtractedHTML:
    title: str
    text: str
    paragraph_count: int
    container: str


class SourceAdapter(Protocol):
    adapter_id: str
    version: str

    def supports(self, url: str) -> bool: ...
    def extract(self, raw: bytes, encoding: str | None = None) -> ExtractedHTML: ...


class GenericHTMLAdapter:
    adapter_id = "generic-html"
    version = "1"

    def supports(self, url: str) -> bool:
        return urlparse(url).scheme in {"http", "https"}

    def extract(self, raw: bytes, encoding: str | None = None) -> ExtractedHTML:
        soup = BeautifulSoup(raw, "html.parser", from_encoding=encoding)

        for node in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "form", "iframe"]):
            node.decompose()

        for node in list(soup.find_all(True)):
            marker = " ".join(
                [str(node.get("id", "")), " ".join(str(item) for item in (node.get("class") or []))]
            )
            if NOISE_TOKEN.search(marker) or node.get("role") in {"navigation", "complementary"}:
                node.decompose()

        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(" ", strip=True)
        if not title:
            og_title = soup.find("meta", attrs={"property": "og:title"})
            if og_title:
                title = str(og_title.get("content", "")).strip()
        if not title and soup.title:
            title = soup.title.get_text(" ", strip=True)

        candidates = []
        for selector in ("article", '[itemprop="articleBody"]', "main", '[role="main"]', "body"):
            candidates.extend(soup.select(selector))
        if not candidates:
            candidates = [soup]

        def score(node) -> tuple[float, int]:
            text = node.get_text("\n", strip=True)
            paragraphs = len(node.find_all("p"))
            linked = sum(len(link.get_text(" ", strip=True)) for link in node.find_all("a"))
            semantic_priority = 10000 if node.name == "article" else 5000 if node.name == "main" else 0
            return (len(text) + paragraphs * 120 - linked * 1.5 + semantic_priority, len(text))

        main = max(candidates, key=score)
        paragraphs = [p.get_text(" ", strip=True) for p in main.find_all("p")]
        if paragraphs:
            text = "\n\n".join(value for value in paragraphs if value)
        else:
            lines = [line.strip() for line in main.get_text("\n").splitlines()]
            text = "\n".join(line for line in lines if line)
        paragraph_count = (
            len([p for p in paragraphs if p])
            if paragraphs
            else len([line for line in text.splitlines() if line.strip()])
        )
        return ExtractedHTML(
            title=title,
            text=text.strip(),
            paragraph_count=paragraph_count,
            container=getattr(main, "name", "document"),
        )


class SourceAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: list[SourceAdapter] = []
        self._fallback: SourceAdapter = GenericHTMLAdapter()

    def register(self, adapter: SourceAdapter) -> None:
        self._adapters = [item for item in self._adapters if item.adapter_id != adapter.adapter_id]
        self._adapters.insert(0, adapter)

    def resolve(self, url: str) -> SourceAdapter:
        for adapter in self._adapters:
            if adapter.supports(url):
                return adapter
        return self._fallback


SOURCE_ADAPTERS = SourceAdapterRegistry()


def register_source_adapter(adapter: SourceAdapter) -> None:
    """Register a domain-specific adapter; newest registrations take precedence."""
    SOURCE_ADAPTERS.register(adapter)


def resolve_source_adapter(url: str) -> SourceAdapter:
    return SOURCE_ADAPTERS.resolve(url)


def extract_generic_html(raw: bytes, encoding: str | None = None) -> ExtractedHTML:
    return GenericHTMLAdapter().extract(raw, encoding)
