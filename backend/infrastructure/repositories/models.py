from typing import Optional, List, Dict, Any
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
import uuid


# We need a dedicated DB model that maps to the SQL table
# but also aligns with the Domain Entity
class UserDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class VideoDB(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    title: str
    description: str
    creator_id: str = Field(index=True)
    url: str | None = None  # Corrected: url can be None
    thumbnail_url: str | None = None  # New field
    status: str
    views: int = Field(default=0)
    likes: int = Field(default=0)
    duration: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.now)


class LikeDB(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    video_id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)


class CommentDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    video_id: str = Field(index=True)
    content: str
    username: str  # Denormalized for display speed
    created_at: datetime = Field(default_factory=datetime.now)


class CaptionDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    video_id: str = Field(index=True)
    text: str
    start_time: float
    end_time: float
    language: str = Field(default="en")
    created_at: datetime = Field(default_factory=datetime.now)


class TipDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    sender_id: str = Field(index=True)
    receiver_id: str = Field(index=True)
    video_id: str | None = Field(default=None, index=True)
    amount: float
    currency: str = Field(default="USD")
    created_at: datetime = Field(default_factory=datetime.now)


class FollowDB(SQLModel, table=True):
    follower_id: str = Field(primary_key=True, index=True)
    followed_id: str = Field(primary_key=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now)


class PasswordResetDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)


class NotificationDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    type: str = Field(index=True)
    title: str
    message: str
    data: str | None = Field(default=None)  # JSON string for additional context
    status: str = Field(default="unread", index=True)
    read_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)


class HashtagDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(unique=True, index=True)
    count: int = Field(default=0)
    trending_score: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.now)
    last_used_at: datetime | None = Field(default=None)


class ContentModerationDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    content_type: str = Field(index=True)
    content_id: str = Field(index=True)
    user_id: str | None = Field(default=None, index=True)
    reporter_id: str | None = Field(default=None, index=True)
    status: str = Field(default="pending", index=True)
    moderation_type: str = Field(default="automatic", index=True)
    severity: str = Field(default="low", index=True)
    reason: str | None = Field(default=None)
    confidence_score: float | None = Field(default=None)
    ai_labels: str | None = Field(default=None)  # JSON string
    human_reviewer_id: str | None = Field(default=None, index=True)
    human_notes: str | None = Field(default=None)
    auto_action: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    reviewed_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

class EmailVerificationDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    email: str = Field(index=True)
    token: str = Field(unique=True, index=True)
    status: str = Field(default="pending", index=True)
    expires_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    verified_at: datetime | None = Field(default=None)

class TwoFactorSecretDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    method: str = Field(index=True)
    secret: str = Field(unique=True)
    backup_codes: str | None = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    last_used_at: datetime | None = Field(default=None)

class TwoFactorVerificationDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    secret_id: str = Field(index=True)
    code: str = Field(index=True)
    expires_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    used_at: datetime | None = Field(default=False)
    is_verified: bool = Field(default=False)

class VideoProjectDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    title: str
    description: Optional[str] = None
    status: str = Field(default="draft", index=True)
    thumbnail_url: Optional[str] = None
    duration: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    settings: Optional[str] = Field(default=None)  # JSON string
    metadata: Optional[str] = Field(default=None)  # JSON string
    permission: str = Field(default="private", index=True)

class VideoEditorAssetDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    type: str = Field(index=True)
    name: str
    original_url: Optional[str] = None
    storage_url: Optional[str] = None
    metadata: Optional[str] = Field(default=None)
    duration: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VideoEditorTransitionDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    asset_id: str = Field(index=True)
    type: str  Field(index=True)
    start_time: float = Field(default=0.0)
    end_time: float = Field(default=0.0)
    duration: float = Field(default=0.0)
    easing: str = Field(default="linear")
    parameters: Optional[str] = None

class VideoEditorTrackDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    asset_id: str = Field(index=True)
    type: str = Field(index=True)
    start_time: float = Field(default=0.0)
    end_time: float = Field(default=0.0)
    content: Optional[Dict[str, Any]] = None

class VideoEditorCaptionDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    video_asset_id: str = Field(index=True)
    start_time: float = Field(default=0.0)
    end_time: float = Field(default=0.0)
    text: str = ""
    style: Optional[Dict[str, Any]] = None
    is_auto_generated: bool = Field(default=False)
    language: str = Field(default="en")
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class EmailVerificationDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    email: str = Field(index=True)
    token: str = Field(unique=True, index=True)
    status: str = Field(default="pending", index=True)
    expires_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    verified_at: datetime | None = Field(default=None)


class TwoFactorSecretDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    method: str = Field(index=True)
    secret: str = Field(unique=True)  # Encrypted secret
    backup_codes: str | None = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    last_used_at: datetime | None = Field(default=None)


from typing import List, Optional
from sqlmodel import Session, select, func, and_, desc
from ...domain.entities.video import Video
from ...domain.ports.repository_ports import VideoRepositoryPort
from .database import engine
from .models import VideoDB, VideoProjectDB, VideoEditorAssetDB, VideoEditorTransitionDB, VideoEditorTrackDB, VideoEditorCaptionDB

class SQLiteVideoEditorRepository(VideoRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def save_video_project(self, project: VideoProject) -> VideoProject:
        project_db = VideoProjectDB.model_validate(project)
        project_db = self.session.merge(project_db)
        self.session.commit()
        self.session.refresh(project_db)
        return VideoProject(**project_db.model_dump())

    def get_user_projects(self, user_id: str, limit: int = 20, status: Optional[str] = None) -> List[VideoProject]:
        query = select(VideoProjectDB).where(VideoProjectDB.user_id == user_id)
        
        if status:
            status_enum = VideoProjectStatus(status)
            query = query.where(VideoProjectDB.status == status_enum)
        
        query = query.order_by(VideoProjectDB.updated_at.desc()).limit(limit)
        
        results = self.session.exec(query).all()
        return [VideoProject(**project.model_dump()) for project in results]

    def delete_video_project(self, project_id: str) -> bool:
        project_db = self.session.get(VideoProjectDB, project_id)
        if not project_db:
            return False
        
        self.session.delete(project_db)
        self.session.commit(    )
        return True


# Payment and Wallet Models
class TransactionDB(SQLModel, table=True):
    __tablename__ = "transactions"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    amount: float
    currency: str = Field(default="USD")
    transaction_type: str = Field(index=True)  # TransactionType enum value
    status: str = Field(default="pending", index=True)  # TransactionStatus enum value
    description: Optional[str] = None
    reference_id: Optional[str] = Field(index=True)  # External reference
    metadata: Optional[str] = Field(default=None)  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Relationships
    user: "UserDB" = Relationship(back_populates="transactions")


class CreatorWalletDB(SQLModel, table=True):
    __tablename__ = "creator_wallets"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", unique=True, index=True)
    balance: float = Field(default=0.0)
    pending_balance: float = Field(default=0.0)
    total_earned: float = Field(default=0.0)
    total_withdrawn: float = Field(default=0.0)
    currency: str = Field(default="USD")
    status: str = Field(default="active")  # WalletStatus enum value
    stripe_account_id: Optional[str] = Field(index=True)
    payout_schedule: str = Field(default="weekly")
    minimum_payout: float = Field(default=10.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_payout_at: Optional[datetime] = None
    
    # Relationships
    user: "UserDB" = Relationship(back_populates="wallet")
    transactions: List["TransactionDB"] = Relationship(back_populates="user")
    payouts: List["PayoutDB"] = Relationship(back_populates="wallet")


class PayoutDB(SQLModel, table=True):
    __tablename__ = "payouts"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    wallet_id: str = Field(foreign_key="creator_wallets.id")
    user_id: str = Field(foreign_key="users.id", index=True)
    amount: float
    currency: str = Field(default="USD")
    status: str = Field(default="pending", index=True)  # PayoutStatus enum value
    stripe_payout_id: Optional[str] = Field(index=True)
    bank_account_id: Optional[str] = None
    fee_amount: float = Field(default=0.0)
    net_amount: float
    description: Optional[str] = None
    metadata: Optional[str] = Field(default=None)  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_reason: Optional[str] = None
    
    # Relationships
    wallet: "CreatorWalletDB" = Relationship(back_populates="payouts")


class SubscriptionDB(SQLModel, table=True):
    __tablename__ = "subscriptions"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)  # Subscriber
    creator_id: str = Field(foreign_key="users.id", index=True)  # Creator being subscribed to
    stripe_subscription_id: str = Field(unique=True, index=True)
    status: str = Field(index=True)  # Stripe subscription status
    amount: float
    currency: str = Field(default="USD")
    interval: str  # month, year
    current_period_start: datetime
    current_period_end: datetime
    cancelled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Relationships
    subscriber: "UserDB" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[SubscriptionDB.user_id]"}
    )
    creator: "UserDB" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[SubscriptionDB.creator_id]"}
    )


