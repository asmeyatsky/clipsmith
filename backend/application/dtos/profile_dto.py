from pydantic import BaseModel
from typing import List
from .video_dto import VideoResponseDTO

class PublicProfileDTO(BaseModel):
    id: str
    username: str
    # We can add bio, avatar_url, etc. later

class ProfileResponseDTO(BaseModel):
    user: PublicProfileDTO
    videos: List[VideoResponseDTO]
