import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from ...application.services.payment_service import PaymentService
from ...infrastructure.repositories.sqlite_payment_repo import SQLitePaymentRepository
from ...infrastructure.services.stripe_service import StripeService
from ...infrastructure.repositories.database import get_session
from .auth_router import get_current_user
from ...domain.entities.payment import TransactionType, Transaction
from sqlmodel import Session, select
from datetime import datetime
import json

logger = logging.getLogger(__name__)

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

    allowed_hosts = os.getenv(
        "ALLOWED_REDIRECT_HOSTS", "localhost,clipsmith.com,www.clipsmith.com"
    ).split(",")
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


# ==================== Stripe Webhook Endpoints ====================


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request, service: PaymentService = Depends(get_payment_service)
):
    """Handle Stripe webhooks with signature verification.

    Processes the following event types:
    - checkout.session.completed
    - payment_intent.succeeded / payment_intent.failed
    - customer.subscription.created / updated / deleted
    - invoice.payment_succeeded / invoice.payment_failed
    - payout.*
    - account.updated
    """
    body = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        logger.warning("Stripe webhook received without signature header")
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    # Verify webhook signature
    event_result = await service.stripe_service.construct_webhook_event(
        payload=body.decode(),
        signature=signature,
        secret=None,  # Will use default from service
    )

    if not event_result["success"]:
        logger.warning(f"Stripe webhook signature verification failed: {event_result.get('error')}")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event = event_result["event"]
    event_type = event["type"]
    logger.info(f"Processing Stripe webhook event: {event_type} (id={event.get('id', 'unknown')})")

    try:
        # Handle different event types
        if event_type == "checkout.session.completed":
            await _handle_checkout_session_completed(event, service)
        elif event_type == "payment_intent.succeeded":
            await _handle_payment_intent_succeeded(event, service)
        elif event_type == "payment_intent.failed":
            await _handle_payment_intent_failed(event, service)
        elif event_type.startswith("invoice.payment_"):
            await _handle_invoice_payment(event, service)
        elif event_type == "customer.subscription.created":
            await _handle_subscription_created(event, service)
        elif event_type == "customer.subscription.updated":
            await _handle_subscription_updated(event, service)
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(event, service)
        elif event_type.startswith("payout."):
            await _handle_payout_event(event, service)
        elif event_type == "account.updated":
            await _handle_account_update(event, service)
        else:
            logger.debug(f"Unhandled Stripe webhook event type: {event_type}")

        return JSONResponse(
            status_code=200,
            content={"success": True, "received": True}
        )

    except Exception as e:
        logger.error(f"Webhook processing failed for {event_type}: {e}", exc_info=True)
        # Return 200 to prevent Stripe from retrying on application errors.
        # Only signature failures should return 4xx.
        return JSONResponse(
            status_code=200,
            content={"success": False, "error": "Processing failed, will retry internally"}
        )


# Also register the webhook at the /webhooks/stripe path (standard convention)
@router.post("/webhooks/stripe")
async def stripe_webhook_alt(
    request: Request, service: PaymentService = Depends(get_payment_service)
):
    """Alias for /webhook/stripe to support the standard /webhooks/ convention."""
    return await stripe_webhook(request, service)


# ==================== Webhook Handlers ====================


async def _handle_checkout_session_completed(event: dict, service: PaymentService):
    """Handle checkout.session.completed event.

    This fires when a Checkout Session payment is successful.
    Used for one-time payments and subscription initial payments via Checkout.
    """
    session_obj = event["data"]["object"]
    mode = session_obj.get("mode")  # "payment", "subscription", or "setup"
    payment_status = session_obj.get("payment_status")
    metadata = session_obj.get("metadata", {})

    logger.info(
        f"Checkout session completed: mode={mode}, "
        f"payment_status={payment_status}, session_id={session_obj['id']}"
    )

    if payment_status != "paid":
        logger.info(f"Checkout session {session_obj['id']} not yet paid, skipping")
        return

    if mode == "payment":
        # One-time payment completed
        payment_intent_id = session_obj.get("payment_intent")
        customer_id = session_obj.get("customer")

        if metadata.get("type") == "tip":
            # Tip payment via Checkout
            sender_id = metadata.get("sender_id")
            receiver_id = metadata.get("receiver_id")
            if payment_intent_id:
                await service.complete_tip_transaction(
                    payment_intent_id=payment_intent_id,
                    charge_id=payment_intent_id,  # Will be resolved in handler
                )

        elif metadata.get("type") == "premium_purchase":
            # Premium content purchase via Checkout
            logger.info(
                f"Premium content purchase completed via Checkout: "
                f"session={session_obj['id']}"
            )

    elif mode == "subscription":
        # Subscription created via Checkout
        stripe_subscription_id = session_obj.get("subscription")
        customer_id = session_obj.get("customer")
        logger.info(
            f"Subscription {stripe_subscription_id} created via Checkout "
            f"for customer {customer_id}"
        )


