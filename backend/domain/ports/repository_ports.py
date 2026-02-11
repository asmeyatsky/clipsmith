from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from ..entities.video import Video
from ..entities.user import User
from ..entities.caption import Caption  # Import Caption entity
from ..entities.tip import Tip  # Import Tip entity
from ..entities.follow import Follow  # Import Follow entity
from ..entities.notification import Notification, NotificationStatus
from ..entities.hashtag import Hashtag
from ..entities.content_moderation import (
    ContentModeration,
    ModerationStatus,
    ModerationSeverity,
)
from ..entities.video_editor import (
    VideoProject,
    VideoEditorAsset,
    VideoEditorTransition,
    VideoEditorTrack,
    VideoEditorCaption,
    VideoProjectStatus,
)


class VideoRepositoryPort(ABC):
    @abstractmethod
    def save(self, video: Video) -> Video:
        pass

    @abstractmethod
    def get_by_id(self, video_id: str) -> Optional[Video]:
        pass

    @abstractmethod
    def find_all(self, offset: int = 0, limit: int = 20) -> List[Video]:
        pass

    @abstractmethod
    def count_all(self) -> int:
        pass

    @abstractmethod
    def list_by_creator(self, creator_id: str) -> List[Video]:
        pass

    @abstractmethod
    def delete(self, video_id: str) -> bool:
        pass

    @abstractmethod
    def increment_views(self, video_id: str) -> Optional[Video]:
        pass

    @abstractmethod
    def search(self, query: str, offset: int = 0, limit: int = 20) -> List[Video]:
        pass

    @abstractmethod
    def count_search(self, query: str) -> int:
        pass


class InteractionRepositoryPort(ABC):
    @abstractmethod
    def toggle_like(self, user_id: str, video_id: str) -> bool:
        pass

    @abstractmethod
    def has_user_liked(self, user_id: str, video_id: str) -> bool:
        pass

    @abstractmethod
    def add_comment(self, user_id: str, username: str, video_id: str, content: str):
        pass

    @abstractmethod
    def list_comments(self, video_id: str) -> List:
        pass

    def get_user_interactions(self, user_id: str) -> List:
        return []

    def get_all_interactions(self, limit: int = 5000) -> List:
        return []

    def get_user_following(self, user_id: str) -> List:
        return []


class UserRepositoryPort(ABC):
    @abstractmethod
    def save(self, user: User) -> User:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        pass


class CaptionRepositoryPort(ABC):
    @abstractmethod
    def save(self, caption: Caption) -> Caption:
        pass

    @abstractmethod
    def get_by_video_id(self, video_id: str) -> List[Caption]:
        pass

    @abstractmethod
    def delete_by_video_id(self, video_id: str) -> bool:
        pass


class TipRepositoryPort(ABC):
    @abstractmethod
    def save(self, tip: Tip) -> Tip:
        pass

    @abstractmethod
    def get_tips_by_receiver_id(self, receiver_id: str) -> List[Tip]:
        pass

    @abstractmethod
    def get_tips_by_sender_id(self, sender_id: str) -> List[Tip]:
        pass

    @abstractmethod
    def get_tips_by_video_id(self, video_id: str) -> List[Tip]:
        pass


class FollowRepositoryPort(ABC):
    @abstractmethod
    def follow(self, follower_id: str, followed_id: str) -> Follow:
        pass

    @abstractmethod
    def unfollow(self, follower_id: str, followed_id: str) -> bool:
        pass


