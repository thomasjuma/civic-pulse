import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.config import Settings, get_settings

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def resolve_database_path(settings: Settings | None = None) -> Path:
    active_settings = settings or get_settings()
    path = active_settings.database_path
    if not path.is_absolute():
        path = BACKEND_ROOT / path
    return path


@contextmanager
def get_connection(settings: Settings | None = None) -> Iterator[sqlite3.Connection]:
    database_path = resolve_database_path(settings)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db(settings: Settings | None = None) -> None:
    with get_connection(settings) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                source_url TEXT,
                summary TEXT NOT NULL,
                full_text TEXT NOT NULL,
                date TEXT NOT NULL,
                image TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, title)
            );

            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clerk_user_id TEXT,
                email TEXT NOT NULL,
                whatsapp_number TEXT NOT NULL,
                has_whatsapp_consent INTEGER NOT NULL DEFAULT 0,
                consented_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(email, whatsapp_number)
            );

            CREATE TABLE IF NOT EXISTS article_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                subscriber_id INTEGER NOT NULL,
                sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE,
                FOREIGN KEY(subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE,
                UNIQUE(article_id, subscriber_id)
            );
            """
        )
