"""Stripe webhook signature verification and tier transitions.

A stub: it can verify a real webhook and move a `Subscription` between
tiers on the two events that matter (a subscription created/updated, and a
subscription deleted), but nothing yet creates the Stripe customer or
checkout session that would produce these events in the first place -
that's the rest of the Stripe integration this stub is dormant until (see
`models.py`'s module docstring, which says the same about the Subscription
columns themselves).

Verification is hand-rolled rather than via the `stripe` package - Stripe's
signature scheme (HMAC-SHA256 over `"{timestamp}.{payload}"`) is simple
enough that pulling in the full SDK for one function isn't worth it while
the rest of the integration doesn't exist yet.
"""

import hashlib
import hmac
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.billing.models import Subscription, SubscriptionStatus, Tier

_SIGNATURE_TOLERANCE_SECONDS = 300

_ACTIVE_STRIPE_STATUSES = {"active", "trialing"}
_PAST_DUE_STRIPE_STATUSES = {"past_due", "unpaid", "incomplete"}

_SUBSCRIPTION_EVENT_TYPES = {
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
}


class InvalidSignatureError(Exception):
    """Raised when a webhook's signature doesn't verify against the
    configured secret, or the header is malformed."""


def verify_signature(payload: bytes, header: str, secret: str) -> None:
    """Stripe's documented manual verification algorithm. Raises
    `InvalidSignatureError` rather than returning a bool - there's no
    partially-valid signature, so a caller should never need to inspect
    the failure beyond "reject this request"."""
    parts = dict(item.split("=", 1) for item in header.split(",") if "=" in item)
    timestamp = parts.get("t")
    signature = parts.get("v1")
    if timestamp is None or signature is None:
        raise InvalidSignatureError("Malformed Stripe-Signature header.")

    try:
        age = time.time() - int(timestamp)
    except ValueError as exc:
        raise InvalidSignatureError("Malformed Stripe-Signature header.") from exc
    if abs(age) > _SIGNATURE_TOLERANCE_SECONDS:
        raise InvalidSignatureError("Webhook timestamp is outside the tolerance window.")

    signed_payload = f"{timestamp}.".encode() + payload
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise InvalidSignatureError("Signature does not match.")


def _tier_and_status_for(stripe_status: str) -> tuple[Tier, SubscriptionStatus]:
    if stripe_status in _ACTIVE_STRIPE_STATUSES:
        return Tier.PREMIUM, SubscriptionStatus.ACTIVE
    if stripe_status in _PAST_DUE_STRIPE_STATUSES:
        return Tier.PREMIUM, SubscriptionStatus.PAST_DUE
    return Tier.FREE, SubscriptionStatus.CANCELED


async def apply_event(db: AsyncSession, event: dict[str, Any]) -> None:
    """Moves a `Subscription` between tiers for the two event types that
    matter. A no-op for every other event type, and for a subscription
    event whose Stripe customer isn't already linked to a row - nothing yet
    creates that link (see the module docstring), so there is deliberately
    nothing to backfill it onto.
    """
    if event.get("type") not in _SUBSCRIPTION_EVENT_TYPES:
        return

    data = event.get("data", {}).get("object", {})
    stripe_customer_id = data.get("customer")
    if stripe_customer_id is None:
        return

    subscription = await db.scalar(
        select(Subscription).where(Subscription.stripe_customer_id == stripe_customer_id)
    )
    if subscription is None:
        return

    if event["type"] == "customer.subscription.deleted":
        subscription.tier = Tier.FREE
        subscription.status = SubscriptionStatus.CANCELED
    else:
        tier, sub_status = _tier_and_status_for(data.get("status", ""))
        subscription.tier = tier
        subscription.status = sub_status
        subscription.stripe_subscription_id = data.get("id")
        period_end = data.get("current_period_end")
        if period_end is not None:
            subscription.current_period_end = datetime.fromtimestamp(period_end, tz=UTC)

    await db.commit()
