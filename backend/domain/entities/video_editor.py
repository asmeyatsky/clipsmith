from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid


class VideoProjectStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class VideoProjectPermission(str, Enum):
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class VideoEditorTransitionType(str, Enum):
    CUT = "cut"
    TRIM = "trim"
    SPLIT = "split"
    MERGE = "merge"
    CLONE = "clone"
    ROTATE = "rotate"
    SCALE = "scale"
    FILTER = "filter"
    TEXT_ADD = "text_add"
    EFFECT_APPLY = "effect_apply"
    AUDIO_ADJUST = "audio_adjust"


@dataclass(frozen=True, kw_only=True)
class VideoProject:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    video_id: Optional[str] = None  # Base video this project edits
    title: str = "Untitled Project"
    description: Optional[str] = None
    status: VideoProjectStatus = VideoProjectStatus.DRAFT
    thumbnail_url: Optional[str] = None  # Generated thumbnail of project
    duration: float = 0.0  # Project duration in seconds
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    settings: Optional[Dict[str, Any]] = None  # Editor settings (zoom, quality, etc.)
    metadata: Optional[Dict[str, Any]] = None  # Project metadata
    permission: VideoProjectPermission = VideoProjectPermission.PRIVATE

    def add_video(self, video_id: str) -> "VideoProject":
        """Add video to project."""
        # This would update project metadata like video count, total duration
        return replace(self, updated_at=datetime.utcnow())

    def remove_video(self, video_id: str) -> "VideoProject":
        """Remove video from project."""
        return replace(self, updated_at=datetime.utcnow())

    def update_thumbnail(self, thumbnail_url: str) -> "VideoProject":
        """Update project thumbnail."""
        return replace(self, thumbnail_url=thumbnail_url, updated_at=datetime.utcnow())

    def update_settings(self, **kwargs) -> "VideoProject":
        """Update editor settings."""
        return replace(
            self,
            settings={**(self.settings or {}), **kwargs},
            updated_at=datetime.utcnow(),
        )

    def set_permission(self, permission: VideoProjectPermission) -> "VideoProject":
        """Update project permission."""
        return replace(self, permission=permission, updated_at=datetime.utcnow())

    def publish(self) -> "VideoProject":
        """Publish project as completed video."""
        return replace(
            self,
            status=VideoProjectStatus.PUBLISHED,
            published_at=datetime.utcnow(),
            permission=VideoProjectPermission.PUBLIC,
        )

    def archive(self) -> "VideoProject":
        """Archive project."""
        return replace(
            self,
            status=VideoProjectStatus.ARCHIVED,
            permission=VideoProjectPermission.PRIVATE,
            updated_at=datetime.utcnow(),
        )


@dataclass(frozen=True, kw_only=True)
class VideoEditorAsset:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    type: str  # "video", "image", "audio", "text", "effect", "transition", "caption"
    name: str
    original_url: Optional[str] = None  # URL of original asset if applicable
    storage_url: Optional[str] = None  # Cloud storage URL
    metadata: Optional[Dict[str, Any]] = None
    duration: Optional[float] = None  # Duration for audio/video assets
    created_at: datetime = field(default_factory=datetime.utcnow)

    def set_storage_url(self, storage_url: str) -> "VideoEditorAsset":
        """Set cloud storage URL."""
        return replace(self, storage_url=storage_url)


@dataclass(frozen=True, kw_only=True)
class VideoEditorEffect:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # "filter", "transition", "color_correction", "blur", "audio_enhancement", "visual_effect"
    parameters: Optional[Dict[str, Any]] = None  # Effect-specific parameters
    preview_url: Optional[str] = None  # Preview thumbnail URL
    is_premium: bool = False  # Whether this is a premium effect
    created_at: datetime = field(default_factory=datetime.utcnow)


class VideoEditorTransition:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    asset_id: str
    type: VideoEditorTransitionType
    parameters: Optional[Dict[str, Any]] = None
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    easing: str = "linear"  # "linear", "ease-in", "ease-out", "ease-in-out"

    def __init__(
        self,
        type: VideoEditorTransitionType,
        start_time: float,
        end_time: float,
        duration: float,
        easing: str = "linear",
        parameters: Optional[Dict[str, Any]] = None,
    ):
        return replace(
            self,
            type=type,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            easing=easing,
            parameters=parameters,
        )


class VideoEditorTrack:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    asset_id: str
    type: str  # "video", "audio", "text", "caption"
    start_time: float = 0.0
    end_time: float = 0.0
    content: Optional[Dict[str, Any]] = (
        None  # Track content (text, position, effects, etc.)
    )

    def __init__(
        self,
        project_id: str,
        asset_id: str,
        type: str,
        start_time: float,
        end_time: float,
        content: Optional[Dict[str, Any]] = None,
    ):
        return replace(
            self,
            project_id=project_id,
            asset_id=asset_id,
            type=type,
            start_time=start_time,
            end_time=end_time,
            content=content,
        )


class VideoEditorCaption:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    video_asset_id: str
    start_time: float = 0.0
    end_time: float = 0.0
    text: str = ""
    style: Optional[Dict[str, Any]] = (
        None  # Caption styling (font, color, position, etc.)
    )
    is_auto_generated: bool = False
    language: str = "en"  # ISO language code

    def __init__(
        self,
        project_id: str,
        video_asset_id: str,
        start_time: float,
        end_time: float,
        text: str,
        style: Optional[Dict[str, Any]] = None,
        is_auto_generated: bool = False,
        language: str = "en",
    ):
        return replace(
            self,
            project_id=project_id,
            video_asset_id=video_asset_id,
            start_time=start_time,
            end_time=end_time,
            text=text,
            style=style,
            is_auto_generated=is_auto_generated,
            language=language,
        )
