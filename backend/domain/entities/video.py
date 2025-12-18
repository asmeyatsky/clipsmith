from dataclasses import dataclass, replace
from enum import Enum
from ..base import Entity

class VideoStatus(str, Enum):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"

@dataclass(frozen=True, kw_only=True)
class Video(Entity):
    title: str
    description: str
    creator_id: str
    url: str | None = None
    thumbnail_url: str | None = None  # New field
    status: VideoStatus = VideoStatus.UPLOADING
    views: int = 0
    likes: int = 0
    
    def mark_as_processing(self) -> 'Video':
        return replace(self, status=VideoStatus.PROCESSING)

    def mark_as_ready(self, url: str, thumbnail_url: str) -> 'Video': # Updated method
        return replace(self, status=VideoStatus.READY, url=url, thumbnail_url=thumbnail_url)

    def mark_as_failed(self) -> 'Video':
        return replace(self, status=VideoStatus.FAILED)
