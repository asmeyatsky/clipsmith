from typing import List
from ...domain.ports.repository_ports import (
    ContentModerationRepositoryPort,
    VideoRepositoryPort,
)
from ...application.services.content_moderation_service import (
    AIModerationService,
    HumanModerationService,
)


class ContentModerationUseCase:
    """Use case for content moderation workflow."""

    def __init__(
        self,
        moderation_repo: ContentModerationRepositoryPort,
        video_repo: VideoRepositoryPort,
    ):
        self.moderation_repo = moderation_repo
        self.video_repo = video_repo
        self.ai_service = AIModerationService(moderation_repo)
        self.human_service = HumanModerationService(moderation_repo)

    def moderate_video_on_upload(
        self, video_id: str, title: str, description: str, thumbnail_url: str
    ):
        """Automatically moderate video when uploaded."""
        # Run AI analysis on video
        moderation = self.ai_service.analyze_video(
            video_id, title, description, thumbnail_url
        )

        # Save moderation result
        saved_moderation = self.moderation_repo.save(moderation)

        # If automatically rejected, update video status
        if moderation.status.value == "rejected":
            # In a real system, you'd update the video status to REJECTED
            # For now, we'll just log it
            print(f"Video {video_id} automatically rejected due to policy violations")

        return saved_moderation

    def moderate_comment_on_create(self, comment_id: str, content: str, user_id: str):
        """Automatically moderate comment when created."""
        moderation = self.ai_service.analyze_comment(comment_id, content, user_id)

        # Save moderation result
        saved_moderation = self.moderation_repo.save(moderation)

        # If automatically rejected, comment would need to be hidden
        if moderation.status.value == "rejected":
            print(
                f"Comment {comment_id} automatically rejected due to policy violations"
            )

        return saved_moderation

    def get_pending_reviews(self, reviewer_id: str, limit: int = 50):
        """Get content pending human review for a moderator."""
        return self.human_service.review_pending_content(limit)

    def approve_content(self, moderation_id: str, reviewer_id: str, notes: str = None):
        """Approve content after human review."""
        return self.human_service.approve_content(moderation_id, reviewer_id, notes)

    def reject_content(
        self,
        moderation_id: str,
        reviewer_id: str,
        reason: str,
        severity: str,
        notes: str = None,
    ):
        """Reject content after human review."""
        from ...domain.entities.content_moderation import (
            ModerationReason,
            ModerationSeverity,
        )

        # Convert string to enum
        try:
            reason_enum = ModerationReason(reason)
            severity_enum = ModerationSeverity(severity)
        except ValueError as e:
            raise ValueError(f"Invalid reason or severity: {e}")

        return self.human_service.reject_content(
            moderation_id, reviewer_id, reason_enum, severity_enum, notes
        )

    def get_moderation_statistics(self, days: int = 30):
        """Get moderation statistics for admin dashboard."""
        return self.moderation_repo.get_statistics(days)

    def get_content_moderation_history(
        self, content_id: str, content_type: str = "video"
    ):
        """Get moderation history for specific content."""
        return self.moderation_repo.get_moderations_by_content_id(
            content_id, content_type
        )

    def bulk_moderate_videos(self, video_data_list: List[dict]):
        """Bulk moderate multiple videos (useful for batch processing)."""
        results = []

        for video_data in video_data_list:
            try:
                moderation = self.moderate_video_on_upload(
                    video_data["id"],
                    video_data["title"],
                    video_data["description"],
                    video_data.get("thumbnail_url"),
                )
                results.append(
                    {
                        "video_id": video_data["id"],
                        "moderation_id": moderation.id,
                        "status": moderation.status.value,
                        "success": True,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "video_id": video_data["id"],
                        "moderation_id": None,
                        "status": "error",
                        "success": False,
                        "error": str(e),
                    }
                )

        return results
