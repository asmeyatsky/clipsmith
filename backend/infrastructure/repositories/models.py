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
    url: str | None = None # Corrected: url can be None
    thumbnail_url: str | None = None # New field
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
    username: str # Denormalized for display speed
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
