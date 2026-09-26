import os
from datetime import datetime, timezone

import psycopg


DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    return psycopg.connect(
        DATABASE_URL,
        connect_timeout=10,
    )


def init_database():
    """
    Creates the orders table if it doesn't exist.

    There is no credit/balance system.
    Each approved order represents exactly one generation.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS email_orders (
                    id BIGSERIAL PRIMARY KEY,

                    order_id VARCHAR(32) UNIQUE NOT NULL,

                    telegram_user_id BIGINT NOT NULL,

                    quantity BIGINT NOT NULL,

                    price_usd NUMERIC(12, 2) NOT NULL,

                    crypto VARCHAR(32) NOT NULL,

                    payment_address TEXT NOT NULL,

                    tx_hash TEXT,

                    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',

                    generation_used BOOLEAN NOT NULL DEFAULT FALSE,

                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

                    paid_at TIMESTAMPTZ,

                    approved_at TIMESTAMPTZ,

                    generated_at TIMESTAMPTZ,

                    rejected_at TIMESTAMPTZ
                )
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_email_orders_user
                ON email_orders (telegram_user_id)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_email_orders_status
                ON email_orders (status)
                """
            )

            conn.commit()


def create_order(
    order_id,
    telegram_user_id,
    quantity,
    price_usd,
    crypto,
    payment_address,
):
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO email_orders (
                    order_id,
                    telegram_user_id,
                    quantity,
                    price_usd,
                    crypto,
                    payment_address
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    order_id,
                    telegram_user_id,
                    quantity,
                    price_usd,
                    crypto,
                    payment_address,
                ),
            )

            conn.commit()


def get_order(order_id):
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    order_id,
                    telegram_user_id,
                    quantity,
                    price_usd,
                    crypto,
                    payment_address,
                    tx_hash,
                    status,
                    generation_used,
                    created_at,
                    paid_at,
                    approved_at,
                    generated_at,
                    rejected_at
                FROM email_orders
                WHERE order_id = %s
                """,
                (order_id,),
            )

            row = cur.fetchone()

            if not row:
                return None

            columns = [
                "id",
                "order_id",
                "telegram_user_id",
                "quantity",
                "price_usd",
                "crypto",
                "payment_address",
                "tx_hash",
                "status",
                "generation_used",
                "created_at",
                "paid_at",
                "approved_at",
                "generated_at",
                "rejected_at",
            ]

            return dict(zip(columns, row))


def attach_tx_hash(order_id, tx_hash):
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE email_orders
                SET
                    tx_hash = %s,
                    status = 'PAYMENT_SUBMITTED',
                    paid_at = NOW()
                WHERE order_id = %s
                  AND status = 'PENDING'
                """,
                (
                    tx_hash,
                    order_id,
                ),
            )

            updated = cur.rowcount

            conn.commit()

            return updated == 1


def approve_order(order_id):
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE email_orders
                SET
                    status = 'APPROVED',
                    approved_at = NOW()
                WHERE order_id = %s
                  AND status = 'PAYMENT_SUBMITTED'
                  AND generation_used = FALSE
                """,
                (order_id,),
            )

            updated = cur.rowcount

            conn.commit()

            return updated == 1


def reject_order(order_id):
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE email_orders
                SET
                    status = 'REJECTED',
                    rejected_at = NOW()
                WHERE order_id = %s
                  AND status = 'PAYMENT_SUBMITTED'
                """,
                (order_id,),
            )

            updated = cur.rowcount

            conn.commit()

            return updated == 1


def claim_generation(order_id, telegram_user_id):
    """
    Atomically consumes the ONE generation.

    This is the important protection against double-clicks,
    retries, or two simultaneous requests.

    Returns the order if successfully claimed.
    Returns None if it was already used or isn't approved.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE email_orders
                SET
                    generation_used = TRUE,
                    status = 'GENERATING',
                    generated_at = NOW()
                WHERE order_id = %s
                  AND telegram_user_id = %s
                  AND status = 'APPROVED'
                  AND generation_used = FALSE
                RETURNING
                    order_id,
                    telegram_user_id,
                    quantity,
                    price_usd,
                    crypto
                """,
                (
                    order_id,
                    telegram_user_id,
                ),
            )

            row = cur.fetchone()

            if not row:
                conn.rollback()
                return None

            conn.commit()

            return {
                "order_id": row[0],
                "telegram_user_id": row[1],
                "quantity": row[2],
                "price_usd": float(row[3]),
                "crypto": row[4],
            }


def mark_generation_complete(order_id):
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE email_orders
                SET status = 'COMPLETED'
                WHERE order_id = %s
                  AND status = 'GENERATING'
                """,
                (order_id,),
            )

            conn.commit()


def mark_generation_failed(order_id):
    """
    If generation fails after the order was claimed,
    put the order into GENERATION_FAILED.

    This does NOT automatically give another generation.
    Admin can inspect the failed order and decide what to do.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE email_orders
                SET status = 'GENERATION_FAILED'
                WHERE order_id = %s
                  AND status = 'GENERATING'
                """,
                (order_id,),
            )

            conn.commit()


def get_latest_user_order(telegram_user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    order_id,
                    quantity,
                    price_usd,
                    crypto,
                    status,
                    generation_used,
                    created_at
                FROM email_orders
                WHERE telegram_user_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (telegram_user_id,),
            )

            row = cur.fetchone()

            if not row:
                return None

            return {
                "order_id": row[0],
                "quantity": row[1],
                "price_usd": float(row[2]),
                "crypto": row[3],
                "status": row[4],
                "generation_used": row[5],
                "created_at": row[6],
            }