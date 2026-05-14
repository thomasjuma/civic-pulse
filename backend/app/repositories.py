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


def get_subscriber_by_whatsapp_number(
    connection: sqlite3.Connection,
    whatsapp_number: str,
) -> Subscriber | None:
    normalized_number = whatsapp_number.replace("+", "").replace(" ", "").replace("-", "")
    row = connection.execute(
        """
        SELECT id, clerk_user_id, email, whatsapp_number, has_whatsapp_consent, consented_at
        FROM subscribers
        WHERE whatsapp_number = ?
           OR REPLACE(REPLACE(REPLACE(whatsapp_number, '+', ''), ' ', ''), '-', '') = ?
        """,
        (whatsapp_number, normalized_number),
    ).fetchone()
    return _subscriber_from_row(row) if row else None


def get_latest_notified_article_for_subscriber(
    connection: sqlite3.Connection,
    subscriber_id: int,
) -> Article | None:
    row = connection.execute(
        """
        SELECT articles.id, articles.title, articles.source, articles.source_url,
               articles.summary, articles.full_text, articles.date, articles.image
        FROM article_notifications
        JOIN articles ON articles.id = article_notifications.article_id
        WHERE article_notifications.subscriber_id = ?
        ORDER BY article_notifications.sent_at DESC, article_notifications.id DESC
        LIMIT 1
        """,
        (subscriber_id,),
    ).fetchone()
    return _article_from_row(row) if row else None


def get_or_create_chat_conversation(
    connection: sqlite3.Connection,
    subscriber_id: int,
    article_id: int,
) -> int:
    now = _utc_now()
    connection.execute(
        """
        INSERT INTO chat_conversations (subscriber_id, article_id, started_at, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(subscriber_id, article_id)
        DO UPDATE SET updated_at = excluded.updated_at
        """,
        (subscriber_id, article_id, now, now),
    )
    row = connection.execute(
        """
        SELECT id
        FROM chat_conversations
        WHERE subscriber_id = ? AND article_id = ?
        """,
        (subscriber_id, article_id),
    ).fetchone()
    if row is None:
        raise RuntimeError("Chat conversation upsert failed")
    return int(row["id"])


def list_chat_messages(
    connection: sqlite3.Connection,
    conversation_id: int,
    limit: int = 10,
) -> list[dict[str, str]]:
    rows = connection.execute(
        """
        SELECT role, content
        FROM chat_messages
        WHERE conversation_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (conversation_id, limit),
    ).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def add_chat_message(
    connection: sqlite3.Connection,
    conversation_id: int,
    role: str,
    content: str,
    whatsapp_message_id: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO chat_messages (conversation_id, role, content, whatsapp_message_id)
        VALUES (?, ?, ?, ?)
        """,
        (conversation_id, role, content, whatsapp_message_id),
    )
    connection.execute(
        """
        UPDATE chat_conversations
        SET updated_at = ?
        WHERE id = ?
        """,
        (_utc_now(), conversation_id),
    )


def mark_article_notification_sent(
    connection: sqlite3.Connection,
    article_id: int,
    subscriber_id: int,
) -> None:
    now = _utc_now()
    connection.execute(
        """
        INSERT OR IGNORE INTO article_notifications (article_id, subscriber_id, sent_at)
        VALUES (?, ?, ?)
        """,
        (article_id, subscriber_id, now),
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO chat_conversations (subscriber_id, article_id, started_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (subscriber_id, article_id, now, now),
    )