# Analytics Database Models
class VideoAnalyticsDB(SQLModel, table=True):
    __tablename__ = "video_analytics"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    video_id: str = Field(index=True)
    user_id: str = Field(index=True)
    views: int = Field(default=0)
    likes: int = Field(default=0)
    comments: int = Field(default=0)
    shares: int = Field(default=0)
    tips_count: int = Field(default=0)
    tips_amount: float = Field(default=0.0)
    watch_time: float = Field(default=0.0)
    average_watch_time: float = Field(default=0.0)
    engagement_rate: float = Field(default=0.0)
    reach: int = Field(default=0)
    impressions: int = Field(default=0)
    period_start: datetime
    period_end: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class CreatorAnalyticsDB(SQLModel, table=True):
    __tablename__ = "creator_analytics"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    period: str = Field(index=True)  # TimePeriod enum value
    period_start: datetime
    period_end: datetime
    total_followers: int = Field(default=0)
    new_followers: int = Field(default=0)
    follower_growth_rate: float = Field(default=0.0)
    total_videos: int = Field(default=0)
    total_views: int = Field(default=0)
    total_likes: int = Field(default=0)
    total_comments: int = Field(default=0)
    total_shares: int = Field(default=0)
    average_engagement_rate: float = Field(default=0.0)
    top_performing_videos: Optional[str] = Field(default=None)  # JSON string
    total_tips: float = Field(default=0.0)
    total_subscriptions: float = Field(default=0.0)
    total_revenue: float = Field(default=0.0)
    average_revenue_per_follower: float = Field(default=0.0)
    most_viewed_video: Optional[str] = Field(default=None)
    most_liked_video: Optional[str] = Field(default=None)
    most_commented_video: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: Optional[datetime] = None


class TimeSeriesDataDB(SQLModel, table=True):
    __tablename__ = "time_series_data"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    metric_type: str = Field(index=True)  # MetricType enum value
    time_period: str = Field(index=True)  # TimePeriod enum value
    data_points: Optional[str] = Field(default=None)  # JSON string
    period_start: datetime
    period_end: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class AudienceDemographicsDB(SQLModel, table=True):
    __tablename__ = "audience_demographics"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    age_groups: Optional[str] = Field(default=None)  # JSON string
    gender_distribution: Optional[str] = Field(default=None)  # JSON string
    location_distribution: Optional[str] = Field(default=None)  # JSON string
    device_distribution: Optional[str] = Field(default=None)  # JSON string
    language_distribution: Optional[str] = Field(default=None)  # JSON string
    period_start: datetime
    period_end: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class ContentPerformanceDB(SQLModel, table=True):
    __tablename__ = "content_performance"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    video_id: str = Field(index=True)
    content_type: str = Field(index=True)  # ContentType enum value
    views: int = Field(default=0)
    views_per_day: float = Field(default=0.0)
    retention_rate: float = Field(default=0.0)
    click_through_rate: float = Field(default=0.0)
    likes: int = Field(default=0)
    comments: int = Field(default=0)
    shares: int = Field(default=0)
    saves: int = Field(default=0)
    tips_amount: float = Field(default=0.0)
    subscription_conversions: int = Field(default=0)
    peak_view_time: Optional[datetime] = None
    publish_date: datetime
    first_24h_views: int = Field(default=0)
    first_7d_views: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: Optional[datetime] = None
