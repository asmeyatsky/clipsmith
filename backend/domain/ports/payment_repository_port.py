from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from ..entities.payment import Transaction, CreatorWallet, Payout, Subscription, TransactionType, TransactionStatus, PayoutStatus


class PaymentRepositoryPort(ABC):
    """Repository port for payment and wallet operations."""
    
    # Wallet operations
    @abstractmethod
    def save_wallet(self, wallet: CreatorWallet) -> CreatorWallet:
        """Save or update a creator wallet."""
        pass
    
    @abstractmethod
    def get_wallet_by_user_id(self, user_id: str) -> Optional[CreatorWallet]:
        """Get wallet by user ID."""
        pass
    
    @abstractmethod
    def get_wallet_by_id(self, wallet_id: str) -> Optional[CreatorWallet]:
        """Get wallet by ID."""
        pass
    
    @abstractmethod
    def update_wallet_stripe_account(self, wallet_id: str, stripe_account_id: str) -> CreatorWallet:
        """Update wallet with Stripe Connect account ID."""
        pass
    
    # Transaction operations
    @abstractmethod
    def save_transaction(self, transaction: Transaction) -> Transaction:
        """Save or update a transaction."""
        pass
    
    @abstractmethod
    def get_transaction_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID."""
        pass
    
    @abstractmethod
    def get_user_transactions(self, user_id: str, limit: int = 50, 
                            transaction_type: Optional[TransactionType] = None,
                            status: Optional[TransactionStatus] = None) -> List[Transaction]:
        """Get user's transaction history."""
        pass
    
    @abstractmethod
    def get_transactions_by_reference(self, reference_id: str) -> List[Transaction]:
        """Get transactions by external reference ID."""
        pass
    
    # Payout operations
    @abstractmethod
    def save_payout(self, payout: Payout) -> Payout:
        """Save or update a payout."""
        pass
    
    @abstractmethod
    def get_payout_by_id(self, payout_id: str) -> Optional[Payout]:
        """Get payout by ID."""
        pass
    
    @abstractmethod
    def get_user_payouts(self, user_id: str, limit: int = 50,
                         status: Optional[PayoutStatus] = None) -> List[Payout]:
        """Get user's payout history."""
        pass
    
    @abstractmethod
    def get_pending_payouts(self) -> List[Payout]:
        """Get all pending payouts for processing."""
        pass
    
    # Subscription operations
    @abstractmethod
    def save_subscription(self, subscription: Subscription) -> Subscription:
        """Save or update a subscription."""
        pass
    
    @abstractmethod
    def get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID."""
        pass
    
    @abstractmethod
    def get_user_subscriptions(self, user_id: str, include_cancelled: bool = False) -> List[Subscription]:
        """Get user's subscriptions."""
        pass
    
    @abstractmethod
    def get_creator_subscribers(self, creator_id: str, include_cancelled: bool = False) -> List[Subscription]:
        """Get all subscribers for a creator."""
        pass
    
    @abstractmethod
    def get_subscription_by_stripe_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID."""
        pass
    
    # Analytics operations
    @abstractmethod
    def get_wallet_balance(self, user_id: str) -> float:
        """Get current wallet balance for user."""
        pass
    
    @abstractmethod
    def get_total_earnings(self, user_id: str, days: int = 30) -> float:
        """Get total earnings for user in specified period."""
        pass
    
    @abstractmethod
    def get_transaction_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get transaction summary for analytics."""
        pass


class StripeServicePort(ABC):
    """Service port for Stripe operations."""
    
    # Payment processing
    @abstractmethod
    async def create_payment_intent(self, amount: float, currency: str = "USD", 
                                 metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a Stripe payment intent."""
        pass
    
    @abstractmethod
    async def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm a payment intent."""
        pass
    
    @abstractmethod
    async def refund_payment(self, charge_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Refund a payment."""
        pass
    
    # Connect accounts (for creators)
    @abstractmethod
    async def create_connect_account(self, user_id: str, email: str) -> Dict[str, Any]:
        """Create a Stripe Connect account for creator."""
        pass
    
    @abstractmethod
    async def create_account_link(self, account_id: str, refresh_url: str, 
                                return_url: str) -> Dict[str, Any]:
        """Create account link for Stripe Connect onboarding."""
        pass
    
    @abstractmethod
    async def get_connect_account(self, account_id: str) -> Dict[str, Any]:
        """Get Stripe Connect account details."""
        pass
    
    @abstractmethod
    async def update_connect_account(self, account_id: str, 
                                  updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update Stripe Connect account."""
        pass
    
    # Payouts
    @abstractmethod
    async def create_payout(self, amount: float, destination: str,
                          currency: str = "USD", metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a payout to a bank account."""
        pass
    
    @abstractmethod
    async def get_payout(self, payout_id: str) -> Dict[str, Any]:
        """Get payout details."""
        pass
    
    # Subscriptions
    @abstractmethod
    async def create_subscription(self, price_id: str, customer_id: str,
                                metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a subscription."""
        pass
    
    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription."""
        pass
    
    @abstractmethod
    async def create_price(self, amount: float, currency: str = "USD",
                         interval: str = "month", product_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a price for subscriptions."""
        pass
    
    @abstractmethod
    async def create_customer(self, email: str, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a Stripe customer."""
        pass
    
    # Webhooks
    @abstractmethod
    async def construct_webhook_event(self, payload: str, signature: str, 
                                    secret: str) -> Dict[str, Any]:
        """Construct and verify webhook event."""
        pass