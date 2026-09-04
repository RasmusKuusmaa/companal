"""Subscription and AI usage endpoints - what a client needs to render a
usage meter or an upgrade prompt."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.domains.billing.schemas import SubscriptionSummary
from app.domains.billing.service import get_subscription_summary
from app.domains.users.models import User

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/subscription", response_model=SubscriptionSummary)
async def read_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionSummary:
    return await get_subscription_summary(db, current_user.id)
