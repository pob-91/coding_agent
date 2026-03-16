from dataclasses import dataclass

import requests
from ddgs import DDGS
from html_to_markdown import convert

from utils.logger import get_logger

logger = get_logger(__name__)


def search(phrase: str, max_results: int = 10) -> list[dict[str, str]]:
    results = DDGS().text(phrase, max_results=max_results)
    return results


@dataclass
class WebResult:
    status_code: int
    body: str


def visit_webpage(url: str) -> WebResult:
    result = requests.get(url=url)
    if result.status_code != 200:
        return WebResult(
            status_code=result.status_code,
            body="",
        )

    return WebResult(
        status_code=200,
        body=convert(result.text),
    )
