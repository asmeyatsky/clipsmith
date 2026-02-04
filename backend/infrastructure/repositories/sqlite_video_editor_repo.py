from typing import List, Optional
from sqlmodel import Session, select, func, and_, desc
from ...domain.entities.video_editor import (
    VideoProject,
    VideoEditorAsset,
    VideoEditorTransition,
    VideoEditorTrack,
    VideoEditorCaption,
    VideoProjectStatus,
)
from ...domain.ports.video_editor_repository_port import VideoEditorRepositoryPort
from .database import engine
from .models import (
    VideoProjectDB,
    VideoEditorAssetDB,
    VideoEditorTransitionDB,
    VideoEditorTrackDB,
    VideoEditorCaptionDB,
)


class SQLiteVideoEditorRepository(VideoEditorRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def save_project(self, project: VideoProject) -> VideoProject:
        project_db = VideoProjectDB.model_validate(project)
        project_db = self.session.merge(project_db)
        self.session.commit()
        self.session.refresh(project_db)
        return VideoProject(**project_db.model_dump())

    def get_project_by_id(self, project_id: str) -> Optional[VideoProject]:
        project_db = self.session.get(VideoProjectDB, project_id)
        if project_db:
            return VideoProject(**project_db.model_dump())
        return None

    def get_user_projects(
        self, user_id: str, limit: int = 20, status: Optional[VideoProjectStatus] = None
    ) -> List[VideoProject]:
        """Get user's video editor projects."""
        query = select(VideoProjectDB).where(VideoProjectDB.user_id == user_id)

        if status:
            status_enum = VideoProjectStatus(status)
            query = query.where(VideoProjectDB.status == status_enum)

        query = query.order_by(VideoProjectDB.updated_at.desc()).limit(limit)

        results = self.session.exec(query).all()
        return [VideoProject(**project.model_dump()) for project in results]

    def get_all_projects(self, limit: int = 50) -> List[VideoProject]:
        """Get all video editor projects."""
        query = (
            select(VideoProjectDB)
            .order_by(VideoProjectDB.created_at.desc())
            .limit(limit)
        )

        results = self.session.exec(query).all()
        return [VideoProject(**project.model_dump()) for project in results]

    def delete_project(self, project_id: str) -> bool:
        """Delete a video editor project."""
        project_db = self.session.get(VideoProjectDB, project_id)
        if project_db:
            self.session.delete(project_db)
            self.session.commit()
            return True
        return False

    def save_asset(self, asset: VideoEditorAsset) -> VideoEditorAsset:
        asset_db = VideoEditorAssetDB.model_validate(asset)
        asset_db = self.session.merge(asset_db)
        self.session.commit()
        self.session.refresh(asset_db)
        return VideoEditorAsset(**asset_db.model_dump())

    def get_project_assets(
        self, project_id: str, asset_type: Optional[str] = None
    ) -> List[VideoEditorAsset]:
        """Get all assets for a specific project."""
        query = select(VideoEditorAssetDB).where(
            VideoEditorAssetDB.project_id == project_id
        )

        if asset_type:
            query = query.where(VideoEditorAssetDB.type == asset_type)

        query = query.order_by(VideoEditorAssetDB.created_at.desc())

        results = self.session.exec(query).all()
        return [VideoEditorAsset(**asset.model_dump()) for asset in results]

    def get_asset_by_id(self, asset_id: str) -> Optional[VideoEditorAsset]:
        """Get specific asset by ID."""
        asset_db = self.session.get(VideoEditorAssetDB, asset_id)
        if asset_db:
            return VideoEditorAsset(**asset_db.model_dump())
        return None

    def delete_asset(self, asset_id: str) -> bool:
        """Delete an asset."""
        asset_db = self.session.get(VideoEditorAssetDB, asset_id)
        if asset_db:
            self.session.delete(asset_db)
            self.session.commit()
            return True
        return False

    def save_transition(
        self, transition: VideoEditorTransition
    ) -> VideoEditorTransition:
        transition_db = VideoEditorTransitionDB.model_validate(transition)
        transition_db = self.session.merge(transition_db)
        self.session.commit()
        self.session.refresh(transition_db)
        return VideoEditorTransition(**transition_db.model_dump())

    def get_project_transitions(self, project_id: str) -> List[VideoEditorTransition]:
        """Get all transitions for a project."""
        query = select(VideoEditorTransitionDB).where(
            VideoEditorTransitionDB.project_id == project_id
        )
        query = query.order_by(VideoEditorTransitionDB.start_time.asc())

        results = self.session.exec(query).all()
        return [
            VideoEditorTransition(**transition.model_dump()) for transition in results
        ]

    def save_track(self, track: VideoEditorTrack) -> VideoEditorTrack:
        track_db = VideoEditorTrackDB.model_validate(track)
        track_db = self.session.merge(track_db)
        self.session.commit()
        self.session.refresh(track_db)
        return VideoEditorTrack(**track.model_dump())

    def get_project_tracks(self, project_id: str) -> List[VideoEditorTrack]:
        """Get all tracks for a project."""
        query = select(VideoEditorTrackDB).where(
            VideoEditorTrackDB.project_id == project_id
        )
        query = query.order_by(VideoEditorTrackDB.start_time.asc())

        results = self.session.exec(query).all()
        return [VideoEditorTrack(**track.model_dump()) for track in results]

    def save_caption(self, caption: VideoEditorCaption) -> VideoEditorCaption:
        caption_db = VideoEditorCaptionDB.model_validate(caption)
        caption_db = self.session.merge(caption_db)
        self.session.commit()
        self.session.refresh(caption_db)
        return VideoEditorCaption(**caption_db.model_dump())

    def get_project_captions(
        self, project_id: str, video_asset_id: str
    ) -> List[VideoEditorCaption]:
        """Get all captions for a specific video in a project."""
        query = select(VideoEditorCaptionDB).where(
            and_(
                VideoEditorCaptionDB.project_id == project_id,
                VideoEditorCaptionDB.video_asset_id == video_asset_id,
            )
        )
        query = query.order_by(VideoEditorCaptionDB.start_time.asc())

        results = self.session.exec(query).all()
        return [VideoEditorCaption(**caption.model_dump()) for caption in results]

    def delete_caption(self, caption_id: str) -> bool:
        """Delete a caption."""
        caption_db = self.session.get(VideoEditorCaptionDB, caption_id)
        if caption_db:
            self.session.delete(caption_db)
            self.session.commit()
            return True
        return False
