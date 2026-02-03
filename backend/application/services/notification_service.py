import logging
from typing import Dict, Any, Optional
from datetime import datetime
from ..domain.entities.notification import Notification, NotificationType
from ..domain.ports.repository_ports import (
    NotificationRepositoryPort,
    UserRepositoryPort,
    VideoRepositoryPort,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing user notifications."""

    def __init__(
        self,
        notification_repo: NotificationRepositoryPort,
        user_repo: UserRepositoryPort,
        video_repo: VideoRepositoryPort,
    ):
        self.notification_repo = notification_repo
        self.user_repo = user_repo
        self.video_repo = video_repo

    def create_like_notification(
        self, video_id: str, liker_user_id: str, video_owner_id: str
    ) -> Notification:
        """Create notification for video like."""
        video = self.video_repo.get_by_id(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")

        liker_user = self.user_repo.get_by_id(liker_user_id)
        if not liker_user:
            raise ValueError(f"User {liker_user_id} not found")

        return Notification(
            user_id=video_owner_id,
            type=NotificationType.LIKE,
            title="New Like!",
            message=f"{liker_user.username} liked your video '{video.title}'",
            data={
                "video_id": video_id,
                "from_user_id": liker_user_id,
                "from_username": liker_user.username,
            },
        )

    def create_comment_notification(
        self,
        video_id: str,
        commenter_user_id: str,
        video_owner_id: str,
        comment_content: str,
    ) -> Notification:
        """Create notification for video comment."""
        video = self.video_repo.get_by_id(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")

        commenter_user = self.user_repo.get_by_id(commenter_user_id)
        if not commenter_user:
            raise ValueError(f"User {commenter_user_id} not found")

        # Truncate long comments
        comment_preview = (
            comment_content[:100] + "..."
            if len(comment_content) > 100
            else comment_content
        )

        return Notification(
            user_id=video_owner_id,
            type=NotificationType.COMMENT,
            title="New Comment!",
            message=f"{commenter_user.username} commented on your video '{video.title}': \"{comment_preview}\"",
            data={
                "video_id": video_id,
                "from_user_id": commenter_user_id,
                "from_username": commenter_user.username,
                "comment_preview": comment_preview,
            },
        )

    def create_follow_notification(
        self, follower_user_id: str, followed_user_id: str
    ) -> Notification:
        """Create notification for new follower."""
        follower_user = self.user_repo.get_by_id(follower_user_id)
        if not follower_user:
            raise ValueError(f"User {follower_user_id} not found")

        followed_user = self.user_repo.get_by_id(followed_user_id)
        if not followed_user:
            raise ValueError(f"User {followed_user_id} not found")

        return Notification(
            user_id=followed_user_id,
            type=NotificationType.FOLLOW,
            title="New Follower!",
            message=f"{follower_user.username} started following you",
            data={
                "from_user_id": follower_user_id,
                "from_username": follower_user.username,
            },
        )

    def create_tip_notification(
        self,
        video_id: str,
        tipper_user_id: str,
        creator_user_id: str,
        amount: float,
        currency: str = "USD",
    ) -> Notification:
        """Create notification for received tip."""
        video = self.video_repo.get_by_id(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")

        tipper_user = self.user_repo.get_by_id(tipper_user_id)
        if not tipper_user:
            raise ValueError(f"User {tipper_user_id} not found")

        return Notification(
            user_id=creator_user_id,
            type=NotificationType.TIP,
            title="New Tip!",
            message=f"{tipper_user.username} sent you a {currency} {amount:.2f} tip on your video '{video.title}'",
            data={
                "video_id": video_id,
                "from_user_id": tipper_user_id,
                "from_username": tipper_user.username,
                "amount": amount,
                "currency": currency,
            },
        )

    def create_video_processed_notification(
        self,
        user_id: str,
        video_id: str,
        success: bool,
        thumbnail_url: Optional[str] = None,
    ) -> Notification:
        """Create notification for video processing completion."""
        video = self.video_repo.get_by_id(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")

        if success:
            return Notification(
                user_id=user_id,
                type=NotificationType.VIDEO_PROCESSED,
                title="Video Ready!",
                message=f"Your video '{video.title}' has been processed and is now live",
                data={"video_id": video_id, "thumbnail_url": thumbnail_url},
            )
        else:
            return Notification(
                user_id=user_id,
                type=NotificationType.VIDEO_FAILED,
                title="Video Processing Failed",
                message=f"There was an error processing your video '{video.title}'. Please try uploading again.",
                data={"video_id": video_id},
            )

    def create_caption_generated_notification(
        self, user_id: str, video_id: str, caption_count: int
    ) -> Notification:
        """Create notification for caption generation."""
        video = self.video_repo.get_by_id(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")

        return Notification(
            user_id=user_id,
            type=NotificationType.CAPTION_GENERATED,
            title="Captions Generated!",
            message=f"Auto-generated captions are now available for your video '{video.title}' ({caption_count} captions)",
            data={"video_id": video_id, "caption_count": caption_count},
        )

    def create_system_notification(
        self,
        user_id: Optional[str],
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Create system-wide notification (can be for all users or specific user)."""
        return Notification(
            user_id=user_id,
            type=NotificationType.SYSTEM_UPDATE,
            title=title,
            message=message,
            data=data,
        )

    def send_notification(self, notification: Notification) -> bool:
        """Save notification to repository and trigger real-time delivery."""
        try:
            saved_notification = self.notification_repo.save(notification)

            # Here you would trigger real-time delivery via WebSocket, Push notification, etc.
            # For now, just log it
            logger.info(
                f"Notification created for user {notification.user_id}: {notification.title}"
            )

            # TODO: Add WebSocket push notification
            # TODO: Add email notification for important types

            return True
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    def send_bulk_notifications(self, notifications: list[Notification]) -> int:
        """Send multiple notifications efficiently."""
        success_count = 0
        for notification in notifications:
            if self.send_notification(notification):
                success_count += 1
        return success_count

    def mark_notifications_read(
        self, user_id: str, notification_ids: Optional[list[str]] = None
    ) -> int:
        """Mark notifications as read."""
        if notification_ids:
            # Mark specific notifications as read
            count = 0
            for notification_id in notification_ids:
                if self.notification_repo.mark_as_read(notification_id):
                    count += 1
            return count
        else:
            # Mark all as read
            return self.notification_repo.mark_all_as_read(user_id)

    def get_notification_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of user's notifications."""
        unread_count = self.notification_repo.get_unread_count(user_id)
        total_count = self.notification_repo.count_user_notifications(user_id)

        # Get recent notifications for breakdown
        recent_notifications = self.notification_repo.get_user_notifications(
            user_id, limit=10
        )

        # Count by type
        type_counts = {}
        for notification in recent_notifications:
            type_counts[notification.type.value] = (
                type_counts.get(notification.type.value, 0) + 1
            )

        return {
            "unread_count": unread_count,
            "total_count": total_count,
            "recent_type_breakdown": type_counts,
            "recent_notifications": [n.to_dict() for n in recent_notifications],
        }
