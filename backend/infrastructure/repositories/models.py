from typing import Optional
from sqlmodel import Field, SQLModel
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
    secret: str = Field(unique=True)  # Encrypted secret
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
    used_at: datetime | None = Field(default=None)
    is_verified: bool = Field(default=False)
