"""Subscription and AI usage endpoints - what a client needs to render a
usage meter or an upgrade prompt - plus the (dormant) Stripe webhook."""

import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.domains.billing.schemas import SubscriptionSummary
from app.domains.billing.service import get_subscription_summary
from app.domains.billing.stripe_webhook import InvalidSignatureError, apply_event, verify_signature
from app.domains.users.models import User

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/subscription", response_model=SubscriptionSummary)
async def read_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionSummary:
    return await get_subscription_summary(db, current_user.id)


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
) -> dict[str, str]:
    """No `get_current_user` here - Stripe authenticates via the payload
    signature, not a bearer token.

    Inert without `STRIPE_WEBHOOK_SECRET` configured: every request is
    accepted and ignored, so a deployment that hasn't turned billing on
    yet never hands Stripe a retry-worthy failure.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        return {"status": "ignored"}

    payload = await request.body()
    if stripe_signature is None:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header.")

    try:
        verify_signature(payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET)
    except InvalidSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await apply_event(db, json.loads(payload))
    return {"status": "ok"}
