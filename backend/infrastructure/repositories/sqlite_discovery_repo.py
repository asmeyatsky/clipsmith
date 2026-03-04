from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlmodel import Session, select, func
from sqlalchemy import text
from .models import (
    PlaylistDB,
    PlaylistItemDB,
    PlaylistCollaboratorDB,
    UserPreferencesDB,
    FavoriteCreatorDB,
    TrafficSourceDB,
    RetentionDataDB,
    PostingTimeRecommendationDB,
    VideoDB,
)


class SQLiteDiscoveryRepository:
    def __init__(self, session: Session):
        self.session = session

    # ---- Playlist operations ----

    def save_playlist(self, playlist: PlaylistDB) -> PlaylistDB:
        playlist = self.session.merge(playlist)
        self.session.commit()
        self.session.refresh(playlist)
        return playlist

    def get_playlist(self, playlist_id: str) -> Optional[PlaylistDB]:
        return self.session.get(PlaylistDB, playlist_id)

    def get_playlists_by_user(self, user_id: str) -> List[PlaylistDB]:
        statement = (
            select(PlaylistDB)
            .where(PlaylistDB.creator_id == user_id)
            .order_by(PlaylistDB.created_at.desc())
        )
        return list(self.session.exec(statement).all())

    def get_playlists_by_creator(self, creator_id: str) -> List[PlaylistDB]:
        return self.get_playlists_by_user(creator_id)

    def get_public_playlists(
        self, limit: int = 20, offset: int = 0
    ) -> List[PlaylistDB]:
        statement = (
            select(PlaylistDB)
            .where(PlaylistDB.is_public == True)
            .order_by(PlaylistDB.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def delete_playlist(self, playlist_id: str) -> bool:
        playlist = self.session.get(PlaylistDB, playlist_id)
        if playlist:
            self.session.delete(playlist)
            self.session.commit()
            return True
        return False

    def save_playlist_item(self, item: PlaylistItemDB) -> PlaylistItemDB:
        item = self.session.merge(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def get_playlist_items(self, playlist_id: str) -> List[PlaylistItemDB]:
        statement = (
            select(PlaylistItemDB)
            .where(PlaylistItemDB.playlist_id == playlist_id)
            .order_by(PlaylistItemDB.position.asc())
        )
        return list(self.session.exec(statement).all())

    def remove_playlist_item(self, playlist_id: str, video_id: str) -> bool:
        statement = select(PlaylistItemDB).where(
            PlaylistItemDB.playlist_id == playlist_id,
            PlaylistItemDB.video_id == video_id,
        )
        item = self.session.exec(statement).first()
        if item:
            self.session.delete(item)
            self.session.commit()
            return True
        return False

    def save_playlist_collaborator(
        self, collaborator: PlaylistCollaboratorDB
    ) -> PlaylistCollaboratorDB:
        collaborator = self.session.merge(collaborator)
        self.session.commit()
        self.session.refresh(collaborator)
        return collaborator

    def get_playlist_collaborator(
        self, playlist_id: str, user_id: str
    ) -> Optional[PlaylistCollaboratorDB]:
        statement = select(PlaylistCollaboratorDB).where(
            PlaylistCollaboratorDB.playlist_id == playlist_id,
            PlaylistCollaboratorDB.user_id == user_id,
        )
        return self.session.exec(statement).first()

    def remove_playlist_collaborator(
        self, playlist_id: str, user_id: str
    ) -> bool:
        collaborator = self.get_playlist_collaborator(playlist_id, user_id)
        if collaborator:
            self.session.delete(collaborator)
            self.session.commit()
            return True
        return False

    # ---- User Preferences operations ----

    def get_user_preferences(self, user_id: str) -> Optional[UserPreferencesDB]:
        statement = select(UserPreferencesDB).where(
            UserPreferencesDB.user_id == user_id
        )
        return self.session.exec(statement).first()

    def save_user_preferences(
        self, preferences: UserPreferencesDB
    ) -> UserPreferencesDB:
        preferences = self.session.merge(preferences)
        self.session.commit()
        self.session.refresh(preferences)
        return preferences

    def update_user_preferences(
        self, user_id: str, preferences_data: Dict[str, Any]
    ) -> None:
        import json

        prefs = self.get_user_preferences(user_id)
        if prefs:
            if "interest_weight" in preferences_data:
                prefs.interest_weight = preferences_data["interest_weight"]
            if "community_weight" in preferences_data:
                prefs.community_weight = preferences_data["community_weight"]
            if "virality_weight" in preferences_data:
                prefs.virality_weight = preferences_data["virality_weight"]
            if "freshness_weight" in preferences_data:
                prefs.freshness_weight = preferences_data["freshness_weight"]
            if "preferred_categories" in preferences_data:
                prefs.preferred_categories = json.dumps(
                    preferences_data["preferred_categories"]
                )
            if "preferred_languages" in preferences_data:
                prefs.preferred_languages = json.dumps(
                    preferences_data["preferred_languages"]
                )
            if "location" in preferences_data:
                prefs.location = preferences_data["location"]
            prefs.updated_at = datetime.utcnow()
            self.session.add(prefs)
            self.session.commit()

    # ---- Favorite Creator operations ----

    def get_favorite_creator(
        self, user_id: str, creator_id: str
    ) -> Optional[FavoriteCreatorDB]:
        statement = select(FavoriteCreatorDB).where(
            FavoriteCreatorDB.user_id == user_id,
            FavoriteCreatorDB.creator_id == creator_id,
        )
        return self.session.exec(statement).first()

    def save_favorite_creator(
        self, favorite: FavoriteCreatorDB
    ) -> FavoriteCreatorDB:
        favorite = self.session.merge(favorite)
        self.session.commit()
        self.session.refresh(favorite)
        return favorite

    def delete_favorite_creator(self, user_id: str, creator_id: str) -> bool:
        favorite = self.get_favorite_creator(user_id, creator_id)
        if favorite:
            self.session.delete(favorite)
            self.session.commit()
            return True
        return False

    def get_favorite_creators(self, user_id: str) -> List[FavoriteCreatorDB]:
        statement = (
            select(FavoriteCreatorDB)
            .where(FavoriteCreatorDB.user_id == user_id)
            .order_by(FavoriteCreatorDB.created_at.desc())
        )
        return list(self.session.exec(statement).all())

    # ---- Discovery Score helper methods ----

    def calculate_interest_score(self, video_id: str, user_id: str) -> float:
        """Calculate interest-based relevance score. Returns 0.0 to 1.0."""
        # Simple heuristic: check if user has preferences matching the video
        return 0.5  # Default mid-range score

    def calculate_community_score(self, video_id: str, user_id: str) -> float:
        """Calculate community-based relevance score. Returns 0.0 to 1.0."""
        return 0.5

    def calculate_virality_score(self, video_id: str) -> float:
        """Calculate virality score based on video engagement. Returns 0.0 to 1.0."""
        video = self.session.get(VideoDB, video_id)
        if not video:
            return 0.0
        # Simple heuristic based on views and likes
        views = video.views or 0
        likes = video.likes or 0
        if views == 0:
            return 0.0
        engagement = likes / views if views > 0 else 0
        # Normalize: cap at 1.0
        return min(engagement * 10, 1.0)

    def calculate_freshness_score(self, video_id: str) -> float:
        """Calculate freshness score based on video recency. Returns 0.0 to 1.0."""
        video = self.session.get(VideoDB, video_id)
        if not video:
            return 0.0
        age_hours = (datetime.utcnow() - video.created_at).total_seconds() / 3600
        # Videos less than 24h old get full freshness, decaying over 7 days
        if age_hours <= 24:
            return 1.0
        if age_hours >= 168:  # 7 days
            return 0.0
        return max(0.0, 1.0 - (age_hours - 24) / 144)

    # ---- Traffic Source operations ----

    def save_traffic_source(self, source: TrafficSourceDB) -> TrafficSourceDB:
        source = self.session.merge(source)
        self.session.commit()
        self.session.refresh(source)
        return source

    def get_traffic_sources(self, video_id: str) -> List[TrafficSourceDB]:
        statement = (
            select(TrafficSourceDB)
            .where(TrafficSourceDB.video_id == video_id)
            .order_by(TrafficSourceDB.created_at.desc())
        )
        return list(self.session.exec(statement).all())

    # ---- Retention Data operations ----

    def save_retention_data(self, retention: RetentionDataDB) -> RetentionDataDB:
        retention = self.session.merge(retention)
        self.session.commit()
        self.session.refresh(retention)
        return retention

    def get_retention_data(self, video_id: str) -> List[RetentionDataDB]:
        statement = (
            select(RetentionDataDB)
            .where(RetentionDataDB.video_id == video_id)
            .order_by(RetentionDataDB.second_offset.asc())
        )
        return list(self.session.exec(statement).all())

    # ---- Posting Time Recommendation operations ----

    def save_posting_recommendation(
        self, recommendation: PostingTimeRecommendationDB
    ) -> PostingTimeRecommendationDB:
        recommendation = self.session.merge(recommendation)
        self.session.commit()
        self.session.refresh(recommendation)
        return recommendation

    def get_posting_recommendations(
        self, user_id: str
    ) -> List[PostingTimeRecommendationDB]:
        statement = (
            select(PostingTimeRecommendationDB)
            .where(PostingTimeRecommendationDB.user_id == user_id)
            .order_by(PostingTimeRecommendationDB.engagement_score.desc())
        )
        return list(self.session.exec(statement).all())

    def get_video_performance_by_time(
        self, user_id: str
    ) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """Get aggregated video performance data grouped by day of week and hour.

        Returns a dict keyed by (day_of_week, hour) with performance metrics.
        """
        statement = (
            select(VideoDB)
            .where(VideoDB.creator_id == user_id)
            .order_by(VideoDB.created_at.desc())
        )
        videos = self.session.exec(statement).all()

        performance: Dict[Tuple[int, int], Dict[str, Any]] = {}
        for video in videos:
            day = video.created_at.weekday()  # 0=Monday
            hour = video.created_at.hour
            key = (day, hour)

            if key not in performance:
                performance[key] = {
                    "total_engagement": 0.0,
                    "sample_size": 0,
                    "avg_engagement": 0.0,
                }

            views = video.views or 0
            likes = video.likes or 0
            engagement = (likes / views) if views > 0 else 0.0
            performance[key]["total_engagement"] += engagement
            performance[key]["sample_size"] += 1
            performance[key]["avg_engagement"] = (
                performance[key]["total_engagement"]
                / performance[key]["sample_size"]
            )

        return performance