class NotificationRepositoryPort(ABC):
    @abstractmethod
    def save(self, notification: "Notification") -> "Notification":
        pass

    @abstractmethod
    def get_by_id(self, notification_id: str) -> Optional["Notification"]:
        pass

    @abstractmethod
    def get_user_notifications(
        self,
        user_id: str,
        status: Optional["NotificationStatus"] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List["Notification"]:
        pass

    @abstractmethod
    def count_user_notifications(
        self, user_id: str, status: Optional["NotificationStatus"] = None
    ) -> int:
        pass

    @abstractmethod
    def mark_as_read(self, notification_id: str) -> Optional["Notification"]:
        pass

    @abstractmethod
    def mark_all_as_read(self, user_id: str) -> int:
        pass

    @abstractmethod
    def delete_notification(self, notification_id: str) -> bool:
        pass

    @abstractmethod
    def get_unread_count(self, user_id: str) -> int:
        pass


class HashtagRepositoryPort(ABC):
    @abstractmethod
    def save(self, hashtag: "Hashtag") -> "Hashtag":
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional["Hashtag"]:
        pass

    @abstractmethod
    def get_trending_hashtags(self, limit: int = 50) -> List["Hashtag"]:
        pass

    @abstractmethod
    def get_popular_hashtags(self, limit: int = 50) -> List["Hashtag"]:
        pass

    @abstractmethod
    def search_hashtags(self, query: str, limit: int = 20) -> List["Hashtag"]:
        pass

    @abstractmethod
    def update_hashtag_usage(self, hashtag_name: str) -> Optional["Hashtag"]:
        pass

    @abstractmethod
    def update_trending_scores(self, hashtag_scores: dict[str, float]) -> int:
        pass

    @abstractmethod
    def get_recent_hashtags(self, hours: int = 24, limit: int = 20) -> List["Hashtag"]:
        pass


class ContentModerationRepositoryPort(ABC):
    @abstractmethod
    def save(self, moderation: "ContentModeration") -> "ContentModeration":
        pass

    @abstractmethod
    def get_by_id(self, moderation_id: str) -> Optional["ContentModeration"]:
        pass

    @abstractmethod
    def get_pending_moderations(self, limit: int = 50) -> List["ContentModeration"]:
        pass

    @abstractmethod
    def get_moderations_by_content_id(
        self, content_id: str, content_type: Optional[str] = None
    ) -> List["ContentModeration"]:
        pass

    @abstractmethod
    def get_moderations_by_status(
        self, status: "ModerationStatus"
    ) -> List["ContentModeration"]:
        pass

    @abstractmethod
    def get_moderations_by_reviewer(
        self, reviewer_id: str, limit: int = 100
    ) -> List["ContentModeration"]:
        pass

    @abstractmethod
    def get_flagged_content(
        self, severity: Optional[ModerationSeverity] = None, limit: int = 50
    ) -> List["ContentModeration"]:
        pass

    @abstractmethod
    def get_statistics(self, days: int = 30) -> Dict[str, int]:
        pass

    @abstractmethod
    def delete_old_records(self, days: int = 90) -> int:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional["Hashtag"]:
        pass

    @abstractmethod
    def get_trending_hashtags(self, limit: int = 50) -> List["Hashtag"]:
        pass

    @abstractmethod
    def get_popular_hashtags(self, limit: int = 50) -> List["Hashtag"]:
        pass

    @abstractmethod
    def search_hashtags(self, query: str, limit: int = 20) -> List["Hashtag"]:
        pass

    @abstractmethod
    def update_hashtag_usage(self, hashtag_name: str) -> Optional["Hashtag"]:
        pass

    @abstractmethod
    def update_trending_scores(self, hashtag_scores: dict[str, float]) -> int:
        pass

    @abstractmethod
    def get_recent_hashtags(self, hours: int = 24, limit: int = 20) -> List["Hashtag"]:
        pass

    @abstractmethod
    def get_by_id(self, notification_id: str) -> Optional["Notification"]:
        pass

    @abstractmethod
    def get_user_notifications(
        self,
        user_id: str,
        status: Optional["NotificationStatus"] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List["Notification"]:
        pass

    @abstractmethod
    def count_user_notifications(
        self, user_id: str, status: Optional["NotificationStatus"] = None
    ) -> int:
        pass

    @abstractmethod
    def mark_as_read(self, notification_id: str) -> Optional["Notification"]:
        pass

    @abstractmethod
    def mark_all_as_read(self, user_id: str) -> int:
        pass

    @abstractmethod
    def delete_notification(self, notification_id: str) -> bool:
        pass

    @abstractmethod
    def get_unread_count(self, user_id: str) -> int:
        pass

    @abstractmethod
    def is_following(self, follower_id: str, followed_id: str) -> bool:
        pass

    @abstractmethod
    def get_followers(self, user_id: str) -> List[Follow]:
        pass

    @abstractmethod
    def get_following(self, user_id: str) -> List[Follow]:
        pass
