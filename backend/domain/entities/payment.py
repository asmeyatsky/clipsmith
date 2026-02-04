from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid


class TransactionType(str, Enum):
    TIP = "tip"
    SUBSCRIPTION = "subscription"
    PURCHASE = "purchase"
    REFUND = "refund"
    PAYOUT = "payout"
    PLATFORM_FEE = "platform_fee"
    BONUS = "bonus"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PayoutStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WalletStatus(str, Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    SUSPENDED = "suspended"
    CLOSED = "closed"


@dataclass(frozen=True, kw_only=True)
class Transaction:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    amount: float  # Positive for credits, negative for debits
    currency: str = "USD"
    transaction_type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING
    description: Optional[str] = None
    reference_id: Optional[str] = None  # External reference (Stripe payment ID, etc.)
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def complete(self) -> "Transaction":
        """Mark transaction as completed."""
        return self.replace(
            status=TransactionStatus.COMPLETED,
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

    def fail(self) -> "Transaction":
        """Mark transaction as failed."""
        return self.replace(
            status=TransactionStatus.FAILED, updated_at=datetime.utcnow()
        )

    def refund(self) -> "Transaction":
        """Mark transaction as refunded."""
        return self.replace(
            status=TransactionStatus.REFUNDED, updated_at=datetime.utcnow()
        )


@dataclass(frozen=True, kw_only=True)
class CreatorWallet:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    balance: float = 0.0
    pending_balance: float = 0.0  # Amount pending clearance
    total_earned: float = 0.0
    total_withdrawn: float = 0.0
    currency: str = "USD"
    status: WalletStatus = WalletStatus.ACTIVE
    stripe_account_id: Optional[str] = None  # Stripe Connect account ID
    payout_schedule: str = "weekly"  # weekly, biweekly, monthly
    minimum_payout: float = 10.0
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: Optional[datetime] = None
    last_payout_at: Optional[datetime] = None

    def add_funds(self, amount: float) -> "CreatorWallet":
        """Add funds to wallet (pending clearance)."""
        return self.replace(
            pending_balance=self.pending_balance + amount,
            total_earned=self.total_earned + amount,
            updated_at=datetime.utcnow(),
        )

    def clear_funds(self, amount: float) -> "CreatorWallet":
        """Clear pending funds to available balance."""
        return self.replace(
            balance=self.balance + amount,
            pending_balance=self.pending_balance - amount,
            updated_at=datetime.utcnow(),
        )

    def withdraw_funds(self, amount: float) -> "CreatorWallet":
        """Withdraw funds from wallet."""
        return self.replace(
            balance=self.balance - amount,
            total_withdrawn=self.total_withdrawn + amount,
            updated_at=datetime.utcnow(),
            last_payout_at=datetime.utcnow(),
        )

    def freeze(self) -> "CreatorWallet":
        """Freeze wallet."""
        return self.replace(status=WalletStatus.FROZEN, updated_at=datetime.utcnow())

    def activate(self) -> "CreatorWallet":
        """Activate wallet."""
        return self.replace(status=WalletStatus.ACTIVE, updated_at=datetime.utcnow())


@dataclass(frozen=True, kw_only=True)
class Payout:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    wallet_id: str
    user_id: str
    amount: float
    currency: str = "USD"
    status: PayoutStatus = PayoutStatus.PENDING
    stripe_payout_id: Optional[str] = None
    bank_account_id: Optional[str] = None
    fee_amount: float = 0.0
    net_amount: float  # Amount after fees
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_reason: Optional[str] = None

    def process(self) -> "Payout":
        """Mark payout as processing."""
        return self.replace(
            status=PayoutStatus.PROCESSING, updated_at=datetime.utcnow()
        )

    def complete(self, stripe_payout_id: str) -> "Payout":
        """Mark payout as completed."""
        return self.replace(
            status=PayoutStatus.COMPLETED,
            stripe_payout_id=stripe_payout_id,
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

    def fail(self, reason: str) -> "Payout":
        """Mark payout as failed."""
        return self.replace(
            status=PayoutStatus.FAILED,
            failed_reason=reason,
            updated_at=datetime.utcnow(),
        )


@dataclass(frozen=True, kw_only=True)
class Subscription:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    creator_id: str  # The creator being subscribed to
    stripe_subscription_id: str
    status: str  # active, cancelled, past_due, unpaid
    amount: float
    currency: str = "USD"
    interval: str  # month, year
    current_period_start: datetime
    current_period_end: datetime
    cancelled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: Optional[datetime] = None

    def cancel(self) -> "Subscription":
        """Cancel subscription."""
        return self.replace(
            status="cancelled",
            cancelled_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def renew(self, new_period_end: datetime) -> "Subscription":
        """Renew subscription."""
        return self.replace(
            current_period_start=datetime.utcnow(),
            current_period_end=new_period_end,
            updated_at=datetime.utcnow(),
        )
