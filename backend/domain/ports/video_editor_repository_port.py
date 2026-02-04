from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from ..entities.video_editor import (
    VideoProject,
    VideoEditorAsset,
    VideoEditorTransition,
    VideoEditorTrack,
    VideoEditorCaption,
    VideoProjectStatus,
)


class VideoEditorRepositoryPort(ABC):
    """Repository port for video editor operations."""

    # Project operations
    @abstractmethod
    def save_project(self, project: VideoProject) -> VideoProject:
        """Save or update a video project."""
        pass

    @abstractmethod
    def get_project_by_id(self, project_id: str) -> Optional[VideoProject]:
        """Get a specific project by ID."""
        pass

    @abstractmethod
    def get_user_projects(
        self, user_id: str, limit: int = 20, status: Optional[VideoProjectStatus] = None
    ) -> List[VideoProject]:
        """Get user's video editor projects."""
        pass

    @abstractmethod
    def get_all_projects(self, limit: int = 50) -> List[VideoProject]:
        """Get all video editor projects."""
        pass

    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        """Delete a video editor project."""
        pass

    # Asset operations
    @abstractmethod
    def save_asset(self, asset: VideoEditorAsset) -> VideoEditorAsset:
        """Save or update an editor asset."""
        pass

    @abstractmethod
    def get_project_assets(
        self, project_id: str, asset_type: Optional[str] = None
    ) -> List[VideoEditorAsset]:
        """Get all assets for a specific project."""
        pass

    @abstractmethod
    def get_asset_by_id(self, asset_id: str) -> Optional[VideoEditorAsset]:
        """Get specific asset by ID."""
        pass

    @abstractmethod
    def delete_asset(self, asset_id: str) -> bool:
        """Delete an asset."""
        pass

    # Transition operations
    @abstractmethod
    def save_transition(
        self, transition: VideoEditorTransition
    ) -> VideoEditorTransition:
        """Save or update a transition."""
        pass

    @abstractmethod
    def get_project_transitions(self, project_id: str) -> List[VideoEditorTransition]:
        """Get all transitions for a project."""
        pass

    # Track operations
    @abstractmethod
    def save_track(self, track: VideoEditorTrack) -> VideoEditorTrack:
        """Save or update a track."""
        pass

    @abstractmethod
    def get_project_tracks(self, project_id: str) -> List[VideoEditorTrack]:
        """Get all tracks for a project."""
        pass

    # Caption operations
    @abstractmethod
    def save_caption(self, caption: VideoEditorCaption) -> VideoEditorCaption:
        """Save or update a caption."""
        pass

    @abstractmethod
    def get_project_captions(
        self, project_id: str, video_asset_id: str
    ) -> List[VideoEditorCaption]:
        """Get all captions for a specific video in a project."""
        pass

    @abstractmethod
    def delete_caption(self, caption_id: str) -> bool:
        """Delete a caption."""
        pass
