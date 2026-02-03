from typing import List, Optional, Set
from datetime import datetime
from ...domain.ports.repository_ports import (
    VideoRepositoryPort,
    InteractionRepositoryPort,
    UserRepositoryPort,
)
from ...domain.entities.video import Video
from ..services.recommendation_engine import RecommendationEngine


class GetPersonalizedFeedUseCase:
    """Use case for generating personalized video feeds."""

    def __init__(
        self,
        video_repo: VideoRepositoryPort,
        interaction_repo: InteractionRepositoryPort,
        user_repo: UserRepositoryPort,
    ):
        self.video_repo = video_repo
        self.interaction_repo = interaction_repo
        self.user_repo = user_repo
        self.recommendation_engine = RecommendationEngine()

    def execute(
        self,
        user_id: str,
        feed_type: str = "foryou",  # "foryou", "following", "trending"
        page: int = 1,
        page_size: int = 20,
    ) -> List[Video]:
        """
        Generate personalized feed based on feed type.

        Args:
            user_id: Current user ID
            feed_type: Type of feed ("foryou", "following", "trending")
            page: Page number for pagination
            page_size: Number of videos per page

        Returns:
            List of Video objects
        """

        # Get user's following list
        user_following = self._get_user_following(user_id)

        # Get user interaction history
        user_interactions = self.interaction_repo.get_user_interactions(user_id)

        # Get all ready videos for recommendations
        all_videos = self.video_repo.find_all(offset=0, limit=1000)  # Get larger pool
        all_interactions = self.interaction_repo.get_all_interactions(limit=10000)

        if feed_type == "foryou":
            feed_videos = self.recommendation_engine.get_for_you_feed(
                user_id=user_id,
                user_interactions=user_interactions,
                all_videos=all_videos,
                all_interactions=all_interactions,
                user_following=user_following,
                include_trending=True,
            )

        elif feed_type == "following":
            # Get videos from creators user follows
            feed_videos = self.video_repo.get_videos_from_creators(
                creator_ids=list(user_following),
                offset=(page - 1) * page_size,
                limit=page_size,
            )

        elif feed_type == "trending":
            # Get trending videos
            trending_videos = self.recommendation_engine.get_trending_videos(
                all_videos=all_videos,
                all_interactions=all_interactions,
                hours=24,  # Last 24 hours
            )
            feed_videos = trending_videos

        else:
            # Default to foryou
            feed_videos = self.recommendation_engine.get_for_you_feed(
                user_id=user_id,
                user_interactions=user_interactions,
                all_videos=all_videos,
                all_interactions=all_interactions,
                user_following=user_following,
            )

        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        return feed_videos[start_idx:end_idx]

    def get_feed_count(self, user_id: str, feed_type: str = "foryou") -> int:
        """Get total count of videos in feed type."""

        if feed_type == "following":
            user_following = self._get_user_following(user_id)
            return self.video_repo.count_videos_from_creators(list(user_following))

        elif feed_type == "trending":
            # For trending, we return a fixed number
            all_videos = self.video_repo.find_all(offset=0, limit=1000)
            all_interactions = self.interaction_repo.get_all_interactions(limit=10000)
            trending_videos = self.recommendation_engine.get_trending_videos(
                all_videos=all_videos, all_interactions=all_interactions, hours=24
            )
            return len(trending_videos)

        # For "foryou" feed, we return a reasonable limit
        return 50  # We limit to 50 recommendations per user

    def _get_user_following(self, user_id: str) -> Set[str]:
        """Get set of creator IDs that user follows."""
        following_interactions = self.interaction_repo.get_user_following(user_id)
        return set(interaction.target_user_id for interaction in following_interactions)
