from ...domain.ports.repository_ports import VideoRepositoryPort
from ...domain.ports.storage_port import StoragePort
from ...domain.entities.video import Video
from ..dtos.video_dto import VideoCreateDTO, VideoResponseDTO
from typing import BinaryIO
import uuid

class UploadVideoUseCase:
    def __init__(self, video_repo: VideoRepositoryPort, storage_adapter: StoragePort):
        self._video_repo = video_repo
        self._storage_adapter = storage_adapter

    async def execute(self, dto: VideoCreateDTO, file_data: BinaryIO, filename: str) -> VideoResponseDTO:
        # Generate unique filename to prevent collisions
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Save file to storage
        video_url = await self._storage_adapter.save(unique_filename, file_data)
        
        # Create domain entity
        video = Video(
            title=dto.title,
            description=dto.description,
            creator_id=dto.creator_id,
            url=video_url,
            status="READY" # For now we skip processing state
        )
        
        # Save to repo
        saved_video = await self._video_repo.save(video)
        
        # Return DTO
        return VideoResponseDTO(
            id=saved_video.id,
            title=saved_video.title,
            description=saved_video.description,
            status=saved_video.status,
            url=saved_video.url,
            views=saved_video.views,
            likes=saved_video.likes
        )
