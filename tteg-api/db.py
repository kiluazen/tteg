"""Database operations for tteg-api billing and rate limiting."""
from __future__ import annotations

import os
import secrets
from datetime import date

import psycopg2
from psycopg2.extras import RealDictCursor

FREE_DAILY_LIMIT = 50


def _get_conn():
    url = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("SUPABASE_CONNECTION_STRING")
    )
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(url, connect_timeout=3)


def validate_api_key(key: str) -> str | None:
    """Return plan name if key is valid and active, else None."""
    try:
        conn = _get_conn()
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT plan FROM api_keys WHERE key = %s AND active = TRUE",
                (key,),
            )
            row = cur.fetchone()
            return row["plan"] if row else None
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def check_and_increment_usage(ip: str) -> tuple[bool, int]:
    """
    Increment daily usage counter for the given IP.
    Returns (allowed, current_count).
    Fails open: if the DB is unreachable, allows the request.
    """
    try:
        conn = _get_conn()
        today = date.today().isoformat()
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO daily_usage (ip, date, count)
                VALUES (%s, %s, 1)
                ON CONFLICT (ip, date)
                DO UPDATE SET count = daily_usage.count + 1
                RETURNING count
                """,
                (ip, today),
            )
            count: int = cur.fetchone()["count"]
            return count <= FREE_DAILY_LIMIT, count
    except Exception:
        return True, 0  # fail open
    finally:
        try:
            conn.close()
        except Exception:
            pass


def create_api_key(
    email: str,
    plan: str,
    subscription_id: str,
    checkout_session_id: str | None = None,
) -> str:
    """Generate and persist a new API key. Returns the raw key."""
    key = f"tteg_{secrets.token_urlsafe(32)}"
    conn = _get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_keys
                    (key, email, plan, stripe_subscription_id, stripe_checkout_session_id, active)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                """,
                (key, email, plan, subscription_id, checkout_session_id),
            )
        return key
    finally:
        conn.close()


def get_key_for_session(stripe_session_id: str) -> str | None:
    """Look up an API key by the Stripe checkout session ID."""
    try:
        conn = _get_conn()
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT key FROM api_keys WHERE stripe_checkout_session_id = %s AND active = TRUE",
                (stripe_session_id,),
            )
            row = cur.fetchone()
            return row["key"] if row else None
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def deactivate_subscription(subscription_id: str) -> None:
    """Mark all keys for a subscription as inactive."""
    try:
        conn = _get_conn()
        with conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE api_keys SET active = FALSE WHERE stripe_subscription_id = %s",
                (subscription_id,),
            )
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
