from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import uuid


class NotificationType(str, Enum):
    LIKE = "like"
    COMMENT = "comment"
    FOLLOW = "follow"
    TIP = "tip"
    VIDEO_PROCESSED = "video_processed"
    VIDEO_FAILED = "video_failed"
    CAPTION_GENERATED = "caption_generated"
    MENTION = "mention"
    SYSTEM_UPDATE = "system_update"


class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


@dataclass(frozen=True, kw_only=True)
class Notification:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: NotificationType
    title: str
    message: str
    data: Optional[Dict[str, Any]] = (
        None  # Additional context (video_id, from_user, etc.)
    )
    status: NotificationStatus = NotificationStatus.UNREAD
    created_at: datetime = field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None

    def mark_as_read(self) -> "Notification":
        return replace(self, status=NotificationStatus.READ, read_at=datetime.utcnow())

    def mark_as_archived(self) -> "Notification":
        return replace(self, status=NotificationStatus.ARCHIVED)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }
