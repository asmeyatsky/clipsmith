import os
import stripe
from typing import Dict, Any, Optional
from ...domain.ports.payment_repository_port import StripeServicePort


class StripeService(StripeServicePort):
    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    # Payment processing
    async def create_payment_intent(self, amount: float, currency: str = "USD",
                                 metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a Stripe payment intent."""
        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)
            
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True},
                # Add future features like payment method types
                payment_method_types=["card"]
            )
            
            return {
                "success": True,
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "amount": intent.amount,
                "currency": intent.currency,
                "status": intent.status
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    async def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm a payment intent."""
        try:
            intent = stripe.PaymentIntent.confirm(payment_intent_id)
            
            return {
                "success": True,
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
                "charge_id": intent.charges.data[0].id if intent.charges.data else None
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    async def refund_payment(self, charge_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Refund a payment."""
        try:
            refund_params = {"charge": charge_id}
            
            if amount:
                refund_params["amount"] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_params)
            
            return {
                "success": True,
                "refund_id": refund.id,
                "amount": refund.amount,
                "currency": refund.currency,
                "status": refund.status
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    # Connect accounts (for creators)
    async def create_connect_account(self, user_id: str, email: str) -> Dict[str, Any]:
        """Create a Stripe Connect account for creator."""
        try:
            account = stripe.Account.create(
                type="express",
                country="US",
                email=email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                metadata={"user_id": user_id}
            )
            
            return {
                "success": True,
                "account_id": account.id,
                "status": account.capabilities
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    async def create_account_link(self, account_id: str, refresh_url: str,
                                return_url: str) -> Dict[str, Any]:
        """Create account link for Stripe Connect onboarding."""
        try:
            account_link = stripe.AccountLink.create(
                account=account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type="account_onboarding"
            )
            
            return {
                "success": True,
                "url": account_link.url,
                "expires_at": account_link.expires_at
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    async def get_connect_account(self, account_id: str) -> Dict[str, Any]:
        """Get Stripe Connect account details."""
        try:
            account = stripe.Account.retrieve(account_id)
            
            return {
                "success": True,
                "account": account
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    async def update_connect_account(self, account_id: str,
                                  updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update Stripe Connect account."""
        try:
            account = stripe.Account.modify(account_id, **updates)
            
            return {
                "success": True,
                "account": account
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    # Payouts
    async def create_payout(self, amount: float, destination: str,
                          currency: str = "USD", metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a payout to a bank account."""
        try:
            amount_cents = int(amount * 100)
            
            payout = stripe.Payout.create(
                amount=amount_cents,
                currency=currency.lower(),
                destination=destination,
                metadata=metadata or {}
            )
            
            return {
                "success": True,
                "payout_id": payout.id,
                "amount": payout.amount,
                "currency": payout.currency,
                "status": payout.status,
                "arrival_date": payout.arrival_date
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    async def get_payout(self, payout_id: str) -> Dict[str, Any]:
        """Get payout details."""
        try:
            payout = stripe.Payout.retrieve(payout_id)
            
            return {
                "success": True,
                "payout": payout
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    # Subscriptions
    async def create_subscription(self, price_id: str, customer_id: str,
                                metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a subscription."""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                metadata=metadata or {},
                payment_behavior="create_if_missing"
            )
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "amount": subscription.items.data[0].price.unit_amount / 100,
                "currency": subscription.items.data[0].price.currency
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription."""
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            
            return {
                "success": True,
                "subscription_id": subscription.id,
                "status": subscription.status,
                "canceled_at": subscription.canceled_at
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    async def create_price(self, amount: float, currency: str = "USD",
                         interval: str = "month", product_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a price for subscriptions."""
        try:
            amount_cents = int(amount * 100)
            
            price_params = {
                "unit_amount": amount_cents,
                "currency": currency.lower(),
                "recurring": {"interval": interval}
            }
            
            if product_id:
                price_params["product"] = product_id
            else:
                # Create a default product if none provided
                price_params["product_data"] = {
                    "name": "Creator Subscription",
                    "description": "Monthly subscription to creator content"
                }
            
            price = stripe.Price.create(**price_params)
            
            return {
                "success": True,
                "price_id": price.id,
                "amount": price.unit_amount,
                "currency": price.currency,
                "interval": price.recurring.interval
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    async def create_customer(self, email: str, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a Stripe customer."""
        try:
            customer = stripe.Customer.create(
                email=email,
                metadata=metadata or {}
            )
            
            return {
                "success": True,
                "customer_id": customer.id,
                "email": customer.email
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            }
    
    # Webhooks
    async def construct_webhook_event(self, payload: str, signature: str,
                                    secret: str) -> Dict[str, Any]:
        """Construct and verify webhook event."""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, secret or self.webhook_secret
            )
            
            return {
                "success": True,
                "event": event
            }
            
        except stripe.error.SignatureVerificationError:
            return {
                "success": False,
                "error": "Invalid signature",
                "error_type": "SignatureVerificationError"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }