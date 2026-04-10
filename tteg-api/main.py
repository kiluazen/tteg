from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
import requests

from models import ImageResult
from sources.unsplash import search_unsplash
import billing
import db

app = FastAPI(title="tteg-api", version="0.3.0")

LANDING_URL = "https://tteg.kushalsm.com"


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _resolve_access_key() -> str:
    return os.environ.get("UNSPLASH_ACCESS_KEY") or os.environ.get("ACCESS_KEY") or ""


def _serialize_result(result: ImageResult, index: int) -> dict[str, object]:
    return {
        "id": index,
        "title": result.title,
        "image_url": result.image_url,
        "thumb_url": result.thumb_url,
    }


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.on_event("startup")
def startup() -> None:
    _load_local_env()


# ── health / auth config ──────────────────────────────────────────────────────


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/auth/config")
def auth_config() -> dict[str, object]:
    supabase_url = os.environ.get("SUPABASE_URL", "")
    publishable_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
    auth_enabled = bool(supabase_url and publishable_key)
    return {
        "auth_enabled": auth_enabled,
        "supabase_url": supabase_url,
        "supabase_publishable_key": publishable_key,
    }


# ── search ────────────────────────────────────────────────────────────────────


@app.get("/search")
def search(
    request: Request,
    q: str,
    n: int = Query(default=5, ge=1, le=10),
    orientation: str = Query(default="any", pattern="^(any|landscape|portrait|square)$"),
    width: int | None = Query(default=None, ge=1, le=10000),
    height: int | None = Query(default=None, ge=1, le=10000),
) -> dict[str, object]:
    # ── resolve tier from API key header ─────────────────────────────────────
    raw_key = (
        request.headers.get("X-API-Key")
        or request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    )
    tier = "free"

    if raw_key.startswith("tteg_"):
        plan = db.validate_api_key(raw_key)
        if plan is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid or inactive API key. Visit https://tteg.kushalsm.com to manage your subscription.",
            )
        tier = plan
    else:
        # Free tier: enforce daily query limit per IP
        client_ip = _get_client_ip(request)
        allowed, _count = db.check_and_increment_usage(client_ip)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Free tier limit ({db.FREE_DAILY_LIMIT} queries/day) reached. "
                    f"Upgrade at {LANDING_URL}/#pricing"
                ),
            )

    # ── Unsplash search ───────────────────────────────────────────────────────
    access_key = _resolve_access_key()
    if not access_key:
        raise HTTPException(status_code=500, detail="UNSPLASH_ACCESS_KEY is not configured")

    try:
        results = search_unsplash(
            access_key=access_key,
            query=q,
            count=n,
            orientation=orientation,
            width=width,
            height=height,
        )
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        detail = exc.response.text if exc.response is not None and exc.response.text else str(exc)
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    payload: dict[str, object] = {
        "query": q,
        "results": [_serialize_result(result, index) for index, result in enumerate(results, start=1)],
    }
    if tier == "free":
        payload["_tier"] = "free"
        payload["_upgrade_url"] = f"{LANDING_URL}/#pricing"

    _track_downloads(results, access_key)
    return payload


def _track_downloads(results: list[ImageResult], access_key: str) -> None:
    """Ping Unsplash download_location URLs for API compliance."""
    for result in results:
        if not result.download_location:
            continue
        try:
            requests.get(
                result.download_location,
                headers={"Authorization": f"Client-ID {access_key}"},
                timeout=5,
            )
        except Exception:
            pass


# ── billing ───────────────────────────────────────────────────────────────────


@app.post("/checkout")
def create_checkout(plan: str = Query(pattern="^(pro|team)$")) -> dict[str, str]:
    """Create a Stripe Checkout session and return the redirect URL."""
    if not billing.is_configured():
        raise HTTPException(status_code=503, detail="Billing not yet configured")
    try:
        checkout_url = billing.create_checkout_session(
            plan=plan,
            success_url=f"{LANDING_URL}/success.html?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{LANDING_URL}/#pricing",
        )
        return {"checkout_url": checkout_url}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/checkout/key")
def get_key_for_session(session_id: str) -> dict[str, object]:
    """
    Called by the success page to retrieve the provisioned API key.
    The webhook may arrive slightly after the redirect, so the client polls.
    """
    key = db.get_key_for_session(session_id)
    if key is None:
        raise HTTPException(status_code=404, detail="Key not ready yet, please retry in a moment")
    return {"key": key}


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request) -> dict[str, str]:
    """Handle Stripe webhook events."""
    if not billing.is_configured():
        raise HTTPException(status_code=503, detail="Billing not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = billing.parse_webhook_event(payload, sig_header)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid webhook: {exc}") from exc

    if event.type == "checkout.session.completed":
        session = event.data.object
        customer_details = session.customer_details or {}
        email = customer_details.get("email") or "unknown"
        plan = (session.metadata or {}).get("plan", "pro")
        subscription_id = session.subscription
        session_id = session.id

        db.create_api_key(
            email=email,
            plan=plan,
            subscription_id=subscription_id,
            checkout_session_id=session_id,
        )

    elif event.type in ("customer.subscription.deleted", "customer.subscription.paused"):
        db.deactivate_subscription(event.data.object.id)

    return {"status": "ok"}
