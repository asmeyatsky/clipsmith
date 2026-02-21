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
    extra_metadata: Optional[str] = Field(
        default=None, sa_column_kwargs={"name": "extra_metadata"}
    )  # JSON string
    permission: str = Field(default="private", index=True)


class VideoEditorAssetDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    type: str = Field(index=True)
    name: str
    original_url: Optional[str] = None
    storage_url: Optional[str] = None
    extra_metadata: Optional[str] = Field(
        default=None, sa_column_kwargs={"name": "extra_metadata"}
    )
    duration: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VideoEditorTransitionDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    asset_id: str = Field(index=True)
    type: str = Field(index=True)
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
    content: Optional[str] = Field(default=None)  # JSON string


class VideoEditorCaptionDB(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    video_asset_id: str = Field(index=True)
    start_time: float = Field(default=0.0)
    end_time: float = Field(default=0.0)
    text: str = ""
    style: Optional[str] = Field(default=None)  # JSON string
    is_auto_generated: bool = Field(default=False)
    language: str = Field(default="en")
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class VideoEditorKeyframeDB(SQLModel, table=True):
    """Keyframe support for animations and effects."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    track_id: str = Field(index=True)
    property_name: str  # e.g., "opacity", "scale", "position"
    time: float
    value: str  # JSON value (can be number, string, or array for position)
    easing: str = Field(default="linear")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VideoEditorColorGradeDB(SQLModel, table=True):
    """Color grading settings for video tracks."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    track_id: str = Field(index=True)
    brightness: float = Field(default=0.0)  # -100 to 100
    contrast: float = Field(default=0.0)  # -100 to 100
    saturation: float = Field(default=0.0)  # -100 to 100
    temperature: float = Field(default=0.0)  # -100 to 100 (cool to warm)
    tint: float = Field(default=0.0)  # -100 to 100 (green to magenta)
    highlights: float = Field(default=0.0)  # -100 to 100
    shadows: float = Field(default=0.0)  # -100 to 100
    vibrance: float = Field(default=0.0)  # -100 to 100
    filters: Optional[str] = Field(default=None)  # JSON array of filter names
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class VideoEditorAudioMixDB(SQLModel, table=True):
    """Audio mixing settings for tracks."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    track_id: str = Field(index=True)
    volume: float = Field(default=1.0)  # 0.0 to 2.0
    pan: float = Field(default=0.0)  # -1.0 (left) to 1.0 (right)
    mute: bool = Field(default=False)
    solo: bool = Field(default=False)
    fade_in: float = Field(default=0.0)  # seconds
    fade_out: float = Field(default=0.0)  # seconds
    equalizer: Optional[str] = Field(
        default=None
    )  # JSON: {"low": 0, "mid": 0, "high": 0}
    audio_effects: Optional[str] = Field(default=None)  # JSON array of effect names
    duck_others: bool = Field(default=False)  # Lower other tracks when this one plays
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class VideoEditorChromaKeyDB(SQLModel, table=True):
    """Chroma key (green screen) settings."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    track_id: str = Field(index=True)
    enabled: bool = Field(default=False)
    key_color: str = Field(default="#00FF00")  # RGB hex color
    similarity: float = Field(default=0.4)  # 0.0 to 1.0
    smoothness: float = Field(default=0.1)  # 0.0 to 1.0
    spill_suppression: float = Field(default=0.1)  # 0.0 to 1.0
    background_type: str = Field(default="none")  # none, color, image, video
    background_value: Optional[str] = None  # color hex, image URL, or video asset ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class VideoEditorEffectDB(SQLModel, table=True):
    """Effects that can be applied to tracks."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    track_id: str = Field(index=True)
    effect_type: str  # blur, sharpen, distort, etc.
    parameters: str  # JSON object with effect-specific params
    start_time: float = Field(default=0.0)
    end_time: float = Field(default=0.0)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# AI-Powered Tools Models
class AICaptionJobDB(SQLModel, table=True):
    """AI-generated caption jobs."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    user_id: str = Field(index=True)
    video_asset_id: str = Field(index=True)
    status: str = Field(
        default="pending", index=True
    )  # pending, processing, completed, failed
    language: str = Field(default="en")
    result: Optional[str] = None  # JSON array of captions
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class AITemplateDB(SQLModel, table=True):
    """AI-generated templates."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    description: Optional[str] = None
    category: str = Field(index=True)  # intro, outro, social, promo, etc.
    style: str  # modern, vintage, cinematic, etc.
    thumbnail_url: Optional[str] = None
    project_data: str  # JSON project structure
    is_premium: bool = Field(default=False)
    price: float = Field(default=0.0)
    usage_count: int = Field(default=0)
    creator_id: Optional[str] = Field(index=True)
    is_public: bool = Field(default=True)
    tags: Optional[str] = None  # JSON array
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class AIVideoGenerationDB(SQLModel, table=True):
    """AI video generation jobs (text-to-video, image-to-video)."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    user_id: str = Field(index=True)
    generation_type: str  # text_to_video, image_to_video, style_transfer
    prompt: str
    negative_prompt: Optional[str] = None
    duration: float = Field(default=5.0)  # seconds
    status: str = Field(default="pending", index=True)
    model_version: str = Field(default="v1")
    settings: Optional[str] = None  # JSON: resolution, fps, etc.
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class AIVoiceOverDB(SQLModel, table=True):
    """AI voice-over generation jobs."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(index=True)
    user_id: str = Field(index=True)
    text: str
    voice_id: str  # Voice model ID
    language: str = Field(default="en")
    speed: float = Field(default=1.0)
    status: str = Field(default="pending", index=True)
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


# Premium Content Models
class PremiumContentDB(SQLModel, table=True):
    """Premium/pay-per-view content."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    creator_id: str = Field(index=True)
    video_id: str = Field(index=True)
    price: float
    currency: str = Field(default="USD")
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    purchase_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class PremiumPurchaseDB(SQLModel, table=True):
    """Records of premium content purchases."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    premium_content_id: str = Field(index=True)
    amount: float
    currency: str = Field(default="USD")
    stripe_payment_id: Optional[str] = Field(index=True)
    status: str = Field(default="pending")  # pending, completed, refunded
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Brand Collaboration Models
class BrandCampaignDB(SQLModel, table=True):
    """Brand collaboration campaigns."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    brand_id: str = Field(index=True)
    creator_id: str = Field(index=True)
    title: str
    description: Optional[str] = None
    budget: float
    requirements: Optional[str] = None  # JSON
    deliverables: Optional[str] = None  # JSON
    deadline: Optional[datetime] = None
    status: str = Field(
        default="pending"
    )  # pending, accepted, rejected, completed, cancelled
    payment_status: str = Field(default="unpaid")  # unpaid, paid
    stripe_payment_id: Optional[str] = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class BrandProfileDB(SQLModel, table=True):
    """Brand/company profiles for collaborations."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(unique=True, index=True)  # The brand's user account
    company_name: str
    industry: str
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


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
    extra_metadata: Optional[str] = Field(
        default=None, sa_column_kwargs={"name": "extra_metadata"}
    )  # JSON string
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
    extra_metadata: Optional[str] = Field(
        default=None, sa_column_kwargs={"name": "extra_metadata"}
    )  # JSON string
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
    creator_id: str = Field(
        foreign_key="users.id", index=True
    )  # Creator being subscribed to
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


class ProjectMonetizationDB(SQLModel, table=True):
    __tablename__ = "project_monetization"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(unique=True, index=True)
    tips_enabled: bool = Field(default=True)
    subscriptions_enabled: bool = Field(default=False)
    suggested_tip_amounts: str = Field(default="[1, 5, 10, 20]")
    subscription_price: float = Field(default=9.99)
    subscription_tier_name: str = Field(default="Premium")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
