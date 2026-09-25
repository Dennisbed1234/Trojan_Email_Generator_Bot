import sqlite3
from pathlib import Path

DB_PATH = Path("bot.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            domain TEXT NOT NULL DEFAULT 'example.test',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


def ensure_user(user_id: int):
    connection = get_connection()

    connection.execute(
        """
        INSERT OR IGNORE INTO users (user_id)
        VALUES (?)
        """,
        (user_id,),
    )

    connection.commit()
    connection.close()


def get_domain(user_id: int) -> str:
    connection = get_connection()

    row = connection.execute(
        """
        SELECT domain
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

    connection.close()

    if row:
        return row["domain"]

    return "example.test"


def set_domain(user_id: int, domain: str):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO users (user_id, domain)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET domain = excluded.domain
        """,
        (user_id, domain),
    )

    connection.commit()
    connection.close()