async def _handle_payment_intent_succeeded(event: dict, service: PaymentService):
    """Handle payment_intent.succeeded event.

    Completes the corresponding tip transaction and credits the receiver.
    """
    payment_intent = event["data"]["object"]
    payment_intent_id = payment_intent["id"]
    metadata = payment_intent.get("metadata", {})

    logger.info(f"Payment intent succeeded: {payment_intent_id}")

    # Extract charge ID safely
    charges = payment_intent.get("charges", {})
    charges_data = charges.get("data", []) if isinstance(charges, dict) else []
    charge_id = charges_data[0]["id"] if charges_data else payment_intent.get("latest_charge")

    if not charge_id:
        logger.warning(f"No charge ID found for payment intent {payment_intent_id}")
        charge_id = payment_intent_id  # Fallback

    await service.complete_tip_transaction(
        payment_intent_id=payment_intent_id,
        charge_id=charge_id,
    )


async def _handle_payment_intent_failed(event: dict, service: PaymentService):
    """Handle payment_intent.failed event.

    Marks the corresponding transaction as failed.
    """
    payment_intent = event["data"]["object"]
    payment_intent_id = payment_intent["id"]
    failure_message = payment_intent.get("last_payment_error", {}).get("message", "Payment failed")

    logger.warning(f"Payment intent failed: {payment_intent_id} - {failure_message}")

    # Find and fail the corresponding transaction
    transactions = service.repository.get_transactions_by_reference(payment_intent_id)
    for transaction in transactions:
        if transaction.status == "pending":
            failed_transaction = transaction.fail(failure_message)
            service.repository.save_transaction(failed_transaction)
            logger.info(f"Transaction {transaction.id} marked as failed")


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
                    reference_id=invoice.get("charge", invoice["id"]),
                    metadata={
                        "subscriber_id": subscription.user_id,
                        "subscription_id": subscription.id,
                        "invoice_id": invoice["id"],
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

                logger.info(
                    f"Invoice payment recorded for subscription {subscription_id}: "
                    f"${saved_transaction.amount}"
                )

    elif event["type"] == "invoice.payment_failed":
        subscription_id = invoice.get("subscription")
        logger.warning(
            f"Invoice payment failed for subscription {subscription_id}: "
            f"invoice={invoice['id']}"
        )


async def _handle_subscription_created(event: dict, service: PaymentService):
    """Handle customer.subscription.created event.

    Logs the event. The subscription is typically already saved to the DB
    when created via the API, but this handles subscriptions created
    externally (e.g., via Stripe Dashboard or Checkout).
    """
    subscription = event["data"]["object"]
    stripe_subscription_id = subscription["id"]
    status = subscription.get("status")
    metadata = subscription.get("metadata", {})

    logger.info(
        f"Subscription created: {stripe_subscription_id}, status={status}, "
        f"metadata={metadata}"
    )

    # Check if already in our database (created via our API)
    db_subscription = service.repository.get_subscription_by_stripe_id(
        stripe_subscription_id
    )
    if db_subscription:
        logger.debug(f"Subscription {stripe_subscription_id} already in database")
        return

    # If created externally, we could create a record here if we have
    # enough metadata to identify the subscriber and creator
    subscriber_id = metadata.get("subscriber_id")
    creator_id = metadata.get("creator_id")
    if subscriber_id and creator_id:
        from ...domain.entities.payment import Subscription as SubscriptionEntity
        new_sub = SubscriptionEntity(
            user_id=subscriber_id,
            creator_id=creator_id,
            stripe_subscription_id=stripe_subscription_id,
            status=status,
            amount=subscription["items"]["data"][0]["price"]["unit_amount"] / 100 if subscription.get("items", {}).get("data") else 0,
            currency=subscription["items"]["data"][0]["price"]["currency"] if subscription.get("items", {}).get("data") else "usd",
            interval=subscription["items"]["data"][0]["price"]["recurring"]["interval"] if subscription.get("items", {}).get("data") else "month",
            current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
            current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
        )
        service.repository.save_subscription(new_sub)
        logger.info(f"Externally created subscription {stripe_subscription_id} saved to database")


async def _handle_subscription_updated(event: dict, service: PaymentService):
    """Handle customer.subscription.updated event.

    Updates the local subscription record with the latest status and period info.
    """
    subscription = event["data"]["object"]
    stripe_subscription_id = subscription["id"]
    new_status = subscription.get("status")

    logger.info(f"Subscription updated: {stripe_subscription_id}, new_status={new_status}")

    db_subscription = service.repository.get_subscription_by_stripe_id(
        stripe_subscription_id
    )
    if not db_subscription:
        logger.warning(f"Subscription {stripe_subscription_id} not found in database")
        return

    # Update status and period
    updated = db_subscription.replace(
        status=new_status,
        current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
        current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
    )

    # Handle cancellation
    if new_status == "canceled" and not updated.cancelled_at:
        updated = updated.replace(cancelled_at=datetime.utcnow())

    service.repository.save_subscription(updated)


async def _handle_subscription_deleted(event: dict, service: PaymentService):
    """Handle customer.subscription.deleted event.

    Marks the subscription as cancelled and records the end time.
    """
    subscription = event["data"]["object"]
    stripe_subscription_id = subscription["id"]

    logger.info(f"Subscription deleted: {stripe_subscription_id}")

    db_subscription = service.repository.get_subscription_by_stripe_id(
        stripe_subscription_id
    )
    if not db_subscription:
        logger.warning(f"Subscription {stripe_subscription_id} not found in database")
        return

    updated_subscription = db_subscription.replace(status="cancelled")
    updated_subscription = updated_subscription.replace(ended_at=datetime.utcnow())
    if not updated_subscription.cancelled_at:
        updated_subscription = updated_subscription.replace(cancelled_at=datetime.utcnow())

    service.repository.save_subscription(updated_subscription)
    logger.info(f"Subscription {stripe_subscription_id} marked as cancelled")


async def _handle_payout_event(event: dict, service: PaymentService):
    """Handle payout events (payout.paid, payout.failed, etc.)."""
    payout = event["data"]["object"]
    stripe_payout_id = payout["id"]
    payout_status = payout.get("status")

    logger.info(f"Payout event: {event['type']}, payout_id={stripe_payout_id}, status={payout_status}")

    # Future: look up payout by stripe_payout_id and update status
    # This requires a query method like: repository.get_payout_by_stripe_id(stripe_payout_id)


async def _handle_account_update(event: dict, service: PaymentService):
    """Handle Stripe Connect account.updated events.

    Logs account verification status changes.
    """
    account = event["data"]["object"]
    account_id = account["id"]
    charges_enabled = account.get("charges_enabled", False)
    payouts_enabled = account.get("payouts_enabled", False)

    logger.info(
        f"Connect account updated: {account_id}, "
        f"charges_enabled={charges_enabled}, payouts_enabled={payouts_enabled}"
    )

    # Future: update wallet status based on account capabilities
    # e.g., service.repository.update_wallet_status_by_stripe_account(account_id, ...)


# ==================== Premium Content Endpoints ====================


@router.post("/premium/content")
async def create_premium_content(
    video_id: str = Form(...),
    price: float = Form(...),
    description: str = Form(None),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create premium content for a video."""
    from ..infrastructure.repositories.models import PremiumContentDB

    existing = session.exec(
        select(PremiumContentDB).where(
            PremiumContentDB.video_id == video_id,
            PremiumContentDB.creator_id == current_user["id"],
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400, detail="Premium content already exists for this video"
        )

    premium = PremiumContentDB(
        creator_id=current_user["id"],
        video_id=video_id,
        price=price,
        description=description,
    )
    session.add(premium)
    session.commit()

    return {"success": True, "premium_content_id": premium.id}


@router.get("/premium/{video_id}")
async def get_premium_content(
    video_id: str,
    session: Session = Depends(get_session),
):
    """Get premium content info for a video."""
    from ..infrastructure.repositories.models import PremiumContentDB

    premium = session.exec(
        select(PremiumContentDB).where(
            PremiumContentDB.video_id == video_id, PremiumContentDB.is_active == True
        )
    ).first()

    if not premium:
        return {"is_premium": False, "price": None}

    return {
        "is_premium": True,
        "price": premium.price,
        "description": premium.description,
        "purchase_count": premium.purchase_count,
    }


@router.post("/premium/{premium_content_id}/purchase")
async def purchase_premium_content(
    premium_content_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Purchase premium content."""
    from ..infrastructure.repositories.models import PremiumContentDB, PremiumPurchaseDB

    premium = session.get(PremiumContentDB, premium_content_id)
    if not premium or not premium.is_active:
        raise HTTPException(status_code=404, detail="Premium content not found")

    existing_purchase = session.exec(
        select(PremiumPurchaseDB).where(
            PremiumPurchaseDB.user_id == current_user["id"],
            PremiumPurchaseDB.premium_content_id == premium_content_id,
            PremiumPurchaseDB.status == "completed",
        )
    ).first()

    if existing_purchase:
        raise HTTPException(status_code=400, detail="Already purchased")

    purchase = PremiumPurchaseDB(
        user_id=current_user["id"],
        premium_content_id=premium_content_id,
        amount=premium.price,
    )
    session.add(purchase)
    session.commit()

    return {
        "success": True,
        "purchase_id": purchase.id,
        "amount": premium.price,
        "message": "Purchase initiated",
    }


@router.get("/premium/purchases")
async def get_purchased_content(
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get user's purchased premium content."""
    from ..infrastructure.repositories.models import PremiumContentDB, PremiumPurchaseDB

    purchases = session.exec(
        select(PremiumPurchaseDB).where(
            PremiumPurchaseDB.user_id == current_user["id"],
            PremiumPurchaseDB.status == "completed",
        )
    ).all()

    result = []
    for p in purchases:
        premium = session.get(PremiumContentDB, p.premium_content_id)
        if premium:
            result.append(
                {
                    "purchase_id": p.id,
                    "video_id": premium.video_id,
                    "amount": p.amount,
                    "purchased_at": p.created_at.isoformat() if p.created_at else None,
                }
            )

    return {"purchases": result}


@router.get("/premium/{video_id}/access")
async def check_premium_access(
    video_id: str,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Check if user has access to premium content for a video.
    Enforces access control: only purchasers, subscribers, or the creator can access."""
    from ...infrastructure.repositories.models import PremiumContentDB, PremiumPurchaseDB, SubscriptionDB

    premium = session.exec(
        select(PremiumContentDB).where(
            PremiumContentDB.video_id == video_id, PremiumContentDB.is_active == True
        )
    ).first()

    if not premium:
        return {"has_access": True, "is_premium": False}

    # Creator always has access
    if premium.creator_id == current_user["id"]:
        return {"has_access": True, "is_premium": True, "reason": "creator"}

    # Check purchase
    purchase = session.exec(
        select(PremiumPurchaseDB).where(
            PremiumPurchaseDB.user_id == current_user["id"],
            PremiumPurchaseDB.premium_content_id == premium.id,
            PremiumPurchaseDB.status == "completed",
        )
    ).first()

    if purchase:
        return {"has_access": True, "is_premium": True, "reason": "purchased"}

    # Check active subscription to creator
    subscription = session.exec(
        select(SubscriptionDB).where(
            SubscriptionDB.user_id == current_user["id"],
            SubscriptionDB.creator_id == premium.creator_id,
            SubscriptionDB.status == "active",
        )
    ).first()

    if subscription:
        return {"has_access": True, "is_premium": True, "reason": "subscriber"}

    return {
        "has_access": False,
        "is_premium": True,
        "price": premium.price,
        "message": "Purchase required to access this content",
    }


# ==================== Subscription Tiers ====================


@router.get("/subscription-tiers/{creator_id}")
async def get_creator_subscription_tiers(
    creator_id: str,
    session: Session = Depends(get_session),
):
    """Get predefined subscription tiers for a creator (PRD: $2.99-$9.99/month)."""
    from ...infrastructure.repositories.models import SubscriptionTierDB

    tiers = session.exec(
        select(SubscriptionTierDB).where(
            SubscriptionTierDB.creator_id == creator_id,
            SubscriptionTierDB.is_active == True,
        )
    ).all()

    if not tiers:
        # Return default PRD tiers
        return {
            "tiers": [
                {"name": "Supporter", "price": 2.99, "interval": "month",
                 "benefits": ["Ad-free viewing", "Supporter badge", "Early access"]},
                {"name": "Super Fan", "price": 5.99, "interval": "month",
                 "benefits": ["All Supporter perks", "Exclusive content", "Behind-the-scenes", "Priority comments"]},
                {"name": "VIP", "price": 9.99, "interval": "month",
                 "benefits": ["All Super Fan perks", "Direct messaging", "Monthly Q&A", "Custom badge", "Shoutouts"]},
            ]
        }

    return {
        "tiers": [
            {
                "id": t.id,
                "name": t.name,
                "price": t.price,
                "interval": t.interval,
                "description": t.description,
                "benefits": t.benefits,
            }
            for t in tiers
        ]
    }


# ==================== Brand Collaboration Endpoints ====================


@router.post("/brand/profile")
async def create_brand_profile(
    request: Request,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a brand profile."""
    from ..infrastructure.repositories.models import BrandProfileDB

    body = await request.json()

    existing = session.exec(
        select(BrandProfileDB).where(BrandProfileDB.user_id == current_user["id"])
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Brand profile already exists")

    brand = BrandProfileDB(
        user_id=current_user["id"],
        company_name=body.get("company_name"),
        industry=body.get("industry"),
        website=body.get("website"),
        description=body.get("description"),
        logo_url=body.get("logo_url"),
    )
    session.add(brand)
    session.commit()

    return {"success": True, "brand_profile_id": brand.id}


@router.get("/brand/profile")
async def get_brand_profile(
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get brand profile."""
    from ..infrastructure.repositories.models import BrandProfileDB

    brand = session.exec(
        select(BrandProfileDB).where(BrandProfileDB.user_id == current_user["id"])
    ).first()

    if not brand:
        return {"has_profile": False}

    return {
        "has_profile": True,
        "company_name": brand.company_name,
        "industry": brand.industry,
        "website": brand.website,
        "description": brand.description,
        "logo_url": brand.logo_url,
        "is_verified": brand.is_verified,
    }


@router.post("/brand/campaigns")
async def create_campaign(
    request: Request,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a brand campaign."""
    from ..infrastructure.repositories.models import BrandCampaignDB

    body = await request.json()

    campaign = BrandCampaignDB(
        brand_id=current_user["id"],
        creator_id=body.get("creator_id"),
        title=body.get("title"),
        description=body.get("description"),
        budget=body.get("budget"),
        requirements=json.dumps(body.get("requirements", [])),
        deliverables=json.dumps(body.get("deliverables", [])),
    )
    session.add(campaign)
    session.commit()

    return {"success": True, "campaign_id": campaign.id}


@router.get("/brand/campaigns")
async def list_campaigns(
    status: str = None,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """List campaigns."""
    from ..infrastructure.repositories.models import BrandCampaignDB

    query = select(BrandCampaignDB).where(
        (BrandCampaignDB.brand_id == current_user["id"])
        | (BrandCampaignDB.creator_id == current_user["id"])
    )

    if status:
        query = query.where(BrandCampaignDB.status == status)

    campaigns = session.exec(query).all()

    return {
        "campaigns": [
            {
                "id": c.id,
                "title": c.title,
                "budget": c.budget,
                "status": c.status,
                "payment_status": c.payment_status,
            }
            for c in campaigns
        ]
    }


@router.post("/brand/campaigns/{campaign_id}/respond")
async def respond_to_campaign(
    campaign_id: str,
    accept: bool,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Accept or reject a campaign."""
    from ..infrastructure.repositories.models import BrandCampaignDB

    campaign = session.get(BrandCampaignDB, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.creator_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    campaign.status = "accepted" if accept else "rejected"
    session.add(campaign)
    session.commit()

    return {"success": True, "status": campaign.status}
