from typing import List, Optional
from ...domain.entities.video_editor import (
    VideoProject,
    VideoEditorAsset,
    VideoEditorTransition,
    VideoEditorTrack,
    VideoEditorCaption,
    VideoProjectStatus,
)
from ...domain.ports.video_editor_repository_port import VideoEditorRepositoryPort


class VideoEditorService:
    """Service layer for video editor operations."""

    def __init__(self, repository: VideoEditorRepositoryPort):
        self.repository = repository

    # Project operations
    def create_project(
        self,
        user_id: str,
        title: str = "Untitled Project",
        description: Optional[str] = None,
    ) -> VideoProject:
        """Create a new video project."""
        project = VideoProject(user_id=user_id, title=title, description=description)
        return self.repository.save_project(project)

    def get_project(self, project_id: str) -> Optional[VideoProject]:
        """Get a specific project."""
        return self.repository.get_project_by_id(project_id)

    def get_user_projects(
        self, user_id: str, limit: int = 20, status: Optional[VideoProjectStatus] = None
    ) -> List[VideoProject]:
        """Get user's projects."""
        return self.repository.get_user_projects(user_id, limit, status)

    def update_project_title(
        self, project_id: str, title: str
    ) -> Optional[VideoProject]:
        """Update project title."""
        project = self.repository.get_project_by_id(project_id)
        if not project:
            return None

        updated_project = project.replace(title=title)
        return self.repository.save_project(updated_project)

    def update_project_description(
        self, project_id: str, description: str
    ) -> Optional[VideoProject]:
        """Update project description."""
        project = self.repository.get_project_by_id(project_id)
        if not project:
            return None

        updated_project = project.replace(description=description)
        return self.repository.save_project(updated_project)

    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        return self.repository.delete_project(project_id)

    # Asset operations
    def upload_asset(
        self,
        project_id: str,
        asset_type: str,
        filename: str,
        file_size: int,
        mime_type: str,
        url: str,
    ) -> VideoEditorAsset:
        """Upload a new asset to a project."""
        asset = VideoEditorAsset(
            project_id=project_id,
            type=asset_type,
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            url=url,
        )
        return self.repository.save_asset(asset)

    def get_project_assets(
        self, project_id: str, asset_type: Optional[str] = None
    ) -> List[VideoEditorAsset]:
        """Get all assets for a project."""
        return self.repository.get_project_assets(project_id, asset_type)

    def get_asset(self, asset_id: str) -> Optional[VideoEditorAsset]:
        """Get a specific asset by ID."""
        return self.repository.get_asset_by_id(asset_id)

    def delete_asset(self, asset_id: str) -> bool:
        """Delete an asset."""
        return self.repository.delete_asset(asset_id)

    # Transition operations
    def add_transition(
        self,
        project_id: str,
        transition_type: str,
        start_time: float,
        end_time: float,
        duration: float,
        parameters: Optional[dict] = None,
    ) -> VideoEditorTransition:
        """Add a transition to a project."""
        transition = VideoEditorTransition(
            project_id=project_id,
            type=transition_type,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            parameters=parameters,
        )
        return self.repository.save_transition(transition)

    def get_project_transitions(
        self, project_id: str
    ) -> List[VideoEditorTransition]:
        """Get all transitions for a project."""
        return self.repository.get_project_transitions(project_id)

    # Track operations
    def add_track(
        self,
        project_id: str,
        asset_id: str,
        track_type: str,
        start_time: float,
        end_time: float,
    ) -> VideoEditorTrack:
        """Add a track to a project."""
        track = VideoEditorTrack(
            project_id=project_id,
            asset_id=asset_id,
            type=track_type,
            start_time=start_time,
            end_time=end_time,
        )
        return self.repository.save_track(track)

    def get_project_tracks(self, project_id: str) -> List[VideoEditorTrack]:
        """Get all tracks for a project."""
        return self.repository.get_project_tracks(project_id)

    # Caption operations
    def add_caption(
        self,
        project_id: str,
        video_asset_id: str,
        text: str,
        start_time: float,
        end_time: float,
    ) -> VideoEditorCaption:
        """Add a caption to a video."""
        caption = VideoEditorCaption(
            project_id=project_id,
            video_asset_id=video_asset_id,
            text=text,
            start_time=start_time,
            end_time=end_time,
        )
        return self.repository.save_caption(caption)

    def get_project_captions(
        self, project_id: str, video_asset_id: str
    ) -> List[VideoEditorCaption]:
        """Get all captions for a video."""
        return self.repository.get_project_captions(project_id, video_asset_id)

    def get_caption(self, caption_id: str) -> Optional[VideoEditorCaption]:
        """Get a specific caption by ID."""
        return self.repository.get_caption_by_id(caption_id)

    def delete_caption(self, caption_id: str) -> bool:
        """Delete a caption."""
        return self.repository.delete_caption(caption_id)
