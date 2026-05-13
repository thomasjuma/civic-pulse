from fastapi import APIRouter, HTTPException

from app.database import get_connection
from app.models import Article
from app.repositories import get_article, list_articles

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=list[Article])
def read_articles() -> list[Article]:
    with get_connection() as connection:
        return list_articles(connection)


@router.get("/{article_id}", response_model=Article)
def read_article(article_id: int) -> Article:
    with get_connection() as connection:
        article = get_article(connection, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

