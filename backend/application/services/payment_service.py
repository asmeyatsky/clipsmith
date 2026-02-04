from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..domain.entities.payment import (
    Transaction,
    CreatorWallet,
    Payout,
    Subscription,
    TransactionType,
    TransactionStatus,
    PayoutStatus,
    WalletStatus,
)
from ..domain.ports.payment_repository_port import (
    PaymentRepositoryPort,
    StripeServicePort,
)


class PaymentService:
    """Service layer for payment and wallet operations."""

    def __init__(
        self, repository: PaymentRepositoryPort, stripe_service: StripeServicePort
    ):
        self.repository = repository
        self.stripe_service = stripe_service

    # Wallet operations
    async def create_wallet(self, user_id: str) -> CreatorWallet:
        """Create a new wallet for user."""
        existing_wallet = self.repository.get_wallet_by_user_id(user_id)
        if existing_wallet:
            return existing_wallet

        wallet = CreatorWallet(user_id=user_id)
        return self.repository.save_wallet(wallet)

    async def get_wallet(self, user_id: str) -> Optional[CreatorWallet]:
        """Get user's wallet."""
        return self.repository.get_wallet_by_user_id(user_id)

    async def setup_stripe_connect(
        self, user_id: str, email: str, return_url: str, refresh_url: str
    ) -> Dict[str, Any]:
        """Setup Stripe Connect for creator."""
        # Get or create wallet
        wallet = await self.create_wallet(user_id)

        # Create Stripe Connect account
        account_result = await self.stripe_service.create_connect_account(
            user_id, email
        )

        if not account_result["success"]:
            return {"success": False, "error": account_result["error"]}

        # Update wallet with Stripe account ID
        self.repository.update_wallet_stripe_account(
            wallet.id, account_result["account_id"]
        )

        # Create onboarding link
        link_result = await self.stripe_service.create_account_link(
            account_result["account_id"], refresh_url, return_url
        )

        if not link_result["success"]:
            return {"success": False, "error": link_result["error"]}

        return {
            "success": True,
            "account_id": account_result["account_id"],
            "onboarding_url": link_result["url"],
        }

    # Transaction operations
    async def create_tip_transaction(
        self,
        sender_id: str,
        receiver_id: str,
        amount: float,
        video_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a tip transaction."""
        # Create payment intent for sender
        payment_result = await self.stripe_service.create_payment_intent(
            amount=amount,
            metadata={
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "type": "tip",
                "video_id": video_id or "",
            },
        )

        if not payment_result["success"]:
            return payment_result

        # Create pending transaction
        transaction = Transaction(
            user_id=sender_id,
            amount=-amount,  # Debit from sender
            transaction_type=TransactionType.TIP,
            description=f"Tip to creator {receiver_id}",
            reference_id=payment_result["payment_intent_id"],
            metadata={"receiver_id": receiver_id, "video_id": video_id},
        )

        saved_transaction = self.repository.save_transaction(transaction)

        return {
            "success": True,
            "payment_intent_id": payment_result["payment_intent_id"],
            "client_secret": payment_result["client_secret"],
            "transaction_id": saved_transaction.id,
        }

    async def complete_tip_transaction(
        self, payment_intent_id: str, charge_id: str
    ) -> Dict[str, Any]:
        """Complete a tip transaction after successful payment."""
        transactions = self.repository.get_transactions_by_reference(payment_intent_id)

        for transaction in transactions:
            if transaction.transaction_type == TransactionType.TIP:
                # Update sender transaction
                completed_transaction = transaction.complete()
                self.repository.save_transaction(completed_transaction)

                # Create receiver transaction (credit)
                receiver_id = transaction.metadata.get("receiver_id")
                if receiver_id:
                    receiver_transaction = Transaction(
                        user_id=receiver_id,
                        amount=abs(transaction.amount),
                        transaction_type=TransactionType.TIP,
                        description="Tip received",
                        reference_id=charge_id,
                        metadata={
                            "sender_id": transaction.user_id,
                            "original_transaction_id": transaction.id,
                        },
                    )

                    completed_receiver = receiver_transaction.complete()
                    saved_receiver = self.repository.save_transaction(
                        completed_receiver
                    )

                    # Update receiver's wallet
                    receiver_wallet = await self.create_wallet(receiver_id)
                    updated_wallet = receiver_wallet.add_funds(abs(transaction.amount))
                    self.repository.save_wallet(updated_wallet)

                    return {
                        "success": True,
                        "transaction_id": transaction.id,
                        "receiver_transaction_id": saved_receiver.id,
                    }

        return {"success": False, "error": "Transaction not found"}

    async def get_transaction_history(
        self,
        user_id: str,
        limit: int = 50,
        transaction_type: Optional[TransactionType] = None,
    ) -> List[Transaction]:
        """Get user's transaction history."""
        return self.repository.get_user_transactions(user_id, limit, transaction_type)

    # Payout operations
    async def request_payout(self, user_id: str) -> Dict[str, Any]:
        """Request payout for available balance."""
        wallet = self.repository.get_wallet_by_user_id(user_id)
        if not wallet:
            return {"success": False, "error": "Wallet not found"}

        if wallet.balance < wallet.minimum_payout:
            return {
                "success": False,
                "error": f"Minimum payout amount is ${wallet.minimum_payout}",
            }

        if not wallet.stripe_account_id:
            return {"success": False, "error": "Stripe Connect account not setup"}

        # Calculate payout amount with fees
        platform_fee_rate = 0.05  # 5% platform fee
        fee_amount = wallet.balance * platform_fee_rate
        net_amount = wallet.balance - fee_amount

        # Create payout record
        payout = Payout(
            wallet_id=wallet.id,
            user_id=user_id,
            amount=wallet.balance,
            net_amount=net_amount,
            fee_amount=fee_amount,
            description="Weekly payout",
        )

        saved_payout = self.repository.save_payout(payout)

        # Process payout via Stripe
        payout_result = await self.stripe_service.create_payout(
            amount=net_amount,
            destination=wallet.stripe_account_id,
            metadata={"payout_id": saved_payout.id},
        )

        if payout_result["success"]:
            # Update payout with Stripe ID
            completed_payout = saved_payout.process()
            completed_payout = completed_payout.replace(
                stripe_payout_id=payout_result["payout_id"]
            )
            final_payout = self.repository.save_payout(completed_payout)

            # Update wallet balance
            updated_wallet = wallet.withdraw_funds(wallet.balance)
            self.repository.save_wallet(updated_wallet)

            return {
                "success": True,
                "payout_id": final_payout.id,
                "amount": wallet.balance,
                "net_amount": net_amount,
                "estimated_arrival": payout_result.get("arrival_date"),
            }
        else:
            # Mark payout as failed
            failed_payout = saved_payout.fail(payout_result["error"])
            self.repository.save_payout(failed_payout)

            return {"success": False, "error": payout_result["error"]}

    async def get_payout_history(self, user_id: str, limit: int = 50) -> List[Payout]:
        """Get user's payout history."""
        return self.repository.get_user_payouts(user_id, limit)

    # Subscription operations
    async def create_subscription(
        self,
        subscriber_id: str,
        creator_id: str,
        amount: float,
        interval: str = "month",
    ) -> Dict[str, Any]:
        """Create a subscription to a creator."""
        # Create or get customer for subscriber
        # This would typically get user email from user service
        customer_result = await self.stripe_service.create_customer(
            email=f"user_{subscriber_id}@example.com",
            metadata={"user_id": subscriber_id},
        )

        if not customer_result["success"]:
            return {"success": False, "error": customer_result["error"]}

        # Create price for subscription
        price_result = await self.stripe_service.create_price(
            amount=amount, interval=interval
        )

        if not price_result["success"]:
            return {"success": False, "error": price_result["error"]}

        # Create subscription
        subscription_result = await self.stripe_service.create_subscription(
            price_id=price_result["price_id"],
            customer_id=customer_result["customer_id"],
            metadata={"subscriber_id": subscriber_id, "creator_id": creator_id},
        )

        if not subscription_result["success"]:
            return {"success": False, "error": subscription_result["error"]}

        # Save subscription to database
        subscription = Subscription(
            user_id=subscriber_id,
            creator_id=creator_id,
            stripe_subscription_id=subscription_result["subscription_id"],
            status=subscription_result["status"],
            amount=subscription_result["amount"],
            currency=subscription_result["currency"],
            interval=interval,
            current_period_start=datetime.fromtimestamp(
                subscription_result["current_period_start"]
            ),
            current_period_end=datetime.fromtimestamp(
                subscription_result["current_period_end"]
            ),
        )

        saved_subscription = self.repository.save_subscription(subscription)

        return {
            "success": True,
            "subscription_id": saved_subscription.id,
            "status": saved_subscription.status,
            "amount": saved_subscription.amount,
            "next_billing_date": saved_subscription.current_period_end,
        }

    async def cancel_subscription(
        self, subscription_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Cancel a subscription."""
        subscription = self.repository.get_subscription_by_id(subscription_id)
        if not subscription or subscription.user_id != user_id:
            return {
                "success": False,
                "error": "Subscription not found or access denied",
            }

        # Cancel in Stripe
        stripe_result = await self.stripe_service.cancel_subscription(
            subscription.stripe_subscription_id
        )

        if not stripe_result["success"]:
            return {"success": False, "error": stripe_result["error"]}

        # Update database
        cancelled_subscription = subscription.cancel()
        updated_subscription = self.repository.save_subscription(cancelled_subscription)

        return {
            "success": True,
            "subscription_id": updated_subscription.id,
            "status": updated_subscription.status,
            "cancelled_at": updated_subscription.cancelled_at,
        }

    async def get_user_subscriptions(self, user_id: str) -> List[Subscription]:
        """Get user's active subscriptions."""
        return self.repository.get_user_subscriptions(user_id, include_cancelled=False)

    async def get_creator_subscribers(self, creator_id: str) -> List[Subscription]:
        """Get creator's active subscribers."""
        return self.repository.get_creator_subscribers(
            creator_id, include_cancelled=False
        )

    # Analytics
    async def get_wallet_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive wallet summary."""
        wallet = self.repository.get_wallet_by_user_id(user_id)
        if not wallet:
            return {"error": "Wallet not found"}

        # Get transaction summary for last 30 days
        transaction_summary = self.repository.get_transaction_summary(user_id, days=30)

        return {
            "balance": wallet.balance,
            "pending_balance": wallet.pending_balance,
            "total_earned": wallet.total_earned,
            "total_withdrawn": wallet.total_withdrawn,
            "status": wallet.status,
            "stripe_account_id": wallet.stripe_account_id,
            "last_30_days": transaction_summary,
        }

    async def get_creator_analytics(
        self, creator_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for creator earnings."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get subscribers count
        subscribers = self.repository.get_creator_subscribers(creator_id)

        # Get transaction summary
        transaction_summary = self.repository.get_transaction_summary(creator_id, days)

        # Get payout summary
        payouts = self.repository.get_user_payouts(creator_id)
        recent_payouts = [p for p in payouts if p.created_at >= cutoff_date]

        return {
            "period_days": days,
            "active_subscribers": len(subscribers),
            "monthly_revenue": transaction_summary["total_earnings"],
            "total_tips": transaction_summary["tips_count"],
            "total_subscriptions": transaction_summary["subscriptions_count"],
            "recent_payouts": len(recent_payouts),
            "average_tip_amount": (
                transaction_summary["total_earnings"]
                / transaction_summary["tips_count"]
                if transaction_summary["tips_count"] > 0
                else 0
            ),
            "subscriber_growth": self._calculate_subscriber_growth(creator_id, days),
        }

    def _calculate_subscriber_growth(self, creator_id: str, days: int) -> float:
        """Calculate subscriber growth rate."""
        # This would typically compare current period with previous period
        # For now, return placeholder value
        current_subscribers = len(self.repository.get_creator_subscribers(creator_id))

        if days <= 0:
            return 0.0

        # Simple growth calculation (new subscribers per day)
        return float(current_subscribers) / days
