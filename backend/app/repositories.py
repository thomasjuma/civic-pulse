import sqlite3
from datetime import UTC, datetime

from app.models import Article, ArticleCreate, Subscriber, SubscriberUpsert


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _article_from_row(row: sqlite3.Row) -> Article:
    return Article(
        id=row["id"],
        title=row["title"],
        source=row["source"],
        source_url=row["source_url"],
        summary=row["summary"],
        full_text=row["full_text"],
        date=row["date"],
        image=row["image"],
    )


def _subscriber_from_row(row: sqlite3.Row) -> Subscriber:
    return Subscriber(
        id=row["id"],
        clerk_user_id=row["clerk_user_id"],
        email=row["email"],
        whatsapp_number=row["whatsapp_number"],
        has_whatsapp_consent=bool(row["has_whatsapp_consent"]),
        consented_at=row["consented_at"],
    )


def list_articles(connection: sqlite3.Connection) -> list[Article]:
    rows = connection.execute(
        """
        SELECT id, title, source, source_url, summary, full_text, date, image
        FROM articles
        ORDER BY date DESC, id DESC
        """
    ).fetchall()
    return [_article_from_row(row) for row in rows]


def get_article(connection: sqlite3.Connection, article_id: int) -> Article | None:
    row = connection.execute(
        """
        SELECT id, title, source, source_url, summary, full_text, date, image
        FROM articles
        WHERE id = ?
        """,
        (article_id,),
    ).fetchone()
    return _article_from_row(row) if row else None


def upsert_article(connection: sqlite3.Connection, article: ArticleCreate) -> Article:
    now = _utc_now()
    connection.execute(
        """
        INSERT INTO articles (title, source, source_url, summary, full_text, date, image, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source, title)
        DO UPDATE SET
            source_url = excluded.source_url,
            summary = excluded.summary,
            full_text = excluded.full_text,
            date = excluded.date,
            image = excluded.image,
            updated_at = excluded.updated_at
        """,
        (
            article.title,
            article.source,
            article.source_url,
            article.summary,
            article.full_text,
            article.date,
            article.image,
            now,
            now,
        ),
    )
    row = connection.execute(
        """
        SELECT id, title, source, source_url, summary, full_text, date, image
        FROM articles
        WHERE source = ? AND title = ?
        """,
        (article.source, article.title),
    ).fetchone()
    if row is None:
        raise RuntimeError("Article upsert failed")
    return _article_from_row(row)


def upsert_subscriber(connection: sqlite3.Connection, subscriber: SubscriberUpsert) -> Subscriber:
    now = _utc_now()
    consented_at = now if subscriber.has_whatsapp_consent else None
    connection.execute(
        """
        INSERT INTO subscribers (
            clerk_user_id, email, whatsapp_number, has_whatsapp_consent, consented_at, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(email, whatsapp_number)
        DO UPDATE SET
            clerk_user_id = excluded.clerk_user_id,
            has_whatsapp_consent = excluded.has_whatsapp_consent,
            consented_at = excluded.consented_at,
            updated_at = excluded.updated_at
        """,
        (
            subscriber.clerk_user_id,
            str(subscriber.email),
            subscriber.whatsapp_number,
            int(subscriber.has_whatsapp_consent),
            consented_at,
            now,
            now,
        ),
    )
    row = connection.execute(
        """
        SELECT id, clerk_user_id, email, whatsapp_number, has_whatsapp_consent, consented_at
        FROM subscribers
        WHERE email = ? AND whatsapp_number = ?
        """,
        (str(subscriber.email), subscriber.whatsapp_number),
    ).fetchone()
    if row is None:
        raise RuntimeError("Subscriber upsert failed")
    return _subscriber_from_row(row)


def list_consenting_subscribers(connection: sqlite3.Connection, article_id: int) -> list[Subscriber]:
    rows = connection.execute(
        """
        SELECT id, clerk_user_id, email, whatsapp_number, has_whatsapp_consent, consented_at
        FROM subscribers
        WHERE has_whatsapp_consent = 1
          AND id NOT IN (
              SELECT subscriber_id FROM article_notifications WHERE article_id = ?
          )
        """,
        (article_id,),
    ).fetchall()
    return [_subscriber_from_row(row) for row in rows]


def mark_article_notification_sent(
    connection: sqlite3.Connection,
    article_id: int,
    subscriber_id: int,
) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO article_notifications (article_id, subscriber_id)
        VALUES (?, ?)
        """,
        (article_id, subscriber_id),
    )

