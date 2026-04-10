"""Stripe billing integration for tteg-api."""
from __future__ import annotations

import os
from typing import Any

import stripe as _stripe


PLAN_NAMES = {"pro": "tteg Pro", "team": "tteg Team"}
PLAN_PRICES = {"pro": "$9/mo", "team": "$29/mo"}


def _client() -> Any:
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        return None
    _stripe.api_key = key
    return _stripe


def create_checkout_session(plan: str, success_url: str, cancel_url: str) -> str:
    """Create a Stripe Checkout session and return the URL."""
    s = _client()
    if s is None:
        raise RuntimeError("STRIPE_SECRET_KEY not configured")

    price_id = os.environ.get(f"STRIPE_{'PRO' if plan == 'pro' else 'TEAM'}_PRICE_ID", "")
    if not price_id:
        raise RuntimeError(f"STRIPE_{plan.upper()}_PRICE_ID not configured")

    session = s.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"plan": plan},
    )
    return session.url


def parse_webhook_event(payload: bytes, sig_header: str) -> Any:
    """Validate and parse a Stripe webhook event. Raises on invalid sig."""
    s = _client()
    if s is None:
        raise RuntimeError("STRIPE_SECRET_KEY not configured")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    return s.Webhook.construct_event(payload, sig_header, webhook_secret)


def is_configured() -> bool:
    return bool(os.environ.get("STRIPE_SECRET_KEY"))
