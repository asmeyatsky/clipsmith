import os
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from typing import List, Optional
from ...application.services.payment_service import PaymentService
from ...infrastructure.repositories.sqlite_payment_repo import SQLitePaymentRepository
from ...infrastructure.services.stripe_service import StripeService
from ...infrastructure.repositories.database import get_session
from .auth_router import get_current_user
from ...domain.entities.payment import TransactionType, Transaction
from sqlmodel import Session
from datetime import datetime
import json

router = APIRouter(prefix="/api/payments", tags=["payments"])


def get_payment_service(session: Session = Depends(get_session)) -> PaymentService:
    """Dependency injection for payment service."""
    repository = SQLitePaymentRepository(session)
    stripe_service = StripeService()
    return PaymentService(repository, stripe_service)


# Wallet endpoints
@router.get("/wallet")
async def get_wallet(
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Get user's wallet information."""
    wallet = await service.get_wallet(current_user["id"])
    if not wallet:
        wallet = await service.create_wallet(current_user["id"])

    return {"success": True, "wallet": wallet}


@router.get("/wallet/summary")
async def get_wallet_summary(
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Get comprehensive wallet summary."""
    summary = await service.get_wallet_summary(current_user["id"])
    return {"success": True, "summary": summary}


def _validate_redirect_url(url: str) -> str:
    """Validate that a redirect URL is safe (same-origin or allowed domain)."""
    from urllib.parse import urlparse
    allowed_hosts = os.getenv("ALLOWED_REDIRECT_HOSTS", "localhost,clipsmith.com,www.clipsmith.com").split(",")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Invalid URL scheme")
    if parsed.hostname and parsed.hostname not in allowed_hosts:
        raise HTTPException(status_code=400, detail="Redirect URL not allowed")
    return url


@router.post("/wallet/setup-connect")
async def setup_stripe_connect(
    return_url: str = Form(...),
    refresh_url: str = Form(...),
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Setup Stripe Connect for creator payouts."""
    return_url = _validate_redirect_url(return_url)
    refresh_url = _validate_redirect_url(refresh_url)

    result = await service.setup_stripe_connect(
        user_id=current_user["id"],
        email=current_user.get("email", f"user_{current_user['id']}@example.com"),
        return_url=return_url,
        refresh_url=refresh_url,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"success": True, **result}


# Transaction endpoints
@router.post("/tip")
async def create_tip(
    creator_id: str = Form(...),
    amount: float = Form(...),
    video_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Create a tip transaction."""
    if current_user["id"] == creator_id:
        raise HTTPException(status_code=400, detail="Cannot tip yourself")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    result = await service.create_tip_transaction(
        sender_id=current_user["id"],
        receiver_id=creator_id,
        amount=amount,
        video_id=video_id,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"success": True, **result}


@router.get("/transactions")
async def get_transaction_history(
    limit: int = 50,
    transaction_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Get user's transaction history."""
    from ...domain.entities.payment import TransactionType

    trans_type = TransactionType(transaction_type) if transaction_type else None

    transactions = await service.get_transaction_history(
        user_id=current_user["id"], limit=limit, transaction_type=trans_type
    )

    return {"success": True, "transactions": transactions}


# Payout endpoints
@router.post("/payouts/request")
async def request_payout(
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Request a payout for available balance."""
    result = await service.request_payout(current_user["id"])

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"success": True, **result}


@router.get("/payouts")
async def get_payout_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Get user's payout history."""
    payouts = await service.get_payout_history(current_user["id"], limit)
    return {"success": True, "payouts": payouts}


# Subscription endpoints
@router.post("/subscriptions")
async def create_subscription(
    creator_id: str = Form(...),
    amount: float = Form(...),
    interval: str = Form("month"),
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Create a subscription to a creator."""
    if current_user["id"] == creator_id:
        raise HTTPException(status_code=400, detail="Cannot subscribe to yourself")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    if interval not in ["month", "year"]:
        raise HTTPException(
            status_code=400, detail="Interval must be 'month' or 'year'"
        )

    result = await service.create_subscription(
        subscriber_id=current_user["id"],
        creator_id=creator_id,
        amount=amount,
        interval=interval,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"success": True, **result}


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Cancel a subscription."""
    result = await service.cancel_subscription(
        subscription_id=subscription_id, user_id=current_user["id"]
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"success": True, **result}


@router.get("/subscriptions")
async def get_user_subscriptions(
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Get user's active subscriptions."""
    subscriptions = await service.get_user_subscriptions(current_user["id"])
    return {"success": True, "subscriptions": subscriptions}


@router.get("/creator/{creator_id}/subscribers")
async def get_creator_subscribers(
    creator_id: str,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Get creator's subscribers (creator only)."""
    if current_user["id"] != creator_id:
        raise HTTPException(status_code=403, detail="Access denied")

    subscribers = await service.get_creator_subscribers(creator_id)
    return {"success": True, "subscribers": subscribers}


# Analytics endpoints
@router.get("/creator/{creator_id}/analytics")
async def get_creator_analytics(
    creator_id: str,
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    """Get analytics for creator earnings."""
    if current_user["id"] != creator_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if days <= 0 or days > 365:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 365")

    analytics = await service.get_creator_analytics(creator_id, days)
    return {"success": True, "analytics": analytics}


# Stripe webhook endpoint
@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request, service: PaymentService = Depends(get_payment_service)
):
    """Handle Stripe webhooks."""
    body = await request.body()
    signature = request.headers.get("stripe-signature")

    # Verify webhook signature
    event_result = await service.stripe_service.construct_webhook_event(
        payload=body.decode(),
        signature=signature,
        secret=None,  # Will use default from service
    )

    if not event_result["success"]:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event = event_result["event"]
    event_type = event["type"]

    try:
        # Handle different event types
        if event_type.startswith("payment_intent."):
            await _handle_payment_intent(event, service)
        elif event_type.startswith("invoice.payment_"):
            await _handle_invoice_payment(event, service)
        elif event_type.startswith("customer.subscription."):
            await _handle_subscription_event(event, service)
        elif event_type.startswith("payout."):
            await _handle_payout_event(event, service)
        elif event_type == "account.updated":
            await _handle_account_update(event, service)

        return {"success": True, "received": True}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Webhook processing failed: {str(e)}"
        )


# Webhook handlers
async def _handle_payment_intent(event: dict, service: PaymentService):
    """Handle payment intent events."""
    payment_intent = event["data"]["object"]

    if event["type"] == "payment_intent.succeeded":
        # Complete tip transaction
        await service.complete_tip_transaction(
            payment_intent_id=payment_intent["id"],
            charge_id=payment_intent["charges"]["data"][0]["id"],
        )


async def _handle_invoice_payment(event: dict, service: PaymentService):
    """Handle invoice payment events (subscriptions)."""
    invoice = event["data"]["object"]

    if event["type"] == "invoice.payment_succeeded":
        # Create transaction for subscription payment
        subscription_id = invoice.get("subscription")
        if subscription_id:
            subscription = service.repository.get_subscription_by_stripe_id(
                subscription_id
            )
            if subscription:
                transaction = Transaction(
                    user_id=subscription.creator_id,
                    amount=invoice["amount_paid"] / 100,
                    transaction_type=TransactionType.SUBSCRIPTION,
                    description=f"Subscription payment from {subscription.user_id}",
                    reference_id=invoice["charge"],
                    metadata={
                        "subscriber_id": subscription.user_id,
                        "subscription_id": subscription.id,
                    },
                )

                completed_transaction = transaction.complete()
                saved_transaction = service.repository.save_transaction(
                    completed_transaction
                )

                # Update creator's wallet
                wallet = await service.create_wallet(subscription.creator_id)
                updated_wallet = wallet.add_funds(saved_transaction.amount)
                service.repository.save_wallet(updated_wallet)


async def _handle_subscription_event(event: dict, service: PaymentService):
    """Handle subscription events."""
    subscription = event["data"]["object"]
    stripe_subscription_id = subscription["id"]

    db_subscription = service.repository.get_subscription_by_stripe_id(
        stripe_subscription_id
    )
    if not db_subscription:
        return

    if event["type"] == "customer.subscription.deleted":
        # Update subscription status
        updated_subscription = db_subscription.replace(status="cancelled")
        updated_subscription = updated_subscription.replace(ended_at=datetime.utcnow())
        service.repository.save_subscription(updated_subscription)


async def _handle_payout_event(event: dict, service: PaymentService):
    """Handle payout events."""
    payout = event["data"]["object"]
    stripe_payout_id = payout["id"]

    # Find corresponding payout in database
    # This would need additional query method in repository
    pass


async def _handle_account_update(event: dict, service: PaymentService):
    """Handle Stripe Connect account updates."""
    account = event["data"]["object"]
    account_id = account["id"]

    # Update account status if needed
    # Could update wallet status based on account capabilities
    pass
