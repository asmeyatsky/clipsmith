from pydantic import BaseModel
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
    views: int
    likes: int
