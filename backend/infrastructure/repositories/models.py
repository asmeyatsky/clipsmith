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
    url: str
    status: str
    views: int = Field(default=0)
    likes: int = Field(default=0)
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
