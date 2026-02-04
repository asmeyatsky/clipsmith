from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, and_, desc, func
from ...domain.entities.payment import (
    Transaction,
    CreatorWallet,
    Payout,
    Subscription,
    TransactionType,
    TransactionStatus,
    PayoutStatus,
)
from ...domain.ports.payment_repository_port import PaymentRepositoryPort
from .database import engine
from .models import TransactionDB, CreatorWalletDB, PayoutDB, SubscriptionDB
import json


class SQLitePaymentRepository(PaymentRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    # Wallet operations
    def save_wallet(self, wallet: CreatorWallet) -> CreatorWallet:
        wallet_db = CreatorWalletDB.model_validate(wallet)
        wallet_db = self.session.merge(wallet_db)
        self.session.commit()
        self.session.refresh(wallet_db)
        return CreatorWallet(**wallet_db.model_dump())

    def get_wallet_by_user_id(self, user_id: str) -> Optional[CreatorWallet]:
        wallet_db = self.session.exec(
            select(CreatorWalletDB).where(CreatorWalletDB.user_id == user_id)
        ).first()
        if wallet_db:
            return CreatorWallet(**wallet_db.model_dump())
        return None

    def get_wallet_by_id(self, wallet_id: str) -> Optional[CreatorWallet]:
        wallet_db = self.session.get(CreatorWalletDB, wallet_id)
        if wallet_db:
            return CreatorWallet(**wallet_db.model_dump())
        return None

    def update_wallet_stripe_account(
        self, wallet_id: str, stripe_account_id: str
    ) -> CreatorWallet:
        wallet_db = self.session.get(CreatorWalletDB, wallet_id)
        if not wallet_db:
            raise ValueError("Wallet not found")

        wallet_db.stripe_account_id = stripe_account_id
        self.session.commit()
        self.session.refresh(wallet_db)
        return CreatorWallet(**wallet_db.model_dump())

    # Transaction operations
    def save_transaction(self, transaction: Transaction) -> Transaction:
        transaction_db = TransactionDB.model_validate(transaction)
        # Convert metadata dict to JSON string if needed
        if transaction.metadata:
            transaction_db.metadata = json.dumps(transaction.metadata)

        transaction_db = self.session.merge(transaction_db)
        self.session.commit()
        self.session.refresh(transaction_db)
        return Transaction(**transaction_db.model_dump())

    def get_transaction_by_id(self, transaction_id: str) -> Optional[Transaction]:
        transaction_db = self.session.get(TransactionDB, transaction_id)
        if transaction_db:
            return Transaction(**transaction_db.model_dump())
        return None

    def get_user_transactions(
        self,
        user_id: str,
        limit: int = 50,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
    ) -> List[Transaction]:
        query = select(TransactionDB).where(TransactionDB.user_id == user_id)

        if transaction_type:
            query = query.where(
                TransactionDB.transaction_type == transaction_type.value
            )

        if status:
            query = query.where(TransactionDB.status == status.value)

        query = query.order_by(TransactionDB.created_at.desc()).limit(limit)

        results = self.session.exec(query).all()
        return [Transaction(**transaction.model_dump()) for transaction in results]

    def get_transactions_by_reference(self, reference_id: str) -> List[Transaction]:
        query = select(TransactionDB).where(TransactionDB.reference_id == reference_id)
        query = query.order_by(TransactionDB.created_at.desc())

        results = self.session.exec(query).all()
        return [Transaction(**transaction.model_dump()) for transaction in results]

    # Payout operations
    def save_payout(self, payout: Payout) -> Payout:
        payout_db = PayoutDB.model_validate(payout)
        # Convert metadata dict to JSON string if needed
        if payout.metadata:
            payout_db.metadata = json.dumps(payout.metadata)

        payout_db = self.session.merge(payout_db)
        self.session.commit()
        self.session.refresh(payout_db)
        return Payout(**payout_db.model_dump())

    def get_payout_by_id(self, payout_id: str) -> Optional[Payout]:
        payout_db = self.session.get(PayoutDB, payout_id)
        if payout_db:
            return Payout(**payout_db.model_dump())
        return None

    def get_user_payouts(
        self, user_id: str, limit: int = 50, status: Optional[PayoutStatus] = None
    ) -> List[Payout]:
        query = select(PayoutDB).where(PayoutDB.user_id == user_id)

        if status:
            query = query.where(PayoutDB.status == status.value)

        query = query.order_by(PayoutDB.created_at.desc()).limit(limit)

        results = self.session.exec(query).all()
        return [Payout(**payout.model_dump()) for payout in results]

    def get_pending_payouts(self) -> List[Payout]:
        query = select(PayoutDB).where(PayoutDB.status == PayoutStatus.PENDING.value)
        query = query.order_by(PayoutDB.created_at.asc())

        results = self.session.exec(query).all()
        return [Payout(**payout.model_dump()) for payout in results]

    # Subscription operations
    def save_subscription(self, subscription: Subscription) -> Subscription:
        subscription_db = SubscriptionDB.model_validate(subscription)
        subscription_db = self.session.merge(subscription_db)
        self.session.commit()
        self.session.refresh(subscription_db)
        return Subscription(**subscription_db.model_dump())

    def get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        subscription_db = self.session.get(SubscriptionDB, subscription_id)
        if subscription_db:
            return Subscription(**subscription_db.model_dump())
        return None

    def get_user_subscriptions(
        self, user_id: str, include_cancelled: bool = False
    ) -> List[Subscription]:
        query = select(SubscriptionDB).where(SubscriptionDB.user_id == user_id)

        if not include_cancelled:
            query = query.where(SubscriptionDB.status != "cancelled")

        query = query.order_by(SubscriptionDB.created_at.desc())

        results = self.session.exec(query).all()
        return [Subscription(**subscription.model_dump()) for subscription in results]

    def get_creator_subscribers(
        self, creator_id: str, include_cancelled: bool = False
    ) -> List[Subscription]:
        query = select(SubscriptionDB).where(SubscriptionDB.creator_id == creator_id)

        if not include_cancelled:
            query = query.where(SubscriptionDB.status == "active")

        query = query.order_by(SubscriptionDB.created_at.desc())

        results = self.session.exec(query).all()
        return [Subscription(**subscription.model_dump()) for subscription in results]

    def get_subscription_by_stripe_id(
        self, stripe_subscription_id: str
    ) -> Optional[Subscription]:
        subscription_db = self.session.exec(
            select(SubscriptionDB).where(
                SubscriptionDB.stripe_subscription_id == stripe_subscription_id
            )
        ).first()
        if subscription_db:
            return Subscription(**subscription_db.model_dump())
        return None

    # Analytics operations
    def get_wallet_balance(self, user_id: str) -> float:
        wallet = self.get_wallet_by_user_id(user_id)
        return wallet.balance if wallet else 0.0

    def get_total_earnings(self, user_id: str, days: int = 30) -> float:
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = self.session.exec(
            select(func.sum(TransactionDB.amount)).where(
                and_(
                    TransactionDB.user_id == user_id,
                    TransactionDB.transaction_type == TransactionType.TIP.value,
                    TransactionDB.status == TransactionStatus.COMPLETED.value,
                    TransactionDB.created_at >= cutoff_date,
                )
            )
        ).first()

        return float(result) if result else 0.0

    def get_transaction_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get transactions in date range
        transactions = self.session.exec(
            select(TransactionDB)
            .where(
                and_(
                    TransactionDB.user_id == user_id,
                    TransactionDB.created_at >= cutoff_date,
                )
            )
            .order_by(TransactionDB.created_at.desc())
        ).all()

        summary = {
            "total_earnings": 0.0,
            "total_spending": 0.0,
            "transaction_count": len(transactions),
            "tips_count": 0,
            "subscriptions_count": 0,
            "payouts_count": 0,
            "refunds_count": 0,
        }

        for transaction in transactions:
            if transaction.amount > 0:
                summary["total_earnings"] += transaction.amount
            else:
                summary["total_spending"] += abs(transaction.amount)

            # Count by type
            if transaction.transaction_type == TransactionType.TIP.value:
                summary["tips_count"] += 1
            elif transaction.transaction_type == TransactionType.SUBSCRIPTION.value:
                summary["subscriptions_count"] += 1
            elif transaction.transaction_type == TransactionType.PAYOUT.value:
                summary["payouts_count"] += 1
            elif transaction.transaction_type == TransactionType.REFUND.value:
                summary["refunds_count"] += 1

        return summary
