"""Database operations for tteg-api — user auth and rate limiting."""
from __future__ import annotations

import os
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


def verify_supabase_token(token: str) -> dict | None:
    """
    Verify a Supabase JWT by querying auth.users.
    Returns {"id": uuid, "email": str} if valid, None otherwise.
    """
    try:
        conn = _get_conn()
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Supabase stores sessions — verify the token maps to a live user
            # We use the Supabase auth schema directly
            cur.execute(
                """
                SELECT au.id, au.email
                FROM auth.sessions s
                JOIN auth.users au ON au.id = s.user_id
                WHERE s.not_after > NOW()
                LIMIT 1
                """
            )
            # Fallback: just check if any user exists with recent activity
            # For proper JWT validation, use Supabase's GoTrue or a JWT lib
            # For now, validate by checking the token against Supabase REST API
            pass
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # Use Supabase REST API to validate the token — more reliable
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
    if not supabase_url or not supabase_key:
        return None

    try:
        import requests
        resp = requests.get(
            f"{supabase_url}/auth/v1/user",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {token}",
            },
            timeout=5,
        )
        if resp.ok:
            data = resp.json()
            return {"id": data.get("id"), "email": data.get("email")}
    except Exception:
        pass

    return None


def track_user_request(user_id: str, query: str) -> None:
    """Log a request from an authenticated user."""
    try:
        conn = _get_conn()
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_requests (user_id, query, date)
                VALUES (%s, %s, %s)
                """,
                (user_id, query, date.today().isoformat()),
            )
    except Exception:
        pass  # fail open — don't block search if tracking fails
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
