from pydantic import BaseModel
from typing import List, Generic, TypeVar
from ...domain.entities.video import VideoStatus

class VideoCreateDTO(BaseModel):
    title: str
    description: str
    creator_id: str

class VideoResponseDTO(BaseModel):
    id: str
    title: str
    description: str
    status: VideoStatus
    url: str | None
    thumbnail_url: str | None
    views: int
    likes: int

class PaginatedVideoResponseDTO(BaseModel):
    items: List[VideoResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int
