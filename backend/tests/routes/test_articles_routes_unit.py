from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi import HTTPException

from app.models import Article
from app.routes import articles


@contextmanager
def _connection() -> Iterator[object]:
    yield object()


def _article(article_id: int = 1) -> Article:
    return Article(
        id=article_id,
        title="Audit Report",
        source="oagkenya.go.ke",
        source_url="https://example.test/report",
        summary="A formal summary.",
        full_text="The complete report text.",
        date="2026-05-13",
        image="",
    )


def test_read_articles_returns_articles(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = [_article()]
    monkeypatch.setattr(articles, "get_connection", _connection)
    monkeypatch.setattr(articles, "list_articles", lambda connection: expected)

    assert articles.read_articles() == expected


def test_read_article_returns_article(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = _article(article_id=5)
    monkeypatch.setattr(articles, "get_connection", _connection)
    monkeypatch.setattr(articles, "get_article", lambda connection, article_id: expected)

    assert articles.read_article(5) == expected


def test_read_article_raises_404_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(articles, "get_connection", _connection)
    monkeypatch.setattr(articles, "get_article", lambda connection, article_id: None)

    with pytest.raises(HTTPException) as exc_info:
        articles.read_article(999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Article not found"

